
"""Flask backend API and web UI for the Railway Reservation System."""

from functools import wraps

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from config import Config
from modules import auth, search
from modules.allocation import check_availability
from modules.reservations import book_ticket, cancel_ticket, lookup_pnr

app = Flask(__name__)
app.config.from_object(Config)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Log in to continue.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user_id, errors = auth.register_user(
            request.form.get("name"),
            request.form.get("email"),
            request.form.get("password"),
        )
        if errors:
            for message in errors:
                flash(message, "error")
            return render_template("register.html", form=request.form), 400

        flash("Account created. Log in to continue.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form={})


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = auth.authenticate(
            request.form.get("email"),
            request.form.get("password"),
        )

        if user is None:
            flash("Email or password is incorrect.", "error")
            return render_template("login.html", form=request.form), 401

        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["role"] = user["role"]

        nxt = request.args.get("next", "")
        # Only allow same-site relative redirects.
        if nxt.startswith("/") and not nxt.startswith("//"):
            return redirect(nxt)

        return redirect(url_for("dashboard"))

    return render_template("login.html", form={})


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You are logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/search", methods=["GET"])
@login_required
def search_page():
    source = request.args.get("source")
    destination = request.args.get("destination")
    travel_date = request.args.get("date")
    submitted = any([source, destination, travel_date])

    trains, errors = [], []
    if submitted:
        trains, errors = search.search_trains(
            source, destination, travel_date
        )
        for message in errors:
            flash(message, "error")

    return render_template(
        "search.html",
        trains=trains,
        submitted=submitted,
        errors=errors,
        form=request.args,
    )


# Seat availability page
@app.route("/availability", methods=["GET"])
@login_required
def availability_page():
    return render_template("availability.html")


# Seat availability API
@app.route("/api/availability", methods=["GET"])
@login_required
def seat_availability():
    train_id = request.args.get("train_id")
    travel_date = request.args.get("date")
    class_code = request.args.get("class")

    if not train_id or not train_id.isdigit():
        return jsonify({
            "error": "Valid train_id is required."
        }), 400

    if not travel_date or not class_code:
        return jsonify({
            "error": "Date and class are required."
        }), 400

    try:
        result = check_availability(
            int(train_id),
            travel_date,
            class_code,
        )

        if result is None:
            return jsonify({
                "error": "Train schedule or class not found."
            }), 404

        return jsonify(result), 200

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("Availability lookup failed")
        return jsonify({
            "error": "Unable to retrieve seat availability."
        }), 500


# Booking creation, PNR tracking and cancellation APIs.
@app.route("/api/bookings", methods=["POST"])
@login_required
def create_booking_api():
    data = request.get_json(silent=True) if request.is_json else request.form
    booking, errors, status_code = book_ticket(session["user_id"], data or {})
    if not request.is_json:
        if errors:
            for message in errors:
                flash(message, "error")
            return redirect(url_for("search_page"))
        flash(f"Booking created with PNR {booking['pnr']} ({booking['status']}).", "success")
        return redirect(url_for("pnr_page", pnr=booking["pnr"]))
    if errors:
        return jsonify({"errors": errors}), status_code
    return jsonify(booking), status_code


@app.route("/pnr", methods=["GET"])
@login_required
def pnr_page():
    pnr = request.args.get("pnr", "").strip()
    booking = None
    errors = []
    if pnr:
        booking, errors, _ = lookup_pnr(pnr)
        # Passengers may only view their own booking details.
        if booking:
            from repository.reservation_repo import get_booking_by_pnr
            # ownership is checked by a dedicated repository query below.
            from repository.reservation_repo import booking_belongs_to_user
            if not booking_belongs_to_user(pnr, session["user_id"]):
                booking = None
                errors = ["No booking was found for that PNR."]
    return render_template("pnr.html", booking=booking, errors=errors, pnr=pnr)


@app.route("/api/pnr/<pnr>", methods=["GET"])
@login_required
def pnr_lookup_api(pnr):
    booking, errors, status_code = lookup_pnr(pnr)
    if errors:
        return jsonify({"errors": errors}), status_code
    from repository.reservation_repo import booking_belongs_to_user
    if not booking_belongs_to_user(pnr, session["user_id"]):
        return jsonify({"errors": ["No booking was found for that PNR."]}), 404
    return jsonify(booking), 200


@app.route("/api/bookings/<pnr>/cancel", methods=["POST"])
@login_required
def cancel_booking_api(pnr):
    data = request.get_json(silent=True) or request.form
    confirmed = str(data.get("confirm", "")).lower() in {"true", "1", "yes", "on"}
    result, errors, status_code = cancel_ticket(pnr, session["user_id"], confirmed)
    if not request.is_json:
        if errors:
            for message in errors:
                flash(message, "error")
        else:
            flash(
                f"Booking cancelled. Refund recorded: ₹{result['refund_amount']} ({result['refund_percent']}%).",
                "success",
            )
        return redirect(url_for("pnr_page", pnr=pnr))
    if errors:
        return jsonify({"errors": errors}), status_code
    return jsonify(result), 200


if __name__ == "__main__":
    app.run(debug=True)
