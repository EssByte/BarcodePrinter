"""Bridges the license portal to the same signing logic tools/generate_license.py
uses, so both always sign identical bytes for a given hardware ID."""
import base64
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

from modules.licensing import normalize_hardware_id  # noqa: E402
from tools._signing_key import load_private_key  # noqa: E402


def generate_license_key(hardware_id: str) -> str:
    private_key = load_private_key()
    message = normalize_hardware_id(hardware_id).encode("utf-8")
    signature = private_key.sign(message)
    return base64.b64encode(signature).decode("ascii")
