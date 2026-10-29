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
| `modules/` | Auth, Search (add Booking, Payment, Allocation, Admin here) |
| `repository/` | All SQL, one file per area |
| `schema.sql`, `seed.sql` | Database tables and sample data |
| `templates/`, `static/` | HTML and CSS |
