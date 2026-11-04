"""Unit tests for booking audit log repository operations (Issue #19, TC-Ops-01)."""

from unittest.mock import MagicMock, patch
import pytest

from repository import audit_repo


def test_write_audit_log():
    """Verify that an audit event is inserted correctly."""

    cursor = MagicMock()

    expected_event = {
        "id": 1,
        "user_id": 10,
        "action": "BOOKING_CREATED",
        "booking_id": 101,
        "details": "Provisional booking created",
        "created_at": "2026-11-04 10:00:00",
    }

    cursor.fetchone.return_value = expected_event

    result = audit_repo.write_audit_log(
        cursor,
        10,
        "BOOKING_CREATED",
        101,
        "Provisional booking created",
    )

    assert result == expected_event

    cursor.execute.assert_called_once()

    query, params = cursor.execute.call_args[0]

    assert "INSERT INTO audit_log" in query
    assert "booking_id" in query
    assert params == (
        10,
        "BOOKING_CREATED",
        101,
        "Provisional booking created",
    )


def test_get_booking_audit_logs():
    """Verify that audit events are retrieved for a booking in chronological order."""

    expected_logs = [
        {
            "id": 1,
            "user_id": 10,
            "action": "BOOKING_CREATED",
            "booking_id": 101,
            "details": "Provisional booking created",
            "created_at": "2026-11-04 10:00:00",
        },
        {
            "id": 2,
            "user_id": 10,
            "action": "PAYMENT_SUCCESS",
            "booking_id": 101,
            "details": "Payment SUCCESS; booking status: CONFIRMED",
            "created_at": "2026-11-04 10:05:00",
        },
    ]

    cursor = MagicMock()
    cursor.fetchall.return_value = expected_logs

    mock_context = MagicMock()
    mock_context.__enter__.return_value = cursor

    with patch.object(
        audit_repo,
        "get_cursor",
        return_value=mock_context,
    ) as mock_get_cursor:

        result = audit_repo.get_booking_audit_logs(101)

    assert result == expected_logs

    mock_get_cursor.assert_called_once_with()

    cursor.execute.assert_called_once()

    query, params = cursor.execute.call_args[0]

    assert "FROM audit_log" in query
    assert "WHERE booking_id = %s" in query
    assert "ORDER BY created_at ASC" in query
    assert params == (101,)


@pytest.mark.parametrize("action", [
    "BOOKING_CREATED",
    "PAYMENT_SUCCESS",
    "PAYMENT_FAILED",
    "PAYMENT_TIMEOUT",
    "BOOKING_CANCELLED",
    "BOOKING_EXPIRED",
])
def test_all_six_required_lifecycle_actions_supported(action):
    """TC-Ops-01: Ensure all 6 required audit action types can be written."""
    cursor = MagicMock()
    cursor.fetchone.return_value = {
        "id": 42,
        "user_id": 7,
        "action": action,
        "booking_id": 200,
        "details": f"Test event {action}",
        "created_at": "2026-11-04 12:00:00",
    }

    result = audit_repo.write_audit_log(
        cursor,
        7,
        action,
        200,
        f"Test event {action}",
    )

    assert result["action"] == action
    assert result["booking_id"] == 200
    cursor.execute.assert_called_once()
    query, params = cursor.execute.call_args[0]
    assert "INSERT INTO audit_log" in query
    assert params == (7, action, 200, f"Test event {action}")


def test_get_recent_audit_logs_unfiltered_and_filtered():
    """Verify retrieval of recent audit logs with optional action filter."""
    cursor = MagicMock()
    cursor.fetchall.return_value = [{"id": 1, "action": "PAYMENT_FAILED"}]

    mock_context = MagicMock()
    mock_context.__enter__.return_value = cursor

    with patch.object(audit_repo, "get_cursor", return_value=mock_context):
        # 1. Unfiltered
        res1 = audit_repo.get_recent_audit_logs(limit=25)
        assert len(res1) == 1
        query1, params1 = cursor.execute.call_args[0]
        assert "LIMIT %s" in query1
        assert params1 == (25,)

        # 2. Filtered by action
        res2 = audit_repo.get_recent_audit_logs(limit=10, action="PAYMENT_FAILED")
        assert len(res2) == 1
        query2, params2 = cursor.execute.call_args[0]
        assert "WHERE action = %s" in query2
        assert params2 == ("PAYMENT_FAILED", 10)
