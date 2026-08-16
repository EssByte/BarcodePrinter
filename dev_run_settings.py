"""
Dev-only launcher: runs the Settings window standalone, without the
password gate or the rest of the app, so it can be visually tested on
Linux (main.py needs pywin32/pyodbc/libusb, which are Windows-only here).
"""
import sys
from PyQt5.QtWidgets import QApplication
from settings3 import SettingsWindow

app = QApplication(sys.argv)
window = SettingsWindow()
window.show()
sys.exit(app.exec_())
