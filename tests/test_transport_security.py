"""TC-Sec-02 (PRJ-SR-001): connections without TLS are rejected; TLS 1.2+ only."""
import shutil
import socket
import ssl
import subprocess
import threading

from flask import Flask, jsonify

from modules import transport_security


def _client(require_https=True, trust_proxy=False):
    app = Flask(__name__)
    app.secret_key = "test"
    app.config.update(REQUIRE_HTTPS=require_https, TRUST_PROXY=trust_proxy)

    @app.get("/page")
    def page():
        return "page"

    @app.post("/submit")
    def submit():
        return "submitted"

    @app.get("/api/data")
    def data():
        return jsonify(ok=True)

    transport_security.register(app)
    return app.test_client()


HTTP, HTTPS = "http://localhost", "https://localhost"


def test_plain_http_page_is_redirected_to_https():
    r = _client().get("/page?x=1", base_url=HTTP)
    assert r.status_code == 308
    assert r.headers["Location"] == "https://localhost/page?x=1"


def test_plain_http_api_and_posts_are_rejected():
    c = _client()
    r = c.get("/api/data", base_url=HTTP)
    assert r.status_code == 403 and r.get_json()["code"] == "https_required"
    assert c.post("/submit", base_url=HTTP).status_code == 403


def test_https_requests_work_and_get_hsts():
    r = _client().get("/page", base_url=HTTPS)
    assert r.status_code == 200
    assert "max-age=31536000" in r.headers["Strict-Transport-Security"]


def test_rule_is_off_by_default_for_local_development():
    r = _client(require_https=False).get("/page", base_url=HTTP)
    assert r.status_code == 200 and "Strict-Transport-Security" not in r.headers


def test_forwarded_proto_is_ignored_unless_proxy_is_trusted():
    headers = {"X-Forwarded-Proto": "https"}
    assert _client(trust_proxy=False).get("/page", base_url=HTTP, headers=headers).status_code == 308
    assert _client(trust_proxy=True).get("/page", base_url=HTTP, headers=headers).status_code == 200


def test_safe_headers_are_always_sent():
    r = _client(require_https=False).get("/page", base_url=HTTP)
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"


def test_ssl_context_refuses_anything_below_tls_1_2():
    if shutil.which("openssl") is None:
        return  # cannot create a certificate here; the handshake check is skipped
    import tempfile
    folder = tempfile.mkdtemp()
    cert, key = f"{folder}/c.pem", f"{folder}/k.pem"
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
                    "-keyout", key, "-out", cert, "-subj", "/CN=localhost"],
                   check=True, capture_output=True)
    context = transport_security.build_ssl_context(cert, key)
    assert context.minimum_version == ssl.TLSVersion.TLSv1_2

    def serve(listener):
        for _ in range(2):
            try:
                raw, _addr = listener.accept()
                with context.wrap_socket(raw, server_side=True) as tls:
                    tls.recv(1)
            except (ssl.SSLError, OSError):
                pass

    def connect(port, minimum, maximum):
        client = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        client.check_hostname = False
        client.verify_mode = ssl.CERT_NONE
        try:
            client.minimum_version, client.maximum_version = minimum, maximum
            with socket.create_connection(("127.0.0.1", port), timeout=5) as raw:
                with client.wrap_socket(raw) as tls:
                    tls.sendall(b"x")
                    return tls.version()
        except (ssl.SSLError, ValueError, OSError):
            return None

    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(2)
    thread = threading.Thread(target=serve, args=(listener,), daemon=True)
    thread.start()
    port = listener.getsockname()[1]
    assert connect(port, ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_3) in ("TLSv1.2", "TLSv1.3")
    assert connect(port, ssl.TLSVersion.MINIMUM_SUPPORTED, ssl.TLSVersion.TLSv1_1) is None
    listener.close()
