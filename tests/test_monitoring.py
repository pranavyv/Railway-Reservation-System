"""RRS-NF-002: health check, retries and availability evidence."""
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch

from flask import Flask

import reliability
from modules import monitoring
from modules.ops_routes import ops_bp

NOW = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)


# ---- retry helper ----------------------------------------------------------------
class Boom(Exception):
    pass


def test_retry_succeeds_after_transient_failures_with_doubling_delay():
    attempts, delays = [], []

    def flaky():
        attempts.append(1)
        if len(attempts) < 3:
            raise Boom()
        return "connected"

    assert reliability.retry(flaky, attempts=3, base_delay=0.3, retry_on=(Boom,),
                             sleep=delays.append) == "connected"
    assert delays == [0.3, 0.6]


def test_retry_gives_up_after_the_last_attempt():
    calls = []

    def always():
        calls.append(1)
        raise Boom()

    try:
        reliability.retry(always, attempts=3, retry_on=(Boom,), sleep=lambda s: None)
    except Boom:
        pass
    else:
        raise AssertionError("expected Boom")
    assert len(calls) == 3


def test_retry_does_not_repeat_other_errors():
    calls = []

    def wrong():
        calls.append(1)
        raise KeyError("bug")

    try:
        reliability.retry(wrong, attempts=3, retry_on=(Boom,), sleep=lambda s: None)
    except KeyError:
        pass
    assert len(calls) == 1


# ---- metrics -----------------------------------------------------------------------
def test_metrics_count_requests_and_server_errors():
    clock = iter([100.0, 160.0])
    m = monitoring.Metrics(clock=lambda: next(clock))
    for code in (200, 404, 500, 503):
        m.record(code)
    snap = m.snapshot()
    assert snap == {"uptime_seconds": 60, "requests": 4, "server_errors": 2, "error_rate_percent": 50.0}


def test_empty_metrics_have_zero_error_rate():
    assert monitoring.Metrics().snapshot()["error_rate_percent"] == 0.0


# ---- probe log -----------------------------------------------------------------------
def _log(tmp, rows):
    path = f"{tmp}/logs/uptime.csv"
    for minutes_ago, ok in rows:
        monitoring.append_probe_row(path, ok, 12, now=NOW - timedelta(minutes=minutes_ago))
    return path


def test_availability_percentage_from_log():
    import tempfile
    path = _log(tempfile.mkdtemp(), [(5, True)] * 99 + [(5, False)])
    summary = monitoring.availability_from_log(path, now=NOW)
    assert summary["checks"] == 100 and summary["up"] == 99
    assert summary["availability_percent"] == 99.0


def test_availability_window_and_missing_or_damaged_log():
    import tempfile
    folder = tempfile.mkdtemp()
    path = _log(folder, [(600, False), (30, True), (20, True)])
    assert monitoring.availability_from_log(path, since_hours=1, now=NOW)["checks"] == 2
    assert monitoring.availability_from_log(f"{folder}/nope.csv") is None
    with open(path, "a") as handle:
        handle.write("garbage line\n,,\n")
    assert monitoring.availability_from_log(path, now=NOW)["checks"] == 3  # damaged lines skipped


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200 if self.path == "/health" else 500)
        self.end_headers()
        self.wfile.write(b"x")

    def log_message(self, *args):
        pass


def test_probe_once_reports_up_down_and_unreachable():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    assert monitoring.probe_once(base + "/health")[0] is True
    assert monitoring.probe_once(base + "/broken")[0] is False
    server.shutdown()
    assert monitoring.probe_once(base + "/health", timeout=1)[0] is False


# ---- routes ----------------------------------------------------------------------------
def _client(role=None, log=None):
    app = Flask(__name__)
    app.secret_key = "test"
    app.config.update(UPTIME_LOG=log or "/nonexistent/uptime.csv", AVAILABILITY_TARGET=99.0)
    app.register_blueprint(ops_bp)
    monitoring.register(app)

    @app.get("/login")
    def login():
        return "login"

    client = app.test_client()
    if role:
        with client.session_transaction() as s:
            s["user_id"], s["role"] = 1, role
    return client


def test_health_is_200_when_database_answers_and_503_otherwise_without_leaking():
    with patch("modules.ops_routes._db_ok", return_value=True):
        r = _client().get("/health")
    assert r.status_code == 200 and r.get_json()["status"] == "ok"
    with patch("modules.ops_routes._db_ok", return_value=False):
        r = _client().get("/health")
    assert r.status_code == 503 and r.get_json() == {"status": "degraded", "database": "down"}


def test_db_ok_hides_exception_details():
    app = Flask(__name__)
    app.register_blueprint(ops_bp)
    from modules import ops_routes

    class Broken:
        @staticmethod
        def check_db():
            raise RuntimeError("password=hunter2 host=db.internal")

    with app.app_context(), patch.dict("sys.modules", {"repository.health_repo": Broken}), \
            patch("repository.health_repo", Broken, create=True):
        assert ops_routes._db_ok() is False


def test_availability_report_is_admin_only():
    assert _client().get("/api/admin/availability").status_code == 401
    assert _client("passenger").get("/api/admin/availability").status_code == 403


def test_availability_report_contents():
    import tempfile
    path = _log(tempfile.mkdtemp(), [(5, True)] * 99 + [(5, False)])
    with patch("modules.ops_routes._payment_counts", return_value=(20, 3)):
        data = _client("admin", log=path).get("/api/admin/availability").get_json()
    assert data["probe"]["availability_percent"] == 99.0
    assert data["target_percent"] == 99.0 and data["meets_target"] is True
    assert data["transaction_failure_rate_percent"] == 15.0
    assert "uptime_seconds" in data["process"]


def test_availability_report_without_data_yet():
    with patch("modules.ops_routes._payment_counts", return_value=None):
        data = _client("admin").get("/api/admin/availability").get_json()
    assert data["probe"] is None and data["meets_target"] is None
    assert data["transaction_failure_rate_percent"] is None
