"""
Dev-only launcher: runs the license activation dialog standalone, so it can
be visually tested on Linux. winreg isn't available here, so get_hardware_id()
falls through to its MAC-based fallback automatically -- the same path a
locked-down Windows machine would take.

Prints a matching license key for the current (fallback) hardware ID so you
can paste it into the dialog and prove the full activate loop end-to-end,
or type garbage to exercise the inline-error path.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tools"))

from PyQt5.QtWidgets import QApplication
from modules.Configurations import BarcodeConfig
from modules.licensing import get_hardware_id
from modules.ui.license_dialog import LicenseDialog
from generate_license import generate_license_key  # vendor-only tool, dev/testing use only

app = QApplication(sys.argv)

config = BarcodeConfig()
config.set_license_key("")  # force the fresh/unactivated visual state on every dev run

hwid = get_hardware_id()
print("Hardware ID:  ", hwid)
print("Matching key: ", generate_license_key(hwid), "(paste this into the dialog to test the accept path)")

dialog = LicenseDialog(config)
result = dialog.exec_()
print("Dialog result:", "Accepted" if result else "Rejected/closed")
sys.exit(0)
