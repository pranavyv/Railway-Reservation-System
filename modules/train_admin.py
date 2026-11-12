"""Admin: add, update and remove trains and schedules (RRS-F-060, TC-Admin-01).

Search reads the same tables, so every change shows up in search results at once.
Each change is written to the audit log in the same database transaction
(PRJ-SR-006). Routes live in modules/train_admin_routes.py and are admin-only.
"""
import re
from datetime import date, datetime

from modules.audit import redact

CLASS_CODES = ("SL", "3A", "2A")
MAX_SEATS = 1000
MAX_FARE = 100000
TRAIN_NO_RE = re.compile(r"^[A-Za-z0-9]{1,10}$")
TEXT_FIELDS = {"name": "Train name", "source": "Source station", "destination": "Destination station"}
TIME_FIELDS = {"departure_time": "Departure time", "arrival_time": "Arrival time"}


class ValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__(" ".join(errors))


class NotFound(Exception):
    pass


class Conflict(Exception):
    pass


def _repo(repo):
    if repo is not None:
        return repo
    from repository import train_admin_repo  # lazy import keeps tests database-free

    return train_admin_repo


# ---- validation ---------------------------------------------------------------
def _parse_time(value):
    try:
        return datetime.strptime(str(value).strip(), "%H:%M").strftime("%H:%M")
    except ValueError:
        return None


def validate_train(data, partial=False):
    """Returns cleaned values. With partial=True only the supplied fields are checked."""
    data = data or {}
    errors, clean = [], {}

    if not partial or "train_no" in data:
        number = str(data.get("train_no") or "").strip()
        if not TRAIN_NO_RE.match(number):
            errors.append("Train number must be 1 to 10 letters or digits.")
        else:
            clean["train_no"] = number.upper()

    for field, label in TEXT_FIELDS.items():
        if not partial or field in data:
            text = " ".join(str(data.get(field) or "").split())
            if not text or len(text) > 80:
                errors.append(f"{label} is required (up to 80 characters).")
            else:
                clean[field] = text

    for field, label in TIME_FIELDS.items():
        if not partial or field in data:
            parsed = _parse_time(data.get(field))
            if parsed is None:
                errors.append(f"{label} must be a time like 06:30.")
            else:
                clean[field] = parsed

    if "active" in data:
        if not isinstance(data["active"], bool):
            errors.append("Active must be true or false.")
        else:
            clean["active"] = data["active"]

    if partial and not clean and not errors:
        errors.append("Nothing to update.")
    if (clean.get("source") and clean.get("destination")
            and clean["source"].lower() == clean["destination"].lower()):
        errors.append("Source and destination must be different.")

    if errors:
        raise ValidationError(errors)
    return clean


def validate_classes(classes):
    """classes: [{"class_code": "SL", "total_seats": 72, "fare": 350}, ...]"""
    errors, clean, seen = [], [], set()
    if not isinstance(classes, list) or not classes:
        raise ValidationError(["Add at least one class with seats and fare."])
    for item in classes:
        item = item if isinstance(item, dict) else {}
        code = str(item.get("class_code") or "").strip().upper()
        if code not in CLASS_CODES:
            errors.append(f"Class must be one of {', '.join(CLASS_CODES)}.")
            continue
        if code in seen:
            errors.append(f"Class {code} is listed twice.")
            continue
        seen.add(code)
        seats, fare = item.get("total_seats"), item.get("fare")
        if isinstance(seats, bool) or not isinstance(seats, int) or not 1 <= seats <= MAX_SEATS:
            errors.append(f"Seats for {code} must be a whole number from 1 to {MAX_SEATS}.")
            continue
        try:
            fare_value = round(float(fare), 2)
        except (TypeError, ValueError):
            fare_value = -1
        if isinstance(fare, bool) or not 0 < fare_value <= MAX_FARE:
            errors.append(f"Fare for {code} must be more than 0 and at most {MAX_FARE}.")
            continue
        clean.append({"class_code": code, "total_seats": seats, "fare": fare_value})
    if errors:
        raise ValidationError(errors)
    return clean


