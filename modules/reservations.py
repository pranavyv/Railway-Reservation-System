"""Validation and orchestration for booking, PNR lookup and cancellation."""
import re
from datetime import date

PNR_RE = re.compile(r"^\d{9}$")
VALID_CLASSES = {"SL", "3A", "2A"}


def _repo(repo=None):
    if repo is not None:
        return repo
    from repository import reservation_repo
    return reservation_repo


def book_ticket(user_id, data, repo=None):
    errors = []
    try:
        schedule_id = int(data.get("schedule_id"))
        if schedule_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        errors.append("A valid schedule_id is required.")
        schedule_id = None

    class_code = str(data.get("class_code", "")).strip().upper()
    if class_code not in VALID_CLASSES:
        errors.append("Choose a valid travel class (SL, 3A or 2A).")
    name = str(data.get("passenger_name", "")).strip()
    if not name:
        errors.append("Passenger name is required.")
    try:
        age = int(data.get("passenger_age"))
        if not 1 <= age <= 120:
            raise ValueError
    except (TypeError, ValueError):
        errors.append("Passenger age must be between 1 and 120.")
        age = None
    gender = str(data.get("passenger_gender", "")).strip()
    if gender not in {"Female", "Male", "Other"}:
        errors.append("Choose Female, Male or Other for passenger gender.")
    preference = str(data.get("berth_preference", "")).strip() or None
    if errors:
        return None, errors, 400
    booking = _repo(repo).create_booking(
        user_id, schedule_id, class_code, name, age, gender, preference
    )
    if booking is None:
        return None, ["The selected schedule or class was not found."], 404
    return booking, [], 201


def lookup_pnr(pnr, repo=None):
    pnr = str(pnr or "").strip()
    if not PNR_RE.fullmatch(pnr):
        return None, ["Enter a valid 9-digit PNR."], 400
    booking = _repo(repo).get_booking_by_pnr(pnr)
    if booking is None:
        return None, ["No booking was found for that PNR."], 404
    # psycopg date/time/decimal values are not directly JSON serializable.
    for key, value in list(booking.items()):
        if hasattr(value, "isoformat"):
            booking[key] = value.isoformat()
        elif value is not None and key == "fare":
            booking[key] = str(value)
    return booking, [], 200


def cancel_ticket(pnr, user_id, confirmed, repo=None):
    if not confirmed:
        return None, ["Cancellation must be explicitly confirmed."], 400
    if not PNR_RE.fullmatch(str(pnr or "").strip()):
        return None, ["Enter a valid 9-digit PNR."], 400
    result, status_code = _repo(repo).cancel_booking_and_refund(pnr.strip(), user_id)
    if status_code != 200:
        return None, [result["error"]], status_code
    return result, [], 200
