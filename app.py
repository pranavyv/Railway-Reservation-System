"""Flask backend API and web UI for the Railway Reservation System."""
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for

from config import Config
from modules import auth, search

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
            request.form.get("name"), request.form.get("email"), request.form.get("password")
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
        user = auth.authenticate(request.form.get("email"), request.form.get("password"))
        if user is None:
            flash("Email or password is incorrect.", "error")
            return render_template("login.html", form=request.form), 401
        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["role"] = user["role"]
        nxt = request.args.get("next", "")
        # Only allow same-site relative redirects
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
        trains, errors = search.search_trains(source, destination, travel_date)
        for message in errors:
            flash(message, "error")
    return render_template(
        "search.html",
        trains=trains,
        submitted=submitted,
        errors=errors,
        form=request.args,
    )


if __name__ == "__main__":
    app.run(debug=True)
