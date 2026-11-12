"""SQL for the health check and payment failure figures (RRS-NF-002)."""
from db import get_cursor


def check_db():
    """True when the database answers a trivial query."""
    with get_cursor() as cursor:
        cursor.execute("SELECT 1 AS ok")
        return cursor.fetchone()["ok"] == 1


def payment_counts():
    """Totals of payment outcomes, for the transaction failure rate (SAD 4.4)."""
    with get_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) AS total, "
            "COUNT(*) FILTER (WHERE status <> 'SUCCESS') AS failed FROM payments"
        )
        return cursor.fetchone()
