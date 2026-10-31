"""Auth module: registration and login (RRS-F-001, RRS-F-002, PRJ-SR-002).

Repository is injected so the logic can be unit-tested without a database.
Lockout after repeated failures (RRS-F-003) and idle timeout (PRJ-SR-004)
are Sprint 2.
"""
import re

from werkzeug.security import check_password_hash, generate_password_hash

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


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


def authenticate(email, password, repo=None):
    """Returns the user dict on success, otherwise None."""
    if not email or not password:
        return None
    user = _repo(repo).get_by_email(email.strip().lower())
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None
