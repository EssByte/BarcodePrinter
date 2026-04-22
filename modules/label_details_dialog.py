import os
import sys
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import Qt

class LabelDetailsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Label Details")
        self.setFixedWidth(350)
        
        self.layout = QVBoxLayout(self)
        
        # Premium Style
        self.setStyleSheet("""
            QDialog { background-color: #f8fafc; }
            QLabel { font-family: 'Segoe UI', 'Roboto', sans-serif; color: #334155; font-weight: 600; font-size: 13px; margin-bottom: 2px; }
            QLineEdit { background-color: #ffffff; border: 2px solid #e2e8f0; border-radius: 8px; padding: 10px; font-size: 14px; color: #1e293b; }
            QLineEdit:focus { border-color: #3498db; background-color: #ffffff; }
            QPushButton { border-radius: 8px; padding: 12px 24px; font-weight: bold; font-size: 13px; }
        """)

        # Net Weight Field
        self.layout.addWidget(QLabel("Net Weight (Berat Bersih):"))
        self.et_weight = QLineEdit(self)
        self.et_weight.setPlaceholderText("e.g. 500g")
        self.layout.addWidget(self.et_weight)
        
        self.layout.addSpacing(15)

        # Remark / Expiry Field
        self.layout.addWidget(QLabel("Expiry Date / Remark:"))
        self.et_remark = QLineEdit(self)
        self.et_remark.setPlaceholderText("e.g. 2024-12-31")
        self.layout.addWidget(self.et_remark)

        self.layout.addSpacing(15)

        # Batch Field
        self.layout.addWidget(QLabel("Batch Number:"))
        self.et_batch = QLineEdit(self)
        self.et_batch.setPlaceholderText("e.g. LOT123")
        self.layout.addWidget(self.et_batch)
        
        self.layout.addSpacing(25)

        # Buttons
        self.btn_layout = QHBoxLayout()
        
        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setStyleSheet("""
            QPushButton { background-color: #ffffff; border: 1px solid #d1d5db; color: #4b5563; }
            QPushButton:hover { background-color: #f9fafb; border-color: #9ca3af; }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("Confirm & Print", self)
        self.btn_ok.setCursor(Qt.PointingHandCursor)
        self.btn_ok.setStyleSheet("""
            QPushButton { background-color: #3498db; color: white; border: none; }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.btn_ok.clicked.connect(self.on_ok)
        
        self.btn_layout.addWidget(self.btn_cancel)
        self.btn_layout.addWidget(self.btn_ok)
        self.layout.addLayout(self.btn_layout)
        
        self.weight = ""
        self.batch = ""
        self.remark = ""
        self.is_accepted = False

    def on_ok(self):
        self.weight = self.et_weight.text().strip()
        self.batch = self.et_batch.text().strip()
        self.remark = self.et_remark.text().strip()
        self.is_accepted = True
        self.accept()

    def get_data(self):
        return {
            'weight': self.weight,
            'batch': self.batch,
            'remark': self.remark,
            'accepted': self.is_accepted
        }
