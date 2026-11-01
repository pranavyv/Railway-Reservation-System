"""Allocation module: decide Confirmed / RAC / Waitlisted (RRS-F-050).

Rule, applied at booking time:
  * seats still free                -> CONFIRMED
  * seats full, RAC quota not full  -> RAC
  * otherwise                       -> WAITLISTED

RAC quota is RAC_PERCENT of the class capacity (rounded up).
Promotion of waiting passengers on cancellation is RRS-F-051 (Sprint 2).
"""
import math

RAC_PERCENT = 10

CONFIRMED = "CONFIRMED"
RAC = "RAC"
WAITLISTED = "WAITLISTED"


def _repo(repo):
    if repo is not None:
        return repo
    from repository import allocation_repo  # lazy import keeps tests database-free

    return allocation_repo


def rac_capacity(total_seats):
    if total_seats <= 0:
        return 0
    return math.ceil(total_seats * RAC_PERCENT / 100)


def decide_status(total_seats, held_seats, rac_count):
    """Pure rule: which status does the next booking get?"""
    if held_seats < total_seats:
        return CONFIRMED
    if rac_count < rac_capacity(total_seats):
        return RAC
    return WAITLISTED


def assign_status(schedule_id, class_code, repo=None):
    """Status a new booking would get now, or None if the schedule/class is unknown."""
    if not isinstance(schedule_id, int) or isinstance(schedule_id, bool) or schedule_id <= 0:
        raise ValueError("Invalid schedule ID.")
    class_code = str(class_code or "").strip().upper()
    if not class_code:
        raise ValueError("Travel class is required.")

    counts = _repo(repo).get_counts(schedule_id, class_code)
    if counts is None:
        return None

    total = int(counts["total_seats"])
    held = int(counts["held_seats"])
    rac = int(counts["rac_count"])
    return {
        "schedule_id": schedule_id,
        "class_code": class_code,
        "status": decide_status(total, held, rac),
        "total_seats": total,
        "held_seats": held,
        "rac_count": rac,
        "waitlist_count": int(counts["waitlist_count"]),
        "rac_capacity": rac_capacity(total),
    }
