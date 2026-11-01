from datetime import date, datetime, time
from decimal import Decimal

from modules import cancellation

NOW = datetime(2026, 11, 18, 6, 0)
POLICY_ROWS = [
    {"min_hours_before": 48, "refund_percent": 90},
    {"min_hours_before": 12, "refund_percent": 75},
    {"min_hours_before": 4, "refund_percent": 50},
]


def _booking(status="CONFIRMED", travel_date=date(2026, 11, 25), user_id=7, fare=900):
    return {
        "id": 1, "pnr": "1234567890", "user_id": user_id, "status": status,
        "class_code": "3A", "passenger_name": "Asha", "fare": fare,
        "travel_date": travel_date, "train_no": "10001", "train_name": "Silicon Express",
        "source": "Bengaluru", "destination": "Chennai", "departure_time": time(6, 0),
    }


class FakeRepo:
    def __init__(self, booking):
        self.booking = booking
        self.refunds = []

    def get_booking_by_pnr(self, pnr):
        return self.booking if self.booking and self.booking["pnr"] == pnr else None

    def get_policy(self):
        return POLICY_ROWS

    def cancel_and_record_refund(self, booking_id, amount, percent):
        if self.booking["status"] == "CANCELLED":
            return False
        self.booking["status"] = "CANCELLED"
        self.refunds.append((booking_id, amount, percent))
        return True


def _expect(error, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except error:
        return
    raise AssertionError(f"expected {error.__name__}")


def test_cancel_updates_status_and_records_refund():  # TC-Cancel-01, TC-Cancel-02
    repo = FakeRepo(_booking())  # 7 days ahead -> 90%
    result = cancellation.cancel_booking("1234567890", 7, True, repo=repo, now=NOW)
    assert repo.booking["status"] == "CANCELLED"
    assert result["status"] == "CANCELLED"
    assert result["refund_percent"] == 90 and result["refund_amount"] == 810.0
    assert repo.refunds == [(1, Decimal("810.00"), 90)]


def test_refund_shrinks_close_to_departure():  # TC-Cancel-02
    close = _booking(travel_date=date(2026, 11, 18))  # departs 06:00 today, now is 06:00
    assert cancellation.preview_refund("1234567890", 7, repo=FakeRepo(close), now=NOW)["refund_amount"] == 0.0
    later = _booking(travel_date=date(2026, 11, 19))  # 24h ahead -> 75%
    assert cancellation.preview_refund("1234567890", 7, repo=FakeRepo(later), now=NOW)["refund_percent"] == 75


def test_preview_does_not_cancel():
    repo = FakeRepo(_booking())
    cancellation.preview_refund("1234567890", 7, repo=repo, now=NOW)
    assert repo.booking["status"] == "CONFIRMED" and repo.refunds == []


def test_confirmation_is_required():  # TC-Cancel-01
    repo = FakeRepo(_booking())
    for flag in (False, None, "yes", 1):
        _expect(cancellation.ConfirmationRequired, cancellation.cancel_booking,
                "1234567890", 7, flag, repo=repo, now=NOW)
    assert repo.booking["status"] == "CONFIRMED"


def test_cannot_cancel_someone_elses_ticket():
    repo = FakeRepo(_booking(user_id=7))
    _expect(cancellation.BookingNotFound, cancellation.cancel_booking,
            "1234567890", 8, True, repo=repo, now=NOW)
    assert repo.booking["status"] == "CONFIRMED"


def test_admin_can_cancel_any_ticket():
    repo = FakeRepo(_booking(user_id=7))
    result = cancellation.cancel_booking("1234567890", 99, True, role="admin", repo=repo, now=NOW)
    assert result["status"] == "CANCELLED"


def test_cannot_cancel_twice():
    repo = FakeRepo(_booking())
    cancellation.cancel_booking("1234567890", 7, True, repo=repo, now=NOW)
    _expect(cancellation.AlreadyCancelled, cancellation.cancel_booking,
            "1234567890", 7, True, repo=repo, now=NOW)
    assert len(repo.refunds) == 1


def test_unknown_or_malformed_pnr():
    repo = FakeRepo(_booking())
    _expect(cancellation.BookingNotFound, cancellation.cancel_booking,
            "9999999999", 7, True, repo=repo, now=NOW)
    _expect(ValueError, cancellation.cancel_booking, "abc", 7, True, repo=repo, now=NOW)
