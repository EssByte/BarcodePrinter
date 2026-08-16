from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget, QVBoxLayout, QFrame, QLabel, QLineEdit, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal
from datetime import datetime
from settings3 import SettingsWindow
import sys
import os

# Same "label stock" identity used across the rest of the app.
PW_INK = "#191b1f"
PW_CANVAS = "#f5f3ef"
PW_SURFACE = "#ffffff"
PW_BORDER = "#e6e2d9"
PW_TEXT = "#1f2226"
PW_TEXT_MUTED = "#74716a"
PW_ACCENT = "#c81d31"
PW_ACCENT_HOVER = "#a91729"

class PasswordCheck(QMainWindow):
    closed = pyqtSignal()

    def __init__(self, config=None):
        super().__init__()
        self.config = config
        self.setWindowTitle("Authorization")
        self.setFixedSize(450, 420)

        # Main container with background color
        self.central_widget = QWidget()
        self.central_widget.setObjectName("central_widget")
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet(f"QWidget#central_widget {{ background-color: {PW_CANVAS}; }}")

        # Layout for centering the card
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setAlignment(Qt.AlignCenter)

        # The Login Card
        self.card = QFrame()
        self.card.setObjectName("card")
        self.card.setFixedSize(350, 340)
        self.card.setStyleSheet(f"""
            QFrame#card {{
                background-color: {PW_SURFACE};
                border: 1px solid {PW_BORDER};
                border-radius: 12px;
            }}
        """)

        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(34, 36, 34, 36)
        self.card_layout.setSpacing(6)

        # Header
        self.label_logo = QLabel()
        self.label_logo.setPixmap(QIcon(self.resource_path("images/logo.ico")).pixmap(40, 40))
        self.label_logo.setAlignment(Qt.AlignCenter)
        self.card_layout.addWidget(self.label_logo)
        self.card_layout.addSpacing(12)

        self.label_title = QLabel("Admin Access")
        self.label_title.setAlignment(Qt.AlignCenter)
        self.label_title.setStyleSheet(f"font-family: 'Segoe UI Semibold'; font-size: 20px; font-weight: 700; color: {PW_INK};")
        self.card_layout.addWidget(self.label_title)

        self.label_subtitle = QLabel("Enter the password to continue")
        self.label_subtitle.setAlignment(Qt.AlignCenter)
        self.label_subtitle.setStyleSheet(f"font-family: 'Segoe UI'; font-size: 12.5px; color: {PW_TEXT_MUTED};")
        self.card_layout.addWidget(self.label_subtitle)

        self.card_layout.addSpacing(18)

        # Password Input
        self.et_password = QLineEdit()
        self.et_password.setEchoMode(QLineEdit.Password)
        self.et_password.setPlaceholderText("Password")
        self.et_password.setFixedSize(282, 42)
        self.et_password.setStyleSheet(f"""
            QLineEdit {{
                background-color: {PW_SURFACE};
                border: 1px solid {PW_BORDER};
                border-radius: 7px;
                padding: 0 12px;
                font-family: 'Segoe UI';
                font-size: 13px;
                color: {PW_TEXT};
            }}
            QLineEdit:hover {{ border-color: #cfc9ba; }}
            QLineEdit:focus {{ border: 1.5px solid {PW_ACCENT}; }}
        """)
        self.card_layout.addWidget(self.et_password)
        self.card_layout.addSpacing(8)

        # Check Button
        self.btn_checkPassword = QPushButton("Authorize")
        self.btn_checkPassword.setFixedSize(282, 42)
        self.btn_checkPassword.setCursor(Qt.PointingHandCursor)
        self.btn_checkPassword.setStyleSheet(f"""
            QPushButton {{
                background-color: {PW_ACCENT};
                color: white;
                border: none;
                border-radius: 7px;
                font-family: 'Segoe UI';
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: {PW_ACCENT_HOVER}; }}
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
        self.main_window.closed.connect(self.closed.emit)
        self.main_window.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PasswordCheck()
    window.showMaximized()
    sys.exit(app.exec_())
