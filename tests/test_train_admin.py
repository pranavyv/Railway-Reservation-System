"""TC-Admin-01 (RRS-F-060): admin train and schedule management."""
from datetime import date

from modules import train_admin
from modules.train_admin import Conflict, NotFound, ValidationError

TODAY = date(2026, 11, 10)
GOOD_TRAIN = {"train_no": "10006", "name": "Test Express", "source": "Bengaluru",
              "destination": "Mysuru", "departure_time": "06:30", "arrival_time": "09:00"}
GOOD_CLASSES = [{"class_code": "sl", "total_seats": 72, "fare": 350},
                {"class_code": "3A", "total_seats": 64, "fare": "900.50"}]


class FakeRepo:
    def __init__(self):
        self.calls = []
        self.rows = []
        self.train = {"id": 1, "train_no": "10006", "name": "Test Express", "source": "Bengaluru",
                      "destination": "Mysuru", "departure_time": "06:30:00",
                      "arrival_time": "09:00:00", "active": True}
        self.fail = None
        self.missing = False

    def _maybe_fail(self):
        if self.fail:
            raise ValueError(self.fail)

    def list_rows(self):
        return self.rows

    def insert_train(self, values, actor, details):
        self._maybe_fail()
        self.calls.append(("insert_train", values, actor, details))
        return dict(self.train, **values, id=1, active=True)

    def update_train(self, train_id, values, actor, details):
        self._maybe_fail()
        self.calls.append(("update_train", train_id, values, actor, details))
        return None if self.missing else dict(self.train, **values)

    def remove_train(self, train_id, actor):
        self.calls.append(("remove_train", train_id, actor))
        return None if self.missing else "deleted"

    def insert_schedule(self, train_id, travel_date, classes, actor, details):
        self._maybe_fail()
        self.calls.append(("insert_schedule", train_id, travel_date, classes, actor, details))
        return None if self.missing else {"id": 5}

    def update_schedule(self, schedule_id, classes, actor, details):
        self._maybe_fail()
        self.calls.append(("update_schedule", schedule_id, classes, actor, details))
        return None if self.missing else {"id": schedule_id}

    def remove_schedule(self, schedule_id, actor, details):
        self._maybe_fail()
        self.calls.append(("remove_schedule", schedule_id, actor, details))
        return None if self.missing else True


