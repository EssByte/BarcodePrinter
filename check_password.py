from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget, QVBoxLayout, QFrame, QLabel, QLineEdit, QPushButton, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt5.QtGui import QPixmap, QIcon, QFont, QColor
from PyQt5.QtCore import Qt, QSize
from datetime import datetime
from settings3 import SettingsWindow
import sys
import os

class PasswordCheck(QMainWindow):
    def __init__(self, config=None):
        super().__init__()
        self.config = config
        self.setWindowTitle("Authorization")
        self.setFixedSize(450, 400)
        
        # Main container with background color
        self.central_widget = QWidget()
        self.central_widget.setObjectName("central_widget")
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("QWidget#central_widget { background-color: #f0f2f5; }")

        # Layout for centering the card
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setAlignment(Qt.AlignCenter)

        # The Login Card
        self.card = QFrame()
        self.card.setObjectName("card")
        self.card.setFixedSize(350, 320)
        self.card.setStyleSheet("""
            QFrame#card {
                background-color: white;
                border-radius: 15px;
            }
        """)
        
        # Shadow effect for the card
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.card.setGraphicsEffect(shadow)

        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(30, 40, 30, 40)
        self.card_layout.setSpacing(20)

        # Header
        self.label_title = QLabel("Admin Access")
        self.label_title.setAlignment(Qt.AlignCenter)
        self.label_title.setStyleSheet("font-family: 'Segoe UI'; font-size: 22px; font-weight: bold; color: #2c3e50;")
        self.card_layout.addWidget(self.label_title)

        self.label_subtitle = QLabel("Please enter password to continue")
        self.label_subtitle.setAlignment(Qt.AlignCenter)
        self.label_subtitle.setStyleSheet("font-family: 'Segoe UI'; font-size: 13px; color: #7f8c8d;")
        self.card_layout.addWidget(self.label_subtitle)
        
        self.card_layout.addSpacing(10)

        # Password Input
        self.et_password = QLineEdit()
        self.et_password.setEchoMode(QLineEdit.Password)
        self.et_password.setPlaceholderText("Password")
        self.et_password.setFixedSize(290, 45)
        self.et_password.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e6ed;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        self.card_layout.addWidget(self.et_password)

        # Check Button
        self.btn_checkPassword = QPushButton("Authorize")
        self.btn_checkPassword.setFixedSize(290, 45)
        self.btn_checkPassword.setCursor(Qt.PointingHandCursor)
        self.btn_checkPassword.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2980b9, stop:1 #1f6391);
            }
            QPushButton:pressed {
                background-color: #1f6391;
            }
        """)
        self.card_layout.addWidget(self.btn_checkPassword)

        self.main_layout.addWidget(self.card)

        # Core logic setup
        self.et_password.returnPressed.connect(self.validate_password)
        self.btn_checkPassword.clicked.connect(self.validate_password)
        self.setWindowIcon(QIcon(self.resource_path("images/logo.ico")))

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
        self.close()
        self.main_window = SettingsWindow(self.config)
        self.main_window.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PasswordCheck()
    window.showMaximized()
    sys.exit(app.exec_())
