"""Database connection helper (Supabase / PostgreSQL).

All SQL lives in the repository/ package; modules never open connections.
"""
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

from config import Config


@contextmanager
def get_cursor(commit=False):
    conn = psycopg2.connect(Config.DATABASE_URL, sslmode=Config.DB_SSLMODE)
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
