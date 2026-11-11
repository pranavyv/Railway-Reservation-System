"""Database connection helper (Supabase / PostgreSQL).

All SQL lives in the repository/ package; modules never open connections.
Opening a connection is retried a few times so a short database or network blip
does not turn into a failed request (RRS-NF-002, SAD risk "database unavailable").
"""
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

from config import Config
from reliability import retry


def _connect():
    return psycopg2.connect(
        Config.DATABASE_URL,
        sslmode=Config.DB_SSLMODE,
        connect_timeout=Config.DB_CONNECT_TIMEOUT,
    )


@contextmanager
def get_cursor(commit=False):
    conn = retry(
        _connect,
        attempts=Config.DB_CONNECT_ATTEMPTS,
        base_delay=0.3,
        retry_on=(psycopg2.OperationalError,),
    )
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
