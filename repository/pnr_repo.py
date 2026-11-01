"""Database queries for PNR generation and lookup (RRS-F-040)."""
import psycopg2

from db import get_cursor

_BOOKING_SELECT = """
    SELECT b.id, b.pnr, b.user_id, b.status, b.class_code,
           b.passenger_name, b.fare,
           s.travel_date,
           t.train_no, t.name AS train_name, t.source, t.destination, t.departure_time
    FROM bookings b
    JOIN schedules s ON s.id = b.schedule_id
    JOIN trains t    ON t.id = s.train_id
"""


def get_booking(booking_id):
    with get_cursor() as cursor:
        cursor.execute(_BOOKING_SELECT + " WHERE b.id = %s", (booking_id,))
        return cursor.fetchone()


def get_booking_by_pnr(pnr):
    with get_cursor() as cursor:
        cursor.execute(_BOOKING_SELECT + " WHERE b.pnr = %s", (pnr,))
        return cursor.fetchone()


def pnr_exists(pnr):
    with get_cursor() as cursor:
        cursor.execute("SELECT 1 FROM bookings WHERE pnr = %s", (pnr,))
        return cursor.fetchone() is not None


def set_pnr(booking_id, pnr):
    """Store the PNR on a CONFIRMED booking that has none yet. True if it was stored."""
    try:
        with get_cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE bookings SET pnr = %s "
                "WHERE id = %s AND pnr IS NULL AND status = 'CONFIRMED'",
                (pnr, booking_id),
            )
            return cursor.rowcount == 1
    except psycopg2.errors.UniqueViolation:
        return False
