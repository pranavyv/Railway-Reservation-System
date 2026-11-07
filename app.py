
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
from modules import auth, search, payment, session_guard
from modules.allocation import check_availability

app = Flask(__name__)
app.config.from_object(Config)

from modules.pnr_routes import pnr_bp  # noqa: E402
from modules.audit_routes import audit_bp  # noqa: E402

app.register_blueprint(pnr_bp)
app.register_blueprint(audit_bp)
session_guard.register(app)  # PRJ-SR-004: end idle sessions


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
        try:
            user = auth.authenticate(
                request.form.get("email"),
                request.form.get("password"),
                max_attempts=app.config["MAX_FAILED_LOGINS"],
                lock_minutes=app.config["LOCKOUT_MINUTES"],
            )
        except auth.AccountLocked as locked:  # RRS-F-003
            flash(str(locked), "error")
            return render_template("login.html", form=request.form), 429

        if user is None:
            flash("Email or password is incorrect.", "error")
            return render_template("login.html", form=request.form), 401

        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["role"] = user["role"]
        session_guard.touch()

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


# Mock payment API
@app.route("/api/pay", methods=["POST"])
@login_required
def pay_booking():
    """Process a mock payment for the logged-in user's booking."""

    data = request.get_json(silent=True) or {}
    booking_id = data.get("booking_id")
    payment_outcome = data.get("payment_outcome", "SUCCESS")

    if (
        not isinstance(booking_id, int)
        or isinstance(booking_id, bool)
        or booking_id <= 0
    ):
        return jsonify({
            "error": "Valid booking_id is required."
        }), 400

    try:
        result = payment.process_payment(
            user_id=session["user_id"],
            booking_id=booking_id,
            payment_outcome=payment_outcome,
        )

        if result["status"] in {"FAILED", "TIMEOUT"}:
            return jsonify(result), 402

        return jsonify(result), 200

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("Payment processing failed")
        return jsonify({
            "error": "Unable to process payment."
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
