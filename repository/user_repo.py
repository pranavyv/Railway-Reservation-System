"""SQL for the users table (repository layer)."""
from psycopg2 import errors

from db import get_cursor


def create_user(name, email, password_hash, role="passenger"):
    """Insert a user. Returns the new id, or None if the email already exists."""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO users (name, email, password_hash, role) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (name, email, password_hash, role),
            )
            return cur.fetchone()["id"]
    except errors.UniqueViolation:
        return None


def get_by_email(email):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, name, email, password_hash, role, failed_attempts, locked_until "
            "FROM users WHERE email = %s",
            (email,),
        )
        return cur.fetchone()


def record_failed_login(user_id, max_attempts, lock_minutes):
    """Count one wrong password in a single atomic UPDATE (RRS-F-003).

    On the max_attempts-th failure the counter resets to 0 and the account is
    locked for lock_minutes. Returns {"failed_attempts", "locked_until"}.
    """
    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE users SET "
            "  failed_attempts = CASE WHEN failed_attempts + 1 >= %s THEN 0 "
            "                         ELSE failed_attempts + 1 END, "
            "  locked_until = CASE WHEN failed_attempts + 1 >= %s "
            "                      THEN now() + make_interval(mins => %s) "
            "                      ELSE locked_until END "
            "WHERE id = %s RETURNING failed_attempts, locked_until",
            (max_attempts, max_attempts, lock_minutes, user_id),
        )
        return cur.fetchone()


def reset_failed_logins(user_id):
    """Clear the counter and any lock after a successful login."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = %s",
            (user_id,),
        )
