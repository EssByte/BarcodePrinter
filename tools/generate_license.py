"""
INTERNAL / VENDOR-ONLY -- holds the Ed25519 PRIVATE key. Never shipped in
any customer-facing build (not referenced by build_all.bat or
build_exe.bat, and the app's own modules/licensing.py only ever holds the
public half). Anyone with this file's secret can mint valid license keys,
so treat it the same way you'd treat any other signing credential --
don't paste it into chat, don't publish this repo publicly with it intact
if that ever becomes a concern, etc.

Usage:
    python tools/generate_license.py                       # interactive prompt
    python tools/generate_license.py A1B2-C3D4-E5F6-1234    # one-shot
"""
import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.licensing import normalize_hardware_id

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# Generated once with:
#   python -c "from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey; \
#              from cryptography.hazmat.primitives import serialization; \
#              k = Ed25519PrivateKey.generate(); \
#              print(k.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()).hex())"
# Never regenerate -- doing so invalidates every license key already issued
# to customers, since modules/licensing.py's embedded public key would no
# longer match.
_PRIVATE_KEY_BYTES = bytes.fromhex("REDACTED-KEY-PURGED-FROM-HISTORY-0001")


def generate_license_key(hardware_id: str) -> str:
    private_key = Ed25519PrivateKey.from_private_bytes(_PRIVATE_KEY_BYTES)
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
