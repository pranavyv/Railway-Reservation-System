"""Tests for booking repository audit logging."""

from unittest.mock import MagicMock, call, patch

from repository import booking_repo


def test_expired_bookings_generate_audit_events():
    """Verify that every expired provisional booking is audited."""

    cursor = MagicMock()

    cursor.fetchone.side_effect = [
        {"total_seats": 10, "fare": 900},
        {"allocated": 0},
        {"id": 103, "fare": 900, "held_until": "test expiry"},
    ]

    expired_bookings = [
        {"id": 101, "user_id": 10},
        {"id": 102, "user_id": 20},
    ]
    cursor.fetchall.return_value = expired_bookings

    mock_context = MagicMock()
    mock_context.__enter__.return_value = cursor

    with patch.object(
        booking_repo, "get_cursor", return_value=mock_context
    ), patch.object(booking_repo, "write_audit_log") as mock_audit:

        booking_repo.create_provisional_booking(
            user_id=30,
            schedule_id=5,
            class_code="3A",
            passenger_name="Test Passenger",
            passenger_age=21,
            passenger_gender="Male",
            berth_preference="Lower",
        )

    assert mock_audit.call_args_list == [
        call(cursor, 10, "BOOKING_EXPIRED", 101,
             "Provisional booking hold expired"),
        call(cursor, 20, "BOOKING_EXPIRED", 102,
             "Provisional booking hold expired"),
        call(cursor, 30, "BOOKING_CREATED", 103,
             "Provisional booking created"),
    ]