def _errors(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except ValidationError as error:
        return error.errors
    raise AssertionError("expected ValidationError")


# ---- validation ----------------------------------------------------------------
def test_valid_train_is_cleaned():
    clean = train_admin.validate_train(dict(GOOD_TRAIN, train_no=" ab12 ", name="  Test   Express "))
    assert clean["train_no"] == "AB12" and clean["name"] == "Test Express"
    assert clean["departure_time"] == "06:30"


def test_train_rejects_bad_fields():
    errors = _errors(train_admin.validate_train, {"train_no": "bad no!", "name": "", "source": "A",
                                                  "destination": "a", "departure_time": "25:00",
                                                  "arrival_time": "x"})
    text = " ".join(errors)
    for expected in ("Train number", "Train name", "Departure time", "Arrival time", "different"):
        assert expected in text


def test_partial_update_checks_only_supplied_fields():
    assert train_admin.validate_train({"name": "New name"}, partial=True) == {"name": "New name"}
    assert _errors(train_admin.validate_train, {}, partial=True) == ["Nothing to update."]
    assert _errors(train_admin.validate_train, {"active": "yes"}, partial=True)


def test_classes_validation():
    clean = train_admin.validate_classes(GOOD_CLASSES)
    assert clean[0] == {"class_code": "SL", "total_seats": 72, "fare": 350.0}
    assert clean[1]["fare"] == 900.5
    for bad in (None, [], [{"class_code": "XX", "total_seats": 5, "fare": 1}],
                [{"class_code": "SL", "total_seats": 0, "fare": 10}],
                [{"class_code": "SL", "total_seats": 5.5, "fare": 10}],
                [{"class_code": "SL", "total_seats": True, "fare": 10}],
                [{"class_code": "SL", "total_seats": 5, "fare": 0}],
                [{"class_code": "SL", "total_seats": 5, "fare": "free"}],
                [{"class_code": "SL", "total_seats": 5, "fare": 1}, {"class_code": "sl", "total_seats": 5, "fare": 1}],
                [{"class_code": "SL", "total_seats": 5000, "fare": 10}]):
        _errors(train_admin.validate_classes, bad)


def test_travel_date_validation():
    assert train_admin.validate_travel_date("2026-11-10", today=TODAY) == "2026-11-10"
    for bad in ("2026-11-09", "10-11-2026", "", None):
        _errors(train_admin.validate_travel_date, bad, today=TODAY)


# ---- actions -------------------------------------------------------------------
def test_add_train_records_actor_and_returns_view():
    repo = FakeRepo()
    view = train_admin.add_train(GOOD_TRAIN, 42, repo=repo)
    assert view["train_no"] == "10006" and view["departure_time"] == "06:30" and view["active"] is True
    assert repo.calls[0][2] == 42


def test_invalid_train_never_reaches_the_repository():
    repo = FakeRepo()
    _errors(train_admin.add_train, {"train_no": ""}, 1, repo=repo)
    assert repo.calls == []


def test_duplicate_train_becomes_conflict():
    repo = FakeRepo()
    repo.fail = "A train with this number already exists."
    try:
        train_admin.add_train(GOOD_TRAIN, 1, repo=repo)
    except Conflict as error:
        assert "already exists" in str(error)
    else:
        raise AssertionError("expected Conflict")


def test_update_and_remove_train_not_found():
    repo = FakeRepo()
    repo.missing = True
    for call in (lambda: train_admin.update_train(9, {"name": "X"}, 1, repo=repo),
                 lambda: train_admin.remove_train(9, 1, repo=repo)):
        try:
            call()
        except NotFound:
            continue
        raise AssertionError("expected NotFound")


def test_update_train_passes_only_changed_fields_and_audit_details():
    repo = FakeRepo()
    train_admin.update_train(1, {"name": "Renamed", "ignored": "x"}, 7, repo=repo)
    _, train_id, values, actor, details = repo.calls[0]
    assert (train_id, values, actor) == (1, {"name": "Renamed"}, 7)
    assert details == {"train_id": 1, "name": "Renamed"}


def test_add_schedule_cleans_classes_and_date():
    repo = FakeRepo()
    result = train_admin.add_schedule(1, {"travel_date": "2026-12-01", "classes": GOOD_CLASSES}, 3,
                                      repo=repo, today=TODAY)
    assert result["travel_date"] == "2026-12-01" and result["classes"][0]["class_code"] == "SL"
    assert repo.calls[0][2] == "2026-12-01" and repo.calls[0][4] == 3


def test_schedule_clash_and_missing_train():
    repo = FakeRepo()
    repo.fail = "This train already has a schedule on that date."
    try:
        train_admin.add_schedule(1, {"travel_date": "2026-12-01", "classes": GOOD_CLASSES}, 1,
                                 repo=repo, today=TODAY)
    except Conflict:
        pass
    else:
        raise AssertionError("expected Conflict")
    repo = FakeRepo()
    repo.missing = True
    try:
        train_admin.add_schedule(99, {"travel_date": "2026-12-01", "classes": GOOD_CLASSES}, 1,
                                 repo=repo, today=TODAY)
    except NotFound:
        pass
    else:
        raise AssertionError("expected NotFound")


def test_remove_schedule_with_bookings_is_a_conflict():
    repo = FakeRepo()
    repo.fail = "This schedule has bookings and cannot be removed."
    try:
        train_admin.remove_schedule(5, 1, repo=repo)
    except Conflict as error:
        assert "bookings" in str(error)
    else:
        raise AssertionError("expected Conflict")


def test_list_trains_groups_rows_into_trains_schedules_classes():
    repo = FakeRepo()
    base = {"train_id": 1, "train_no": "10001", "name": "Silicon Express", "source": "Bengaluru",
            "destination": "Chennai", "departure_time": "06:00:00", "arrival_time": "11:30:00",
            "active": True}
    repo.rows = [
        dict(base, schedule_id=10, travel_date=date(2026, 11, 20), class_code="3A", total_seats=64, fare=900),
        dict(base, schedule_id=10, travel_date=date(2026, 11, 20), class_code="SL", total_seats=72, fare=350),
        dict(base, schedule_id=11, travel_date=date(2026, 11, 21), class_code="SL", total_seats=72, fare=350),
        dict(base, train_id=2, train_no="10002", schedule_id=None, travel_date=None, class_code=None,
             total_seats=None, fare=None),
    ]
    trains = train_admin.list_trains(repo=repo)
    assert [t["train_no"] for t in trains] == ["10001", "10002"]
    assert [len(s["classes"]) for s in trains[0]["schedules"]] == [2, 1]
    assert trains[0]["departure_time"] == "06:00" and trains[1]["schedules"] == []
