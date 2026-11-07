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
