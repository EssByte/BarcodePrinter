import os
import sys
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton

class FunBakeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fun Bake Label Details")
        self.setFixedWidth(350)
        
        self.layout = QVBoxLayout(self)
        
        # Style
        self.setStyleSheet("""
            QDialog { background-color: white; }
            QLabel { font-weight: bold; font-size: 14px; }
            QLineEdit { padding: 8px; border: 1px solid #ccc; border-radius: 5px; font-size: 14px; }
            QPushButton { padding: 10px; border-radius: 5px; font-weight: bold; }
        """)

        # Net Weight Field
        self.layout.addWidget(QLabel("Net Weight (Berat Bersih):"))
        self.et_weight = QLineEdit(self)
        self.et_weight.setPlaceholderText("e.g. 500g")
        self.layout.addWidget(self.et_weight)
        
        self.layout.addSpacing(15)

        # Batch Field
        self.layout.addWidget(QLabel("Batch / Lot Number:"))
        self.et_batch = QLineEdit(self)
        self.et_batch.setPlaceholderText("e.g. LOT123")
        self.layout.addWidget(self.et_batch)
        
        self.layout.addSpacing(20)

        # Buttons
        self.btn_layout = QHBoxLayout()
        
        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_cancel.setStyleSheet("background-color: #f44336; color: white;")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("Confirm & Print", self)
        self.btn_ok.setStyleSheet("background-color: #2196F3; color: white;")
        self.btn_ok.clicked.connect(self.on_ok)
        
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
