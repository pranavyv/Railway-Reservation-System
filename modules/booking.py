
"""Booking validation and business logic (RRS-F-021, RRS-F-022)."""

VALID_CLASSES = {"SL", "3A", "2A"}

VALID_GENDERS = {"Male", "Female", "Other"}

VALID_BERTHS = {
    "",
    "Any",
    "Lower",
    "Middle",
    "Upper",
    "Side Lower",
    "Side Upper",
}


def create_booking(
    user_id,
    schedule_id,
    class_code,
    passenger_name,
    passenger_age,
    passenger_gender,
    berth_preference="",
    repo=None,
):
    """Validate booking details and create a provisional booking."""

    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("Please log in before booking.")

    if not isinstance(schedule_id, int) or schedule_id <= 0:
        raise ValueError("Invalid train schedule.")

    name = str(passenger_name or "").strip()

    if not name:
        raise ValueError("Passenger name is required.")

    if len(name) > 100:
        raise ValueError("Passenger name must be 100 characters or fewer.")

    try:
        age = int(passenger_age)
    except (TypeError, ValueError):
        raise ValueError("Enter a valid passenger age.")

    if not 1 <= age <= 120:
        raise ValueError("Passenger age must be between 1 and 120.")

    gender = str(passenger_gender or "").strip().title()

    if gender not in VALID_GENDERS:
        raise ValueError("Select a valid passenger gender.")

    class_code = str(class_code or "").strip().upper()

    if class_code not in VALID_CLASSES:
        raise ValueError("Select a valid travel class.")

    berth = str(berth_preference or "").strip().title()

    if berth not in VALID_BERTHS:
        raise ValueError("Select a valid berth preference.")

    if repo is None:
        from repository import booking_repo

        repo = booking_repo

    return repo.create_provisional_booking(
        user_id=user_id,
        schedule_id=schedule_id,
        class_code=class_code,
        passenger_name=name,
        passenger_age=age,
        passenger_gender=gender,
        berth_preference=berth or None,
    )
