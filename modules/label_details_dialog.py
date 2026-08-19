import os
import sys
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import Qt

# Same "label stock" identity used across the rest of the app.
LDD_INK = "#191b1f"
LDD_CANVAS = "#f5f3ef"
LDD_SURFACE = "#ffffff"
LDD_BORDER = "#e6e2d9"
LDD_TEXT = "#1f2226"
LDD_TEXT_MUTED = "#74716a"
LDD_ACCENT = "#c81d31"
LDD_ACCENT_HOVER = "#a91729"


class LabelDetailsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Print")
        self.setFixedWidth(360)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(28, 26, 28, 26)
        self.layout.setSpacing(4)

        self.setStyleSheet(f"""
            QDialog {{ background-color: {LDD_CANVAS}; }}
            QLabel {{ font-family: 'Segoe UI'; color: {LDD_TEXT}; font-weight: 600; font-size: 12px; }}
            QLineEdit {{
                background-color: {LDD_SURFACE}; border: 1px solid {LDD_BORDER}; border-radius: 7px;
                padding: 9px 12px; font-family: 'Segoe UI'; font-size: 13px; color: {LDD_TEXT};
            }}
            QLineEdit:hover {{ border-color: #cfc9ba; }}
            QLineEdit:focus {{ border: 1.5px solid {LDD_ACCENT}; }}
        """)

        # Header
        lbl_title = QLabel("Confirm Print")
        lbl_title.setStyleSheet(f"font-family: 'Segoe UI Semibold'; font-size: 17px; font-weight: 700; color: {LDD_INK};")
        self.layout.addWidget(lbl_title)

        lbl_subtitle = QLabel("Add any last details before this label prints")
        lbl_subtitle.setWordWrap(True)
        lbl_subtitle.setStyleSheet(f"font-family: 'Segoe UI'; font-size: 12px; font-weight: 500; color: {LDD_TEXT_MUTED};")
        self.layout.addWidget(lbl_subtitle)
        self.layout.addSpacing(18)

        # Net Weight Field
        self.layout.addWidget(QLabel("Net Weight (Berat Bersih)"))
        self.layout.addSpacing(4)
        self.et_weight = QLineEdit(self)
        self.et_weight.setPlaceholderText("e.g. 500g")
        self.layout.addWidget(self.et_weight)

        self.layout.addSpacing(14)

        # Batch Field
        self.layout.addWidget(QLabel("Batch Number"))
        self.layout.addSpacing(4)
        self.et_batch = QLineEdit(self)
        self.et_batch.setPlaceholderText("e.g. LOT123")
        self.layout.addWidget(self.et_batch)

        self.layout.addSpacing(22)

        # Buttons
        self.btn_layout = QHBoxLayout()
        self.btn_layout.setSpacing(10)

        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setFixedHeight(40)
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {LDD_SURFACE}; border: 1px solid {LDD_BORDER}; border-radius: 7px;
                font-family: 'Segoe UI'; font-weight: 600; font-size: 13px; color: {LDD_TEXT};
            }}
            QPushButton:hover {{ background-color: {LDD_CANVAS}; border-color: #cfc9ba; }}
        """)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_ok = QPushButton("Confirm && Print", self)
        self.btn_ok.setCursor(Qt.PointingHandCursor)
        self.btn_ok.setDefault(True)  # Make Enter key trigger this button
        self.btn_ok.setFixedHeight(40)
        self.btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {LDD_ACCENT}; color: white; border: none; border-radius: 7px;
                font-family: 'Segoe UI'; font-weight: 700; font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {LDD_ACCENT_HOVER}; }}
        """)
        self.btn_ok.clicked.connect(self.on_ok)

        # Connect enter key on all fields
        self.et_weight.returnPressed.connect(self.on_ok)
        self.et_batch.returnPressed.connect(self.on_ok)

        self.btn_layout.addWidget(self.btn_cancel)
        self.btn_layout.addWidget(self.btn_ok)
        self.layout.addLayout(self.btn_layout)

        self.weight = ""
        self.batch = ""
        self.is_accepted = False

    def on_ok(self):
        self.weight = self.et_weight.text().strip()
        self.batch = self.et_batch.text().strip()
        self.is_accepted = True
        self.accept()

    def get_data(self):
        return {
            'weight': self.weight,
            'batch': self.batch,
            'accepted': self.is_accepted
        }
