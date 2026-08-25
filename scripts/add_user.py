"""Add (or reset) a login for the license portal.

Run this yourself, interactively, on the machine that hosts the portal --
the generated password is printed only to this terminal, once, and never
stored in plaintext anywhere.

Usage:
    python scripts/add_user.py <username>
"""
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "webtools" / "license_portal"))
from auth import load_users, save_users  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/add_user.py <username>")
        return

    username = sys.argv[1].strip()
    if not username:
        print("Username can't be empty.")
        return

    password = secrets.token_urlsafe(18)  # ~24 chars, URL-safe
    users = load_users()
    users[username] = {"password_hash": generate_password_hash(password)}
    save_users(users)

    print(f"\nUser '{username}' saved.")
    print(f"Password: {password}")
    print("\nSave this now -- it will not be shown again. Store it in a password manager.")


if __name__ == "__main__":
    main()
