"""Admin-only audit log viewer (PRJ-SR-006, PRJ-SR-003, RRS-NF-004)."""
from flask import Blueprint, jsonify, request

from modules import audit
from modules.rbac import admin_required

audit_bp = Blueprint("audit", __name__)


@audit_bp.get("/api/admin/audit-log")
@admin_required
def audit_log():
    try:
        entries = audit.recent_entries(request.args.get("limit", 50))
    except ValueError as error:
        return jsonify(error=str(error)), 400
    return jsonify(entries=entries), 200
