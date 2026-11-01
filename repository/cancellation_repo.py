"""Database queries for cancellation and refunds (RRS-F-041, RRS-F-042)."""
from db import get_cursor
from repository.pnr_repo import get_booking_by_pnr  # noqa: F401  (re-exported for the module)


def get_policy():
    with get_cursor() as cursor:
        cursor.execute(
            "SELECT min_hours_before, refund_percent FROM cancellation_policy "
            "ORDER BY min_hours_before DESC"
        )
        return cursor.fetchall()


def cancel_and_record_refund(booking_id, amount, percent):
    """Mark the booking CANCELLED and store its refund in one transaction.

    Seats are counted from booking status, so cancelling releases the seat.
    Returns False if the booking was already cancelled.
    """
    with get_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE bookings SET status = 'CANCELLED' "
            "WHERE id = %s AND status <> 'CANCELLED' RETURNING id",
            (booking_id,),
        )
        cancelled = cursor.fetchone() is not None
        if cancelled:
            cursor.execute(
                "INSERT INTO refunds (booking_id, amount, refund_percent) VALUES (%s, %s, %s)",
                (booking_id, amount, percent),
            )
    return cancelled
