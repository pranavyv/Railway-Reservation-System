from modules import seat_allocation as alloc


class FakeRepo:
    def __init__(self, counts):
        self.counts = counts
        self.calls = []

    def get_counts(self, schedule_id, class_code):
        self.calls.append((schedule_id, class_code))
        return self.counts


def _counts(total=10, held=0, rac=0, wl=0):
    return {"total_seats": total, "held_seats": held, "rac_count": rac, "waitlist_count": wl}


def test_rac_capacity_is_ten_percent_rounded_up():
    assert alloc.rac_capacity(64) == 7
    assert alloc.rac_capacity(10) == 1
    assert alloc.rac_capacity(1) == 1
    assert alloc.rac_capacity(0) == 0


def test_confirmed_while_seats_are_free():  # TC-Alloc-01
    assert alloc.decide_status(total_seats=10, held_seats=0, rac_count=0) == "CONFIRMED"
    assert alloc.decide_status(total_seats=10, held_seats=9, rac_count=0) == "CONFIRMED"


def test_rac_when_full_and_rac_quota_open():  # TC-Alloc-01
    assert alloc.decide_status(total_seats=10, held_seats=10, rac_count=0) == "RAC"


def test_waitlisted_when_full_and_rac_quota_full():  # TC-Alloc-01
    assert alloc.decide_status(total_seats=10, held_seats=10, rac_count=1) == "WAITLISTED"
    assert alloc.decide_status(total_seats=64, held_seats=64, rac_count=7) == "WAITLISTED"


def test_assign_status_uses_repo_counts():
    repo = FakeRepo(_counts(total=10, held=10, rac=0, wl=3))
    result = alloc.assign_status(5, "3a", repo=repo)
    assert repo.calls == [(5, "3A")]
    assert result["status"] == "RAC"
    assert result["waitlist_count"] == 3
    assert result["rac_capacity"] == 1


def test_assign_status_unknown_schedule_returns_none():
    assert alloc.assign_status(5, "SL", repo=FakeRepo(None)) is None


def test_assign_status_validates_input():
    for bad in [(0, "SL"), (-1, "SL"), ("1", "SL"), (True, "SL"), (1, ""), (1, None)]:
        try:
            alloc.assign_status(bad[0], bad[1], repo=FakeRepo(_counts()))
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for {bad}")
