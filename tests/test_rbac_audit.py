"""TC-Sec-04 (PRJ-SR-003) and TC-Sec-07 (PRJ-SR-006)."""
import json
from datetime import datetime, timezone
from unittest.mock import patch

from flask import Flask, jsonify

from modules import audit
from modules.audit_routes import audit_bp
from modules.rbac import admin_required


class FakeAuditRepo:
    def __init__(self):
        self.entries = []

    def insert(self, user_id, action, details):
        self.entries.append({"user_id": user_id, "action": action, "details": details})

    def recent(self, limit):
        rows = [
            {"id": i + 1, "user_id": e["user_id"], "user_email": "admin@example.com",
             "action": e["action"], "details": e["details"],
             "created_at": datetime(2026, 11, 6, 10, 0, tzinfo=timezone.utc)}
            for i, e in enumerate(self.entries)
        ]
        return list(reversed(rows))[:limit]


def _client(role=None):
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(audit_bp)

    @app.get("/login")
    def login():
        return "login"

    @app.get("/dashboard")
    def dashboard():
        return "dashboard"

    @app.get("/api/admin/secret")
    @admin_required
    def secret():
        return jsonify(ok=True)

    @app.get("/admin/page")
    @admin_required
    def page():
        return "admin page"

    client = app.test_client()
    if role:
        with client.session_transaction() as s:
            s["user_id"] = 1
            s["role"] = role
    return client


# ---- RBAC ----------------------------------------------------------------
def test_anonymous_gets_401_on_admin_api():
    r = _client().get("/api/admin/secret")
    assert r.status_code == 401 and r.get_json()["error"] == "Authentication required."


def test_passenger_direct_api_call_gets_403():  # AC-SR-003
    r = _client("passenger").get("/api/admin/secret")
    assert r.status_code == 403
    assert r.get_json()["error"] == "Administrator privilege required."


def test_admin_is_allowed():
    assert _client("admin").get("/api/admin/secret").status_code == 200


def test_unknown_or_blank_role_is_refused():
    for role in ("superuser", "", "ADMIN"):
        assert _client(role or None).get("/api/admin/secret").status_code in (401, 403)
        if role:
            assert _client(role).get("/api/admin/secret").status_code == 403


def test_html_admin_page_never_leaks_to_passenger():
    assert _client().get("/admin/page").status_code == 302  # to /login
    with patch("modules.rbac.render_template", return_value="dashboard"):
        r = _client("passenger").get("/admin/page")
    assert r.status_code == 403 and b"admin page" not in r.data
    assert _client("admin").get("/admin/page").status_code == 200


def test_audit_log_endpoint_is_admin_only():
    assert _client().get("/api/admin/audit-log").status_code == 401
    assert _client("passenger").get("/api/admin/audit-log").status_code == 403


# ---- Audit log -----------------------------------------------------------
def test_log_action_records_user_action_and_details():
    repo = FakeAuditRepo()
    audit.log_action(5, "UPDATE_SCHEDULE", {"train_id": 3, "date": "2026-11-20"}, repo=repo)
    entry = repo.entries[0]
    assert entry["user_id"] == 5 and entry["action"] == "UPDATE_SCHEDULE"
    assert json.loads(entry["details"]) == {"date": "2026-11-20", "train_id": 3}


def test_log_action_requires_user_and_action():
    repo = FakeAuditRepo()
    for args in [(None, "X"), (1, ""), (1, "   "), (1, None)]:
        try:
            audit.log_action(*args, repo=repo)
        except ValueError:
            continue
        raise AssertionError(f"accepted {args}")
    assert repo.entries == []


def test_details_are_redacted():  # NF-003 / PRJ-SR-005
    repo = FakeAuditRepo()
    audit.log_action(1, "X", {"password": "hunter2", "card_number": "4111", "nested": {"api_token": "t"},
                              "pnr": "1234567890"}, repo=repo)
    stored = repo.entries[0]["details"]
    for secret in ("hunter2", "4111", '"t"'):
        assert secret not in stored
    assert "1234567890" in stored


def test_recent_entries_newest_first_and_limit_clamped():
    repo = FakeAuditRepo()
    for name in ("A", "B", "C"):
        audit.log_action(1, name, repo=repo)
    assert [e["action"] for e in audit.recent_entries(2, repo=repo)] == ["C", "B"]
    assert len(audit.recent_entries(0, repo=repo)) == 1  # clamped up to 1
    assert audit.recent_entries(10_000, repo=repo)[0]["created_at"].startswith("2026-11-06")
    try:
        audit.recent_entries("abc", repo=repo)
    except ValueError:
        pass
    else:
        raise AssertionError("bad limit accepted")


def test_audit_log_endpoint_returns_entries_to_admin():
    repo = FakeAuditRepo()
    audit.log_action(1, "ADMIN_CANCEL_BOOKING", {"pnr": "1234567890"}, repo=repo)
    with patch("modules.audit._repo", return_value=repo):
        r = _client("admin").get("/api/admin/audit-log?limit=5")
        bad = _client("admin").get("/api/admin/audit-log?limit=abc")
    assert r.status_code == 200
    assert r.get_json()["entries"][0]["action"] == "ADMIN_CANCEL_BOOKING"
    assert bad.status_code == 400
