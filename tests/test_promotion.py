"""TC-Alloc-02 (RRS-F-051): a cancellation promotes the earliest eligible waiting booking."""
from unittest.mock import patch

from modules import promotion
from modules.promotion import plan_promotions

C, R, W = "CONFIRMED", "RAC", "WAITLISTED"


# ---- pure planning rule ------------------------------------------------------
def test_free_seat_goes_to_earliest_rac_then_waitlist_refills_rac():
    # 10 seats all held, RAC quota is 1; one RAC (id 5) and two waiting (6, 7); one seat freed
    moves = plan_promotions(10, 9, [5], [6, 7])
    assert moves == [(5, R, C), (6, W, R)]


def test_nothing_changes_when_no_seat_is_free_and_rac_is_full():
    assert plan_promotions(10, 10, [5], [6, 7]) == []


def test_booking_order_is_respected():
    moves = plan_promotions(20, 19, [30, 31, 32], [40])
    assert moves[0] == (30, R, C)  # first in the list = earliest booking


def test_waitlisted_gets_seat_directly_when_nobody_is_in_rac():
    assert plan_promotions(10, 9, [], [8, 9]) == [(8, W, C), (9, W, R)]


def test_two_free_seats_promote_two_rac_passengers():
    moves = plan_promotions(100, 98, [1, 2, 3], [])
    assert moves == [(1, R, C), (2, R, C)]


def test_rac_cancellation_pulls_waitlist_into_rac():
    # seats full, RAC quota 1 and currently empty (the RAC passenger cancelled)
    assert plan_promotions(10, 10, [], [6, 7]) == [(6, W, R)]


def test_rac_quota_is_never_exceeded():
    moves = plan_promotions(10, 10, [], [1, 2, 3, 4])  # quota = ceil(10 * 10%) = 1
    assert [m for m in moves if m[2] == R] == [(1, W, R)]


def test_empty_queues_and_overbooked_inputs_are_safe():
    assert plan_promotions(10, 3, [], []) == []
    assert plan_promotions(10, 15, [1], [2]) == []  # held > total: free is clamped at 0
    assert plan_promotions(0, 0, [], [1]) == []


def test_plan_is_idempotent_once_applied():
    first = plan_promotions(10, 9, [5], [6, 7])
    # after applying: 5 is confirmed (held 10), 6 is RAC, 7 still waiting
    assert plan_promotions(10, 10, [6], [7]) == []
    assert len(first) == 2


# ---- module wrapper ----------------------------------------------------------
def test_rebalance_after_cancel_hands_planner_and_pnr_maker_to_repo():
    class Repo:
        def rebalance_seats(self, booking_id, actor, plan, make_pnr):
            self.args = (booking_id, actor, plan, make_pnr)
            return [{"booking_id": 9, "from": R, "to": C}]

    repo = Repo()
    result = promotion.rebalance_after_cancel(41, 7, repo=repo)
    assert result == [{"booking_id": 9, "from": R, "to": C}]
    assert repo.args[:2] == (41, 7)
    assert repo.args[2] is plan_promotions
    pnr = repo.args[3]()  # generate_pnr with no "exists" check
    assert len(pnr) == 10 and pnr.isdigit()


# ---- repository against an in-memory fake cursor -------------------------------
class FakeCursor:
    """Understands exactly the statements promotion_repo sends."""

    def __init__(self, total_seats, bookings):
        self.total_seats = total_seats
        self.bookings = {b["id"]: dict(b) for b in bookings}
        self.rowcount = 0
        self._result = None
        self.audit = []

    def _group(self, ref):
        return [b for b in self.bookings.values()
                if (b["schedule_id"], b["class_code"]) == ref]

    def execute(self, sql, params=()):
        s = " ".join(sql.split())
        if s.startswith("SELECT schedule_id, class_code FROM bookings"):
            b = self.bookings.get(params[0])
            self._result = [{"schedule_id": b["schedule_id"], "class_code": b["class_code"]}] if b else []
        elif "FROM schedule_classes" in s:
            self._result = [{"total_seats": self.total_seats}]
        elif s.startswith("SELECT COUNT(*) AS held"):
            rows = [b for b in self._group(params) if b["status"] == "CONFIRMED"
                    or (b["status"] == "PROVISIONAL" and b.get("hold_active"))]
            self._result = [{"held": len(rows)}]
        elif "status IN ('RAC', 'WAITLISTED')" in s:
            rows = sorted((b for b in self._group(params) if b["status"] in (R, W)),
                          key=lambda b: (b["created_at"], b["id"]))
            self._result = [{"id": b["id"], "status": b["status"]} for b in rows]
        elif s.startswith("SELECT 1 FROM bookings WHERE pnr"):
            self._result = [{"x": 1}] if any(b.get("pnr") == params[0] for b in self.bookings.values()) else []
        elif s.startswith("UPDATE bookings SET status"):
            new, alloc, pnr, bid, old = params
            b = self.bookings[bid]
            if b["status"] == old:
                b["status"], b["allocation_status"] = new, alloc
                b["pnr"] = b.get("pnr") or pnr
                self.rowcount = 1
            else:
                self.rowcount = 0
        else:
            raise AssertionError(f"unexpected SQL: {s}")

    def fetchone(self):
        return self._result[0] if self._result else None

    def fetchall(self):
        return list(self._result)


