"""RRS-F-060 routes: admin-only (PRJ-SR-003), JSON-only, clear errors."""
from unittest.mock import patch

from flask import Flask

from modules import train_admin
from modules.train_admin_routes import trains_admin_bp
from tests.test_train_admin import FakeRepo, GOOD_CLASSES, GOOD_TRAIN


def _client(role=None, repo=None):
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(trains_admin_bp)

    @app.get("/login")
    def login():
        return "login"

    client = app.test_client()
    if role:
        with client.session_transaction() as s:
            s["user_id"], s["role"] = 5, role
    client.repo = repo or FakeRepo()
    return client


def _call(client, method, url, **kwargs):
    with patch("modules.train_admin._repo", return_value=client.repo):
        return getattr(client, method)(url, **kwargs)


ENDPOINTS = [("post", "/api/admin/trains"), ("get", "/api/admin/trains"),
             ("put", "/api/admin/trains/1"), ("delete", "/api/admin/trains/1"),
             ("post", "/api/admin/trains/1/schedules"), ("put", "/api/admin/schedules/1"),
             ("delete", "/api/admin/schedules/1")]


def test_every_endpoint_rejects_anonymous_and_passengers():  # AC-SR-003
    for method, url in ENDPOINTS:
        assert _call(_client(), method, url, json={}).status_code == 401, url
        assert _call(_client("passenger"), method, url, json={}).status_code == 403, url


def test_passenger_cannot_change_anything():
    client = _client("passenger")
    _call(client, "post", "/api/admin/trains", json=GOOD_TRAIN)
    assert client.repo.calls == []


def test_admin_adds_train():
    client = _client("admin")
    r = _call(client, "post", "/api/admin/trains", json=GOOD_TRAIN)
    assert r.status_code == 201 and r.get_json()["train_no"] == "10006"
    assert client.repo.calls[0][2] == 5  # the logged-in admin is the audited actor


def test_validation_error_is_400_with_messages():
    r = _call(_client("admin"), "post", "/api/admin/trains", json={"train_no": ""})
    assert r.status_code == 400 and r.get_json()["errors"]


def test_form_posts_are_refused_to_block_csrf():
    client = _client("admin")
    r = _call(client, "post", "/api/admin/trains", data=GOOD_TRAIN)
    assert r.status_code == 415 and client.repo.calls == []
    r = _call(client, "post", "/api/admin/trains", data="[1,2]", content_type="application/json")
    assert r.status_code == 415


def test_duplicate_is_409_and_missing_is_404():
    client = _client("admin")
    client.repo.fail = "A train with this number already exists."
    assert _call(client, "post", "/api/admin/trains", json=GOOD_TRAIN).status_code == 409
    client = _client("admin")
    client.repo.missing = True
    assert _call(client, "put", "/api/admin/trains/9", json={"name": "X"}).status_code == 404
    assert _call(client, "delete", "/api/admin/schedules/9").status_code == 404


def test_update_and_remove_train():
    client = _client("admin")
    assert _call(client, "put", "/api/admin/trains/1", json={"name": "Renamed"}).status_code == 200
    r = _call(client, "delete", "/api/admin/trains/1")
    assert r.status_code == 200 and r.get_json() == {"result": "deleted"}


def test_schedule_endpoints():
    client = _client("admin")
    payload = {"travel_date": "2099-01-01", "classes": GOOD_CLASSES}
    assert _call(client, "post", "/api/admin/trains/1/schedules", json=payload).status_code == 201
    assert _call(client, "put", "/api/admin/schedules/5", json={"classes": GOOD_CLASSES}).status_code == 200
    assert _call(client, "delete", "/api/admin/schedules/5").status_code == 200
    client.repo.fail = "This schedule has bookings and cannot be removed."
    assert _call(client, "delete", "/api/admin/schedules/5").status_code == 409


def test_list_endpoint_returns_trains():
    client = _client("admin")
    r = _call(client, "get", "/api/admin/trains")
    assert r.status_code == 200 and r.get_json() == {"trains": []}


def test_page_is_admin_only():
    assert _client().get("/admin/trains").status_code == 302
    with patch("modules.rbac.render_template", return_value="forbidden"):
        assert _client("passenger").get("/admin/trains").status_code == 403
    with patch("modules.train_admin_routes.render_template", return_value="page"):
        assert _client("admin").get("/admin/trains").status_code == 200
