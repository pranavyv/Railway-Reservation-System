"""Database operations for booking audit logs (Issue #19, TC-Ops-01)."""

from db import get_cursor


VALID_AUDIT_ACTIONS = {
    "BOOKING_CREATED",
    "PAYMENT_SUCCESS",
    "PAYMENT_FAILED",
    "PAYMENT_TIMEOUT",
    "BOOKING_CANCELLED",
    "BOOKING_EXPIRED",
}


def write_audit_log(cursor, user_id, action, booking_id, details=None):
    """Insert an audit event using the caller's existing transaction.

    Every audit record captures:
    - id (auto-generated)
    - user_id (actor)
    - action (e.g. BOOKING_CREATED, PAYMENT_SUCCESS, etc.)
    - booking_id (association to the specific booking)
    - details (contextual description)
    - created_at (timestamped event)
    """
    cursor.execute(
        """
        INSERT INTO audit_log (user_id, action, booking_id, details)
        VALUES (%s, %s, %s, %s)
        RETURNING id, user_id, action, booking_id, details, created_at
        """,
        (user_id, action, booking_id, details),
    )
    return cursor.fetchone()


def get_booking_audit_logs(booking_id):
    """Retrieve timestamped audit events for a specific booking in chronological order."""
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, user_id, action, booking_id, details, created_at
            FROM audit_log
            WHERE booking_id = %s
            ORDER BY created_at ASC, id ASC
            """,
            (booking_id,),
        )
        return cursor.fetchall()


def get_recent_audit_logs(limit=100, action=None):
    """Retrieve recent timestamped audit logs for administrative overview."""
    with get_cursor() as cursor:
        if action:
            cursor.execute(
                """
                SELECT id, user_id, action, booking_id, details, created_at
                FROM audit_log
                WHERE action = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (action, limit),
            )
        else:
            cursor.execute(
                """
                SELECT id, user_id, action, booking_id, details, created_at
                FROM audit_log
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (limit,),
            )
        return cursor.fetchall()


# --- Admin-action audit trail (PRJ-SR-006, Pranav Sprint 2) -----------------
def insert(user_id, action, details):
    """Record one admin action in its own transaction (see modules/audit.py)."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO audit_log (user_id, action, details) VALUES (%s, %s, %s)",
            (user_id, action, details),
        )


def recent(limit):
    """Newest entries with the acting user's email, for the admin audit viewer."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT a.id, a.user_id, u.email AS user_email, a.action, a.booking_id, "
            "a.details, a.created_at "
            "FROM audit_log a LEFT JOIN users u ON u.id = a.user_id "
            "ORDER BY a.created_at DESC, a.id DESC LIMIT %s",
            (limit,),
        )
        return cur.fetchall()
