"""Auth module: registration and login (RRS-F-001, RRS-F-002, PRJ-SR-002).

Repository is injected so the logic can be unit-tested without a database.
Lockout after repeated failures (RRS-F-003) lives here; the idle timeout
(PRJ-SR-004) is in modules/session_guard.py.
"""
import math
import re
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8
MAX_FAILED_LOGINS = 5  # RRS-F-003 acceptance criterion: 5 failed attempts
LOCKOUT_MINUTES = 15


class AccountLocked(Exception):
    """Raised when login is refused because of too many failed attempts."""

    def __init__(self, locked_until, now=None):
        self.locked_until = _aware(locked_until)
        now = now or datetime.now(timezone.utc)
        seconds = max((self.locked_until - now).total_seconds(), 0)
        self.minutes_left = max(1, math.ceil(seconds / 60))
        super().__init__(
            f"Too many failed login attempts. Try again in {self.minutes_left} minute(s)."
        )


def _aware(moment):
    """Treat naive datetimes as UTC so comparisons never raise."""
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def _repo(repo):
    if repo is not None:
        return repo
    from repository import user_repo  # imported lazily so tests need no DB driver

    return user_repo


def validate_registration(name, email, password):
    """Return a list of error messages (empty list means valid)."""
    errors = []
    if not name or not name.strip():
        errors.append("Enter your name.")
    if not email or not EMAIL_RE.match(email.strip()):
        errors.append("Enter a valid email address.")
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    return errors


def register_user(name, email, password, repo=None):
    """Returns (user_id, errors). Duplicate emails are rejected."""
    errors = validate_registration(name, email, password)
    if errors:
        return None, errors

    repo = _repo(repo)
    email = email.strip().lower()
    user_id = repo.create_user(name.strip(), email, generate_password_hash(password))
    if user_id is None:
        return None, ["An account with this email already exists."]
    return user_id, []


def authenticate(
    email,
    password,
    repo=None,
    now=None,
    max_attempts=MAX_FAILED_LOGINS,
    lock_minutes=LOCKOUT_MINUTES,
):
    """Returns the user dict on success, otherwise None.

    Raises AccountLocked while the account is locked (RRS-F-003). A locked
    account is refused even when the password is correct, until the lock ends.
    """
    if not email or not password:
        return None
    repo = _repo(repo)
    now = now or datetime.now(timezone.utc)

    user = repo.get_by_email(email.strip().lower())
    if user is None:
        return None

    locked_until = user.get("locked_until")
    if locked_until and _aware(locked_until) > now:
        raise AccountLocked(locked_until, now)

    if check_password_hash(user["password_hash"], password):
        if user.get("failed_attempts") or locked_until:
            repo.reset_failed_logins(user["id"])
        return user

    state = repo.record_failed_login(user["id"], max_attempts, lock_minutes)
    if state and state.get("locked_until") and _aware(state["locked_until"]) > now:
        raise AccountLocked(state["locked_until"], now)
    return None