class Ctx:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, *exc):
        return False


def _booking(i, status, created):
    return {"id": i, "schedule_id": 1, "class_code": "SL", "status": status,
            "created_at": created, "pnr": None}


def _run(cursor, cancelled_id=1, actor=99):
    from repository import promotion_repo

    def audit(cur, user_id, action, booking_id, details=None):
        cursor.audit.append((user_id, action, booking_id, details))

    with patch.object(promotion_repo, "get_cursor", return_value=Ctx(cursor)), \
         patch.object(promotion_repo, "write_audit_log", side_effect=audit):
        return promotion.rebalance_after_cancel(cancelled_id, actor)


def test_repo_promotes_rac_to_confirmed_with_pnr_and_waitlist_to_rac():
    # class SL has 2 seats; booking 1 just cancelled, 2 confirmed, 3 RAC, 4 and 5 waiting
    cursor = FakeCursor(2, [
        _booking(1, "CANCELLED", 1), _booking(2, "CONFIRMED", 2),
        _booking(3, "RAC", 3), _booking(4, "WAITLISTED", 4), _booking(5, "WAITLISTED", 5),
    ])
    result = _run(cursor)
    assert result == [{"booking_id": 3, "from": R, "to": C}, {"booking_id": 4, "from": W, "to": R}]
    b = cursor.bookings
    assert b[3]["status"] == C and b[3]["allocation_status"] == C
    assert len(b[3]["pnr"]) == 10 and b[3]["pnr"].isdigit()  # RRS-F-040: confirmed => PNR
    assert b[4]["status"] == R and b[4]["pnr"] is None
    assert b[5]["status"] == W
    assert [a[1:3] for a in cursor.audit] == [("BOOKING_PROMOTED", 3), ("BOOKING_PROMOTED", 4)]
    assert cursor.audit[0][0] == 99 and "booking #1" in cursor.audit[0][3]


def test_repo_second_run_promotes_nobody_again():
    cursor = FakeCursor(2, [
        _booking(1, "CANCELLED", 1), _booking(2, "CONFIRMED", 2), _booking(3, "RAC", 3),
    ])
    assert len(_run(cursor)) == 1
    assert _run(cursor) == []


def test_repo_booking_order_uses_created_at_then_id():
    cursor = FakeCursor(1, [
        _booking(1, "CANCELLED", 1), _booking(9, "RAC", 5), _booking(4, "RAC", 3),
    ])
    assert _run(cursor)[0]["booking_id"] == 4  # booked earlier, even though its id is larger/smaller


def test_repo_unknown_booking_or_no_free_seat_changes_nothing():
    cursor = FakeCursor(1, [_booking(2, "CONFIRMED", 2), _booking(3, "RAC", 3)])
    assert _run(cursor, cancelled_id=999) == []
    assert _run(cursor, cancelled_id=2) == []  # booking 2 is still CONFIRMED: no seat is free
    assert cursor.bookings[3]["status"] == R


def test_repo_unexpired_provisional_hold_keeps_the_seat():
    held = _booking(2, "PROVISIONAL", 2)
    held["hold_active"] = True
    cursor = FakeCursor(1, [_booking(1, "CANCELLED", 1), held, _booking(3, "RAC", 3)])
    assert _run(cursor) == []


# ---- cancel_booking triggers promotion (needs the patch in modules/cancellation.py) ----
def test_cancel_booking_calls_rebalance_and_survives_its_failure():
    from datetime import date, datetime, time
    from decimal import Decimal

    from modules import cancellation

    class Repo:
        def __init__(self, fail=False):
            self.fail, self.calls = fail, []
            self.booking = {"id": 1, "pnr": "1234567890", "user_id": 7, "status": "CONFIRMED",
                            "class_code": "3A", "passenger_name": "Asha", "fare": 900,
                            "travel_date": date(2026, 11, 25), "departure_time": time(6, 0)}

        def get_booking_by_pnr(self, pnr):
            return self.booking

        def get_policy(self):
            return [{"min_hours_before": 0, "refund_percent": 50}]

        def cancel_and_record_refund(self, booking_id, amount, percent, actor_user_id=None):
            return True

        def rebalance_seats(self, booking_id, actor, plan, make_pnr):
            self.calls.append((booking_id, actor))
            if self.fail:
                raise RuntimeError("database hiccup")
            return []

    now = datetime(2026, 11, 18, 6, 0)
    repo = Repo()
    result = cancellation.cancel_booking("1234567890", 7, True, repo=repo, now=now)
    assert result["status"] == "CANCELLED" and repo.calls == [(1, 7)]

    broken = Repo(fail=True)  # the cancellation itself must still succeed
    assert cancellation.cancel_booking("1234567890", 7, True, repo=broken, now=now)["status"] == "CANCELLED"
    assert Decimal(str(result["refund_amount"])) == Decimal("450.0")
