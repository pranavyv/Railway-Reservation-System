"""Health check and admin availability report (RRS-NF-002, TC-Ops)."""
from flask import Blueprint, current_app, jsonify

from modules import monitoring
from modules.rbac import admin_required

ops_bp = Blueprint("ops", __name__)


def _db_ok():
    from repository import health_repo  # lazy import keeps tests database-free

    try:
        return bool(health_repo.check_db())
    except Exception as error:  # log the type only: driver messages can name hosts and users
        current_app.logger.error("Health check: database unreachable (%s)", type(error).__name__)
        return False


def _payment_counts():
    from repository import health_repo

    try:
        row = health_repo.payment_counts()
        return int(row["total"]), int(row["failed"])
    except Exception as error:
        current_app.logger.error("Availability report: payment counts unavailable (%s)", type(error).__name__)
        return None


@ops_bp.get("/health")
def health():
    """Public and minimal: no versions, hostnames or error text."""
    if _db_ok():
        return jsonify(status="ok", database="ok"), 200
    return jsonify(status="degraded", database="down"), 503


@ops_bp.get("/api/admin/availability")
@admin_required
def availability():
    probe = monitoring.availability_from_log(current_app.config["UPTIME_LOG"])
    target = current_app.config["AVAILABILITY_TARGET"]
    payments = _payment_counts()
    transaction_failure_rate = None
    if payments and payments[0]:
        transaction_failure_rate = round(payments[1] / payments[0] * 100, 2)
    return jsonify(
        process=monitoring.metrics.snapshot(),
        probe=probe,
        target_percent=target,
        meets_target=None if probe is None else probe["availability_percent"] >= target,
        transaction_failure_rate_percent=transaction_failure_rate,
    ), 200
