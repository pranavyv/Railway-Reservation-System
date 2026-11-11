# Railway Reservation System (RRS)

Flask + Supabase (PostgreSQL). Layers: templates (HTML/CSS) -> `app.py` routes -> `modules/` (business logic) -> `repository/` (SQL) -> Supabase.

## Setup
1. `python -m venv venv` then activate it, then `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in `DATABASE_URL`, `DB_SSLMODE` and `SECRET_KEY`
3. Run `schema.sql`, then `seed.sql`, in the Supabase SQL editor
4. `python app.py` and open http://127.0.0.1:5000

## Tests
`pytest` (the unit tests use in-memory fakes, so they need no database)

## Layout
| Path | Purpose |
|---|---|
| `app.py` | Flask routes |
| `modules/` | Auth, Search, Booking, Payment, Allocation, plus `rbac.py` (`@admin_required`), `audit.py` (`log_action`) and `session_guard.py` (idle timeout) |
| `repository/` | All SQL, one file per area |
| `schema.sql`, `seed.sql` | Database tables and sample data |
| `templates/`, `static/` | HTML and CSS |

## Security helpers (Sprint 2)
- Protect any admin-only route with `from modules.rbac import admin_required` and `@admin_required` (returns 401 when logged out, 403 for non-admins).
- Record every admin action with `audit.log_action(session["user_id"], "ACTION_NAME", {"key": "value"})`. Passwords, card-like values and tokens in the details are redacted automatically.
- Promote an account to admin in Supabase: `UPDATE users SET role = 'admin' WHERE email = '...';`
- Run `sql/sprint2_pranav.sql` once if your database was created before the lockout and audit columns existed.


## Sprint 2: seat promotion, train admin, HTTPS and uptime
- **Waitlist/RAC promotion (RRS-F-051):** a cancellation moves the earliest RAC passenger to CONFIRMED (with a PNR) and refills RAC from the waiting list, in booking order. Each move is audited as `BOOKING_PROMOTED`.
- **Train and schedule admin (RRS-F-060):** admins use `/admin/trains` (API under `/api/admin/trains`). Search shows changes straight away. A train with bookings is hidden instead of deleted.
- **HTTPS only (PRJ-SR-001):** `bash scripts/make_dev_cert.sh`, then `REQUIRE_HTTPS=1 python run_https.py` and open https://localhost:5000. Behind a proxy that ends TLS, set `REQUIRE_HTTPS=1` and `TRUST_PROXY=1`.
- **Uptime (RRS-NF-002):** `/health` for checks; `python scripts/uptime_probe.py --url http://localhost:5000/health` writes `logs/uptime.csv`; admins see the percentage at `/api/admin/availability`.
- **Usability (RRS-NF-005):** skip link, labelled fields, status badges with a symbol. Manual walkthrough: `docs/TC-UX-01_usability_walkthrough.md`.
