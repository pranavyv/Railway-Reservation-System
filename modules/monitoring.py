"""Uptime and failure monitoring (RRS-NF-002, SAD 4.4).

* Metrics counts requests and server errors since the app started.
* The uptime probe (scripts/uptime_probe.py) calls /health on a timer and appends
  one row per check to a CSV; availability_from_log() turns that log into the
  percentage that RRS-NF-002 asks for ("uptime logs show 99% or more").
"""
import csv
import os
import ssl
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone


class Metrics:
    def __init__(self, clock=time.time):
        self._clock = clock
        self.started = clock()
        self.requests = 0
        self.server_errors = 0
        self._lock = threading.Lock()

    def record(self, status_code):
        with self._lock:
            self.requests += 1
            if status_code >= 500:
                self.server_errors += 1

    def snapshot(self):
        with self._lock:
            total, errors = self.requests, self.server_errors
        return {
            "uptime_seconds": int(self._clock() - self.started),
            "requests": total,
            "server_errors": errors,
            "error_rate_percent": round(errors / total * 100, 2) if total else 0.0,
        }


metrics = Metrics()


def register(app):
    """Count every response so the admin availability view can report the error rate."""

    @app.after_request
    def count_request(response):
        if not (request_path_is_static()):
            metrics.record(response.status_code)
        return response


def request_path_is_static():
    from flask import request

    return request.endpoint == "static"


# ---- probe log -------------------------------------------------------------------
def append_probe_row(path, ok, latency_ms, now=None):
    now = now or datetime.now(timezone.utc)
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "a", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerow([now.isoformat(timespec="seconds"), 1 if ok else 0, int(latency_ms)])


def probe_once(url, timeout=5.0, insecure=False):
    """GET url once. Returns (ok, latency_ms); ok means HTTP 200 within the timeout."""
    context = None
    if insecure and url.lower().startswith("https"):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # dev certificates only
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout, context=context) as response:
            ok = response.status == 200
    except (urllib.error.URLError, OSError, ValueError):
        ok = False
    return ok, (time.perf_counter() - started) * 1000


def availability_from_log(path, since_hours=None, now=None):
    """Summary of the probe log, or None when there is no usable data yet."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=since_hours) if since_hours else None
    checks = up = 0
    first = None
    try:
        handle = open(path, newline="", encoding="utf-8")
    except FileNotFoundError:
        return None
    with handle:
        for row in csv.reader(handle):
            try:
                moment = datetime.fromisoformat(row[0])
                ok = row[1] == "1"
            except (IndexError, ValueError):
                continue  # skip damaged lines instead of failing the report
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=timezone.utc)
            if cutoff and moment < cutoff:
                continue
            checks += 1
            up += ok
            first = first or moment
    if not checks:
        return None
    return {
        "checks": checks,
        "up": up,
        "availability_percent": round(up / checks * 100, 2),
        "since": first.isoformat(timespec="seconds"),
    }
