"""SQL for admin train and schedule management (RRS-F-060).

Every change and its audit entry are written in the same transaction, so a change
can never exist without its log line (PRJ-SR-006).
"""
import json

import psycopg2

from db import get_cursor
from repository.audit_repo import write_audit_log

_TRAIN_COLUMNS = "id, train_no, name, source, destination, departure_time, arrival_time, active"
_UPDATABLE = ("train_no", "name", "source", "destination", "departure_time", "arrival_time", "active")
_LIVE_SEATS = "(status = 'CONFIRMED' OR (status = 'PROVISIONAL' AND held_until > NOW()))"


def _audit(cursor, actor_id, action, details):
    write_audit_log(cursor, actor_id, action, None, json.dumps(details, default=str, sort_keys=True))


def list_rows():
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT t.id AS train_id, t.train_no, t.name, t.source, t.destination,
                   t.departure_time, t.arrival_time, t.active,
                   s.id AS schedule_id, s.travel_date,
                   sc.class_code, sc.total_seats, sc.fare
            FROM trains t
            LEFT JOIN schedules s         ON s.train_id = t.id
            LEFT JOIN schedule_classes sc ON sc.schedule_id = s.id
            ORDER BY t.train_no, s.travel_date, sc.class_code
            """
        )
        return cursor.fetchall()


def insert_train(values, actor_id, details):
    try:
        with get_cursor(commit=True) as cursor:
            cursor.execute(
                "INSERT INTO trains (train_no, name, source, destination, departure_time, arrival_time) "
                "VALUES (%(train_no)s, %(name)s, %(source)s, %(destination)s, "
                "%(departure_time)s, %(arrival_time)s) RETURNING " + _TRAIN_COLUMNS,
                values,
            )
            row = cursor.fetchone()
            _audit(cursor, actor_id, "ADMIN_ADD_TRAIN", {"train_id": row["id"], **details})
            return row
    except psycopg2.errors.UniqueViolation:
        raise ValueError("A train with this number already exists.")


def update_train(train_id, values, actor_id, details):
    assignments = [f"{column} = %({column})s" for column in _UPDATABLE if column in values]
    try:
        with get_cursor(commit=True) as cursor:
            cursor.execute(
                f"UPDATE trains SET {', '.join(assignments)} WHERE id = %(train_id)s "
                f"RETURNING {_TRAIN_COLUMNS}",
                {**values, "train_id": train_id},
            )
            row = cursor.fetchone()
            if row is not None:
                _audit(cursor, actor_id, "ADMIN_UPDATE_TRAIN", details)
            return row
    except psycopg2.errors.UniqueViolation:
        raise ValueError("A train with this number already exists.")


def remove_train(train_id, actor_id):
    """'deleted' if nobody booked it, 'deactivated' if bookings exist, None if not found."""
    with get_cursor(commit=True) as cursor:
        cursor.execute("SELECT id, train_no FROM trains WHERE id = %s FOR UPDATE", (train_id,))
        train = cursor.fetchone()
        if train is None:
            return None
        cursor.execute(
            "SELECT 1 FROM bookings b JOIN schedules s ON s.id = b.schedule_id "
            "WHERE s.train_id = %s LIMIT 1",
            (train_id,),
        )
        details = {"train_id": train_id, "train_no": train["train_no"]}
        if cursor.fetchone() is None:
            cursor.execute("DELETE FROM trains WHERE id = %s", (train_id,))
            _audit(cursor, actor_id, "ADMIN_DELETE_TRAIN", details)
            return "deleted"
        cursor.execute("UPDATE trains SET active = FALSE WHERE id = %s", (train_id,))
        _audit(cursor, actor_id, "ADMIN_DEACTIVATE_TRAIN", details)
        return "deactivated"


def insert_schedule(train_id, travel_date, classes, actor_id, details):
    try:
        with get_cursor(commit=True) as cursor:
            cursor.execute("SELECT 1 FROM trains WHERE id = %s", (train_id,))
            if cursor.fetchone() is None:
                return None
            cursor.execute(
                "INSERT INTO schedules (train_id, travel_date) VALUES (%s, %s) RETURNING id",
                (train_id, travel_date),
            )
            row = cursor.fetchone()
            for item in classes:
                cursor.execute(
                    "INSERT INTO schedule_classes (schedule_id, class_code, total_seats, fare) "
                    "VALUES (%s, %s, %s, %s)",
                    (row["id"], item["class_code"], item["total_seats"], item["fare"]),
                )
            _audit(cursor, actor_id, "ADMIN_ADD_SCHEDULE", {"schedule_id": row["id"], **details})
            return row
    except psycopg2.errors.UniqueViolation:
        raise ValueError("This train already has a schedule on that date.")


def update_schedule(schedule_id, classes, actor_id, details):
    """Set seats and fare per class (adds a class if it is new). Never drops below booked seats."""
    with get_cursor(commit=True) as cursor:
        cursor.execute("SELECT id FROM schedules WHERE id = %s FOR UPDATE", (schedule_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        for item in classes:
            cursor.execute(
                f"SELECT COUNT(*) AS booked FROM bookings "
                f"WHERE schedule_id = %s AND class_code = %s AND {_LIVE_SEATS}",
                (schedule_id, item["class_code"]),
            )
            booked = int(cursor.fetchone()["booked"])
            if item["total_seats"] < booked:
                raise ValueError(
                    f"Class {item['class_code']} already has {booked} booked seats; "
                    f"seats cannot go below that."
                )
            cursor.execute(
                "INSERT INTO schedule_classes (schedule_id, class_code, total_seats, fare) "
                "VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (schedule_id, class_code) "
                "DO UPDATE SET total_seats = EXCLUDED.total_seats, fare = EXCLUDED.fare",
                (schedule_id, item["class_code"], item["total_seats"], item["fare"]),
            )
        _audit(cursor, actor_id, "ADMIN_UPDATE_SCHEDULE", details)
        return row


def remove_schedule(schedule_id, actor_id, details):
    with get_cursor(commit=True) as cursor:
        cursor.execute("SELECT id FROM schedules WHERE id = %s FOR UPDATE", (schedule_id,))
        if cursor.fetchone() is None:
            return None
        cursor.execute("SELECT 1 FROM bookings WHERE schedule_id = %s LIMIT 1", (schedule_id,))
        if cursor.fetchone() is not None:
            raise ValueError("This schedule has bookings and cannot be removed.")
        cursor.execute("DELETE FROM schedules WHERE id = %s", (schedule_id,))
        _audit(cursor, actor_id, "ADMIN_DELETE_SCHEDULE", details)
        return True
