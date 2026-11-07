"""Idle-session timeout (PRJ-SR-004).

The login route stamps session["last_active"]; this before_request hook ends
the session when the user has been idle longer than IDLE_TIMEOUT_SECONDS and
refreshes the stamp on every other request.
"""
import time

from flask import flash, jsonify, redirect, request, session, url_for

DEFAULT_IDLE_TIMEOUT = 900  # seconds


def is_expired(last_active, now, timeout_seconds):
    """True when the stamp is unreadable or older than the timeout.

    A missing stamp is not expired: session cookies are signed, so one without
    a stamp predates this feature (or was seeded by a test). It gets stamped on
    this request and the timeout applies from then on.
    """
    if last_active is None:
        return False
    try:
        return (now - float(last_active)) > timeout_seconds
    except (TypeError, ValueError):
        return True


def touch(now=None):
    """Mark the current session as active right now."""
    session["last_active"] = int(now if now is not None else time.time())


def register(app, clock=time.time):
    """Attach the idle-timeout check to a Flask app."""

    @app.before_request
    def enforce_idle_timeout():
        if request.endpoint == "static" or "user_id" not in session:
            return None

        now = clock()
        timeout = app.config.get("IDLE_TIMEOUT_SECONDS", DEFAULT_IDLE_TIMEOUT)
        if not is_expired(session.get("last_active"), now, timeout):
            touch(now)
            return None

        session.clear()  # token invalidated: the old cookie no longer carries a user
        message = "Your session expired after a period of inactivity. Log in again."
        if request.path.startswith("/api/"):
            return jsonify(error=message, code="session_expired"), 401
        flash(message, "error")
        if request.method == "GET":
            return redirect(url_for("login", next=request.path))
        return redirect(url_for("login"))
