"""Record uptime evidence for RRS-NF-002.

Calls /health every few seconds and appends one row per check to logs/uptime.csv.
Run it in a second terminal while the app is up (or during the evaluation window):

    python scripts/uptime_probe.py --url http://localhost:5000/health --interval 10 --duration 3600
    python scripts/uptime_probe.py --url https://localhost:5000/health --insecure --once

Then open /api/admin/availability as an admin to see the percentage.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.monitoring import append_probe_row, availability_from_log, probe_once  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--url", default="http://localhost:5000/health")
    parser.add_argument("--log", default=os.environ.get("UPTIME_LOG", "logs/uptime.csv"))
    parser.add_argument("--interval", type=float, default=10.0, help="seconds between checks")
    parser.add_argument("--duration", type=float, default=0, help="stop after this many seconds (0 = until Ctrl+C)")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--insecure", action="store_true", help="accept a self-signed dev certificate")
    parser.add_argument("--once", action="store_true", help="one check, then exit")
    args = parser.parse_args()

    end = time.time() + args.duration if args.duration else None
    try:
        while True:
            ok, latency = probe_once(args.url, timeout=args.timeout, insecure=args.insecure)
            append_probe_row(args.log, ok, latency)
            print(f"{'UP  ' if ok else 'DOWN'} {latency:6.0f} ms  {args.url}")
            if args.once or (end and time.time() >= end):
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    summary = availability_from_log(args.log)
    if summary:
        print(f"Availability so far: {summary['availability_percent']}% "
              f"({summary['up']}/{summary['checks']} checks up) since {summary['since']}")


if __name__ == "__main__":
    main()
