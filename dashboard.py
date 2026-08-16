from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame, QPushButton, QLineEdit, QProgressBar
from PyQt5.QtGui import QPixmap, QIcon, QFont
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

# Same "label stock" identity used across the rest of the app: warm paper
# canvas, deep charcoal chrome, stamped price-tag red as the one accent.
# Status color is used semantically here (green = OK, red = error, muted
# gray = pending) rather than a different decorative color per card.
DASH_INK = "#191b1f"
DASH_CANVAS = "#f5f3ef"
DASH_SURFACE = "#ffffff"
DASH_BORDER = "#e6e2d9"
DASH_TEXT = "#1f2226"
DASH_TEXT_MUTED = "#74716a"
DASH_ACCENT = "#c81d31"
DASH_ACCENT_HOVER = "#a91729"
DASH_SUCCESS = "#2f7d55"
DASH_PENDING = "#9a9d9f"

class DashboardWindow(QMainWindow):
    def __init__(self):
        super(DashboardWindow, self).__init__()
        
        self.logger = setup_logger('DashboardLogger')
        self.logger.info("Initializing DashboardWindow...")
        self.backend = usb.backend.libusb1.get_backend(find_library=self.resource_path('libusb-1.0.ddl'))
        self.config_path = r'C:\barcode\barcode.json'
        
        self.setWindowTitle("System Diagnostic Dashboard")
        self.setFixedSize(1100, 750)

        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {DASH_CANVAS}; }}
            QPushButton {{ font-family: 'Segoe UI'; }}
            QPushButton#btn_primary {{
                background-color: {DASH_ACCENT}; color: white; border: none; border-radius: 8px;
                font-size: 14px; font-weight: 700;
            }}
            QPushButton#btn_primary:hover {{ background-color: {DASH_ACCENT_HOVER}; }}
            QPushButton#btn_primary:disabled {{ background-color: #cfc9ba; color: #8f8b7f; }}
            QPushButton#btn_secondary {{
                background-color: {DASH_SURFACE}; border: 1px solid {DASH_BORDER}; border-radius: 8px;
                font-size: 13px; font-weight: 600; color: {DASH_TEXT};
            }}
            QPushButton#btn_secondary:hover {{ background-color: {DASH_CANVAS}; border-color: #cfc9ba; }}
            QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
            QScrollBar::handle:vertical {{ background: #d8d3c5; border-radius: 5px; min-height: 24px; }}
            QScrollBar::handle:vertical:hover {{ background: #c7c1b1; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(44, 36, 44, 36)
        self.main_layout.setSpacing(28)

        # --- Header ---
        self.header_layout = QHBoxLayout()
        self.header_layout.setSpacing(12)

        self.title_group = QVBoxLayout()
        self.title_group.setSpacing(4)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        self.lbl_logo = QLabel()
        self.lbl_logo.setPixmap(QIcon(self.resource_path("images/logo.ico")).pixmap(30, 30))
        self.lbl_title = QLabel("System Diagnostics")
        self.lbl_title.setStyleSheet(f"font-family: 'Segoe UI Semibold'; font-size: 26px; font-weight: 700; color: {DASH_INK};")
        brand_row.addWidget(self.lbl_logo)
        brand_row.addWidget(self.lbl_title)
        brand_row.addStretch()
        self.title_group.addLayout(brand_row)

        self.lbl_subtitle = QLabel("Real-time system monitor & diagnostics")
        self.lbl_subtitle.setStyleSheet(f"font-family: 'Segoe UI'; font-size: 13px; font-weight: 600; color: {DASH_TEXT_MUTED};")
        self.title_group.addWidget(self.lbl_subtitle)

        self.header_layout.addLayout(self.title_group)
        self.header_layout.addStretch()

        self.time_group = QVBoxLayout()
        self.time_group.setSpacing(2)
        self.lbl_datetime = QLabel("---")
        self.lbl_datetime.setAlignment(Qt.AlignRight)
        self.lbl_datetime.setStyleSheet(f"font-family: 'Segoe UI'; font-size: 15px; font-weight: 700; color: {DASH_TEXT};")
        self.lbl_version = QLabel(f"VERSION {__version__}")
        self.lbl_version.setAlignment(Qt.AlignRight)
        self.lbl_version.setStyleSheet(f"font-family: 'Segoe UI'; font-size: 11px; font-weight: 700; color: {DASH_TEXT_MUTED};")
        self.time_group.addWidget(self.lbl_datetime)
        self.time_group.addWidget(self.lbl_version)
        
        self.header_layout.addLayout(self.time_group)
        self.main_layout.addLayout(self.header_layout)

        # --- Status Cards Grid ---
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(18)

        # 1. Connectivity Card
        self.card_net = self.create_status_card("\U0001F4F6", "Connectivity", "Public Network Access", "lbl_resultConnectivity")
        self.grid_layout.addWidget(self.card_net, 0, 0)

        # 2. Database Card
        self.card_db = self.create_status_card("\U0001F5C4", "Database", "SQL Server Status", "lbl_resultDatabase")
        self.grid_layout.addWidget(self.card_db, 0, 1)

        # 3. Printer Card
        self.card_printer = self.create_status_card("\U0001F5A8", "Hardware", "Connected Printers", "lbl_resultConnectedDevice")
        self.et_printerVid = QLineEdit(); self.et_printerVid.setVisible(False)
        self.et_printerPid = QLineEdit(); self.et_printerPid.setVisible(False)
        self.grid_layout.addWidget(self.card_printer, 1, 0)

        # 4. Configuration Card
        self.card_config = self.create_status_card("⚙", "Config File", "Schema Integrity", "lbl_resultConfiguration")
        self.et_enterToSearch = QLineEdit(); self.et_enterToSearch.setVisible(False)
        self.et_itemCount = QLineEdit(); self.et_itemCount.setVisible(False)
        self.grid_layout.addWidget(self.card_config, 1, 1)

        # 5. Logging Card
        self.card_log = self.create_status_card("\U0001F5D2", "System Logging", "Audit Trail Status", "lbl_loggingResult")
        self.btn_checkLogging = QPushButton("Status Check")
        self.btn_checkLogging.setObjectName("btn_secondary")
        self.btn_checkLogging.setFixedSize(120, 32)
        self.card_log.layout().insertWidget(1, self.btn_checkLogging)
        self.grid_layout.addWidget(self.card_log, 2, 0)

        # 6. Security Card
        self.card_sec = self.create_status_card("\U0001F512", "Security", "Encryption Engine", "lbl_security_status")
        self.grid_layout.addWidget(self.card_sec, 2, 1)

        self.main_layout.addLayout(self.grid_layout)
        # Absorb the fixed window's leftover vertical space here, between
        # the cards and the footer, instead of leaving no stretch anywhere
        # in main_layout -- without this Qt inflates every label above
        # (header title/subtitle/datetime) well beyond its natural text
        # height to fill the fixed 750px window, spreading them apart.
        self.main_layout.addStretch(1)

        # --- Footer Actions ---
        self.footer_layout = QHBoxLayout()
        self.btn_reload = QPushButton("Run System Check")
        self.btn_reload.setObjectName("btn_primary")
        self.btn_reload.setCursor(Qt.PointingHandCursor)
        self.btn_reload.setFixedSize(220, 50)
        self.btn_reload.clicked.connect(self.load_data)

        self.btn_close = QPushButton("Dismiss")
        self.btn_close.setObjectName("btn_secondary")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setFixedSize(140, 50)
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
        self.loading_overlay.setStyleSheet(f"background-color: rgba(25, 27, 31, 0.94); border-radius: 16px; border: 2px solid {DASH_ACCENT};")
        self.loading_overlay.setFixedSize(400, 130)

        overlay_layout = QVBoxLayout(self.loading_overlay)
        lbl_msg = QLabel("SYSTEM SCAN IN PROGRESS...")
        lbl_msg.setStyleSheet("color: white; font-weight: 800; font-size: 14px; border: none;")
        lbl_msg.setAlignment(Qt.AlignCenter)

        self.scan_pbar = QProgressBar()
        self.scan_pbar.setRange(0, 0) # Indeterminate
        self.scan_pbar.setTextVisible(False)
        self.scan_pbar.setStyleSheet(f"""
            QProgressBar {{ border: 1px solid #2a2d33; border-radius: 5px; height: 8px; background: #262930; }}
            QProgressBar::chunk {{ background-color: {DASH_ACCENT}; border-radius: 4px; }}
        """)
        overlay_layout.addStretch()
        overlay_layout.addWidget(lbl_msg)
        overlay_layout.addWidget(self.scan_pbar)
        overlay_layout.addStretch()
        self.loading_overlay.hide()

    def create_status_card(self, icon, title, subtitle, result_name):
        card = QFrame()
        card.setObjectName("status_card")
        card.setStyleSheet(f"""
            QFrame#status_card {{
                background-color: {DASH_SURFACE}; border: 1px solid {DASH_BORDER}; border-radius: 10px;
            }}
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 22px;")
        lbl_icon.setFixedWidth(30)
        layout.addWidget(lbl_icon)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        lbl_t = QLabel(title); lbl_t.setStyleSheet(f"font-family: 'Segoe UI Semibold'; font-size: 14px; font-weight: 700; color: {DASH_TEXT};")
        lbl_s = QLabel(subtitle); lbl_s.setStyleSheet(f"font-family: 'Segoe UI'; font-size: 11.5px; font-weight: 600; color: {DASH_TEXT_MUTED};")
        text_layout.addWidget(lbl_t); text_layout.addWidget(lbl_s)
        layout.addLayout(text_layout)
        layout.addStretch()

        if result_name:
            lbl_res = QLabel("Scanning")
            setattr(self, result_name, lbl_res)
            lbl_res.setAlignment(Qt.AlignCenter)
            self._style_status_pill(lbl_res, DASH_PENDING)
            layout.addWidget(lbl_res)
        return card

    def _style_status_pill(self, label, color):
        # Qt QSS 8-digit hex colors are #AARRGGBB (alpha first), not the
        # web convention of alpha-last -- use rgba() instead so the tint
        # is unambiguous regardless of channel order.
        h = color.lstrip('#')
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        label.setStyleSheet(f"""
            font-family: 'Segoe UI'; font-size: 11px; font-weight: 700; color: {color};
            background-color: rgba({r}, {g}, {b}, 28); border: 1px solid rgba({r}, {g}, {b}, 90);
            border-radius: 10px; padding: 4px 12px;
        """)

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
            if value in ["✅", "Enabled"]:
                self._style_status_pill(widget, DASH_SUCCESS)
            elif value in ["❌", "Disabled", "ERR"]:
                self._style_status_pill(widget, DASH_ACCENT)

    def on_diagnostic_finished(self):
        self.loading_overlay.hide()
        self.btn_reload.setEnabled(True)

    def update_datetime(self):
        self.lbl_datetime.setText(QDateTime.currentDateTime().toString("ddd, MMMM d, yyyy HH:mm:ss"))

    def resource_path(self, relative_path):
        try: base_path = sys._MEIPASS
        except Exception: base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)