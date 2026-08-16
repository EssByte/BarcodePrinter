"""
Offline, node-locked licensing.

Hardware ID: derived from the Windows MachineGuid (stable per-OS-install
identifier), falling back to the MAC address only when MachineGuid can't be
read (non-Windows dev machine, or a locked-down box that blocks the
registry read). MAC is NOT combined with MachineGuid on the normal Windows
path -- uuid.getnode() can return a non-deterministic random value when no
real NIC is found, which would make a combined fingerprint unstable across
runs on some VMs/sandboxes.

License key: HMAC-SHA256 keyed with an app-embedded secret, over the
hardware ID. This is integrity/forgery-resistant (the point of a license
key), not confidentiality -- the hardware ID isn't sensitive. Known,
accepted limitation of purely offline/symmetric schemes: the verification
secret ships inside the .exe, so a determined attacker who decompiles the
PyInstaller binary could in principle extract it and forge keys. This is
the standard tradeoff for small-ISV offline licensing; asymmetric signing
(ship only a public key) would close that gap but needs the `cryptography`
package, which isn't in requirements.txt today. Documented upgrade path,
not implemented now.
"""
import base64
import hashlib
import hmac
import uuid

# Generated once with: python -c "import secrets; print(secrets.token_bytes(32).hex())"
# Never regenerate after keys have been issued to customers -- that
# invalidates every key already sold.
_LICENSE_SECRET = bytes.fromhex("636b238ced4ea4ba449c1e0fe373361ad64eae85c5d1723801dc0819d5b4bdcd")

_KEY_PREFIX = "ALPHA"
_DIGEST_BYTES = 10  # -> 16 base32 chars, no padding, groups evenly into 4x4


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


def _normalize(s: str) -> str:
    """Strip whitespace/dashes and uppercase -- tolerant of however a user
    pastes a hardware ID or license key."""
    return (s or "").strip().upper().replace("-", "").replace(" ", "")


def _group(s: str, size: int = 4, sep: str = "-") -> str:
    return sep.join(s[i:i + size] for i in range(0, len(s), size))


def get_hardware_id() -> str:
    """Human-shareable hardware ID for the CURRENT machine, e.g. 'A1B2-C3D4-E5F6-1234'."""
    raw = _fingerprint_source().encode("utf-8")
    digest_hex = hashlib.sha256(raw).hexdigest().upper()[:16]
    return _group(digest_hex)


def generate_license_key(hardware_id: str) -> str:
    """Vendor-side: compute the license key that matches a given hardware ID.
    hardware_id may be pasted with or without dashes/whitespace/lowercase."""
    normalized_hwid = _normalize(hardware_id)
    digest = hmac.new(_LICENSE_SECRET, normalized_hwid.encode("utf-8"), hashlib.sha256).digest()
    b32 = base64.b32encode(digest[:_DIGEST_BYTES]).decode("ascii").rstrip("=")
    return f"{_KEY_PREFIX}-{_group(b32)}"


def validate_license_key(license_key: str, hardware_id: str = None) -> bool:
    """Recomputes the expected key for hardware_id (defaults to THIS machine's
    current hardware ID -- never trust a stored hardware ID) and compares."""
    if not license_key:
        return False
    hardware_id = hardware_id or get_hardware_id()
    expected = _normalize(generate_license_key(hardware_id).replace(_KEY_PREFIX, "", 1))
    provided = _normalize(license_key)
    if provided.startswith(_KEY_PREFIX):
        provided = provided[len(_KEY_PREFIX):]
    return hmac.compare_digest(expected, provided)


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
    if not validate_license_key(license_key, get_hardware_id()):
        return False
    config.set_license_key(_normalize(license_key))
    return True
