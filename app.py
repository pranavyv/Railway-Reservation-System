
"""Railway Reservation System Flask application."""

from flask import Flask, jsonify, render_template, request

from modules.allocation import check_availability

app = Flask(__name__)


# Homepage
@app.get("/")
def home():
    """Display the homepage."""
    return render_template("availability.html")


# Seat availability page
@app.get("/availability")
def availability_page():
    """Display the seat availability page."""
    return render_template("availability.html")


# Seat availability API
@app.get("/api/availability")
def seat_availability():
    """Return seat availability for a selected train and class."""

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
            class_code
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


if __name__ == "__main__":
    app.run()
