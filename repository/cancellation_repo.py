
"""Database queries for cancellation and refunds (RRS-F-041, RRS-F-042)."""

from db import get_cursor
from repository.pnr_repo import get_booking_by_pnr  # noqa: F401
from repository.audit_repo import write_audit_log


def get_policy():
    """Retrieve the configured cancellation refund policy."""

    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT min_hours_before, refund_percent
            FROM cancellation_policy
            ORDER BY min_hours_before DESC
            """
        )
        return cursor.fetchall()


def cancel_and_record_refund(booking_id, amount, percent, actor_user_id):
    """Cancel a booking, record its refund and audit event atomically.

    Returns False if the booking was already cancelled.
    """

    with get_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE bookings
            SET status = 'CANCELLED'
            WHERE id = %s AND status <> 'CANCELLED'
            RETURNING id
            """,
            (booking_id,),
        )

        cancelled = cursor.fetchone() is not None

        if cancelled:
            cursor.execute(
                """
                INSERT INTO refunds (booking_id, amount, refund_percent)
                VALUES (%s, %s, %s)
                """,
                (booking_id, amount, percent),
            )

            write_audit_log(
                cursor,
                actor_user_id,
                "BOOKING_CANCELLED",
                booking_id,
                f"Booking cancelled; refund percentage: {percent}",
            )

    return cancelled
