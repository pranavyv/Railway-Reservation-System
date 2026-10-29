-- Synthetic sample data only (no real personal data). Development use:
-- TRUNCATE below wipes trains, schedules, classes and anything referencing them.
TRUNCATE trains, schedules, schedule_classes, cancellation_policy RESTART IDENTITY CASCADE;

INSERT INTO trains (train_no, name, source, destination, departure_time, arrival_time) VALUES
 ('10001', 'Silicon Express',    'Bengaluru', 'Chennai',   '06:00', '11:30'),
 ('10002', 'Garden City Mail',   'Bengaluru', 'Mysuru',    '07:15', '10:00'),
 ('10003', 'Deccan Night Link',  'Bengaluru', 'Hyderabad', '20:00', '06:30'),
 ('10004', 'Coastal Runner',     'Mangaluru', 'Bengaluru', '21:30', '06:15'),
 ('10005', 'Southern Shuttle',   'Chennai',   'Bengaluru', '15:00', '20:30');

-- 30 days of schedules for every train
INSERT INTO schedules (train_id, travel_date)
SELECT t.id, d::date
FROM trains t, generate_series(CURRENT_DATE, CURRENT_DATE + 30, interval '1 day') AS d;

INSERT INTO schedule_classes (schedule_id, class_code, total_seats, fare)
SELECT s.id, c.class_code, c.total_seats, c.fare
FROM schedules s,
     (VALUES ('SL', 72, 350.00), ('3A', 64, 900.00), ('2A', 46, 1300.00)) AS c(class_code, total_seats, fare);

-- Refund policy: >=48h 90%, >=12h 50%, >=2h 25%, otherwise 0%
INSERT INTO cancellation_policy (min_hours_before, refund_percent) VALUES (48, 90), (12, 50), (2, 25), (0, 0);
