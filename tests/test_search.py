from datetime import date, time

from modules import search

TODAY = date(2026, 10, 29)


class FakeTrainRepo:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def search_rows(self, source, destination, travel_date):
        self.calls.append((source, destination, travel_date))
        return self.rows


def _row(schedule_id, cls, fare):
    return {
        "train_id": 1, "schedule_id": schedule_id, "train_no": "10001", "name": "Silicon Express",
        "source": "Bengaluru", "destination": "Chennai",
        "departure_time": time(6, 0), "arrival_time": time(11, 30),
        "travel_date": date(2026, 11, 1), "class_code": cls, "fare": fare, "total_seats": 72,
    }


def test_matching_trains_returned_with_class_and_timing():  # TC-Search-01
    repo = FakeTrainRepo([_row(7, "SL", 350), _row(7, "3A", 900)])
    trains, errors = search.search_trains("Bengaluru", "Chennai", "2026-11-01", repo=repo, today=TODAY)
    assert errors == []
    assert len(trains) == 1
    assert [c["class_code"] for c in trains[0]["classes"]] == ["SL", "3A"]
    assert trains[0]["departure_time"] == time(6, 0)
    assert repo.calls == [("Bengaluru", "Chennai", date(2026, 11, 1))]


def test_no_match_returns_empty_list():  # TC-Search-02
    trains, errors = search.search_trains("Bengaluru", "Pune", "2026-11-01", repo=FakeTrainRepo([]), today=TODAY)
    assert trains == []
    assert errors == []


def test_missing_fields_rejected_without_querying():
    repo = FakeTrainRepo([])
    trains, errors = search.search_trains("", "", "", repo=repo, today=TODAY)
    assert trains == [] and len(errors) == 3
    assert repo.calls == []


def test_same_source_and_destination_rejected():
    _, errors = search.parse_search("Chennai", "chennai", "2026-11-01", today=TODAY)
    assert any("different" in e for e in errors)


def test_past_and_malformed_dates_rejected():
    _, past = search.parse_search("A", "B", "2026-10-01", today=TODAY)
    _, bad = search.parse_search("A", "B", "01/11/2026", today=TODAY)
    assert any("past" in e for e in past)
    assert any("YYYY-MM-DD" in e for e in bad)


def test_today_is_allowed():
    cleaned, errors = search.parse_search("A", "B", "2026-10-29", today=TODAY)
    assert errors == [] and cleaned[2] == TODAY
