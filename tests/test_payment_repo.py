"""Unit tests for payment repository and seat release (Issue #15, TC-Pay-02)."""

from decimal import Decimal
from unittest.mock import MagicMock, call, patch

import pytest

from repository import payment_repo


def _make_cursor(booking_row=None, existing_payment=None, rowcount=1):
    cursor = MagicMock()
    cursor.rowcount = rowcount

    # fetchone returns:
    # 1. booking row (from SELECT bookings ... FOR UPDATE)
    # 2. existing payment row (from SELECT 1 FROM payments ...)
    cursor.fetchone.side_effect = [booking_row, existing_payment]
    return cursor


def _make_context(cursor):
    context = MagicMock()
    context.__enter__.return_value = cursor
    return context


def test_successful_payment_confirms_booking_and_records_audit():
    """TC-Pay-02: Successful payment updates booking to CONFIRMED and audits."""
    booking_row = {
        "id": 101,
        "status": "PROVISIONAL",
        "fare": Decimal("900.00"),
        "held_until": "2026-11-20 12:00:00",
        "allocation_status": "CONFIRMED",
        "hold_active": True,
    }
    cursor = _make_cursor(booking_row=booking_row, existing_payment=None)

    with patch.object(payment_repo, "get_cursor", return_value=_make_context(cursor)), \
         patch.object(payment_repo, "write_audit_log") as mock_audit:

        result = payment_repo.record_payment(
            user_id=10,
            booking_id=101,
            transaction_ref="MOCK-TXN-12345",
            status="SUCCESS",
        )

    assert result["status"] == "SUCCESS"
    assert result["booking_status"] == "CONFIRMED"
    assert result["amount"] == Decimal("900.00")

    # Verify audit log was recorded with PAYMENT_SUCCESS
    mock_audit.assert_called_once_with(
        cursor,
        10,
        "PAYMENT_SUCCESS",
        101,
        "Payment SUCCESS; booking status: CONFIRMED",
    )


def test_failed_payment_releases_seat_and_records_audit():
    """TC-Pay-02 / AC-RRS-F-031: Failed payment cancels booking and releases hold."""
    booking_row = {
        "id": 102,
        "status": "PROVISIONAL",
        "fare": Decimal("350.00"),
        "held_until": "2026-11-20 12:00:00",
        "allocation_status": "CONFIRMED",
        "hold_active": True,
    }
    cursor = _make_cursor(booking_row=booking_row, existing_payment=None)

    with patch.object(payment_repo, "get_cursor", return_value=_make_context(cursor)), \
         patch.object(payment_repo, "write_audit_log") as mock_audit:

        result = payment_repo.record_payment(
            user_id=10,
            booking_id=102,
            transaction_ref="MOCK-TXN-FAILED",
            status="FAILED",
        )

    assert result["status"] == "FAILED"
    assert result["booking_status"] == "CANCELLED"

    # Verify that the booking status was set to CANCELLED and held_until set to NOW()
    update_calls = [
        c for c in cursor.execute.call_args_list
        if "UPDATE bookings" in c[0][0]
    ]
    assert len(update_calls) == 1
    update_sql, update_params = update_calls[0][0]
    assert "status = %s" in update_sql
    assert "held_until = NOW()" in update_sql
    assert update_params == ("CANCELLED", 102)

    # Verify audit log was recorded with PAYMENT_FAILED
    mock_audit.assert_called_once_with(
        cursor,
        10,
        "PAYMENT_FAILED",
        102,
        "Payment FAILED; booking status: CANCELLED",
    )


def test_timeout_payment_releases_seat_and_records_audit():
    """TC-Pay-02 / AC-RRS-F-031: Timed-out payment cancels booking and releases hold."""
    booking_row = {
        "id": 103,
        "status": "PROVISIONAL",
        "fare": Decimal("1300.00"),
        "held_until": "2026-11-20 12:00:00",
        "allocation_status": "CONFIRMED",
        "hold_active": True,
    }
    cursor = _make_cursor(booking_row=booking_row, existing_payment=None)

    with patch.object(payment_repo, "get_cursor", return_value=_make_context(cursor)), \
         patch.object(payment_repo, "write_audit_log") as mock_audit:

        result = payment_repo.record_payment(
            user_id=10,
            booking_id=103,
            transaction_ref="MOCK-TXN-TIMEOUT",
            status="TIMEOUT",
        )

    assert result["status"] == "TIMEOUT"
    assert result["booking_status"] == "CANCELLED"

    mock_audit.assert_called_once_with(
        cursor,
        10,
        "PAYMENT_TIMEOUT",
        103,
        "Payment TIMEOUT; booking status: CANCELLED",
    )


