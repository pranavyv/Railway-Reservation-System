"""Hook Yashas's Sprint 2 code into the files other people own.

Run once from the repo root, AFTER the Sprint 2 security PR (modules/rbac.py) and
Narendra's PR are merged into main:

    python apply_yashas_sprint2.py

Each edit must match exactly once. Nothing is written unless every required edit
matches, and running it a second time is harmless ("already applied").
"""
import os
import re
import sys

problems, warnings, changes = [], [], {}


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def current(path):
    return changes.get(path, read(path))


def edit(path, label, pattern, replacement, marker, required=True, flags=0):
    """Replace the single match of regex `pattern`; skip if `marker` is already in the file."""
    if not os.path.exists(path):
        (problems if required else warnings).append(f"{path}: file not found ({label})")
        return
    text = current(path)
    if marker in text:
        print(f"already applied: {label}")
        return
    matches = re.findall(pattern, text, flags)
    if len(matches) != 1:
        message = f"{path}: {label}: expected 1 match, found {len(matches)}"
        (problems if required else warnings).append(message)
        return
    changes[path] = re.sub(pattern, lambda m: replacement(m), text, count=1, flags=flags)


if not os.path.exists("modules/rbac.py"):
    sys.exit("modules/rbac.py is missing. Merge the Sprint 2 security PR into main first.")

# 1. app.py: new blueprints and the HTTPS / monitoring hooks -----------------------------------
edit("app.py", "imports",
     r"from modules\.pnr_routes import pnr_bp  # noqa: E402\n",
     lambda m: m.group(0)
     + "from modules.train_admin_routes import trains_admin_bp  # noqa: E402\n"
       "from modules.ops_routes import ops_bp  # noqa: E402\n"
       "from modules import monitoring, transport_security  # noqa: E402\n",
     "trains_admin_bp")
edit("app.py", "registrations",
     r"app\.register_blueprint\(pnr_bp\)\n",
     lambda m: m.group(0)
     + "transport_security.register(app)  # PRJ-SR-001: refuse plain HTTP when REQUIRE_HTTPS=1\n"
       "monitoring.register(app)  # RRS-NF-002: request and error counters\n"
       "app.register_blueprint(trains_admin_bp)  # RRS-F-060\n"
       "app.register_blueprint(ops_bp)  # /health and admin availability report\n",
     "transport_security.register(app)")

# 2. cancellation: promote the next waiting passenger (RRS-F-051) ------------------------------
HOOK = '''
    # RRS-F-051: the freed seat moves the next RAC / waitlisted passenger up. The cancellation
    # is already saved and the promotion plan only reads current state, so a failure here is
    # logged and can never undo or repeat the cancel.
    if hasattr(r, "rebalance_seats"):
        try:
            from modules import promotion

            promotion.rebalance_after_cancel(booking["id"], user_id, repo=r)
        except Exception:
            import logging

            logging.getLogger(__name__).exception(
                "Waitlist promotion failed after cancelling booking %s", booking["id"]
            )
'''
edit("modules/cancellation.py", "promotion hook",
     r'(\n[ ]+raise AlreadyCancelled\("This ticket is already cancelled\."\)\n)(\n    return \{\n)',
     lambda m: m.group(1) + HOOK + m.group(2),
     "promotion.rebalance_after_cancel")
edit("repository/cancellation_repo.py", "expose rebalance_seats",
     r"\Z",
     lambda m: "\n\nfrom repository.promotion_repo import rebalance_seats  # noqa: E402,F401  (RRS-F-051)\n",
     "from repository.promotion_repo import rebalance_seats")

# 3. templates: skip link, a11y.css, nav link, labelled audit field, status badge -----------------
edit("templates/base.html", "a11y.css link",
     r"(<link rel=\"stylesheet\" href=\"\{\{ url_for\('static', filename='style\.css'\) \}\}\">)",
     lambda m: m.group(1) + "\n  <link rel=\"stylesheet\" href=\"{{ url_for('static', filename='a11y.css') }}\">",
     "a11y.css")
edit("templates/base.html", "skip link",
     r"<body>",
     lambda m: '<body>\n  <a class="skip-link" href="#main">Skip to main content</a>',
     'class="skip-link"')
edit("templates/base.html", "main landmark",
     r"<main>",
     lambda m: '<main id="main" tabindex="-1">',
     'id="main"')
edit("templates/base.html", "Manage Trains link",
     r">Admin Reports</a>",
     lambda m: ">Admin Reports</a>\n          "
               "<a href=\"{{ url_for('trains_admin.trains_page') }}\" class=\"admin-badge\">Manage Trains</a>",
     "trains_admin.trains_page", required=False)
edit("templates/admin_reports.html", "label on the audit lookup field",
     r'<input type="number" id="audit_booking_id"',
     lambda m: '<input type="number" id="audit_booking_id" aria-label="Booking ID"',
     'aria-label="Booking ID"', required=False)
edit("templates/pnr.html", "status badge",
     r"(\n[ ]+)dd\.textContent = view\[f\[0\]\];",
     lambda m: (
         f'{m.group(1)}if (f[0] === "status") {{'
         f'{m.group(1)}  var badge = document.createElement("span");'
         f'{m.group(1)}  badge.className = "badge badge-" + String(view.status).toLowerCase();'
         f'{m.group(1)}  badge.textContent = view.status;'
         f'{m.group(1)}  dd.appendChild(badge);'
         f'{m.group(1)}}} else {{'
         f'{m.group(1)}  dd.textContent = view[f[0]];'
         f'{m.group(1)}}}'),
     "badge badge-", required=False)

# 4. housekeeping: never commit the TLS key or uptime logs; README notes --------------------------
edit(".gitignore", "ignore certs and logs",
     r"\Z",
     lambda m: "\n# Yashas Sprint 2: dev TLS key and uptime logs\ncerts/\nlogs/\n",
     "certs/", required=False)
README = '''

## Sprint 2: seat promotion, train admin, HTTPS and uptime
- **Waitlist/RAC promotion (RRS-F-051):** a cancellation moves the earliest RAC passenger to CONFIRMED (with a PNR) and refills RAC from the waiting list, in booking order. Each move is audited as `BOOKING_PROMOTED`.
- **Train and schedule admin (RRS-F-060):** admins use `/admin/trains` (API under `/api/admin/trains`). Search shows changes straight away. A train with bookings is hidden instead of deleted.
- **HTTPS only (PRJ-SR-001):** `bash scripts/make_dev_cert.sh`, then `REQUIRE_HTTPS=1 python run_https.py` and open https://localhost:5000. Behind a proxy that ends TLS, set `REQUIRE_HTTPS=1` and `TRUST_PROXY=1`.
- **Uptime (RRS-NF-002):** `/health` for checks; `python scripts/uptime_probe.py --url http://localhost:5000/health` writes `logs/uptime.csv`; admins see the percentage at `/api/admin/availability`.
- **Usability (RRS-NF-005):** skip link, labelled fields, status badges with a symbol. Manual walkthrough: `docs/TC-UX-01_usability_walkthrough.md`.
'''
edit("README.md", "README notes",
     r"\Z",
     lambda m: README,
     "Sprint 2: seat promotion, train admin", required=False)

for warning in warnings:
    print("note (optional edit skipped):", warning)
if problems:
    print("NOT WRITTEN. Fix these first:")
    for problem in problems:
        print(" -", problem)
    sys.exit(1)

for path, text in changes.items():
    if path.endswith(".py"):
        compile(text, path, "exec")  # syntax check before touching the file
for path, text in changes.items():
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("updated:", path)
print("Done." if changes else "Nothing to do: everything was already applied.")
