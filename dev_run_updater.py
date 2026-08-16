"""
Dev-only launcher: runs the updater window standalone, so it can be
visually tested on Linux.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib", "updater"))
from PyQt5.QtWidgets import QApplication
from Updater import Updater

app = QApplication(sys.argv)
window = Updater()
window.show()
sys.exit(app.exec_())
