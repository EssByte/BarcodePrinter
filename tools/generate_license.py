"""
INTERNAL / VENDOR-ONLY -- signs license keys with the Ed25519 PRIVATE key.
Never shipped in any customer-facing build (not referenced by
build_all.bat or build_exe.bat, and the app's own modules/licensing.py
only ever holds the public half).

The private key itself lives outside this repo, at
~/.barcodeprinter-portal/secrets/signing_key.hex (see tools/_signing_key.py)
-- it used to be hardcoded here, but that meant it sat in plaintext in git
history. Treat that file the same way you'd treat any other signing
credential: don't paste its contents into chat, don't move it into a
git-tracked path, etc.

Usage:
    python tools/generate_license.py                       # interactive prompt
    python tools/generate_license.py A1B2-C3D4-E5F6-1234    # one-shot
"""
import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.licensing import normalize_hardware_id
from tools._signing_key import load_private_key


def generate_license_key(hardware_id: str) -> str:
    private_key = load_private_key()
    message = normalize_hardware_id(hardware_id).encode("utf-8")
    signature = private_key.sign(message)
    return base64.b64encode(signature).decode("ascii")


def main():
    if len(sys.argv) > 1:
        hardware_id = sys.argv[1]
    else:
        hardware_id = input("Customer Hardware ID: ").strip()

    if not hardware_id:
        print("No hardware ID given.")
        return

    print("License Key:", generate_license_key(hardware_id))


if __name__ == "__main__":
    main()
