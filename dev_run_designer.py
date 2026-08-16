"""
Dev-only launcher: runs the layout designer standalone, without the rest of
the app, so it can be tested on Linux (main.py needs pywin32/pyodbc/libusb,
which are Windows-only in this codebase). Everything works except the
"Print Layout" button, which needs a real printer connection.
"""
import sys
from PyQt5.QtWidgets import QApplication
from modules.barcode_designer import BarcodeDesigner

app = QApplication(sys.argv)
window = BarcodeDesigner()
window.setWindowTitle("Layout Designer (dev preview)")
window.resize(1100, 700)
window.show()
sys.exit(app.exec_())
