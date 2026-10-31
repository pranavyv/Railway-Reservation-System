
"""Database queries for train seat availability."""

from db import get_cursor


def get_seat_availability(train_id, travel_date, class_code):
    """Fetch seat capacity and allocated seat count."""

    query = """
        SELECT
            t.id AS train_id,
            t.train_no,
            t.name AS train_name,
            s.travel_date,
            sc.class_code,
            sc.total_seats,
            COUNT(b.id) AS allocated_seats
        FROM trains t
        JOIN schedules s
            ON s.train_id = t.id
        JOIN schedule_classes sc
            ON sc.schedule_id = s.id
        LEFT JOIN bookings b
            ON b.schedule_id = s.id
            AND b.class_code = sc.class_code
            AND (
                b.status = 'CONFIRMED'
                OR (
                    b.status = 'PROVISIONAL'
                    AND b.held_until > NOW()
                )
            )
        WHERE t.id = %s
          AND s.travel_date = %s
          AND sc.class_code = %s
        GROUP BY
            t.id, t.train_no, t.name,
            s.travel_date, sc.class_code,
            sc.total_seats
    """

    with get_cursor() as cursor:
        cursor.execute(
            query,
            (train_id, travel_date, class_code)
        )
        return cursor.fetchone()
