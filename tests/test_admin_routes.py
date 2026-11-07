"""Integration tests for admin routes and authorization (Issue #18, TC-Admin-02)."""

from unittest.mock import patch
from flask import session

import app as flask_app


def _client(logged_in=True, user_id=1, role="passenger"):
    flask_app.app.config["TESTING"] = True
    client = flask_app.app.test_client()
    if logged_in:
        with client.session_transaction() as s:
            s["user_id"] = user_id
            s["user_name"] = "Admin User" if role == "admin" else "Passenger User"
            s["role"] = role
    return client


def test_admin_reports_page_requires_login():
    client = _client(logged_in=False)
    resp = client.get("/admin/reports")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_admin_reports_page_rejects_passenger():
    """AC-RRS-F-061: Normal passengers must not access admin reports."""
    client = _client(logged_in=True, role="passenger")
    resp = client.get("/admin/reports")
    assert resp.status_code == 403


def test_admin_reports_page_accessible_by_admin():
    client = _client(logged_in=True, role="admin")
    fake_report = {
        "start_date": "",
        "end_date": "",
        "summary": {
            "total_bookings": 5,
            "confirmed_bookings": 4,
            "cancelled_bookings": 1,
            "rac_bookings": 0,
            "waitlisted_bookings": 0,
            "gross_revenue": 4500.0,
            "total_refunds": 400.0,
            "net_revenue": 4100.0,
            "total_capacity": 64,
            "total_allocated": 4,
            "total_remaining": 60,
            "overall_occupancy_percent": 6.25,
        },
        "bookings": {"total_bookings": 5, "confirmed": 4, "cancelled": 1, "rac": 0, "waitlisted": 0, "recent_bookings": []},
        "occupancy": {"schedules": []},
        "revenue": {"successful_payments_count": 4, "refund_count": 1},
    }

    with patch("app.admin.generate_report", return_value=fake_report):
        resp = client.get("/admin/reports")

    assert resp.status_code == 200
    assert b"Administrative Reports" in resp.data
    assert b"Total Bookings" in resp.data


def test_admin_reports_api_requires_login():
    client = _client(logged_in=False)
    resp = client.get("/api/admin/reports")
    assert resp.status_code == 401
    assert "Authentication required" in resp.get_json()["error"]


def test_admin_reports_api_rejects_passenger():
    client = _client(logged_in=True, role="passenger")
    resp = client.get("/api/admin/reports")
    assert resp.status_code == 403
    assert "Administrator privilege required" in resp.get_json()["error"]


def test_admin_reports_api_accessible_by_admin():
    client = _client(logged_in=True, role="admin")
    fake_report = {"summary": {"total_bookings": 10}}

    with patch("app.admin.generate_report", return_value=fake_report):
        resp = client.get("/api/admin/reports?start_date=2026-11-01&end_date=2026-11-30")

    assert resp.status_code == 200
    assert resp.get_json() == fake_report


def test_admin_audit_api_rejects_passenger():
    client = _client(logged_in=True, role="passenger")
    resp = client.get("/api/admin/audit/101")
    assert resp.status_code == 403


def test_admin_audit_api_accessible_by_admin():
    client = _client(logged_in=True, role="admin")
    fake_logs = [
        {
            "id": 1,
            "user_id": 10,
            "action": "BOOKING_CREATED",
            "booking_id": 101,
            "details": "Created",
            "created_at": "2026-11-04 10:00:00",
        }
    ]

    with patch("app.admin.get_audit_trail", return_value=fake_logs):
        resp = client.get("/api/admin/audit/101")

    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["action"] == "BOOKING_CREATED"


def test_create_booking_api_success():
    client = _client(logged_in=True, user_id=5, role="passenger")
    fake_booking = {"id": 42, "fare": 900.0, "held_until": "2026-11-20 12:00:00"}

    with patch("app.booking.create_booking", return_value=fake_booking):
        resp = client.post("/api/book", json={
            "schedule_id": 1,
            "class_code": "3A",
            "passenger_name": "Test Passenger",
            "passenger_age": 28,
            "passenger_gender": "Female",
        })

    assert resp.status_code == 201
    assert resp.get_json()["booking_id"] == 42


def test_create_booking_api_validation_error():
    client = _client(logged_in=True, user_id=5, role="passenger")

    with patch("app.booking.create_booking", side_effect=ValueError("Invalid train schedule.")):
        resp = client.post("/api/book", json={
            "schedule_id": 0,
            "class_code": "3A",
            "passenger_name": "Test",
            "passenger_age": 28,
            "passenger_gender": "Male",
        })

    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Invalid train schedule."
