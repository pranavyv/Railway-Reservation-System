from datetime import date, time

from modules import pnr


def _row(booking_id=1, status="CONFIRMED", pnr_value=None, user_id=7):
    return {
        "id": booking_id, "pnr": pnr_value, "user_id": user_id, "status": status,
        "class_code": "3A", "passenger_name": "Asha", "fare": 900,
        "travel_date": date(2026, 11, 20), "train_no": "10001", "train_name": "Silicon Express",
        "source": "Bengaluru", "destination": "Chennai", "departure_time": time(6, 0),
    }


class FakeRepo:
    def __init__(self, rows):
        self.rows = {r["id"]: r for r in rows}
        self.taken = set()

    def get_booking(self, booking_id):
        return self.rows.get(booking_id)

    def get_booking_by_pnr(self, pnr_value):
        for r in self.rows.values():
            if r["pnr"] == pnr_value:
                return r
        return None

    def pnr_exists(self, pnr_value):
        return pnr_value in self.taken or self.get_booking_by_pnr(pnr_value) is not None

    def set_pnr(self, booking_id, pnr_value):
        row = self.rows[booking_id]
        if row["pnr"] is None and row["status"] == "CONFIRMED":
            row["pnr"] = pnr_value
            return True
        return False


def test_generated_pnr_is_ten_digits():  # TC-PNR-01
    value = pnr.generate_pnr()
    assert len(value) == 10 and value.isdigit() and value[0] != "0"


def test_generate_retries_until_unique():
    seen = []

    def exists(candidate):
        seen.append(candidate)
        return len(seen) < 3  # first two are "taken"

    value = pnr.generate_pnr(exists)
    assert len(seen) == 3 and value == seen[-1]


def test_generate_gives_up_after_attempts():
    try:
        pnr.generate_pnr(lambda _p: True, attempts=3)
    except RuntimeError:
        return
    raise AssertionError("expected RuntimeError")


def test_confirmed_booking_gets_a_pnr():  # TC-PNR-01
    repo = FakeRepo([_row()])
    value = pnr.assign_pnr(1, repo=repo)
    assert repo.rows[1]["pnr"] == value and len(value) == 10


def test_assign_is_idempotent():
    repo = FakeRepo([_row(pnr_value="1234567890")])
    assert pnr.assign_pnr(1, repo=repo) == "1234567890"


def test_unconfirmed_or_missing_booking_gets_no_pnr():
    repo = FakeRepo([_row(status="PROVISIONAL")])
    for booking_id in (1, 99):
        try:
            pnr.assign_pnr(booking_id, repo=repo)
        except ValueError:
            continue
        raise AssertionError("expected ValueError")
    assert repo.rows[1]["pnr"] is None


def test_lookup_returns_correct_status():  # TC-PNR-01
    repo = FakeRepo([_row(pnr_value="1234567890", status="CONFIRMED")])
    booking = pnr.lookup_pnr("1234567890", repo=repo)
    assert booking["status"] == "CONFIRMED"
    assert booking["train_name"] == "Silicon Express"
    assert booking["travel_date"] == "2026-11-20"
    assert booking["fare"] == 900.0


def test_lookup_unknown_pnr_returns_none():
    assert pnr.lookup_pnr("9999999999", repo=FakeRepo([])) is None


def test_lookup_rejects_malformed_pnr():
    for bad in ["", None, "123", "12345678901", "12345abcde"]:
        try:
            pnr.lookup_pnr(bad, repo=FakeRepo([]))
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for {bad!r}")


def test_only_owner_or_admin_can_look_up():
    repo = FakeRepo([_row(pnr_value="1234567890", user_id=7)])
    assert pnr.lookup_pnr("1234567890", user_id=7, repo=repo) is not None
    assert pnr.lookup_pnr("1234567890", user_id=8, repo=repo) is None
    assert pnr.lookup_pnr("1234567890", user_id=8, role="admin", repo=repo) is not None
