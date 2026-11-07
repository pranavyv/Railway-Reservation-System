"""Audit trail for administrative actions (PRJ-SR-006, RRS-NF-004).

Call log_action() from any admin-only operation (schedule changes, refunds).
Every entry stores who did it (user_id) and when (created_at is set by the DB).
Details are scrubbed so passwords, card-like values and tokens never reach the
log (RRS-NF-003, PRJ-SR-005).
"""
import json

SENSITIVE_WORDS = ("password", "passwd", "card", "cvv", "cvc", "secret", "token", "hash")
REDACTED = "[REDACTED]"
MAX_LIMIT = 200


def _repo(repo):
    if repo is not None:
        return repo
    from repository import audit_repo  # lazy: tests need no DB driver

    return audit_repo


def redact(value):
    """Return a copy of value with sensitive-looking keys replaced."""
    if isinstance(value, dict):
        return {
            key: REDACTED if any(w in str(key).lower() for w in SENSITIVE_WORDS) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    return value


def log_action(user_id, action, details=None, repo=None):
    """Record one admin action. Raises ValueError if user or action is missing."""
    if user_id is None:
        raise ValueError("An audit entry needs the acting user.")
    action = (action or "").strip()
    if not action:
        raise ValueError("An audit entry needs an action name.")
    text = None if details is None else json.dumps(redact(details), default=str, sort_keys=True)
    _repo(repo).insert(user_id, action, text)


def recent_entries(limit=50, repo=None):
    """Newest first. limit is clamped to 1..MAX_LIMIT."""
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        raise ValueError("limit must be a whole number.")
    limit = max(1, min(limit, MAX_LIMIT))
    rows = _repo(repo).recent(limit)
    return [
        {
            "id": row["id"],
            "user_id": row["user_id"],
            "user_email": row.get("user_email"),
            "action": row["action"],
            "booking_id": row.get("booking_id"),
            "details": row["details"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }
        for row in rows
    ]
