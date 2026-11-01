
"""Database operations for provisional railway bookings."""

from db import get_cursor


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

        # Expired provisional bookings no longer occupy seats.
        cursor.execute(
            """
            UPDATE bookings
            SET status = 'CANCELLED'
            WHERE schedule_id = %s
              AND class_code = %s
              AND status = 'PROVISIONAL'
              AND held_until <= NOW()
            """,
            (schedule_id, class_code),
        )

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

        return cursor.fetchone()
