import os

from dotenv import load_dotenv

load_dotenv()


def _flag(name, default="0"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")
    DATABASE_URL = os.environ.get("DATABASE_URL")
    DB_SSLMODE = os.environ.get("DB_SSLMODE", "require")
    DB_CONNECT_ATTEMPTS = int(os.environ.get("DB_CONNECT_ATTEMPTS", "3"))
    DB_CONNECT_TIMEOUT = int(os.environ.get("DB_CONNECT_TIMEOUT", "10"))

    # PRJ-SR-004: sessions end after this many seconds without a request.
    IDLE_TIMEOUT_SECONDS = int(os.environ.get("IDLE_TIMEOUT_SECONDS", "900"))

    # RRS-F-003: lock an account after this many wrong passwords in a row.
    MAX_FAILED_LOGINS = int(os.environ.get("MAX_FAILED_LOGINS", "5"))
    LOCKOUT_MINUTES = int(os.environ.get("LOCKOUT_MINUTES", "15"))

    # PRJ-SR-001: refuse plain HTTP. TRUST_PROXY=1 only behind a TLS-terminating proxy.
    REQUIRE_HTTPS = _flag("REQUIRE_HTTPS")
    TRUST_PROXY = _flag("TRUST_PROXY")

    # RRS-NF-002: where the uptime probe writes its log, and the availability goal in percent.
    UPTIME_LOG = os.environ.get("UPTIME_LOG", "logs/uptime.csv")
    AVAILABILITY_TARGET = float(os.environ.get("AVAILABILITY_TARGET", "99.0"))

    # Session cookie hardening (NF-003). Secure cookies are on automatically with REQUIRE_HTTPS.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _flag("SESSION_COOKIE_SECURE") or REQUIRE_HTTPS
