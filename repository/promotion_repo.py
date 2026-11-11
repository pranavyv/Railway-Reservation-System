"""SQL for waitlist / RAC promotion (RRS-F-051).

Everything happens in ONE transaction: the schedule_classes row is locked so two
cancellations cannot promote the same passenger, each promotion is written to the
audit log, and a passenger promoted to CONFIRMED gets their PNR in the same commit.
"""
from db import get_cursor
from repository.audit_repo import write_audit_log


def _pnr_taken(cursor, candidate):
    cursor.execute("SELECT 1 FROM bookings WHERE pnr = %s", (candidate,))
    return cursor.fetchone() is not None


def rebalance_seats(booking_id, actor_user_id, plan, make_pnr):
    """Apply the promotion plan for the schedule/class of booking_id.

    plan(total_seats, held_seats, rac_ids, waitlist_ids) -> [(id, old, new), ...]
    make_pnr(exists) -> a new unique PNR string.
    """
    with get_cursor(commit=True) as cursor:
        cursor.execute(
            "SELECT schedule_id, class_code FROM bookings WHERE id = %s", (booking_id,)
        )
        ref = cursor.fetchone()
        if ref is None:
            return []

        cursor.execute(
            "SELECT total_seats FROM schedule_classes "
            "WHERE schedule_id = %s AND class_code = %s FOR UPDATE",
            (ref["schedule_id"], ref["class_code"]),
        )
        seat_class = cursor.fetchone()
        if seat_class is None:
            return []

        cursor.execute(
            """
            SELECT COUNT(*) AS held
            FROM bookings
            WHERE schedule_id = %s AND class_code = %s
              AND (status = 'CONFIRMED' OR (status = 'PROVISIONAL' AND held_until > NOW()))
            """,
            (ref["schedule_id"], ref["class_code"]),
        )
        held = int(cursor.fetchone()["held"])

        cursor.execute(
            """
            SELECT id, status
            FROM bookings
            WHERE schedule_id = %s AND class_code = %s
              AND status IN ('RAC', 'WAITLISTED')
            ORDER BY created_at ASC, id ASC
            FOR UPDATE
            """,
            (ref["schedule_id"], ref["class_code"]),
        )
        waiting = cursor.fetchall()
        rac_ids = [row["id"] for row in waiting if row["status"] == "RAC"]
        waitlist_ids = [row["id"] for row in waiting if row["status"] == "WAITLISTED"]

        applied = []
        for promoted_id, old_status, new_status in plan(
            int(seat_class["total_seats"]), held, rac_ids, waitlist_ids
        ):
            pnr = None
            if new_status == "CONFIRMED":
                pnr = make_pnr(lambda candidate: _pnr_taken(cursor, candidate))
            cursor.execute(
                "UPDATE bookings "
                "SET status = %s, allocation_status = %s, pnr = COALESCE(pnr, %s) "
                "WHERE id = %s AND status = %s",
                (new_status, new_status, pnr, promoted_id, old_status),
            )
            if cursor.rowcount != 1:
                continue  # someone changed it first; skip rather than guess
            write_audit_log(
                cursor,
                actor_user_id,
                "BOOKING_PROMOTED",
                promoted_id,
                f"Promoted {old_status} to {new_status} after cancellation of booking #{booking_id}",
            )
            applied.append({"booking_id": promoted_id, "from": old_status, "to": new_status})
        return applied
