"""
Offline, node-locked licensing -- verification side (this module ships
inside the customer-facing .exe).

Hardware ID: derived from the Windows MachineGuid (stable per-OS-install
identifier), falling back to the MAC address only when MachineGuid can't be
read (non-Windows dev machine, or a locked-down box that blocks the
registry read). MAC is NOT combined with MachineGuid on the normal Windows
path -- uuid.getnode() can return a non-deterministic random value when no
real NIC is found, which would make a combined fingerprint unstable across
runs on some VMs/sandboxes.

License key: an Ed25519 signature (by the vendor's private key, held only
in tools/generate_license.py -- never shipped) over the hardware ID,
base64-encoded. This module only holds the PUBLIC key, so it can verify a
signature but cannot produce a new one -- unlike the earlier HMAC-based
scheme, decompiling this shipped module reveals nothing that lets an
attacker mint a valid key for a different machine.
"""
import base64
import hashlib
import uuid

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# Public half of the vendor's Ed25519 keypair. Safe to ship -- verification
# only, cannot be used to generate new license keys.
_PUBLIC_KEY_BYTES = bytes.fromhex("214d120a719627f85fb1d9733901aed33768c443cdcc83bcab70f4997a2dc97c")


def _get_machine_guid():
    """Windows MachineGuid from the registry, or None if unavailable
    (non-Windows, or registry read blocked)."""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
        try:
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            return guid
        finally:
            winreg.CloseKey(key)
    except (ImportError, OSError, FileNotFoundError):
        return None


def _get_mac_fallback():
    """MAC-derived fallback, used only when MachineGuid isn't available."""
    return str(uuid.getnode())


def _fingerprint_source() -> str:
    guid = _get_machine_guid()
    return guid if guid else _get_mac_fallback()


def normalize_hardware_id(hardware_id: str) -> str:
    """Strip whitespace/dashes and uppercase -- tolerant of however a user
    (or the vendor tool) types/pastes a hardware ID. Shared with
    tools/generate_license.py so both sides sign/verify the exact same
    normalized bytes."""
    return (hardware_id or "").strip().upper().replace("-", "").replace(" ", "")


def _group(s: str, size: int = 4, sep: str = "-") -> str:
    return sep.join(s[i:i + size] for i in range(0, len(s), size))


def get_hardware_id() -> str:
    """Human-shareable hardware ID for the CURRENT machine, e.g. 'A1B2-C3D4-E5F6-1234'."""
    raw = _fingerprint_source().encode("utf-8")
    digest_hex = hashlib.sha256(raw).hexdigest().upper()[:16]
    return _group(digest_hex)


def validate_license_key(license_key: str, hardware_id: str = None) -> bool:
    """Verifies license_key is a valid Ed25519 signature (by the vendor's
    private key) over hardware_id. hardware_id defaults to THIS machine's
    current hardware ID -- never trust a stored hardware ID."""
    if not license_key:
        return False
    hardware_id = hardware_id or get_hardware_id()
    try:
        signature = base64.b64decode("".join(license_key.split()), validate=True)
    except (ValueError, base64.binascii.Error):
        return False

    public_key = Ed25519PublicKey.from_public_bytes(_PUBLIC_KEY_BYTES)
    message = normalize_hardware_id(hardware_id).encode("utf-8")
    try:
        public_key.verify(signature, message)
        return True
    except InvalidSignature:
        return False


def is_licensed(config) -> bool:
    """config: a BarcodeConfig instance. Always recomputes the hardware ID
    fresh -- copying settings/license to a different PC must not work."""
    stored_key = config.get_license_key()
    if not stored_key:
        return False
    return validate_license_key(stored_key, get_hardware_id())


def activate_license(config, license_key: str) -> bool:
    """Validates license_key against THIS machine and persists it if valid.
    Returns False (and does not persist) on an invalid key."""
    cleaned = "".join((license_key or "").split())
    if not validate_license_key(cleaned, get_hardware_id()):
        return False
    config.set_license_key(cleaned)
    return True
