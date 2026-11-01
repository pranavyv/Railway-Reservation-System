"""SQL for trains, schedules and classes (repository layer)."""
from db import get_cursor


def search_rows(source, destination, travel_date):
    """One row per (train schedule, class) for the route and date."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT t.id AS train_id, t.train_no, t.name, t.source, t.destination,
                   t.departure_time, t.arrival_time,
                   s.id AS schedule_id, s.travel_date,
                   sc.class_code, sc.fare, sc.total_seats
            FROM trains t
            JOIN schedules s         ON s.train_id = t.id
            JOIN schedule_classes sc ON sc.schedule_id = s.id
            WHERE t.active
              AND lower(t.source) = lower(%s)
              AND lower(t.destination) = lower(%s)
              AND s.travel_date = %s
            ORDER BY t.departure_time, sc.class_code
            """,
            (source, destination, travel_date),
        )
        return cur.fetchall()
