"""TLS enforcement and safe response headers (PRJ-SR-001, TC-Sec-02).

With REQUIRE_HTTPS=1 the app refuses plain-HTTP requests: pages are redirected
to the https:// address, everything else (APIs, form posts) gets a 403. Behind a
TLS-terminating proxy set TRUST_PROXY=1 so the proxy's X-Forwarded-Proto is
believed; leave it off otherwise, because anyone can forge that header.
"""
import ssl

from flask import jsonify, redirect, request
from werkzeug.middleware.proxy_fix import ProxyFix


def build_ssl_context(cert_file, key_file):
    """Server-side TLS context that accepts TLS 1.2 and newer only."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(cert_file, key_file)
    return context


def register(app):
    if app.config.get("TRUST_PROXY"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    @app.before_request
    def require_https():
        if not app.config.get("REQUIRE_HTTPS") or request.is_secure:
            return None
        if request.method in ("GET", "HEAD") and not request.path.startswith("/api/"):
            return redirect(request.url.replace("http://", "https://", 1), code=308)
        return jsonify(error="HTTPS is required.", code="https_required"), 403

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        if request.is_secure:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response
