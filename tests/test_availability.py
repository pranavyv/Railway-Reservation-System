
"""Tests for seat availability business logic."""

from unittest.mock import patch

import pytest

from modules.allocation import check_availability


MOCK_RESULT = {
    "train_id": 1,
    "train_no": "10001",
    "train_name": "Silicon Express",
    "travel_date": "2026-11-15",
    "class_code": "3A",
    "total_seats": 64,
    "allocated_seats": 20
}


@patch("modules.allocation.get_seat_availability")
def test_available_seats(mock_query):
    mock_query.return_value = MOCK_RESULT

    result = check_availability(1, "2026-11-15", "3A")

    assert result["total_seats"] == 64
    assert result["allocated_seats"] == 20
    assert result["available_seats"] == 44
    assert result["status"] == "AVAILABLE"


@patch("modules.allocation.get_seat_availability")
def test_fully_booked(mock_query):
    data = MOCK_RESULT.copy()
    data["allocated_seats"] = 64
    mock_query.return_value = data

    result = check_availability(1, "2026-11-15", "3A")

    assert result["available_seats"] == 0
    assert result["status"] == "FULL"


def test_invalid_train_id():
    with pytest.raises(ValueError):
        check_availability(0, "2026-11-15", "3A")


def test_invalid_class():
    with pytest.raises(ValueError):
        check_availability(1, "2026-11-15", "1A")


@patch("modules.allocation.get_seat_availability")
def test_train_not_found(mock_query):
    mock_query.return_value = None

    result = check_availability(1, "2026-11-15", "3A")

    assert result is None
