"""Admin reports and management module (Issue #18, TC-Admin-02).

Provides:
- Date range parsing and validation
- Report aggregation across bookings, occupancy, and revenue
- Audit trail retrieval for individual bookings (Issue #19)
"""

from datetime import date, datetime
from repository import admin_repo, audit_repo


def parse_date_range(start_str, end_str):
    """Validate and clean optional date strings in YYYY-MM-DD format.

    Returns ((start_date_or_none, end_date_or_none), errors_list).
    """
    errors = []
    start_date = None
    end_date = None

    if start_str and str(start_str).strip():
        try:
            start_date = datetime.strptime(str(start_str).strip(), "%Y-%m-%d").date()
        except ValueError:
            errors.append("Start date must be in YYYY-MM-DD format.")

    if end_str and str(end_str).strip():
        try:
            end_date = datetime.strptime(str(end_str).strip(), "%Y-%m-%d").date()
        except ValueError:
            errors.append("End date must be in YYYY-MM-DD format.")

    if start_date and end_date and start_date > end_date:
        errors.append("Start date cannot be after end date.")

    if errors:
        return (None, None), errors

    return (
        str(start_date) if start_date else None,
        str(end_date) if end_date else None,
    ), []


def generate_report(start_str=None, end_str=None, repo=None):
    """Generate admin booking, occupancy and revenue report for selected date range."""
    (start_d, end_d), errors = parse_date_range(start_str, end_str)
    if errors:
        raise ValueError("; ".join(errors))

    r = repo if repo is not None else admin_repo
    return r.get_full_admin_report(start_date=start_d, end_date=end_d)


def get_audit_trail(booking_id, repo=None):
    """Retrieve chronologically ordered audit logs for a sample booking."""
    if not isinstance(booking_id, int) or isinstance(booking_id, bool) or booking_id <= 0:
        raise ValueError("Valid booking_id is required.")

    r = repo if repo is not None else audit_repo
    return r.get_booking_audit_logs(booking_id)
