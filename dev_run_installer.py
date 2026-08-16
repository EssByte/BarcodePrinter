"""
Dev-only launcher: runs the installation wizard standalone, so it can be
visually tested on Linux.
"""
import sys
from PyQt5.QtWidgets import QApplication
from InstallationWizard import InstallationWizard

app = QApplication(sys.argv)
window = InstallationWizard()
window.show()
sys.exit(app.exec_())
