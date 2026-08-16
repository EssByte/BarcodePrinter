"""
Dev-only launcher: runs the Dashboard window with fake diagnostic results
instead of the real DiagnosticThread (which needs pyodbc/USB/win32), so it
can be visually tested on Linux.
"""
import sys
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)

from dashboard import DashboardWindow

window = DashboardWindow()

# Show a realistic mix of states instead of waiting on the real background
# scan (which will fail immediately here -- no real DB/USB on this machine).
window.update_diagnostic_result("lbl_resultConnectivity", "✅")
window.update_diagnostic_result("lbl_resultDatabase", "✅")
window.update_diagnostic_result("lbl_resultConnectedDevice", "❌")
window.update_diagnostic_result("lbl_resultConfiguration", "✅")
window.update_diagnostic_result("lbl_loggingResult", "Enabled")
window.update_diagnostic_result("lbl_security_status", "✅")
window.loading_overlay.hide()
window.btn_reload.setEnabled(True)

window.show()
sys.exit(app.exec_())
