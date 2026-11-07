
-- Issue #19: Associate audit events with railway bookings.
-- Keep booking references so audit history is not deleted
-- automatically when a booking is removed.

ALTER TABLE audit_log
ADD COLUMN IF NOT EXISTS booking_id INTEGER
REFERENCES bookings(id);

CREATE INDEX IF NOT EXISTS idx_audit_log_booking
ON audit_log (booking_id, created_at);
