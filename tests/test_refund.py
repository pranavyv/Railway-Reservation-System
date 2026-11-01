from datetime import date, datetime, time
from decimal import Decimal

from modules import refund

POLICY = [(4, 50), (48, 90), (12, 75)]  # unsorted on purpose


def test_percent_by_time_left():  # TC-Cancel-02
    assert refund.refund_percent(100, POLICY) == 90
    assert refund.refund_percent(30, POLICY) == 75
    assert refund.refund_percent(6, POLICY) == 50


def test_threshold_boundaries_are_inclusive():
    assert refund.refund_percent(48, POLICY) == 90
    assert refund.refund_percent(47.99, POLICY) == 75
    assert refund.refund_percent(12, POLICY) == 75
    assert refund.refund_percent(4, POLICY) == 50
    assert refund.refund_percent(3.99, POLICY) == 0


def test_no_refund_after_departure():
    assert refund.refund_percent(-1, POLICY) == 0
    assert refund.refund_percent(0, POLICY) == 0


def test_default_policy_used_when_table_empty():
    assert refund.refund_percent(100, None) == 90
    assert refund.refund_percent(100, []) == 90


def test_amount_matches_policy():  # TC-Cancel-02
    result = refund.calculate_refund(900, 60, POLICY)
    assert result["percent"] == 90
    assert result["amount"] == Decimal("810.00")


def test_amount_is_rounded_to_paise():
    result = refund.calculate_refund(Decimal("333.33"), 30, POLICY)  # 75%
    assert result["amount"] == Decimal("250.00")
    assert refund.calculate_refund(Decimal("99.99"), 100, POLICY)["amount"] == Decimal("89.99")


def test_zero_refund_amount():
    assert refund.calculate_refund(900, 1, POLICY)["amount"] == Decimal("0.00")


def test_hours_before_departure():
    now = datetime(2026, 11, 18, 6, 0)
    assert refund.hours_before_departure(date(2026, 11, 20), time(6, 0), now) == 48
    assert refund.hours_before_departure(date(2026, 11, 18), time(5, 0), now) == -1
