"""
INTERNAL / VENDOR-ONLY. Not shipped in any customer-facing build -- not
referenced by build_all.bat or build_exe.bat. Generates the license key
matching a customer's Hardware ID.

Usage:
    python tools/generate_license.py                       # interactive prompt
    python tools/generate_license.py A1B2-C3D4-E5F6-1234    # one-shot
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.licensing import generate_license_key


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