def test_expired_hold_forces_timeout_status():
    """When held_until has expired, payment outcome is forced to TIMEOUT."""
    booking_row = {
        "id": 104,
        "status": "PROVISIONAL",
        "fare": Decimal("900.00"),
        "held_until": "2026-11-20 11:50:00",
        "allocation_status": "CONFIRMED",
        "hold_active": False,  # hold already expired
    }
    cursor = _make_cursor(booking_row=booking_row, existing_payment=None)

    with patch.object(payment_repo, "get_cursor", return_value=_make_context(cursor)), \
         patch.object(payment_repo, "write_audit_log") as mock_audit:

        result = payment_repo.record_payment(
            user_id=10,
            booking_id=104,
            transaction_ref="MOCK-TXN-EXPIRED",
            status="SUCCESS",  # Attempted success after hold expired
        )

    assert result["status"] == "TIMEOUT"
    assert result["booking_status"] == "CANCELLED"

    mock_audit.assert_called_once_with(
        cursor,
        10,
        "PAYMENT_TIMEOUT",
        104,
        "Payment TIMEOUT; booking status: CANCELLED",
    )


def test_duplicate_payment_rejected():
    """Attempting a payment on a booking with existing payment record is rejected."""
    booking_row = {
        "id": 105,
        "status": "PROVISIONAL",
        "fare": Decimal("900.00"),
        "held_until": "2026-11-20 12:00:00",
        "allocation_status": "CONFIRMED",
        "hold_active": True,
    }
    existing_payment = {"id": 1}
    cursor = _make_cursor(booking_row=booking_row, existing_payment=existing_payment)

    with patch.object(payment_repo, "get_cursor", return_value=_make_context(cursor)):
        with pytest.raises(ValueError, match="Payment has already been processed for this booking."):
            payment_repo.record_payment(
                user_id=10,
                booking_id=105,
                transaction_ref="MOCK-TXN-DUP",
                status="SUCCESS",
            )


def test_payment_rejected_when_not_provisional():
    """Non-provisional bookings (already CONFIRMED or CANCELLED) cannot be paid."""
    booking_row = {
        "id": 106,
        "status": "CONFIRMED",
        "fare": Decimal("900.00"),
        "held_until": None,
        "allocation_status": "CONFIRMED",
        "hold_active": False,
    }
    cursor = _make_cursor(booking_row=booking_row)

    with patch.object(payment_repo, "get_cursor", return_value=_make_context(cursor)):
        with pytest.raises(ValueError, match="Booking is no longer awaiting payment."):
            payment_repo.record_payment(
                user_id=10,
                booking_id=106,
                transaction_ref="MOCK-TXN-1",
                status="SUCCESS",
            )


def test_payment_rejected_when_booking_not_found():
    """Unknown booking ID or mismatched user ID raises error."""
    cursor = _make_cursor(booking_row=None)

    with patch.object(payment_repo, "get_cursor", return_value=_make_context(cursor)):
        with pytest.raises(ValueError, match="Booking not found."):
            payment_repo.record_payment(
                user_id=999,
                booking_id=99999,
                transaction_ref="MOCK-TXN-1",
                status="SUCCESS",
            )


def test_invalid_status_and_txn_ref_rejected():
    with pytest.raises(ValueError, match="Invalid payment status."):
        payment_repo.record_payment(1, 1, "TXN-1", "PENDING")

    with pytest.raises(ValueError, match="Invalid transaction reference."):
        payment_repo.record_payment(1, 1, "", "SUCCESS")


def test_get_booking_for_user():
    expected = {"id": 1, "pnr": "1234567890", "passenger_name": "Test"}
    cursor = MagicMock()
    cursor.fetchone.return_value = expected

    with patch.object(payment_repo, "get_cursor", return_value=_make_context(cursor)):
        result = payment_repo.get_booking_for_user(user_id=7, booking_id=1)

    assert result == expected
    cursor.execute.assert_called_once()
