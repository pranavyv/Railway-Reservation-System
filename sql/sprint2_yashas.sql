-- Yashas Sprint 2. Optional and safe to run more than once (Supabase SQL editor).
-- Speeds up the "who is next in line" lookup used by waitlist / RAC promotion (RRS-F-051).
CREATE INDEX IF NOT EXISTS idx_bookings_waiting_order
ON bookings (schedule_id, class_code, created_at, id)
WHERE status IN ('RAC', 'WAITLISTED');
