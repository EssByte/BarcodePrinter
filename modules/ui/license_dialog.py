from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                              QFrame, QLabel, QLineEdit, QTextEdit, QPushButton)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer

from modules.licensing import get_hardware_id, activate_license
from modules.utils import resource_path

# Same "label stock" identity used across the rest of the app.
LIC_INK = "#191b1f"
LIC_CANVAS = "#f5f3ef"
LIC_SURFACE = "#ffffff"
LIC_BORDER = "#e6e2d9"
LIC_TEXT = "#1f2226"
LIC_TEXT_MUTED = "#74716a"
LIC_ACCENT = "#c81d31"
LIC_ACCENT_HOVER = "#a91729"
LIC_DANGER = "#7c2d12"


class LicenseDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.hardware_id = get_hardware_id()

        self.setWindowTitle("Activate License")
        self.setFixedSize(460, 580)
        self.setWindowIcon(QIcon(resource_path("images/logo.ico")))
        self.setStyleSheet(f"QDialog {{ background-color: {LIC_CANVAS}; }}")

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        self.card = QFrame()
        self.card.setObjectName("card")
        self.card.setFixedSize(370, 540)
        self.card.setStyleSheet(f"""
            QFrame#card {{
                background-color: {LIC_SURFACE};
                border: 1px solid {LIC_BORDER};
                border-radius: 12px;
            }}
        """)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(34, 32, 34, 30)
        card_layout.setSpacing(6)

        # Header (logo / title / subtitle)
        label_logo = QLabel()
        label_logo.setPixmap(QIcon(resource_path("images/logo.ico")).pixmap(40, 40))
        label_logo.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(label_logo)
        card_layout.addSpacing(10)

        label_title = QLabel("Activate License")
        label_title.setAlignment(Qt.AlignCenter)
        label_title.setStyleSheet(f"font-family: 'Segoe UI Semibold'; font-size: 20px; font-weight: 700; color: {LIC_INK};")
        card_layout.addWidget(label_title)

        label_subtitle = QLabel("This license is locked to this computer")
        label_subtitle.setAlignment(Qt.AlignCenter)
        label_subtitle.setWordWrap(True)
        label_subtitle.setStyleSheet(f"font-family: 'Segoe UI'; font-size: 12.5px; color: {LIC_TEXT_MUTED};")
        card_layout.addWidget(label_subtitle)
        card_layout.addSpacing(20)

        # Hardware ID row: read-only mono field + Copy button
        lbl_hwid = QLabel("Hardware ID")
        lbl_hwid.setStyleSheet(f"font-family: 'Segoe UI'; font-weight: 600; font-size: 12px; color: {LIC_TEXT};")
        card_layout.addWidget(lbl_hwid)
        card_layout.addSpacing(4)

        hwid_row = QHBoxLayout()
        hwid_row.setSpacing(8)
        self.et_hardware_id = QLineEdit(self.hardware_id)
        self.et_hardware_id.setReadOnly(True)  # selectable/copyable, but not editable -- NOT setEnabled(False)
        self.et_hardware_id.setFixedHeight(42)
        self.et_hardware_id.setStyleSheet(self._mono_field_style(editable=False))
        hwid_row.addWidget(self.et_hardware_id)

        self.btn_copy = QPushButton("Copy")
        self.btn_copy.setFixedSize(64, 42)
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.setStyleSheet(self._secondary_button_style())
        self.btn_copy.clicked.connect(self.copy_hardware_id)
        hwid_row.addWidget(self.btn_copy)
        card_layout.addLayout(hwid_row)
        card_layout.addSpacing(18)

        # License key input -- a multi-line paste target, not a single-line
        # field: the key is a base64-encoded Ed25519 signature (~88 chars),
        # not a short typed code, so customers will paste it from an email.
        lbl_key = QLabel("License Key")
        lbl_key.setStyleSheet(f"font-family: 'Segoe UI'; font-weight: 600; font-size: 12px; color: {LIC_TEXT};")
        card_layout.addWidget(lbl_key)
        card_layout.addSpacing(4)

        self.et_license_key = QTextEdit()
        self.et_license_key.setPlaceholderText("Paste the license key you received")
        self.et_license_key.setFixedHeight(84)
        self.et_license_key.setLineWrapMode(QTextEdit.WidgetWidth)
        self.et_license_key.setStyleSheet(self._mono_textedit_style())
        card_layout.addWidget(self.et_license_key)
        card_layout.addSpacing(8)

        # Inline error (hidden until an invalid key is submitted)
        self.lbl_error = QLabel("")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setStyleSheet(f"font-family: 'Segoe UI'; font-size: 12px; color: {LIC_DANGER};")
        self.lbl_error.setVisible(False)
        card_layout.addWidget(self.lbl_error)
        card_layout.addSpacing(6)

        card_layout.addStretch(1)  # avoids the QVBoxLayout label-inflation gotcha on a fixed-size window

        self.btn_activate = QPushButton("Activate")
        self.btn_activate.setFixedHeight(42)
        self.btn_activate.setCursor(Qt.PointingHandCursor)
        self.btn_activate.setStyleSheet(f"""
            QPushButton {{
                background-color: {LIC_ACCENT}; color: white; border: none; border-radius: 7px;
                font-family: 'Segoe UI'; font-size: 14px; font-weight: 700;
            }}
            QPushButton:hover {{ background-color: {LIC_ACCENT_HOVER}; }}
        """)
        card_layout.addWidget(self.btn_activate)

        outer.addWidget(self.card)

        self.btn_activate.clicked.connect(self.activate)

    def _mono_field_style(self, editable=False):
        base = f"""
            QLineEdit {{
                background-color: {LIC_SURFACE if editable else LIC_CANVAS};
                border: 1px solid {LIC_BORDER};
                border-radius: 7px;
                padding: 0 12px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12.5px;
                color: {LIC_TEXT};
            }}
        """
        if editable:
            base += f"""
                QLineEdit:hover {{ border-color: #cfc9ba; }}
                QLineEdit:focus {{ border: 1.5px solid {LIC_ACCENT}; }}
            """
        return base

    def _mono_textedit_style(self):
        return f"""
            QTextEdit {{
                background-color: {LIC_SURFACE};
                border: 1px solid {LIC_BORDER};
                border-radius: 7px;
                padding: 8px 10px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11.5px;
                color: {LIC_TEXT};
            }}
            QTextEdit:focus {{ border: 1.5px solid {LIC_ACCENT}; }}
        """

    def _secondary_button_style(self):
        return f"""
            QPushButton {{
                background-color: {LIC_SURFACE}; border: 1px solid {LIC_BORDER}; border-radius: 7px;
                font-family: 'Segoe UI'; font-weight: 600; font-size: 12px; color: {LIC_TEXT};
            }}
            QPushButton:hover {{ background-color: {LIC_CANVAS}; border-color: #cfc9ba; }}
        """

    def copy_hardware_id(self):
        QApplication.clipboard().setText(self.hardware_id)
        self.btn_copy.setText("Copied")
        QTimer.singleShot(1200, lambda: self.btn_copy.setText("Copy"))

    def activate(self):
        key = self.et_license_key.toPlainText()
        if activate_license(self.config, key):
            self.accept()
        else:
            self.lbl_error.setText("Invalid license key for this computer. Check the key and try again.")
            self.lbl_error.setVisible(True)


if __name__ == "__main__":
    import sys
    from modules.Configurations import BarcodeConfig
    app = QApplication(sys.argv)
    dlg = LicenseDialog(BarcodeConfig())
    sys.exit(0 if dlg.exec_() else 1)
