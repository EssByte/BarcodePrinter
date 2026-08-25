"""User store + auth helpers for the license portal.

Users live in ~/.barcodeprinter-portal/secrets/users.json (outside the
repo, never git-tracked): {"username": {"password_hash": "..."}}.
Created/managed via scripts/add_user.py -- there's no signup flow in the
app itself.
"""
import json
import os
from functools import wraps
from pathlib import Path

from flask import redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

USERS_PATH = Path(os.path.expanduser("~/.barcodeprinter-portal/secrets/users.json"))

# Checked against on an unknown username so a login attempt takes roughly
# the same time whether or not the username exists -- avoids leaking which
# part (username vs password) was wrong via a timing side channel.
_DUMMY_HASH = generate_password_hash("not-a-real-password-used-only-for-timing")


def load_users() -> dict:
    if not USERS_PATH.exists():
        return {}
    return json.loads(USERS_PATH.read_text())


def save_users(users: dict) -> None:
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    USERS_PATH.write_text(json.dumps(users, indent=2))
    os.chmod(USERS_PATH, 0o600)


def verify_password(username: str, password: str) -> bool:
    entry = load_users().get(username)
    if not entry:
        check_password_hash(_DUMMY_HASH, password)
        return False
    return check_password_hash(entry["password_hash"], password)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("username"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped
