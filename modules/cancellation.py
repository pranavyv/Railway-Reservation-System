
"""Cancellation module (RRS-F-041) with refund calculation (RRS-F-042).

After a cancel, a seat is free again. Promoting the next RAC / waitlisted
passenger into it is RRS-F-051 (Sprint 2); call that from cancel_booking()
once it exists.
"""

from datetime import datetime

from modules import refund
from modules.pnr import PNR_RE

CANCELLABLE = {"PROVISIONAL", "CONFIRMED", "RAC", "WAITLISTED"}


class CancellationError(Exception):
    """Base class for expected cancellation problems."""


class BookingNotFound(CancellationError):
    pass


class AlreadyCancelled(CancellationError):
    pass


class ConfirmationRequired(CancellationError):
    pass


def _repo(repo):
    if repo is not None:
        return repo

    from repository import cancellation_repo

    return cancellation_repo


def _prepare(pnr, user_id, role, repo, now):
    pnr = (pnr or "").strip()

    if not PNR_RE.match(pnr):
        raise ValueError("PNR must be exactly 10 digits.")

    r = _repo(repo)

    booking = r.get_booking_by_pnr(pnr)

    # Same answer for "does not exist" and "belongs to someone else".
    if booking is None or (role != "admin" and booking["user_id"] != user_id):
        raise BookingNotFound("No booking found for this PNR.")

    if booking["status"] not in CANCELLABLE:
        raise AlreadyCancelled("This ticket is already cancelled.")

    now = now or datetime.now()

    hours_left = refund.hours_before_departure(
        booking["travel_date"],
        booking["departure_time"],
        now,
    )

    policy = [
        (row["min_hours_before"], row["refund_percent"])
        for row in r.get_policy()
    ]

    result = refund.calculate_refund(
        booking["fare"],
        hours_left,
        policy,
    )

    return r, booking, hours_left, result


def preview_refund(pnr, user_id, role="passenger", repo=None, now=None):
    """What the passenger would get back if they cancelled right now."""

    _, booking, hours_left, result = _prepare(
        pnr, user_id, role, repo, now
    )

    return {
        "pnr": booking["pnr"],
        "status": booking["status"],
        "fare": float(booking["fare"]),
        "refund_percent": result["percent"],
        "refund_amount": float(result["amount"]),
        "hours_before_departure": round(hours_left, 1),
    }


def cancel_booking(pnr, user_id, confirmed, role="passenger", repo=None, now=None):
    """Cancel after confirmation and record the refund and audit event."""

    if confirmed is not True:
        raise ConfirmationRequired("Please confirm the cancellation.")

    r, booking, hours_left, result = _prepare(
        pnr, user_id, role, repo, now
    )

    # Pass the authenticated actor's ID for audit logging.
    if not r.cancel_and_record_refund(
        booking["id"],
        result["amount"],
        result["percent"],
        user_id,
    ):
        raise AlreadyCancelled("This ticket is already cancelled.")

    return {
        "pnr": booking["pnr"],
        "status": "CANCELLED",
        "refund_percent": result["percent"],
        "refund_amount": float(result["amount"]),
        "hours_before_departure": round(hours_left, 1),
    }
