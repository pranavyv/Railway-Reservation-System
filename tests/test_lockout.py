"""TC-Auth-03 (RRS-F-003): lock the account after repeated failed logins."""
from datetime import datetime, timedelta, timezone

from tests.test_auth import FakeUserRepo
from modules import auth

NOW = datetime(2026, 11, 6, 10, 0, tzinfo=timezone.utc)


def _repo_with_user():
    repo = FakeUserRepo(now=NOW)
    auth.register_user("Asha", "asha@example.com", "longenough1", repo=repo)
    return repo


def _fail(repo, times, now=NOW):
    for _ in range(times):
        auth.authenticate("asha@example.com", "wrong-password", repo=repo, now=now)


def _expect_locked(repo, password, now=NOW):
    try:
        auth.authenticate("asha@example.com", password, repo=repo, now=now)
    except auth.AccountLocked as error:
        return error
    raise AssertionError("expected AccountLocked")


def test_four_failures_do_not_lock():
    repo = _repo_with_user()
    _fail(repo, 4)
    assert auth.authenticate("asha@example.com", "longenough1", repo=repo, now=NOW) is not None


def test_fifth_failure_locks_account():
    repo = _repo_with_user()
    _fail(repo, 4)
    error = _expect_locked(repo, "wrong-password")
    assert "Too many failed login attempts" in str(error)
    assert error.minutes_left == auth.LOCKOUT_MINUTES


def test_locked_account_refuses_even_correct_password():
    repo = _repo_with_user()
    try:
        _fail(repo, 5)
    except auth.AccountLocked:
        pass
    _expect_locked(repo, "longenough1")


def test_lock_ends_after_lockout_period():
    repo = _repo_with_user()
    try:
        _fail(repo, 5)
    except auth.AccountLocked:
        pass
    later = NOW + timedelta(minutes=auth.LOCKOUT_MINUTES, seconds=1)
    assert auth.authenticate("asha@example.com", "longenough1", repo=repo, now=later) is not None
    assert repo.users["asha@example.com"]["locked_until"] is None


def test_success_resets_failure_counter():
    repo = _repo_with_user()
    _fail(repo, 3)
    assert auth.authenticate("asha@example.com", "longenough1", repo=repo, now=NOW) is not None
    assert repo.users["asha@example.com"]["failed_attempts"] == 0
    _fail(repo, 4)  # counter restarted, so 4 more failures still do not lock
    assert auth.authenticate("asha@example.com", "longenough1", repo=repo, now=NOW) is not None


def test_unknown_email_never_raises_locked():
    repo = _repo_with_user()
    for _ in range(10):
        assert auth.authenticate("nobody@example.com", "x" * 10, repo=repo, now=NOW) is None


def test_minutes_left_rounds_up():
    error = auth.AccountLocked(NOW + timedelta(seconds=61), now=NOW)
    assert error.minutes_left == 2
    assert auth.AccountLocked(NOW - timedelta(seconds=5), now=NOW).minutes_left == 1


def test_naive_datetime_from_db_is_treated_as_utc():
    repo = _repo_with_user()
    repo.users["asha@example.com"]["locked_until"] = datetime(2026, 11, 6, 10, 30)  # naive
    _expect_locked(repo, "longenough1")
