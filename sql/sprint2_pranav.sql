-- Sprint 2 (Pranav): RRS-F-003 lockout, PRJ-SR-006 audit log.
-- Safe to run more than once, and only needed if your Supabase tables predate schema.sql.

ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS audit_log (
    id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id    INTEGER REFERENCES users(id),
    booking_id INTEGER REFERENCES bookings(id),
    action     TEXT        NOT NULL,
    details    TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS booking_id INTEGER REFERENCES bookings(id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log (created_at DESC);

-- To try the admin-only endpoints, promote one registered account:
-- UPDATE users SET role = 'admin' WHERE email = 'your-admin@example.com';
