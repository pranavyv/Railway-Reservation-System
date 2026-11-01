-- Migration: Add allocation_status to existing bookings table.
-- Safe to run multiple times.

ALTER TABLE bookings
ADD COLUMN IF NOT EXISTS allocation_status TEXT
CHECK (
    allocation_status IN ('CONFIRMED', 'RAC', 'WAITLISTED')
);