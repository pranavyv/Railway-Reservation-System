"""TC-Sec-01 (RRS-NF-003): sensitive data is never stored or exposed in plaintext."""
import re
from pathlib import Path

from flask import Flask, session

from modules import auth, session_guard

SCHEMA = Path("schema.sql").read_text(encoding="utf-8")


def _table_columns(name):
    match = re.search(rf"CREATE TABLE IF NOT EXISTS {name}\s*\((.*?)\n\);", SCHEMA, re.I | re.S)
    assert match, f"{name} table not found"
    return [line.split()[0].lower() for line in match.group(1).splitlines()
            if line.strip() and not line.strip().startswith("--") and not line.strip().startswith("UNIQUE")]


def test_users_table_stores_only_a_password_hash():
    columns = _table_columns("users")
    assert "password_hash" in columns
    assert "password" not in columns and "plain_password" not in columns


def test_no_table_has_card_or_secret_columns():
    forbidden = ("card", "cvv", "cvc", "pan", "plain", "secret")
    for table in ("users", "payments", "bookings", "refunds", "audit_log"):
        for column in _table_columns(table):
            assert not any(column == f or column.startswith(f + "_") or f in column.split("_")
                           for f in forbidden), f"{table}.{column}"


def test_registration_hashes_with_a_salted_algorithm():
    from tests.test_auth import FakeUserRepo

    repo = FakeUserRepo()
    auth.register_user("A", "a@example.com", "longenough1", repo=repo)
    auth.register_user("B", "b@example.com", "longenough1", repo=repo)
    h1, h2 = (repo.users[e]["password_hash"] for e in ("a@example.com", "b@example.com"))
    assert "longenough1" not in h1 and h1 != h2  # salted: same password, different hash
    assert re.match(r"^(scrypt|pbkdf2):", h1)


def test_session_cookie_never_contains_password_or_hash():
    app = Flask(__name__)
    app.secret_key = "test"

    @app.post("/fake-login")
    def fake_login():
        session.clear()
        session["user_id"], session["user_name"], session["role"] = 1, "Asha", "passenger"
        session_guard.touch()
        return "ok"

    client = app.test_client()
    r = client.post("/fake-login")
    assert set(session_keys(client)) == {"user_id", "user_name", "role", "last_active"}
    assert "longenough1" not in r.headers.get("Set-Cookie", "")


def session_keys(client):
    with client.session_transaction() as s:
        return list(s.keys())


def test_app_login_route_stores_only_safe_keys():
    source = Path("app.py").read_text(encoding="utf-8")
    login_block = source[source.index("def login"):source.index("def logout")]
    assert 'session["password' not in login_block and "password_hash" not in login_block


def test_application_code_never_logs_credentials():
    for path in list(Path("modules").glob("*.py")) + [Path("app.py")]:
        for line in path.read_text(encoding="utf-8").splitlines():
            if re.search(r"(logger|logging|print)\b.*\b(password|card|cvv)", line, re.I):
                raise AssertionError(f"{path}: {line.strip()}")


def test_session_cookie_flags_are_hardened():
    from config import Config

    assert Config.SESSION_COOKIE_HTTPONLY is True
    assert Config.SESSION_COOKIE_SAMESITE == "Lax"
