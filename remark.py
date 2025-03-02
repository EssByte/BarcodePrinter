import os
import sys
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
from PyQt5.uic import loadUi

from modules.logger_config import setup_logger  # To load the .ui file directly

# If you converted the .ui file to .py, use this instead:
# from remark_ui import Ui_Dialog

class RemarkDialog(QDialog):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.logger = setup_logger('RemarkUI')
        loadUi(self.resource_path("ui/remark.ui"), self)  

        # Connect buttons to their respective slots
        self.btn_cancel.clicked.connect(self.on_cancel)
        self.btn_write.clicked.connect(self.on_write)
    
        self.__remark = ""
        self.__isAccepted = False

    def resource_path(self, relative_path):
        try:
            # Attempt to get the PyInstaller base path
            self.logger.debug(f"Attempting to resolve resource path for: {relative_path}")
            base_path = sys._MEIPASS
            self.logger.debug(f"PyInstaller base path resolved: {base_path}")
        except AttributeError:
            # Fall back to the current working directory in development mode
            base_path = os.path.abspath(".")
            self.logger.debug(f"Development mode detected. Base path resolved to: {base_path}")
        except Exception as e:
            self.logger.exception(f"Unexpected error while resolving base path: {e}")
            raise

        # Construct the absolute path to the resource
        absolute_path = os.path.join(base_path, relative_path)
        self.logger.debug(f"Absolute resource path resolved: {absolute_path}")
        return absolute_path

    def get_accepted(self):
        return self.__isAccepted
    
    def set_accepted(self, isAccepted):
        self.__isAccepted = isAccepted
    
    def get_remark(self):
        return self.__remark
    
    def set_remark(self, remark):
        self.__remark = remark

    def on_cancel(self):
        self.et_remark.clear()
        self.set_remark("")
        self.set_accepted(False)
        self.close()

    def on_write(self):
        remark_text = self.et_remark.text().strip() 

        if not remark_text:
            QMessageBox.warning(self, "Error", "Remark cannot be empty!")
            return

        self.set_remark(remark_text)
        QMessageBox.information(self, "Success", "Remark saved successfully!")

        self.et_remark.clear()
        self.set_accepted(True)
        self.close()


# Main application
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create and show the dialog
    dialog = RemarkDialog()
    dialog.show()

    # Run the application
    sys.exit(app.exec_())