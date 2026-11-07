"""Unit tests for administrative reports and management module (Issue #18, TC-Admin-02)."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from modules import admin
from repository import admin_repo


def test_parse_date_range_valid():
    (start, end), errors = admin.parse_date_range("2026-11-01", "2026-11-30")
    assert errors == []
    assert start == "2026-11-01"
    assert end == "2026-11-30"


def test_parse_date_range_optional():
    (start, end), errors = admin.parse_date_range("", None)
    assert errors == []
    assert start is None
    assert end is None


def test_parse_date_range_invalid_format():
    _, errors = admin.parse_date_range("01-11-2026", "invalid-date")
    assert len(errors) == 2
    assert "YYYY-MM-DD" in errors[0]
    assert "YYYY-MM-DD" in errors[1]


def test_parse_date_range_start_after_end():
    _, errors = admin.parse_date_range("2026-12-01", "2026-11-01")
    assert len(errors) == 1
    assert "Start date cannot be after end date" in errors[0]


def test_generate_report_calls_repository():
    mock_repo = MagicMock()
    mock_repo.get_full_admin_report.return_value = {
        "summary": {"total_bookings": 10},
        "bookings": {},
        "occupancy": {},
        "revenue": {},
    }

    res = admin.generate_report("2026-11-01", "2026-11-30", repo=mock_repo)
    assert res["summary"]["total_bookings"] == 10
    mock_repo.get_full_admin_report.assert_called_once_with(
        start_date="2026-11-01", end_date="2026-11-30"
    )


def test_generate_report_rejects_invalid_date_range():
    with pytest.raises(ValueError, match="Start date cannot be after end date"):
        admin.generate_report("2026-12-01", "2026-11-01")


def test_get_booking_report_aggregation():
    cursor = MagicMock()
    cursor.fetchone.return_value = {
        "total_bookings": 25,
        "confirmed_count": 18,
        "cancelled_count": 4,
        "rac_count": 2,
        "waitlisted_count": 1,
        "provisional_count": 0,
    }
    cursor.fetchall.side_effect = [
        [{"class_code": "3A", "count": 15}, {"class_code": "SL", "count": 10}],
        [{"id": 1, "pnr": "1234567890", "passenger_name": "Test", "class_code": "3A", "status": "CONFIRMED", "fare": Decimal("900.00"), "created_at": "2026-11-04 10:00:00"}],
    ]

    mock_context = MagicMock()
    mock_context.__enter__.return_value = cursor

    with patch.object(admin_repo, "get_cursor", return_value=mock_context):
        report = admin_repo.get_booking_report("2026-11-01", "2026-11-30")

    assert report["total_bookings"] == 25
    assert report["confirmed"] == 18
    assert report["cancelled"] == 4
    assert report["rac"] == 2
    assert report["waitlisted"] == 1
    assert report["by_class"] == {"3A": 15, "SL": 10}
    assert len(report["recent_bookings"]) == 1


def test_get_occupancy_report_aggregation():
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        {
            "train_id": 1,
            "train_no": "10001",
            "train_name": "Silicon Express",
            "source": "Bengaluru",
            "destination": "Chennai",
            "schedule_id": 10,
            "travel_date": "2026-11-20",
            "class_code": "3A",
            "total_seats": 64,
            "allocated_seats": 48,
            "rac_count": 2,
            "waitlist_count": 0,
        },
        {
            "train_id": 1,
            "train_no": "10001",
            "train_name": "Silicon Express",
            "source": "Bengaluru",
            "destination": "Chennai",
            "schedule_id": 10,
            "travel_date": "2026-11-20",
            "class_code": "SL",
            "total_seats": 72,
            "allocated_seats": 72,
            "rac_count": 5,
            "waitlist_count": 2,
        },
    ]

    mock_context = MagicMock()
    mock_context.__enter__.return_value = cursor

    with patch.object(admin_repo, "get_cursor", return_value=mock_context):
        report = admin_repo.get_occupancy_report()

    assert report["total_capacity"] == 136
    assert report["total_allocated"] == 120
    assert report["total_remaining"] == 16
    assert report["overall_occupancy_percent"] == 88.24
    assert len(report["schedules"]) == 2
    assert report["schedules"][0]["occupancy_percent"] == 75.0
    assert report["schedules"][1]["occupancy_percent"] == 100.0


def test_get_revenue_report_aggregation():
    cursor = MagicMock()
    # 1. Successful payments query
    # 2. Failed / timeout payments query
    # 3. Refunds query
    cursor.fetchone.side_effect = [
        {"gross_revenue": Decimal("25000.00"), "success_count": 25},
        {"failed_count": 3, "timeout_count": 2},
        {"total_refunds": Decimal("2500.00"), "refund_count": 4},
    ]

    mock_context = MagicMock()
    mock_context.__enter__.return_value = cursor

    with patch.object(admin_repo, "get_cursor", return_value=mock_context):
        report = admin_repo.get_revenue_report("2026-11-01", "2026-11-30")

    assert report["gross_revenue"] == 25000.00
    assert report["total_refunds"] == 2500.00
    assert report["net_revenue"] == 22500.00
    assert report["successful_payments_count"] == 25
    assert report["failed_payments_count"] == 3
    assert report["timeout_payments_count"] == 2
    assert report["refund_count"] == 4


def test_empty_reports_handle_zeroes_gracefully():
    """Verify that when no records exist, reports return clean zero metrics without crashing."""
    cursor = MagicMock()
    cursor.fetchone.side_effect = [
        {},  # booking summary
        {},  # revenue
        {},  # payment statuses
        {},  # refunds
    ]
    cursor.fetchall.side_effect = [
        [],  # booking class rows
        [],  # recent bookings
        [],  # occupancy schedules
    ]

    mock_context = MagicMock()
    mock_context.__enter__.return_value = cursor

    with patch.object(admin_repo, "get_cursor", return_value=mock_context):
        full = admin_repo.get_full_admin_report()

    assert full["summary"]["total_bookings"] == 0
    assert full["summary"]["gross_revenue"] == 0.0
    assert full["summary"]["total_refunds"] == 0.0
    assert full["summary"]["net_revenue"] == 0.0
    assert full["summary"]["overall_occupancy_percent"] == 0.0


def test_get_audit_trail_validation():
    with pytest.raises(ValueError, match="Valid booking_id is required"):
        admin.get_audit_trail(-1)

    with pytest.raises(ValueError, match="Valid booking_id is required"):
        admin.get_audit_trail("abc")
