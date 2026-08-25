"""
Self-hosted, drop-in replacement for GitHub Releases: serves the latest
BarcodePrinter build to the installer/updater, and accepts a new build
from CI. Meant to run ONLY behind the `barcodereleases` Cloudflare Tunnel
-- binds to 127.0.0.1, never a public interface (see run.py / systemd
units).

Only /upload requires auth (a bearer token, CI-only, checked against a
locally-stored secret). The /releases/* routes are intentionally public,
same as GitHub Releases were -- that's how customer installers/updaters
have always fetched these files.
"""
import hashlib
import hmac
import json
import logging
import os
import shutil
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

DATA_DIR = Path(os.path.expanduser("~/.barcodeprinter-releases"))
CURRENT_DIR = DATA_DIR / "current"
LATEST_JSON = DATA_DIR / "latest.json"
TOKEN_PATH = DATA_DIR / "secrets" / "upload_token.hex"
LOG_DIR = DATA_DIR / "logs"

ALLOWED_FILENAMES = {"BarcodePrinter.exe", "Updater.exe", "InstallationWizard.exe", "libusb-1.0.dll"}
MAX_CONTENT_LENGTH = 300 * 1024 * 1024  # generous headroom for 4 onefile exes


def _load_upload_token() -> str:
    return TOKEN_PATH.read_text().strip()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    LOG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    handler = RotatingFileHandler(LOG_DIR / "release_server.log", maxBytes=1_000_000, backupCount=3)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    audit_log = logging.getLogger("release_server.audit")
    audit_log.setLevel(logging.INFO)
    audit_log.addHandler(handler)

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers.pop("Server", None)
        return response

    @app.get("/releases/latest")
    def latest():
        if not LATEST_JSON.exists():
            return jsonify({"error": "no release published yet"}), 404
        return jsonify(json.loads(LATEST_JSON.read_text()))

    @app.get("/releases/latest/download/<filename>")
    def download(filename):
        if filename not in ALLOWED_FILENAMES:
            abort(404)
        if not (CURRENT_DIR / filename).exists():
            abort(404)
        return send_from_directory(CURRENT_DIR, filename, as_attachment=True)

    def _check_auth():
        auth = request.headers.get("Authorization", "")
        provided = auth[len("Bearer "):] if auth.startswith("Bearer ") else ""
        if not provided or not hmac.compare_digest(provided, _load_upload_token()):
            audit_log.info("upload rejected: bad/missing token, ip=%s", request.remote_addr)
            abort(401)

    # One request per file (instead of one combined multipart body) --
    # Cloudflare's edge caps request body size well under the ~50MB these
    # onefile PyInstaller builds run, but a single combined upload of all
    # four together exceeds it. CI uploads each file, then calls finalize.
    @app.put("/upload/<filename>")
    def upload_file(filename):
        _check_auth()
        if filename not in ALLOWED_FILENAMES:
            abort(404)

        staging = DATA_DIR / "staging"
        staging.mkdir(parents=True, mode=0o700, exist_ok=True)
        dest = staging / secure_filename(filename)
        with open(dest, "wb") as out:
            shutil.copyfileobj(request.stream, out)

        checksum = hashlib.sha256(dest.read_bytes()).hexdigest()
        audit_log.info("staged file=%s sha256=%s size=%d", filename, checksum, dest.stat().st_size)
        return jsonify({"filename": filename, "sha256": checksum}), 200

    @app.post("/upload/finalize")
    def finalize_upload():
        _check_auth()
        tag_name = (request.form.get("tag_name") or (request.get_json(silent=True) or {}).get("tag_name") or "").strip()
        if not tag_name:
            return jsonify({"error": "tag_name is required"}), 400

        staging = DATA_DIR / "staging"
        missing = [name for name in ALLOWED_FILENAMES if not (staging / name).exists()]
        if missing:
            return jsonify({"error": f"missing staged files: {missing}"}), 400

        # Atomic-ish swap: current/ only ever holds a fully-uploaded set.
        if CURRENT_DIR.exists():
            shutil.rmtree(CURRENT_DIR)
        staging.rename(CURRENT_DIR)

        LATEST_JSON.write_text(json.dumps({"tag_name": tag_name}))

        audit_log.info("release published tag=%s", tag_name)
        return jsonify({"tag_name": tag_name}), 200

    return app


app = create_app()