def validate_travel_date(value, today=None):
    today = today or date.today()
    try:
        travel_date = datetime.strptime(str(value or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError(["Travel date must be in YYYY-MM-DD format."])
    if travel_date < today:
        raise ValidationError(["Travel date cannot be in the past."])
    return travel_date.isoformat()


# ---- views ---------------------------------------------------------------------
def list_trains(repo=None):
    """Trains with their schedules and classes, for the admin page."""
    trains = {}
    for row in _repo(repo).list_rows():
        train = trains.setdefault(row["train_id"], {
            "id": row["train_id"], "train_no": row["train_no"], "name": row["name"],
            "source": row["source"], "destination": row["destination"],
            "departure_time": str(row["departure_time"])[:5],
            "arrival_time": str(row["arrival_time"])[:5],
            "active": bool(row["active"]), "schedules": {},
        })
        if row["schedule_id"] is None:
            continue
        schedule = train["schedules"].setdefault(row["schedule_id"], {
            "id": row["schedule_id"], "travel_date": str(row["travel_date"]), "classes": [],
        })
        if row["class_code"] is not None:
            schedule["classes"].append({
                "class_code": row["class_code"], "total_seats": int(row["total_seats"]),
                "fare": float(row["fare"]),
            })
    result = []
    for train in trains.values():
        train["schedules"] = list(train["schedules"].values())
        result.append(train)
    return result


def _view(row):
    return {
        "id": row["id"], "train_no": row["train_no"], "name": row["name"],
        "source": row["source"], "destination": row["destination"],
        "departure_time": str(row["departure_time"])[:5],
        "arrival_time": str(row["arrival_time"])[:5], "active": bool(row["active"]),
    }


def _run(action, *args):
    try:
        return action(*args)
    except ValueError as error:  # the repository reports clashes in plain words
        raise Conflict(str(error)) from error


# ---- trains --------------------------------------------------------------------
def add_train(data, actor_id, repo=None):
    values = validate_train(data)
    row = _run(_repo(repo).insert_train, values, actor_id, redact(values))
    return _view(row)


def update_train(train_id, data, actor_id, repo=None):
    values = validate_train(data, partial=True)
    row = _run(_repo(repo).update_train, train_id, values, actor_id,
               redact({"train_id": train_id, **values}))
    if row is None:
        raise NotFound("Train not found.")
    return _view(row)


def remove_train(train_id, actor_id, repo=None):
    """Deletes a train nobody has booked; otherwise hides it from search (active = false)."""
    result = _repo(repo).remove_train(train_id, actor_id)
    if result is None:
        raise NotFound("Train not found.")
    return {"result": result}


# ---- schedules -----------------------------------------------------------------
def add_schedule(train_id, data, actor_id, repo=None, today=None):
    data = data or {}
    travel_date = validate_travel_date(data.get("travel_date"), today=today)
    classes = validate_classes(data.get("classes"))
    row = _run(_repo(repo).insert_schedule, train_id, travel_date, classes, actor_id,
               {"train_id": train_id, "travel_date": travel_date, "classes": classes})
    if row is None:
        raise NotFound("Train not found.")
    return {"id": row["id"], "train_id": train_id, "travel_date": travel_date, "classes": classes}


def update_schedule(schedule_id, data, actor_id, repo=None):
    classes = validate_classes((data or {}).get("classes"))
    row = _run(_repo(repo).update_schedule, schedule_id, classes, actor_id,
               {"schedule_id": schedule_id, "classes": classes})
    if row is None:
        raise NotFound("Schedule not found.")
    return {"id": schedule_id, "classes": classes}


def remove_schedule(schedule_id, actor_id, repo=None):
    removed = _run(_repo(repo).remove_schedule, schedule_id, actor_id,
                   {"schedule_id": schedule_id})
    if removed is None:
        raise NotFound("Schedule not found.")
    return {"result": "deleted"}
