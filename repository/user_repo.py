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
            "SELECT id, name, email, password_hash, role FROM users WHERE email = %s",
            (email,),
        )
        return cur.fetchone()
