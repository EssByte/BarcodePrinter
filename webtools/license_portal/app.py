"""
Internal license portal: a trusted vendor user logs in, pastes a customer's
hardware ID, gets back a signed license key. Meant to run ONLY behind the
`barcodeportal` Cloudflare Tunnel -- this process binds to 127.0.0.1 and is
never exposed on a public interface directly (see run.py / systemd units).
"""
import logging
import os
import secrets as pysecrets
from datetime import timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, redirect, render_template, request, session, url_for
from flask_limiter import Limiter
from flask_wtf import CSRFProtect

from auth import login_required, verify_password
from signing import generate_license_key

SECRETS_DIR = Path(os.path.expanduser("~/.barcodeprinter-portal/secrets"))
LOG_DIR = Path(os.path.expanduser("~/.barcodeprinter-portal/logs"))
SECRET_KEY_PATH = SECRETS_DIR / "flask_secret_key"


def _load_or_create_secret_key() -> bytes:
    SECRETS_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    if SECRET_KEY_PATH.exists():
        return bytes.fromhex(SECRET_KEY_PATH.read_text().strip())
    key = pysecrets.token_bytes(32)
    SECRET_KEY_PATH.write_text(key.hex())
    os.chmod(SECRET_KEY_PATH, 0o600)
    return key


def _real_ip() -> str:
    """The tunnel is the only way to reach this process, so Cloudflare's own
    header is authoritative here -- no need for a trusted-proxy allowlist
    the way you would on a directly internet-facing box."""
    return request.headers.get("CF-Connecting-IP", request.remote_addr or "unknown")


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=_load_or_create_secret_key(),
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        MAX_CONTENT_LENGTH=16 * 1024,  # tiny forms only
    )

    CSRFProtect(app)

    limiter = Limiter(key_func=_real_ip, app=app, default_limits=[])

    LOG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    handler = RotatingFileHandler(LOG_DIR / "portal.log", maxBytes=1_000_000, backupCount=3)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    audit_log = logging.getLogger("license_portal.audit")
    audit_log.setLevel(logging.INFO)
    audit_log.addHandler(handler)

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self'; frame-ancestors 'none'; base-uri 'none'; "
            "form-action 'self'"
        )
        response.headers.pop("Server", None)
        return response

    @app.route("/login", methods=["GET", "POST"])
    @limiter.limit("5 per 15 minutes", methods=["POST"])
    def login():
        if session.get("username"):
            return redirect(url_for("generate"))

        error = None
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            if verify_password(username, password):
                session.clear()
                session.permanent = True
                session["username"] = username
                audit_log.info("login success user=%s ip=%s", username, _real_ip())
                next_path = request.args.get("next")
                return redirect(next_path if next_path and next_path.startswith("/") else url_for("generate"))
            audit_log.info("login failed user=%s ip=%s", username or "(empty)", _real_ip())
            error = "Invalid username or password."

        return render_template("login.html", error=error)

    @app.route("/logout", methods=["POST"])
    def logout():
        username = session.get("username")
        session.clear()
        if username:
            audit_log.info("logout user=%s ip=%s", username, _real_ip())
        return redirect(url_for("login"))

    @app.route("/", methods=["GET", "POST"])
    @login_required
    def generate():
        error = None
        license_key = None
        hardware_id_display = ""

        if request.method == "POST":
            hardware_id_display = (request.form.get("hardware_id") or "").strip()
            if not hardware_id_display:
                error = "Enter a hardware ID."
            else:
                try:
                    license_key = generate_license_key(hardware_id_display)
                    audit_log.info("license issued by=%s ip=%s", session["username"], _real_ip())
                except Exception:
                    audit_log.exception("license generation failed by=%s", session["username"])
                    error = "Could not generate a license key. Check the hardware ID format and try again."

        return render_template(
            "generate.html",
            username=session["username"],
            error=error,
            license_key=license_key,
            hardware_id=hardware_id_display,
        )

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", message="Page not found."), 404

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("error.html", message="Something went wrong."), 500

    return app


app = create_app()
