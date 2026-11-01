"""Search module: find trains by source, destination and date (RRS-F-010, RRS-F-011)."""
from datetime import date, datetime


def _repo(repo):
    if repo is not None:
        return repo
    from repository import train_repo  # lazy import, keeps tests DB-free

    return train_repo


def parse_search(source, destination, date_str, today=None):
    """Returns (cleaned_values, errors). cleaned_values is None when invalid."""
    today = today or date.today()
    errors = []
    source = (source or "").strip()
    destination = (destination or "").strip()

    if not source:
        errors.append("Enter a source station.")
    if not destination:
        errors.append("Enter a destination station.")
    if source and destination and source.lower() == destination.lower():
        errors.append("Source and destination must be different.")

    travel_date = None
    try:
        travel_date = datetime.strptime((date_str or "").strip(), "%Y-%m-%d").date()
        if travel_date < today:
            errors.append("Travel date cannot be in the past.")
    except ValueError:
        errors.append("Enter the travel date as YYYY-MM-DD.")

    if errors:
        return None, errors
    return (source, destination, travel_date), []


def group_results(rows):
    """Turn (train, class) rows into one entry per train schedule with a classes list."""
    trains = {}
    for r in rows:
        entry = trains.setdefault(
            r["schedule_id"],
            {
                "train_id": r["train_id"],
                "schedule_id": r["schedule_id"],
                "train_no": r["train_no"],
                "name": r["name"],
                "source": r["source"],
                "destination": r["destination"],
                "departure_time": r["departure_time"],
                "arrival_time": r["arrival_time"],
                "travel_date": r["travel_date"],
                "classes": [],
            },
        )
        entry["classes"].append(
            {"class_code": r["class_code"], "fare": r["fare"], "total_seats": r["total_seats"]}
        )
    return list(trains.values())


def search_trains(source, destination, date_str, repo=None, today=None):
    """Returns (trains, errors). An empty trains list means 'No trains found' (RRS-F-011)."""
    cleaned, errors = parse_search(source, destination, date_str, today=today)
    if errors:
        return [], errors
    rows = _repo(repo).search_rows(*cleaned)
    return group_results(rows), []
