
"""Database operations for mock railway payments."""

from db import get_cursor


def record_payment(user_id, booking_id, transaction_ref, status):
    """Record a mock payment and update the provisional booking."""

    if status not in {"SUCCESS", "FAILED", "TIMEOUT"}:
        raise ValueError("Invalid payment status.")

    if not transaction_ref or not transaction_ref.strip():
        raise ValueError("Invalid transaction reference.")

    with get_cursor(commit=True) as cursor:
        cursor.execute(
            """
            SELECT id, status, fare, held_until, allocation_status,
                   (held_until > NOW()) AS hold_active
            FROM bookings
            WHERE id = %s AND user_id = %s
            FOR UPDATE
            """,
            (booking_id, user_id),
        )
        booking = cursor.fetchone()

        if booking is None:
            raise ValueError("Booking not found.")

        if booking["status"] != "PROVISIONAL":
            raise ValueError("Booking is no longer awaiting payment.")

        if not booking["hold_active"]:
            status = "TIMEOUT"

        cursor.execute(
            "INSERT INTO payments (booking_id, transaction_ref, status, amount) "
            "VALUES (%s, %s, %s, %s)",
            (booking_id, transaction_ref, status, booking["fare"]),
        )

        if status == "SUCCESS":
            new_status = booking["allocation_status"] or "CONFIRMED"
        else:
            new_status = "CANCELLED"

        cursor.execute(
            "UPDATE bookings SET status = %s WHERE id = %s AND status = 'PROVISIONAL'",
            (new_status, booking_id),
        )
        if cursor.rowcount != 1:
            raise ValueError("Unable to update this booking.")

        return {
            "booking_id": booking_id,
            "transaction_ref": transaction_ref,
            "status": status,
            "booking_status": new_status,
            "amount": booking["fare"],
            "pnr": None,
        }


def get_booking_for_user(user_id, booking_id):
    """Retrieve a booking only if it belongs to the specified user."""

    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, pnr, passenger_name, class_code, fare,
                   held_until, status
            FROM bookings
            WHERE id = %s AND user_id = %s
            """,
            (booking_id, user_id),
        )
        return cursor.fetchone()
