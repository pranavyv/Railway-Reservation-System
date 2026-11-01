"""Database queries for seat status assignment (RRS-F-050)."""
from db import get_cursor


def get_counts(schedule_id, class_code):
    """Seat counts for one schedule and class, or None if that class does not exist.

    held_seats = CONFIRMED bookings plus PROVISIONAL bookings whose hold has not expired,
    the same rule used by the availability check.
    """
    query = """
        SELECT
            sc.total_seats,
            COUNT(*) FILTER (
                WHERE b.status = 'CONFIRMED'
                   OR (b.status = 'PROVISIONAL' AND b.held_until > NOW())
            ) AS held_seats,
            COUNT(*) FILTER (WHERE b.status = 'RAC')        AS rac_count,
            COUNT(*) FILTER (WHERE b.status = 'WAITLISTED') AS waitlist_count
        FROM schedule_classes sc
        LEFT JOIN bookings b
               ON b.schedule_id = sc.schedule_id
              AND b.class_code  = sc.class_code
        WHERE sc.schedule_id = %s
          AND sc.class_code  = %s
        GROUP BY sc.total_seats
    """
    with get_cursor() as cursor:
        cursor.execute(query, (schedule_id, class_code))
        return cursor.fetchone()
