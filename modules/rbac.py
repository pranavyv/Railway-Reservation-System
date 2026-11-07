"""Server-side role checks (PRJ-SR-003).

Hiding a button in the UI is not security: every admin-only endpoint must use
@admin_required so a direct API call from a passenger account is refused.
"""
from functools import wraps

from flask import flash, jsonify, redirect, render_template, request, session, url_for


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required."}), 401
            flash("Log in to continue.", "error")
            return redirect(url_for("login", next=request.path))

        if session.get("role") != "admin":
            if request.path.startswith("/api/"):
                return jsonify({"error": "Administrator privilege required."}), 403
            flash("Access denied: Administrator privileges required.", "error")
            return render_template("dashboard.html"), 403

        return view(*args, **kwargs)

    return wrapped
