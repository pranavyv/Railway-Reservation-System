-- Migration 003: Performance Optimization & Admin Reports Indexes (Issue #17, #18)
-- Safe, idempotent index additions for PostgreSQL / Supabase.
-- Optimizes queries for search, booking lookups, payment processing, and admin reporting.

-- 1. Index payments by booking_id to accelerate payment lookups and duplicate prevention
CREATE INDEX IF NOT EXISTS idx_payments_booking
ON payments (booking_id);

-- 2. Index payments by status and created_at for fast revenue report aggregation
CREATE INDEX IF NOT EXISTS idx_payments_status_created
ON payments (status, created_at);

-- 3. Index refunds by created_at for fast refund aggregation in date ranges
CREATE INDEX IF NOT EXISTS idx_refunds_created
ON refunds (created_at);

-- 4. Index bookings by created_at and status for fast booking report aggregation
CREATE INDEX IF NOT EXISTS idx_bookings_created_status
ON bookings (created_at, status);

-- 5. Index bookings by user_id for fast user ticket lookups
CREATE INDEX IF NOT EXISTS idx_bookings_user
ON bookings (user_id);

-- 6. Partial index on active provisional bookings to accelerate hold expiration and seat counting
CREATE INDEX IF NOT EXISTS idx_bookings_provisional_held
ON bookings (schedule_id, class_code, held_until)
WHERE status = 'PROVISIONAL';
