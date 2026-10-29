-- Railway Reservation System: Supabase (PostgreSQL) schema
-- Run in the Supabase SQL editor, or: psql "$DATABASE_URL" -f schema.sql
-- Shared by the whole team: agree on column names before changing them.

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            TEXT        NOT NULL,
    email           TEXT        NOT NULL UNIQUE,
    password_hash   TEXT        NOT NULL,              -- PRJ-SR-002: hash only
    role            TEXT        NOT NULL DEFAULT 'passenger' CHECK (role IN ('passenger', 'admin')),
    failed_attempts INTEGER     NOT NULL DEFAULT 0,    -- used by RRS-F-003 (Sprint 2)
    locked_until    TIMESTAMPTZ,                       -- used by RRS-F-003 (Sprint 2)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS trains (
    id             INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    train_no       TEXT    NOT NULL UNIQUE,
    name           TEXT    NOT NULL,
    source         TEXT    NOT NULL,
    destination    TEXT    NOT NULL,
    departure_time TIME    NOT NULL,
    arrival_time   TIME    NOT NULL,
    active         BOOLEAN NOT NULL DEFAULT TRUE
);

-- One row per train per travel date
CREATE TABLE IF NOT EXISTS schedules (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    train_id    INTEGER NOT NULL REFERENCES trains(id) ON DELETE CASCADE,
    travel_date DATE    NOT NULL,
    UNIQUE (train_id, travel_date)
);

-- Capacity and fare per class for a schedule
CREATE TABLE IF NOT EXISTS schedule_classes (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    schedule_id INTEGER       NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
    class_code  TEXT          NOT NULL,                -- SL, 3A, 2A
    total_seats INTEGER       NOT NULL CHECK (total_seats >= 0),
    fare        NUMERIC(10,2) NOT NULL CHECK (fare >= 0),
    UNIQUE (schedule_id, class_code)
);

-- Booking / Allocation / PNR (Narendra and Yashash)
CREATE TABLE IF NOT EXISTS bookings (
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pnr             TEXT UNIQUE,                       -- set only when CONFIRMED
    user_id         INTEGER NOT NULL REFERENCES users(id),
    schedule_id     INTEGER NOT NULL REFERENCES schedules(id),
    class_code      TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'PROVISIONAL'
                    CHECK (status IN ('PROVISIONAL', 'CONFIRMED', 'RAC', 'WAITLISTED', 'CANCELLED')),
    passenger_name  TEXT    NOT NULL,
    passenger_age   INTEGER NOT NULL CHECK (passenger_age BETWEEN 1 AND 120),
    passenger_gender TEXT   NOT NULL,
    berth_preference TEXT,
    fare            NUMERIC(10,2) NOT NULL,
    held_until      TIMESTAMPTZ,                       -- provisional hold expiry (RRS-F-021)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- PRJ-SR-005: only a transaction reference and status, never card data
CREATE TABLE IF NOT EXISTS payments (
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    booking_id      INTEGER NOT NULL REFERENCES bookings(id),
    transaction_ref TEXT    NOT NULL,
    status          TEXT    NOT NULL CHECK (status IN ('SUCCESS', 'FAILED', 'TIMEOUT')),
    amount          NUMERIC(10,2) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- RRS-F-042: refund percent by hours remaining before departure
CREATE TABLE IF NOT EXISTS cancellation_policy (
    id                 INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    min_hours_before   INTEGER NOT NULL,               -- applies when hours_left >= this value
    refund_percent     INTEGER NOT NULL CHECK (refund_percent BETWEEN 0 AND 100)
);

-- PRJ-SR-006: admin action audit trail
CREATE TABLE IF NOT EXISTS audit_log (
    id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id    INTEGER REFERENCES users(id),
    action     TEXT        NOT NULL,
    details    TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_trains_route      ON trains (lower(source), lower(destination));
CREATE INDEX IF NOT EXISTS idx_schedules_date    ON schedules (travel_date);
CREATE INDEX IF NOT EXISTS idx_bookings_schedule ON bookings (schedule_id, class_code, status);
