
"""Tests for booking validation (RRS-F-021 and RRS-F-022)."""

import pytest

from modules.booking import create_booking


class FakeBookingRepo:
    def __init__(self):
        self.calls = []

    def create_provisional_booking(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "id": 101,
            "fare": 900,
            "held_until": "temporary test expiry",
        }


@pytest.fixture
def repo():
    return FakeBookingRepo()


def valid_booking(repo, **overrides):
    details = {
        "user_id": 1,
        "schedule_id": 10,
        "class_code": "3A",
        "passenger_name": "Narendra Kathare",
        "passenger_age": "21",
        "passenger_gender": "Male",
        "berth_preference": "Lower",
        "repo": repo,
    }
    details.update(overrides)
    return create_booking(**details)


def test_valid_booking_creates_provisional_booking(repo):
    result = valid_booking(repo)

    assert result["id"] == 101
    assert len(repo.calls) == 1
    assert repo.calls[0]["passenger_age"] == 21
    assert repo.calls[0]["passenger_name"] == "Narendra Kathare"


@pytest.mark.parametrize(
    "field,value",
    [
        ("user_id", 0),
        ("schedule_id", 0),
        ("passenger_name", ""),
        ("passenger_name", "   "),
        ("passenger_age", "abc"),
        ("passenger_age", 0),
        ("passenger_age", 121),
        ("passenger_gender", ""),
        ("passenger_gender", "Unknown"),
        ("class_code", "1A"),
        ("berth_preference", "Invalid"),
    ],
)
def test_invalid_booking_details_are_rejected(repo, field, value):
    with pytest.raises(ValueError):
        valid_booking(repo, **{field: value})

    assert repo.calls == []


def test_passenger_name_is_trimmed(repo):
    valid_booking(repo, passenger_name="  Rahul Kumar  ")

    assert repo.calls[0]["passenger_name"] == "Rahul Kumar"


def test_optional_berth_preference_can_be_empty(repo):
    valid_booking(repo, berth_preference="")

    assert repo.calls[0]["berth_preference"] is None
