
"""Database operations for provisional railway bookings."""

from db import get_cursor
from repository.audit_repo import write_audit_log


HOLD_MINUTES = 10


def create_provisional_booking(
    user_id,
    schedule_id,
    class_code,
    passenger_name,
    passenger_age,
    passenger_gender,
    berth_preference,
):
    """Create a temporary booking while locking the class capacity row."""

    with get_cursor(commit=True) as cursor:
        # Lock the class row to prevent concurrent overbooking.
        cursor.execute(
            """
            SELECT total_seats, fare
            FROM schedule_classes
            WHERE schedule_id = %s AND class_code = %s
            FOR UPDATE
            """,
            (schedule_id, class_code),
        )
        seat_class = cursor.fetchone()

        if seat_class is None:
            raise ValueError("Selected train class was not found.")

        # Expire provisional bookings whose holds have ended.
        cursor.execute(
            """
            UPDATE bookings
            SET status = 'CANCELLED'
            WHERE schedule_id = %s
              AND class_code = %s
              AND status = 'PROVISIONAL'
              AND held_until <= NOW()
            RETURNING id, user_id
            """,
            (schedule_id, class_code),
        )

        expired_bookings = cursor.fetchall()

        # Record an audit event for every expired booking.
        for expired in expired_bookings:
            write_audit_log(
                cursor,
                expired["user_id"],
                "BOOKING_EXPIRED",
                expired["id"],
                "Provisional booking hold expired",
            )

        # Count currently allocated seats.
        cursor.execute(
            """
            SELECT COUNT(*) AS allocated
            FROM bookings
            WHERE schedule_id = %s
              AND class_code = %s
              AND (
                    status = 'CONFIRMED'
                    OR (
                        status = 'PROVISIONAL'
                        AND held_until > NOW()
                    )
              )
            """,
            (schedule_id, class_code),
        )
        allocated = int(cursor.fetchone()["allocated"])

        if allocated >= int(seat_class["total_seats"]):
            raise ValueError("Sorry, no seats are currently available.")

        # Create a provisional booking.
        cursor.execute(
            """
            INSERT INTO bookings (
                user_id,
                schedule_id,
                class_code,
                status,
                passenger_name,
                passenger_age,
                passenger_gender,
                berth_preference,
                fare,
                held_until
            )
            VALUES (
                %s, %s, %s, 'PROVISIONAL',
                %s, %s, %s, %s, %s,
                NOW() + (%s * INTERVAL '1 minute')
            )
            RETURNING id, fare, held_until
            """,
            (
                user_id,
                schedule_id,
                class_code,
                passenger_name,
                passenger_age,
                passenger_gender,
                berth_preference,
                seat_class["fare"],
                HOLD_MINUTES,
            ),
        )

        booking = cursor.fetchone()

        # Record booking creation in the same database transaction.
        write_audit_log(
            cursor,
            user_id,
            "BOOKING_CREATED",
            booking["id"],
            "Provisional booking created",
        )

        return booking
