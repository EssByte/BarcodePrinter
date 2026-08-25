"""
Shared loader for the vendor's Ed25519 PRIVATE signing key. Used by
tools/generate_license.py (CLI) and the license portal web app -- both need
the exact same key bytes, kept out of source control.

The key itself lives at ~/.barcodeprinter-portal/secrets/signing_key.hex
(mode 600), not in this repo. It's the same key that was previously
hardcoded in tools/generate_license.py -- moved out, not regenerated, so
every license key already issued to customers stays valid.
"""
import os
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

_KEY_PATH = Path(os.path.expanduser("~/.barcodeprinter-portal/secrets/signing_key.hex"))


def load_private_key() -> Ed25519PrivateKey:
    try:
        hex_bytes = _KEY_PATH.read_text().strip()
    except FileNotFoundError:
        raise SystemExit(
            f"Signing key not found at {_KEY_PATH}. "
            "This file holds the vendor's private license-signing key and is "
            "never committed to git -- it must exist on this machine before "
            "generate_license.py or the license portal can issue keys."
        )
    return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(hex_bytes))
