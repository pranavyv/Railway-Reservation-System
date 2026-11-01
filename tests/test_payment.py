
"""Tests for mock payment processing."""

from unittest.mock import Mock, patch

import pytest

from modules.payment import process_payment


@pytest.fixture
def mock_repo():
    return Mock()


@patch("modules.payment.pnr_module.assign_pnr", return_value="1234567890")
def test_successful_payment(mock_pnr, mock_repo):
    mock_repo.record_payment.return_value = {
        "booking_id": 1,
        "status": "SUCCESS",
        "booking_status": "CONFIRMED",
        "pnr": None,
    }

    result = process_payment(1, 1, "SUCCESS", mock_repo)

    assert result["status"] == "SUCCESS"
    assert result["pnr"] == "1234567890"
    mock_repo.record_payment.assert_called_once()
    mock_pnr.assert_called_once_with(1)


@patch("modules.payment.pnr_module.assign_pnr")
def test_rac_booking_gets_no_pnr(mock_pnr, mock_repo):
    mock_repo.record_payment.return_value = {
        "booking_id": 1,
        "status": "SUCCESS",
        "booking_status": "RAC",
        "pnr": None,
    }

    result = process_payment(1, 1, "SUCCESS", mock_repo)

    assert result["pnr"] is None
    mock_pnr.assert_not_called()


@pytest.mark.parametrize("outcome", ["FAILED", "TIMEOUT"])
def test_unsuccessful_payment(mock_repo, outcome):
    mock_repo.record_payment.return_value = {
        "booking_id": 1,
        "status": outcome,
        "booking_status": "CANCELLED",
        "pnr": None,
    }

    result = process_payment(1, 1, outcome, mock_repo)

    assert result["status"] == outcome
    assert result["booking_status"] == "CANCELLED"
    assert result["pnr"] is None


def test_transaction_reference_generated(mock_repo):
    mock_repo.record_payment.return_value = {
        "booking_id": 1,
        "status": "SUCCESS",
        "booking_status": "RAC",
        "pnr": None,
    }

    process_payment(1, 1, "SUCCESS", mock_repo)

    kwargs = mock_repo.record_payment.call_args.kwargs

    assert kwargs["transaction_ref"].startswith("MOCK-")
    assert kwargs["status"] == "SUCCESS"


@pytest.mark.parametrize("user_id", [0, -1, "1", True])
def test_invalid_user_id(mock_repo, user_id):
    with pytest.raises(ValueError):
        process_payment(user_id, 1, repo=mock_repo)


@pytest.mark.parametrize("booking_id", [0, -1, "1", True])
def test_invalid_booking_id(mock_repo, booking_id):
    with pytest.raises(ValueError):
        process_payment(1, booking_id, repo=mock_repo)


def test_invalid_payment_outcome(mock_repo):
    with pytest.raises(ValueError):
        process_payment(1, 1, "PENDING", mock_repo)


def test_payment_outcome_is_case_insensitive(mock_repo):
    mock_repo.record_payment.return_value = {
        "booking_id": 1,
        "status": "SUCCESS",
        "booking_status": "RAC",
        "pnr": None,
    }

    process_payment(1, 1, "success", mock_repo)

    kwargs = mock_repo.record_payment.call_args.kwargs
    assert kwargs["status"] == "SUCCESS"
