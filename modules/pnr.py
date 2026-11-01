"""PNR module: generate a unique PNR and look it up (RRS-F-040).

Narendra's payment code should call assign_pnr(booking_id) right after a
successful payment turns a booking into CONFIRMED.
"""
import re
import secrets

PNR_RE = re.compile(r"^\d{10}$")


def _repo(repo):
    if repo is not None:
        return repo
    from repository import pnr_repo  # lazy import keeps tests database-free

    return pnr_repo


def generate_pnr(exists=None, attempts=10):
    """Random 10-digit PNR that is not already taken (exists(pnr) -> bool)."""
    for _ in range(attempts):
        pnr = str(secrets.randbelow(9_000_000_000) + 1_000_000_000)
        if exists is None or not exists(pnr):
            return pnr
    raise RuntimeError("Could not generate a unique PNR.")


def assign_pnr(booking_id, repo=None):
    """Give a CONFIRMED booking its PNR (idempotent). Returns the PNR."""
    r = _repo(repo)
    booking = r.get_booking(booking_id)
    if booking is None:
        raise ValueError("Booking not found.")
    if booking["status"] != "CONFIRMED":
        raise ValueError("A PNR is generated only for confirmed bookings.")
    if booking["pnr"]:
        return booking["pnr"]

    for _ in range(5):
        pnr = generate_pnr(r.pnr_exists)
        if r.set_pnr(booking_id, pnr):
            return pnr
        latest = r.get_booking(booking_id)  # someone else may have assigned one meanwhile
        if latest and latest["pnr"]:
            return latest["pnr"]
    raise RuntimeError("Could not assign a PNR.")


def format_booking(row):
    return {
        "booking_id": row["id"],
        "user_id": row["user_id"],
        "pnr": row["pnr"],
        "status": row["status"],
        "train_no": row["train_no"],
        "train_name": row["train_name"],
        "source": row["source"],
        "destination": row["destination"],
        "travel_date": str(row["travel_date"]),
        "departure_time": str(row["departure_time"]),
        "class_code": row["class_code"],
        "passenger_name": row["passenger_name"],
        "fare": float(row["fare"]),
    }


def lookup_pnr(pnr, user_id=None, role="passenger", repo=None):
    """Booking details for a PNR, or None if it does not exist.

    When user_id is given, only the owner (or an admin) can see the booking;
    anyone else gets None, so PNRs cannot be probed.
    """
    pnr = (pnr or "").strip()
    if not PNR_RE.match(pnr):
        raise ValueError("PNR must be exactly 10 digits.")
    row = _repo(repo).get_booking_by_pnr(pnr)
    if row is None:
        return None
    if user_id is not None and role != "admin" and row["user_id"] != user_id:
        return None
    return format_booking(row)
