from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame, QPushButton, QGraphicsDropShadowEffect, QLineEdit, QProgressBar
from PyQt5.QtGui import QPixmap, QIcon, QFont, QColor
from PyQt5.QtCore import Qt, QTimer, QDateTime, QSize
import usb.backend
import usb.backend.libusb1
import json
import usb
import os
import socket
import pyodbc
from modules.logger_config import setup_logger 
from version import __version__

class DashboardWindow(QMainWindow):
    def __init__(self):
        super(DashboardWindow, self).__init__()
        
        self.logger = setup_logger('DashboardLogger')
        self.logger.info("Initializing DashboardWindow...")
        self.backend = usb.backend.libusb1.get_backend(find_library=self.resource_path('libusb-1.0.ddl'))
        self.config_path = r'C:\barcode\barcode.json'
        
        self.setWindowTitle("System Diagnostic Dashboard")
        self.setFixedSize(1100, 750)
        
        # VIBRANT GRADIENT BACKGROUND
        self.setStyleSheet("""
            QMainWindow { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e3c72, stop:1 #2a5298);
            }
        """)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(50, 50, 50, 50)
        self.main_layout.setSpacing(30)

        # --- Header Section (Vibrant) ---
        self.header_layout = QHBoxLayout()
        
        self.title_group = QVBoxLayout()
        self.lbl_title = QLabel("CORE SYSTEMS")
        self.lbl_title.setStyleSheet("font-family: 'Segoe UI'; font-size: 32px; font-weight: 800; color: #ffffff; letter-spacing: 2px;")
        self.lbl_subtitle = QLabel("REAL-TIME SYSTEM MONITOR & DIAGNOSTICS")
        self.lbl_subtitle.setStyleSheet("font-family: 'Segoe UI'; font-size: 14px; font-weight: 600; color: #a5b4fc; letter-spacing: 1px;")
        self.title_group.addWidget(self.lbl_title)
        self.title_group.addWidget(self.lbl_subtitle)
        
        self.header_layout.addLayout(self.title_group)
        self.header_layout.addStretch()
        
        self.time_group = QVBoxLayout()
        self.lbl_datetime = QLabel("---")
        self.lbl_datetime.setAlignment(Qt.AlignRight)
        self.lbl_datetime.setStyleSheet("font-family: 'Segoe UI'; font-size: 18px; font-weight: 700; color: #ffffff;")
        self.lbl_version = QLabel(f"VERSION {__version__}")
        self.lbl_version.setAlignment(Qt.AlignRight)
        self.lbl_version.setStyleSheet("font-family: 'Segoe UI'; font-size: 12px; font-weight: bold; color: #818cf8;")
        self.time_group.addWidget(self.lbl_datetime)
        self.time_group.addWidget(self.lbl_version)
        
        self.header_layout.addLayout(self.time_group)
        self.main_layout.addLayout(self.header_layout)

        # --- Status Cards Grid ---
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(30)
        self.grid_layout.setColumnStretch(0, 7)
        self.grid_layout.setColumnStretch(1, 3)
        
        # 1. Connectivity Card
        self.card_net = self.create_status_card("CONNECTIVITY", "Public Network Access", "lbl_resultConnectivity", "#f59e0b")
        self.grid_layout.addWidget(self.card_net, 0, 0)
        
        # 2. Database Card
        self.card_db = self.create_status_card("DATABASE", "SQL Server Status", "lbl_resultDatabase", "#8b5cf6")
        self.grid_layout.addWidget(self.card_db, 0, 1)
        
        # 3. Printer Card
        self.card_printer = self.create_status_card("HARDWARE", "Connected Printers", "lbl_resultConnectedDevice", "#10b981")
        self.et_printerVid = QLineEdit(); self.et_printerVid.setVisible(False)
        self.et_printerPid = QLineEdit(); self.et_printerPid.setVisible(False)
        self.grid_layout.addWidget(self.card_printer, 1, 0)
        
        # 4. Configuration Card
        self.card_config = self.create_status_card("CONFIG FILE", "Schema Integrity", "lbl_resultConfiguration", "#3b82f6")
        self.et_enterToSearch = QLineEdit(); self.et_enterToSearch.setVisible(False)
        self.et_itemCount = QLineEdit(); self.et_itemCount.setVisible(False)
        self.grid_layout.addWidget(self.card_config, 1, 1)
        
        # 5. Logging Card
        self.card_log = self.create_status_card("SYSTEM LOGGING", "Audit Trail Status", "lbl_loggingResult", "#ec4899")
        self.btn_checkLogging = QPushButton("Status Check")
        self.btn_checkLogging.setFixedSize(140, 35)
        self.btn_checkLogging.setStyleSheet("background: rgba(255,255,255,0.2); border: 1px solid white; color: white; border-radius: 5px; font-weight: bold;")
        self.card_log.layout().insertWidget(1, self.btn_checkLogging)
        self.grid_layout.addWidget(self.card_log, 2, 0)

        # 6. Security Card
        self.card_sec = self.create_status_card("SECURITY", "Encryption Engine", "lbl_security_status", "#ef4444")
        self.grid_layout.addWidget(self.card_sec, 2, 1)

        self.main_layout.addLayout(self.grid_layout)

        # --- Footer Actions ---
        self.footer_layout = QHBoxLayout()
        self.btn_reload = QPushButton("RUN SYSTEM CHECK")
        self.btn_reload.setCursor(Qt.PointingHandCursor)
        self.btn_reload.setFixedSize(250, 60)
        self.btn_reload.setStyleSheet("""
            QPushButton { 
                background-color: #3b82f6; 
                color: white; 
                border-radius: 12px; 
                font-size: 16px; 
                font-weight: 800; 
                letter-spacing: 1px;
                border: 2px solid #60a5fa;
            }
            QPushButton:hover { background-color: #2563eb; border-color: #3b82f6; }
            QPushButton:disabled { background-color: #1e293b; border-color: #334155; color: #475569; }
        """)
        self.btn_reload.clicked.connect(self.load_data)
        
        self.btn_close = QPushButton("DISMISS")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setFixedSize(180, 60)
        self.btn_close.setStyleSheet("""
            QPushButton { 
                background-color: rgba(255, 255, 255, 0.1); 
                border: 2px solid rgba(255, 255, 255, 0.3); 
                color: white; 
                border-radius: 12px; 
                font-weight: bold; 
                font-size: 14px;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.2); }
        """)
        self.btn_close.clicked.connect(self.close)
        
        self.footer_layout.addWidget(self.btn_reload)
        self.footer_layout.addStretch()
        self.footer_layout.addWidget(self.btn_close)
        self.main_layout.addLayout(self.footer_layout)

        # Loading Overlay (Starts Hidden)
        self.setup_loading_overlay()

        # Timer setup
        self.update_datetime()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)

        # Load initial diagnostics
        QTimer.singleShot(800, self.load_data)

    def setup_loading_overlay(self):
        self.loading_overlay = QFrame(self)
        self.loading_overlay.setStyleSheet("background-color: rgba(15, 23, 42, 0.9); border-radius: 20px; border: 2px solid #3b82f6;")
        self.loading_overlay.setFixedSize(400, 130)
        
        overlay_layout = QVBoxLayout(self.loading_overlay)
        lbl_msg = QLabel("CORE SYSTEM SCAN IN PROGRESS...")
        lbl_msg.setStyleSheet("color: white; font-weight: 800; font-size: 14px; letter-spacing: 1px; border: none;")
        lbl_msg.setAlignment(Qt.AlignCenter)
        
        self.scan_pbar = QProgressBar()
        self.scan_pbar.setRange(0, 0) # Indeterminate
        self.scan_pbar.setTextVisible(False)
        self.scan_pbar.setStyleSheet("""
            QProgressBar { border: 1px solid #334155; border-radius: 5px; height: 8px; background: #1e293b; }
            QProgressBar::chunk { background-color: #3b82f6; border-radius: 4px; }
        """)
        overlay_layout.addStretch()
        overlay_layout.addWidget(lbl_msg)
        overlay_layout.addWidget(self.scan_pbar)
        overlay_layout.addStretch()
        self.loading_overlay.hide()

    def create_status_card(self, title, subtitle, result_name, accent_color):
        card = QFrame()
        card.setObjectName("status_card")
        card.setStyleSheet(f"QFrame#status_card {{ background-color: rgba(255, 255, 255, 0.95); border-left: 8px solid {accent_color}; border-radius: 15px; }}")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25); shadow.setXOffset(0); shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 80))
        card.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(card); layout.setContentsMargins(30, 30, 30, 30)
        text_layout = QVBoxLayout()
        lbl_t = QLabel(title); lbl_t.setStyleSheet("font-size: 18px; font-weight: 800; color: #1e293b; letter-spacing: 1px;")
        lbl_s = QLabel(subtitle); lbl_s.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748b;")
        text_layout.addWidget(lbl_t); text_layout.addWidget(lbl_s)
        layout.addLayout(text_layout); layout.addStretch()
        
        if result_name:
            lbl_res = QLabel("SCANNING"); setattr(self, result_name, lbl_res)
            lbl_res.setStyleSheet(f"font-size: 24px; color: {accent_color}; font-weight: 900;")
            layout.addWidget(lbl_res)
        return card

    def load_data(self):
        self.btn_reload.setEnabled(False)
        self.loading_overlay.move(
            (self.width() - self.loading_overlay.width()) // 2,
            (self.height() - self.loading_overlay.height()) // 2
        )
        self.loading_overlay.show()
        
        from modules.threads import DiagnosticThread
        self.diag_thread = DiagnosticThread(self.config_path, "HQ", self.backend)
        self.diag_thread.progress.connect(self.update_diagnostic_result)
        self.diag_thread.finished.connect(self.on_diagnostic_finished)
        self.diag_thread.start()

    def update_diagnostic_result(self, attr_name, value):
        if hasattr(self, attr_name):
            widget = getattr(self, attr_name)
            widget.setText(value)
            if value in ["✅", "Enabled"]: widget.setStyleSheet("font-size: 24px; font-weight: 900; color: #10b981;")
            elif value in ["❌", "Disabled", "ERR"]: widget.setStyleSheet("font-size: 24px; font-weight: 900; color: #ef4444;")

    def on_diagnostic_finished(self):
        self.loading_overlay.hide()
        self.btn_reload.setEnabled(True)

    def update_datetime(self):
        self.lbl_datetime.setText(QDateTime.currentDateTime().toString("ddd, MMMM d, yyyy HH:mm:ss"))

    def resource_path(self, relative_path):
        try: base_path = sys._MEIPASS
        except Exception: base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)