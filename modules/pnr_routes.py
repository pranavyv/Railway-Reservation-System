"""Routes for PNR status, cancellation and seat-status preview (Yashash's Sprint 1 issues)."""
from flask import (
    Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
)

from modules import cancellation, pnr, seat_allocation

pnr_bp = Blueprint("pnr", __name__)


def _login_error():
    return jsonify(error="Log in to continue."), 401


def _public(booking):
    """Never send the internal user id to the browser."""
    return {k: v for k, v in booking.items() if k != "user_id"}


@pnr_bp.get("/pnr")
def pnr_page():
    if "user_id" not in session:
        flash("Log in to continue.", "error")
        return redirect(url_for("login", next=request.path))
    return render_template("pnr.html")


@pnr_bp.get("/api/pnr/<pnr_number>")
def pnr_status(pnr_number):
    if "user_id" not in session:
        return _login_error()
    try:
        booking = pnr.lookup_pnr(pnr_number, user_id=session["user_id"], role=session.get("role", "passenger"))
    except ValueError as error:
        return jsonify(error=str(error)), 400
    if booking is None:
        return jsonify(error="No booking found for this PNR."), 404
    return jsonify(_public(booking)), 200


@pnr_bp.get("/api/cancel/preview")
def cancel_preview():
    if "user_id" not in session:
        return _login_error()
    try:
        result = cancellation.preview_refund(
            request.args.get("pnr"), session["user_id"], role=session.get("role", "passenger")
        )
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except cancellation.BookingNotFound as error:
        return jsonify(error=str(error)), 404
    except cancellation.AlreadyCancelled as error:
        return jsonify(error=str(error)), 409
    return jsonify(result), 200


@pnr_bp.post("/api/cancel")
def cancel():
    if "user_id" not in session:
        return _login_error()
    data = request.get_json(silent=True) or {}
    try:
        result = cancellation.cancel_booking(
            data.get("pnr"), session["user_id"], data.get("confirm"),
            role=session.get("role", "passenger"),
        )
    except (ValueError, cancellation.ConfirmationRequired) as error:
        return jsonify(error=str(error)), 400
    except cancellation.BookingNotFound as error:
        return jsonify(error=str(error)), 404
    except cancellation.AlreadyCancelled as error:
        return jsonify(error=str(error)), 409
    return jsonify(result), 200


@pnr_bp.get("/api/allocation/status")
def allocation_status():
    """Which status a new booking on this schedule and class would get right now."""
    if "user_id" not in session:
        return _login_error()
    schedule_id = request.args.get("schedule_id", "")
    if not schedule_id.isdigit():
        return jsonify(error="Valid schedule_id is required."), 400
    try:
        result = seat_allocation.assign_status(int(schedule_id), request.args.get("class"))
    except ValueError as error:
        return jsonify(error=str(error)), 400
    if result is None:
        return jsonify(error="Schedule or class not found."), 404
    return jsonify(result), 200
