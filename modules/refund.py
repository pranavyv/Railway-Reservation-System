"""Refund calculation (RRS-F-042).

Policy rows are (min_hours_before_departure, refund_percent). The highest
threshold that the remaining time still meets decides the percentage; below
the smallest threshold (or after departure) the refund is 0%.
"""
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

# Used only when the cancellation_policy table is empty.
DEFAULT_POLICY = [(48, 90), (12, 75), (4, 50)]


def hours_before_departure(travel_date, departure_time, now):
    departure = datetime.combine(travel_date, departure_time)
    return (departure - now).total_seconds() / 3600


def refund_percent(hours_left, policy=None):
    rows = sorted(policy or DEFAULT_POLICY, key=lambda row: row[0], reverse=True)
    for min_hours, percent in rows:
        if hours_left >= min_hours:
            return percent
    return 0


def calculate_refund(fare, hours_left, policy=None):
    """Returns {"percent": int, "amount": Decimal rounded to 2 places}."""
    percent = refund_percent(hours_left, policy)
    amount = (Decimal(str(fare)) * percent / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"percent": percent, "amount": amount}
