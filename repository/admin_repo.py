"""Database queries for administrative reports (Issue #18, TC-Admin-02).

Covers:
- Booking reports (counts by status, class breakdown)
- Occupancy reports (train & schedule occupancy, capacity, percentages)
- Revenue reports (gross revenue from SUCCESS payments, refunds, net revenue)
"""

from decimal import Decimal
from db import get_cursor


def get_booking_report(start_date=None, end_date=None):
    """Retrieve booking statistics for an optional date range."""
    conditions = []
    params = []

    if start_date:
        conditions.append("created_at::date >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("created_at::date <= %s")
        params.append(end_date)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    query = f"""
        SELECT
            COUNT(*) AS total_bookings,
            COUNT(*) FILTER (WHERE status = 'CONFIRMED') AS confirmed_count,
            COUNT(*) FILTER (WHERE status = 'CANCELLED') AS cancelled_count,
            COUNT(*) FILTER (WHERE status = 'RAC') AS rac_count,
            COUNT(*) FILTER (WHERE status = 'WAITLISTED') AS waitlisted_count,
            COUNT(*) FILTER (WHERE status = 'PROVISIONAL') AS provisional_count
        FROM bookings
        {where_clause}
    """

    class_query = f"""
        SELECT class_code, COUNT(*) AS count
        FROM bookings
        {where_clause}
        GROUP BY class_code
        ORDER BY class_code
    """

    recent_query = f"""
        SELECT id, pnr, passenger_name, class_code, status, fare, created_at
        FROM bookings
        {where_clause}
        ORDER BY created_at DESC, id DESC
        LIMIT 20
    """

    with get_cursor() as cursor:
        cursor.execute(query, tuple(params))
        summary = cursor.fetchone() or {}

        cursor.execute(class_query, tuple(params))
        class_rows = cursor.fetchall() or []

        cursor.execute(recent_query, tuple(params))
        recent_rows = cursor.fetchall() or []

    return {
        "total_bookings": int(summary.get("total_bookings") or 0),
        "confirmed": int(summary.get("confirmed_count") or 0),
        "cancelled": int(summary.get("cancelled_count") or 0),
        "rac": int(summary.get("rac_count") or 0),
        "waitlisted": int(summary.get("waitlisted_count") or 0),
        "provisional": int(summary.get("provisional_count") or 0),
        "by_class": {r["class_code"]: int(r["count"]) for r in class_rows},
        "recent_bookings": [
            {
                "id": r["id"],
                "pnr": r.get("pnr") or "-",
                "passenger_name": r["passenger_name"],
                "class_code": r["class_code"],
                "status": r["status"],
                "fare": float(r["fare"]),
                "created_at": str(r["created_at"]),
            }
            for r in recent_rows
        ],
    }


def get_occupancy_report(start_date=None, end_date=None, train_id=None):
    """Retrieve occupancy figures train- and schedule-wise."""
    conditions = []
    params = []

    if start_date:
        conditions.append("s.travel_date >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("s.travel_date <= %s")
        params.append(end_date)
    if train_id:
        conditions.append("t.id = %s")
        params.append(train_id)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    query = f"""
        SELECT
            t.id AS train_id,
            t.train_no,
            t.name AS train_name,
            t.source,
            t.destination,
            s.id AS schedule_id,
            s.travel_date,
            sc.class_code,
            sc.total_seats,
            COUNT(b.id) FILTER (
                WHERE b.status = 'CONFIRMED'
                   OR (b.status = 'PROVISIONAL' AND b.held_until > NOW())
            ) AS allocated_seats,
            COUNT(b.id) FILTER (WHERE b.status = 'RAC') AS rac_count,
            COUNT(b.id) FILTER (WHERE b.status = 'WAITLISTED') AS waitlist_count
        FROM schedules s
        JOIN trains t ON t.id = s.train_id
        JOIN schedule_classes sc ON sc.schedule_id = s.id
        LEFT JOIN bookings b ON b.schedule_id = s.id AND b.class_code = sc.class_code
        {where_clause}
        GROUP BY t.id, t.train_no, t.name, t.source, t.destination,
                 s.id, s.travel_date, sc.class_code, sc.total_seats
        ORDER BY s.travel_date ASC, t.train_no ASC, sc.class_code ASC
    """

    with get_cursor() as cursor:
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall() or []

    schedules_report = []
    total_capacity = 0
    total_allocated = 0

    for r in rows:
        cap = int(r["total_seats"])
        alloc = int(r["allocated_seats"])
        remaining = max(0, cap - alloc)
        occupancy_pct = round((alloc / cap * 100), 2) if cap > 0 else 0.0

        total_capacity += cap
        total_allocated += alloc

        schedules_report.append({
            "train_id": r["train_id"],
            "train_no": r["train_no"],
            "train_name": r["train_name"],
            "source": r["source"],
            "destination": r["destination"],
            "travel_date": str(r["travel_date"]),
            "class_code": r["class_code"],
            "total_seats": cap,
            "allocated_seats": alloc,
            "remaining_seats": remaining,
            "occupancy_percent": occupancy_pct,
            "rac_count": int(r["rac_count"]),
            "waitlist_count": int(r["waitlist_count"]),
        })

    total_remaining = max(0, total_capacity - total_allocated)
    overall_occupancy_percent = (
        round((total_allocated / total_capacity * 100), 2)
        if total_capacity > 0 else 0.0
    )

    return {
        "total_capacity": total_capacity,
        "total_allocated": total_allocated,
        "total_remaining": total_remaining,
        "overall_occupancy_percent": overall_occupancy_percent,
        "schedules": schedules_report,
    }


def get_revenue_report(start_date=None, end_date=None):
    """Retrieve revenue and refund totals for an optional date range."""
    p_conds, p_params = [], []
    r_conds, r_params = [], []

    if start_date:
        p_conds.append("created_at::date >= %s")
        p_params.append(start_date)
        r_conds.append("created_at::date >= %s")
        r_params.append(start_date)
    if end_date:
        p_conds.append("created_at::date <= %s")
        p_params.append(end_date)
        r_conds.append("created_at::date <= %s")
        r_params.append(end_date)

    p_where = ("AND " + " AND ".join(p_conds)) if p_conds else ""
    p_all_where = ("WHERE " + " AND ".join(p_conds)) if p_conds else ""
    r_where = ("WHERE " + " AND ".join(r_conds)) if r_conds else ""

    # Gross revenue: strictly payments with status = 'SUCCESS'
    rev_query = f"""
        SELECT
            COALESCE(SUM(amount), 0) AS gross_revenue,
            COUNT(*) AS success_count
        FROM payments
        WHERE status = 'SUCCESS'
        {p_where}
    """

    # Failure / timeout counts
    status_query = f"""
        SELECT
            COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_count,
            COUNT(*) FILTER (WHERE status = 'TIMEOUT') AS timeout_count
        FROM payments
        {p_all_where}
    """

    # Refund totals
    refund_query = f"""
        SELECT
            COALESCE(SUM(amount), 0) AS total_refunds,
            COUNT(*) AS refund_count
        FROM refunds
        {r_where}
    """

    with get_cursor() as cursor:
        cursor.execute(rev_query, tuple(p_params))
        rev_row = cursor.fetchone() or {}

        cursor.execute(status_query, tuple(p_params))
        stat_row = cursor.fetchone() or {}

        cursor.execute(refund_query, tuple(r_params))
        ref_row = cursor.fetchone() or {}

    gross_revenue = Decimal(str(rev_row.get("gross_revenue") or 0))
    total_refunds = Decimal(str(ref_row.get("total_refunds") or 0))
    net_revenue = gross_revenue - total_refunds

    return {
        "gross_revenue": float(gross_revenue),
        "total_refunds": float(total_refunds),
        "net_revenue": float(net_revenue),
        "successful_payments_count": int(rev_row.get("success_count") or 0),
        "failed_payments_count": int(stat_row.get("failed_count") or 0),
        "timeout_payments_count": int(stat_row.get("timeout_count") or 0),
        "refund_count": int(ref_row.get("refund_count") or 0),
    }


def get_full_admin_report(start_date=None, end_date=None):
    """Combine booking, occupancy and revenue reports into one structure."""
    bookings = get_booking_report(start_date=start_date, end_date=end_date)
    occupancy = get_occupancy_report(start_date=start_date, end_date=end_date)
    revenue = get_revenue_report(start_date=start_date, end_date=end_date)

    return {
        "start_date": start_date or "",
        "end_date": end_date or "",
        "summary": {
            "total_bookings": bookings["total_bookings"],
            "confirmed_bookings": bookings["confirmed"],
            "cancelled_bookings": bookings["cancelled"],
            "rac_bookings": bookings["rac"],
            "waitlisted_bookings": bookings["waitlisted"],
            "gross_revenue": revenue["gross_revenue"],
            "total_refunds": revenue["total_refunds"],
            "net_revenue": revenue["net_revenue"],
            "total_capacity": occupancy["total_capacity"],
            "total_allocated": occupancy["total_allocated"],
            "total_remaining": occupancy["total_remaining"],
            "overall_occupancy_percent": occupancy["overall_occupancy_percent"],
        },
        "bookings": bookings,
        "occupancy": occupancy,
        "revenue": revenue,
    }
