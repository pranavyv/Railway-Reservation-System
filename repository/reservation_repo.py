"""Transactional persistence for booking, PNR lookup, cancellation and refunds."""
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal, ROUND_HALF_UP
import secrets
import string

from db import get_cursor


def _new_pnr():
    # Nine numeric digits; uniqueness is enforced by the database constraint.
    return "".join(secrets.choice(string.digits) for _ in range(9))


def create_booking(user_id, schedule_id, class_code, passenger_name, passenger_age,
                   passenger_gender, berth_preference=None):
    """Create a booking while locking class inventory to prevent overbooking."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            """SELECT sc.total_seats, sc.fare, s.id AS schedule_id
               FROM schedule_classes sc
               JOIN schedules s ON s.id = sc.schedule_id
               WHERE s.id = %s AND sc.class_code = %s
               FOR UPDATE OF sc""",
            (schedule_id, class_code),
        )
        inventory = cur.fetchone()
        if inventory is None:
            return None

        cur.execute(
            """SELECT COUNT(*) AS occupied FROM bookings
               WHERE schedule_id = %s AND class_code = %s
                 AND (status IN ('CONFIRMED', 'RAC')
                      OR (status = 'PROVISIONAL' AND held_until > NOW()))""",
            (schedule_id, class_code),
        )
        occupied = int(cur.fetchone()["occupied"])
        total = int(inventory["total_seats"])
        if occupied < total:
            status = "CONFIRMED"
        else:
            cur.execute(
                """SELECT COUNT(*) AS count FROM bookings
                   WHERE schedule_id = %s AND class_code = %s
                     AND status = 'RAC'""",
                (schedule_id, class_code),
            )
            rac_count = int(cur.fetchone()["count"])
            status = "RAC" if rac_count < max(1, total // 10) else "WAITLISTED"

        pnr = _new_pnr()
        cur.execute(
            """INSERT INTO bookings
               (pnr, user_id, schedule_id, class_code, status, passenger_name,
                passenger_age, passenger_gender, berth_preference, fare)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id, pnr, status, fare, schedule_id, class_code""",
            (pnr, user_id, schedule_id, class_code, status, passenger_name,
             passenger_age, passenger_gender, berth_preference, inventory["fare"]),
        )
        return dict(cur.fetchone())


def get_booking_by_pnr(pnr):
    with get_cursor() as cur:
        cur.execute(
            """SELECT b.pnr, b.status, b.passenger_name, b.passenger_age,
                      b.passenger_gender, b.class_code, b.fare, b.created_at,
                      s.travel_date, t.train_no, t.name AS train_name,
                      t.source, t.destination, t.departure_time
               FROM bookings b
               JOIN schedules s ON s.id = b.schedule_id
               JOIN trains t ON t.id = s.train_id
               WHERE b.pnr = %s""",
            (pnr,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def cancel_booking_and_refund(pnr, user_id):
    """Cancel an owned active booking, record policy refund and promote the queue."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            """SELECT b.*, s.travel_date, t.departure_time
               FROM bookings b JOIN schedules s ON s.id = b.schedule_id
               JOIN trains t ON t.id = s.train_id
               WHERE b.pnr = %s AND b.user_id = %s FOR UPDATE OF b""",
            (pnr, user_id),
        )
        booking = cur.fetchone()
        if not booking:
            return {"error": "Booking not found."}, 404
        if booking["status"] == "CANCELLED":
            return {"error": "This booking is already cancelled."}, 409
        if booking["status"] == "WAITLISTED":
            # Waitlisted cancellation does not consume a seat; refund policy still applies.
            pass

        # Train schedules use Indian local time in this project.
        departure = datetime.combine(
            booking["travel_date"], booking["departure_time"],
            tzinfo=ZoneInfo("Asia/Kolkata"),
        )
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        hours_left = max(0, int((departure - now).total_seconds() // 3600))
        cur.execute(
            """SELECT refund_percent FROM cancellation_policy
               WHERE min_hours_before <= %s
               ORDER BY min_hours_before DESC LIMIT 1""",
            (hours_left,),
        )
        policy = cur.fetchone()
        refund_percent = int(policy["refund_percent"]) if policy else 0
        refund_amount = (Decimal(str(booking["fare"])) * Decimal(refund_percent) / 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        cur.execute("UPDATE bookings SET status = 'CANCELLED' WHERE id = %s", (booking["id"],))
        cur.execute(
            """INSERT INTO refunds (booking_id, amount, refund_percent, status)
               VALUES (%s, %s, %s, 'RECORDED')
               ON CONFLICT (booking_id) DO NOTHING""",
            (booking["id"], refund_amount, refund_percent),
        )

        if booking["status"] == "CONFIRMED":
            cur.execute(
                """SELECT id, status FROM bookings
                   WHERE schedule_id = %s AND class_code = %s
                     AND status IN ('RAC', 'WAITLISTED')
                   ORDER BY CASE status WHEN 'RAC' THEN 0 ELSE 1 END, created_at, id
                   LIMIT 1 FOR UPDATE""",
                (booking["schedule_id"], booking["class_code"]),
            )
            next_booking = cur.fetchone()
            if next_booking:
                promoted_status = "CONFIRMED" if next_booking["status"] == "RAC" else "RAC"
                cur.execute("UPDATE bookings SET status = %s WHERE id = %s",
                            (promoted_status, next_booking["id"]))
        return {
            "pnr": pnr,
            "status": "CANCELLED",
            "refund_amount": str(refund_amount),
            "refund_percent": refund_percent,
        }, 200


def booking_belongs_to_user(pnr, user_id):
    with get_cursor() as cur:
        cur.execute("SELECT 1 FROM bookings WHERE pnr = %s AND user_id = %s", (pnr, user_id))
        return cur.fetchone() is not None
