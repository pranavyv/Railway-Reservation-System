from unittest.mock import patch

from flask import Flask

from modules import cancellation
from modules.pnr_routes import pnr_bp


def _client(logged_in=True, user_id=7, role="passenger"):
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(pnr_bp)
    client = app.test_client()
    if logged_in:
        with client.session_transaction() as s:
            s["user_id"] = user_id
            s["role"] = role
    return client


BOOKING = {"booking_id": 1, "user_id": 7, "pnr": "1234567890", "status": "CONFIRMED",
           "train_no": "10001", "train_name": "Silicon Express", "source": "A", "destination": "B",
           "travel_date": "2026-11-20", "departure_time": "06:00:00", "class_code": "3A",
           "passenger_name": "Asha", "fare": 900.0}


def test_api_requires_login():
    client = _client(logged_in=False)
    assert client.get("/api/pnr/1234567890").status_code == 401
    assert client.get("/api/cancel/preview?pnr=1234567890").status_code == 401
    assert client.post("/api/cancel", json={"pnr": "1234567890", "confirm": True}).status_code == 401
    assert client.get("/api/allocation/status?schedule_id=1&class=SL").status_code == 401


def test_pnr_status_hides_internal_user_id():
    with patch("modules.pnr_routes.pnr.lookup_pnr", return_value=dict(BOOKING)):
        r = _client().get("/api/pnr/1234567890")
    assert r.status_code == 200
    assert r.get_json()["status"] == "CONFIRMED"
    assert "user_id" not in r.get_json()


def test_pnr_status_not_found_and_bad_input():
    with patch("modules.pnr_routes.pnr.lookup_pnr", return_value=None):
        assert _client().get("/api/pnr/1234567890").status_code == 404
    assert _client().get("/api/pnr/abc").status_code == 400


def test_cancel_success_and_errors():
    ok = {"pnr": "1234567890", "status": "CANCELLED", "refund_percent": 90, "refund_amount": 810.0}
    body = {"pnr": "1234567890", "confirm": True}
    with patch("modules.pnr_routes.cancellation.cancel_booking", return_value=ok):
        r = _client().post("/api/cancel", json=body)
    assert r.status_code == 200 and r.get_json()["refund_amount"] == 810.0

    for error, code in [(cancellation.BookingNotFound("x"), 404),
                        (cancellation.AlreadyCancelled("x"), 409),
                        (cancellation.ConfirmationRequired("x"), 400)]:
        with patch("modules.pnr_routes.cancellation.cancel_booking", side_effect=error):
            assert _client().post("/api/cancel", json=body).status_code == code


def test_cancel_without_confirm_flag_is_rejected_by_service():
    r = _client().post("/api/cancel", json={"pnr": "1234567890"})
    assert r.status_code == 400


def test_allocation_status_endpoint():
    result = {"schedule_id": 3, "class_code": "SL", "status": "RAC"}
    with patch("modules.pnr_routes.seat_allocation.assign_status", return_value=result):
        r = _client().get("/api/allocation/status?schedule_id=3&class=SL")
    assert r.status_code == 200 and r.get_json()["status"] == "RAC"
    assert _client().get("/api/allocation/status?schedule_id=abc&class=SL").status_code == 400
    with patch("modules.pnr_routes.seat_allocation.assign_status", return_value=None):
        assert _client().get("/api/allocation/status?schedule_id=3&class=SL").status_code == 404
