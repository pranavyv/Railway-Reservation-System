"""TC-Sec-05 (PRJ-SR-004): session token is invalidated after the idle timeout."""
from urllib.parse import unquote

from flask import Flask, jsonify, session

from modules import session_guard

TIMEOUT = 900


class Clock:
    def __init__(self, start=1_000_000):
        self.now = start

    def __call__(self):
        return self.now


def _app(clock):
    app = Flask(__name__)
    app.secret_key = "test"
    app.config["IDLE_TIMEOUT_SECONDS"] = TIMEOUT

    @app.get("/login")
    def login():
        return "login page"

    @app.get("/dashboard")
    def dashboard():
        return "dashboard"

    @app.get("/api/ping")
    def ping():
        return jsonify(user=session.get("user_id"))

    session_guard.register(app, clock=clock)
    return app


def _logged_in_client(clock, last_active):
    client = _app(clock).test_client()
    with client.session_transaction() as s:
        s["user_id"] = 7
        s["role"] = "passenger"
        if last_active is not None:
            s["last_active"] = last_active
    return client


def test_is_expired_boundaries():
    assert not session_guard.is_expired(100, 100 + TIMEOUT, TIMEOUT)
    assert session_guard.is_expired(100, 100 + TIMEOUT + 1, TIMEOUT)
    assert not session_guard.is_expired(None, 100, TIMEOUT)
    assert session_guard.is_expired("garbage", 100, TIMEOUT)


def test_active_session_passes_and_is_refreshed():
    clock = Clock()
    client = _logged_in_client(clock, last_active=clock.now - 100)
    assert client.get("/api/ping").get_json()["user"] == 7
    with client.session_transaction() as s:
        assert s["last_active"] == clock.now


def test_idle_api_call_gets_401_and_session_is_cleared():
    clock = Clock()
    client = _logged_in_client(clock, last_active=clock.now - TIMEOUT - 1)
    r = client.get("/api/ping")
    assert r.status_code == 401
    assert r.get_json()["code"] == "session_expired"
    with client.session_transaction() as s:
        assert "user_id" not in s


def test_old_token_stays_dead_after_expiry():
    clock = Clock()
    client = _logged_in_client(clock, last_active=clock.now - TIMEOUT - 1)
    client.get("/api/ping")  # expires the session
    clock.now += 1
    r = client.get("/api/ping")  # no user in session any more; nothing resurrects it
    assert r.get_json()["user"] is None


def test_idle_page_request_redirects_to_login():
    clock = Clock()
    client = _logged_in_client(clock, last_active=clock.now - TIMEOUT - 1)
    r = client.get("/dashboard")
    assert r.status_code == 302
    location = unquote(r.headers["Location"])
    assert location.startswith("/login") and "next=/dashboard" in location


def test_session_without_timestamp_is_stamped_then_times_out():
    clock = Clock()
    client = _logged_in_client(clock, last_active=None)
    assert client.get("/api/ping").status_code == 200
    clock.now += TIMEOUT + 1
    assert client.get("/api/ping").status_code == 401


def test_anonymous_requests_are_untouched():
    client = _app(Clock()).test_client()
    assert client.get("/login").status_code == 200
    assert client.get("/api/ping").get_json()["user"] is None
