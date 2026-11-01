-- Run once in the Supabase SQL editor (after schema.sql and seed.sql).
-- 1) RRS-F-042: record the refund for every cancelled booking.
CREATE TABLE IF NOT EXISTS refunds (
    id             INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    booking_id     INTEGER       NOT NULL UNIQUE REFERENCES bookings(id),
    amount         NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
    refund_percent INTEGER       NOT NULL CHECK (refund_percent BETWEEN 0 AND 100),
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- 2) Default cancellation policy, only if the table is still empty.
--    90% back at 48h+ before departure, 75% at 12h+, 50% at 4h+, nothing below that.
INSERT INTO cancellation_policy (min_hours_before, refund_percent)
SELECT v.hours, v.pct
FROM (VALUES (48, 90), (12, 75), (4, 50)) AS v(hours, pct)
WHERE NOT EXISTS (SELECT 1 FROM cancellation_policy);
