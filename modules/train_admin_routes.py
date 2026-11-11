"""Admin-only routes for train and schedule management (RRS-F-060)."""
from flask import Blueprint, jsonify, render_template, request, session

from modules import train_admin
from modules.rbac import admin_required

trains_admin_bp = Blueprint("trains_admin", __name__)


def _actor():
    return session["user_id"]


def _body():
    """JSON object body. A browser form cannot send JSON cross-site, which blocks CSRF."""
    if not request.is_json:
        return None
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def _bad_body():
    return jsonify(error="Send the request as a JSON object."), 415


def _guard(action):
    """Run action() and translate expected problems into JSON errors."""
    try:
        return action()
    except train_admin.ValidationError as error:
        return jsonify(error=str(error), errors=error.errors), 400
    except train_admin.NotFound as error:
        return jsonify(error=str(error)), 404
    except train_admin.Conflict as error:
        return jsonify(error=str(error)), 409


@trains_admin_bp.get("/admin/trains")
@admin_required
def trains_page():
    return render_template("admin_trains.html")


@trains_admin_bp.get("/api/admin/trains")
@admin_required
def list_trains():
    return jsonify(trains=train_admin.list_trains()), 200


@trains_admin_bp.post("/api/admin/trains")
@admin_required
def add_train():
    data = _body()
    if data is None:
        return _bad_body()
    return _guard(lambda: (jsonify(train_admin.add_train(data, _actor())), 201))


@trains_admin_bp.put("/api/admin/trains/<int:train_id>")
@admin_required
def update_train(train_id):
    data = _body()
    if data is None:
        return _bad_body()
    return _guard(lambda: (jsonify(train_admin.update_train(train_id, data, _actor())), 200))


@trains_admin_bp.delete("/api/admin/trains/<int:train_id>")
@admin_required
def remove_train(train_id):
    return _guard(lambda: (jsonify(train_admin.remove_train(train_id, _actor())), 200))


@trains_admin_bp.post("/api/admin/trains/<int:train_id>/schedules")
@admin_required
def add_schedule(train_id):
    data = _body()
    if data is None:
        return _bad_body()
    return _guard(lambda: (jsonify(train_admin.add_schedule(train_id, data, _actor())), 201))


@trains_admin_bp.put("/api/admin/schedules/<int:schedule_id>")
@admin_required
def update_schedule(schedule_id):
    data = _body()
    if data is None:
        return _bad_body()
    return _guard(lambda: (jsonify(train_admin.update_schedule(schedule_id, data, _actor())), 200))


@trains_admin_bp.delete("/api/admin/schedules/<int:schedule_id>")
@admin_required
def remove_schedule(schedule_id):
    return _guard(lambda: (jsonify(train_admin.remove_schedule(schedule_id, _actor())), 200))
