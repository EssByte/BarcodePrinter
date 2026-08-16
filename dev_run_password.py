"""
Dev-only launcher: runs the password/authorization window standalone, so
it can be visually tested on Linux.
"""
import sys
from PyQt5.QtWidgets import QApplication
from check_password import PasswordCheck

app = QApplication(sys.argv)
window = PasswordCheck()
window.show()
sys.exit(app.exec_())
