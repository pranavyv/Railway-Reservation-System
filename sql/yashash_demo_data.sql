-- Optional: one CONFIRMED booking with PNR 1234567890 for the first registered user,
-- so you can demo PNR lookup and cancellation before the booking flow is finished.
-- Register a user in the app first. Run in the Supabase SQL editor.
INSERT INTO bookings (pnr, user_id, schedule_id, class_code, status,
                      passenger_name, passenger_age, passenger_gender, fare)
SELECT '1234567890', (SELECT MIN(id) FROM users), sc.schedule_id, sc.class_code,
       'CONFIRMED', 'Demo Passenger', 30, 'F', sc.fare
FROM schedule_classes sc
JOIN schedules s ON s.id = sc.schedule_id
WHERE s.travel_date >= CURRENT_DATE + 3
ORDER BY s.travel_date
LIMIT 1
ON CONFLICT (pnr) DO NOTHING;
