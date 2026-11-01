from modules import reservations


class FakeReservationRepo:
    def __init__(self):
        self.created = None
        self.booking = None
        self.cancel_result = ({"pnr": "123456789", "status": "CANCELLED", "refund_amount": "315.00", "refund_percent": 90}, 200)

    def create_booking(self, *args):
        self.created = args
        return {"id": 1, "pnr": "123456789", "status": "CONFIRMED", "fare": "350.00"}

    def get_booking_by_pnr(self, pnr):
        return self.booking

    def cancel_booking_and_refund(self, pnr, user_id):
        return self.cancel_result


def valid_payload():
    return {
        "schedule_id": 4,
        "class_code": "3a",
        "passenger_name": "Asha Rao",
        "passenger_age": 21,
        "passenger_gender": "Female",
        "berth_preference": "Lower",
    }


def test_booking_validates_and_normalizes_class():
    repo = FakeReservationRepo()
    booking, errors, status = reservations.book_ticket(7, valid_payload(), repo=repo)
    assert errors == [] and status == 201
    assert booking["pnr"] == "123456789"
    assert repo.created[0:3] == (7, 4, "3A")


def test_booking_rejects_invalid_fields():
    payload = valid_payload()
    payload["schedule_id"] = "bad"
    payload["passenger_age"] = 0
    _, errors, status = reservations.book_ticket(7, payload, repo=FakeReservationRepo())
    assert status == 400
    assert any("schedule_id" in error for error in errors)
    assert any("age" in error for error in errors)


def test_pnr_format_is_validated_before_lookup():
    repo = FakeReservationRepo()
    booking, errors, status = reservations.lookup_pnr("abc", repo=repo)
    assert booking is None and status == 400
    assert errors


def test_pnr_lookup_returns_booking():
    repo = FakeReservationRepo()
    repo.booking = {"pnr": "123456789", "status": "CONFIRMED", "fare": 350}
    booking, errors, status = reservations.lookup_pnr("123456789", repo=repo)
    assert errors == [] and status == 200
    assert booking["status"] == "CONFIRMED"
    assert booking["fare"] == "350"


def test_cancellation_requires_explicit_confirmation():
    result, errors, status = reservations.cancel_ticket("123456789", 7, False, repo=FakeReservationRepo())
    assert result is None and status == 400 and errors


def test_cancellation_returns_refund_details():
    result, errors, status = reservations.cancel_ticket("123456789", 7, True, repo=FakeReservationRepo())
    assert errors == [] and status == 200
    assert result["status"] == "CANCELLED"
    assert result["refund_amount"] == "315.00"
