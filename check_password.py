from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from datetime import datetime
from settings3 import SettingsWindow
import sys
import os

class PasswordCheck(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi(self.resource_path("ui/password.ui"), self)
        self.setWindowIcon(QIcon(self.resource_path("images/logo.ico")))
        self.setWindowTitle("Authorization")
        self.setFixedSize(400, 300)

        # Alternatively, set the maximum size equal to the minimum size to prevent maximizing
        self.setMaximumSize(400, 300)
        self.setMinimumSize(400, 300)

        self.et_password = self.findChild(QtWidgets.QLineEdit, 'et_password')
        self.et_password.setPlaceholderText("Enter the Password")
        self.btn_checkPassword = self.findChild(QtWidgets.QPushButton, 'btn_checkPassword')
        self.lbl_background = self.findChild(QtWidgets.QLabel, 'lbl_background')
        self.lbl_iconPassword = self.findChild(QtWidgets.QLabel, "lbl_iconPassword")

        # Connect button signal to check password
        self.et_password.returnPressed.connect(self.validate_password)
        self.btn_checkPassword.clicked.connect(self.validate_password)
        self.lbl_background.setPixmap(QPixmap(self.resource_path("images/background.jpg")))
        self.lbl_iconPassword.setPixmap(QPixmap(self.resource_path("images/passwordIcon.png")))

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)
    
    def validate_password(self):
        # Get current date, month, and year
        now = datetime.now()
        current_date = now.day
        current_month = now.month
        current_year_last_two = now.year

        # Generate the password
        expected_password = current_date * current_month * current_year_last_two

        # Get the entered password
        entered_password = self.et_password.text()

        # Check the password
        if entered_password == str(expected_password):
            self.open_main_window()
        else:
            QMessageBox.warning(self, "Error", "Incorrect password!")

    def open_main_window(self):
        self.close()  # Close the password window
        self.main_window = SettingsWindow()
        self.main_window.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PasswordCheck()
    window.showMaximized()
    sys.exit(app.exec_())
