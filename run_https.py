"""Run the app locally over HTTPS with TLS 1.2+ only (PRJ-SR-001).

    bash scripts/make_dev_cert.sh      # once: creates certs/dev-cert.pem and certs/dev-key.pem
    REQUIRE_HTTPS=1 python run_https.py
    -> https://localhost:5000  (the browser warns about the self-signed certificate)
"""
import os
import sys

# Switch the HTTPS rule on for this launcher unless the caller chose otherwise.
os.environ.setdefault("REQUIRE_HTTPS", "1")

from app import app  # noqa: E402
from modules.transport_security import build_ssl_context  # noqa: E402

CERT = os.environ.get("TLS_CERT", "certs/dev-cert.pem")
KEY = os.environ.get("TLS_KEY", "certs/dev-key.pem")

if __name__ == "__main__":
    if not (os.path.exists(CERT) and os.path.exists(KEY)):
        sys.exit("Certificate not found. Run: bash scripts/make_dev_cert.sh")
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")),
            ssl_context=build_ssl_context(CERT, KEY))
