"""
Dev-only launcher: runs the label-details/confirm-print dialog standalone,
so it can be visually tested on Linux.
"""
import sys
from PyQt5.QtWidgets import QApplication
from modules.label_details_dialog import LabelDetailsDialog

app = QApplication(sys.argv)
dialog = LabelDetailsDialog()
result = dialog.exec_()
print("Accepted" if result else "Cancelled", dialog.get_data())
sys.exit(0)
