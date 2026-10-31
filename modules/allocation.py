
"""Business logic for seat availability."""

from datetime import date

from repository.availability import get_seat_availability


VALID_CLASSES = {"SL", "3A", "2A"}


def check_availability(train_id, travel_date, class_code):
    """Return available seats for a train and class."""

    if not isinstance(train_id, int) or train_id <= 0:
        raise ValueError("Invalid train ID.")

    try:
        journey_date = date.fromisoformat(str(travel_date))
    except (TypeError, ValueError):
        raise ValueError("Invalid travel date. Use YYYY-MM-DD.")

    if journey_date < date.today():
        raise ValueError("Travel date cannot be in the past.")

    class_code = str(class_code).strip().upper()

    if class_code not in VALID_CLASSES:
        raise ValueError("Invalid travel class.")

    result = get_seat_availability(
        train_id,
        journey_date,
        class_code
    )

    if result is None:
        return None

    total = int(result["total_seats"])
    allocated = int(result["allocated_seats"])
    available = max(0, total - allocated)

    return {
        "train_id": result["train_id"],
        "train_no": result["train_no"],
        "train_name": result["train_name"],
        "travel_date": str(result["travel_date"]),
        "class_code": result["class_code"],
        "total_seats": total,
        "allocated_seats": allocated,
        "available_seats": available,
        "status": "AVAILABLE" if available > 0 else "FULL"
    }
