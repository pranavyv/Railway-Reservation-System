
"""Database operations for mock railway payments."""

from uuid import uuid4

from db import get_cursor


def record_payment(user_id, booking_id, transaction_ref, status):
    """Record a mock payment and confirm the booking only on success."""

    # Validate payment status before database operations.
    if status not in {"SUCCESS", "FAILED", "TIMEOUT"}:
        raise ValueError("Invalid payment status.")

    if not transaction_ref or not transaction_ref.strip():
        raise ValueError("Invalid transaction reference.")

    with get_cursor(commit=True) as cursor:
        cursor.execute(
            """
            SELECT id, status, fare, held_until,
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
            raise ValueError(
                "Your booking hold has expired. Please book again."
            )

        cursor.execute(
            """
            INSERT INTO payments (
                booking_id, transaction_ref, status, amount
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                booking_id,
                transaction_ref,
                status,
                booking["fare"],
            ),
        )

        pnr = None

        if status == "SUCCESS":
            pnr = f"RRS{uuid4().hex[:10].upper()}"

            cursor.execute(
                """
                UPDATE bookings
                SET status = 'CONFIRMED', pnr = %s
                WHERE id = %s AND status = 'PROVISIONAL'
                """,
                (pnr, booking_id),
            )

            if cursor.rowcount != 1:
                raise ValueError("Unable to confirm this booking.")

        return {
            "booking_id": booking_id,
            "transaction_ref": transaction_ref,
            "status": status,
            "amount": booking["fare"],
            "pnr": pnr,
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
