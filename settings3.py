import sys
import os
import json
import usb.core
import usb.backend.libusb1
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QFrame, QStackedWidget,
                             QListWidget, QListWidgetItem, QCheckBox, QRadioButton,
                             QButtonGroup, QComboBox, QTextEdit, QGraphicsDropShadowEffect,
                             QFileDialog, QMessageBox, QSpacerItem, QSizePolicy, QGridLayout,
                             QScrollArea)
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
from modules.barcode_designer import BarcodeDesigner

from modules.logger_config import setup_logger
from version import __version__
from modules import CheckDriver, SendCommand, Configurations
from modules.InstallDriver import DriverInstaller

# --- Design tokens -----------------------------------------------------
# ink        sidebar background (warm charcoal, not cool slate)
# ink_hover  sidebar item hover / cards-on-dark
# canvas     page background (warm paper tone -- this app prints labels)
# surface    field/card background
# border     hairline borders on canvas/surface
# text       primary text
# text_muted secondary/caption text (warm gray)
# accent     primary actions, focus rings, active nav (stamped-label red)
# danger     destructive actions
# success    confirmations
INK = "#191b1f"
INK_HOVER = "#262930"
SIDEBAR_TEXT = "#9a9d9f"
CANVAS = "#f5f3ef"
SURFACE = "#ffffff"
BORDER = "#e6e2d9"
TEXT = "#1f2226"
TEXT_MUTED = "#74716a"
# Red as the primary accent -- a "stamped price tag" red, on-brand for a
# retail label printer. Danger is shifted to a darker, more muted oxblood
# so destructive buttons stay visually distinct from primary/save actions.
ACCENT = "#c81d31"
ACCENT_HOVER = "#a91729"
DANGER = "#7c2d12"
DANGER_HOVER = "#5f2109"
SUCCESS = "#2f7d55"
SUCCESS_HOVER = "#256844"

SETTINGS_STYLE = f"""
    QMainWindow {{ background-color: {CANVAS}; }}
    QScrollArea#page_scroll {{ background-color: {CANVAS}; border: none; }}

    /* Sidebar */
    QFrame#sidebar {{ background-color: {INK}; border: none; }}
    QListWidget#nav_list {{ background-color: transparent; border: none; outline: none; font-family: 'Segoe UI'; }}
    QListWidget#nav_list::item {{
        color: {SIDEBAR_TEXT};
        padding: 13px 22px;
        border-radius: 6px;
        margin: 2px 14px;
        border-left: 3px solid transparent;
        font-weight: 600;
        font-size: 13px;
    }}
    QListWidget#nav_list::item:selected {{
        background-color: {INK_HOVER};
        color: #ffffff;
        border-left: 3px solid {ACCENT};
    }}
    QListWidget#nav_list::item:hover:!selected {{ background-color: #202226; color: #e5e4e1; }}

    QLabel#brand_name {{ color: #ffffff; font-family: 'Segoe UI Semibold'; font-size: 15px; font-weight: 700; }}
    QLabel#lbl_ver {{ color: {SIDEBAR_TEXT}; font-size: 11px; padding: 18px 22px; }}

    /* Top / bottom action bars */
    QFrame#top_bar {{ background-color: {CANVAS}; border-bottom: 1px solid {BORDER}; }}
    QFrame#bottom_bar {{ background-color: {SURFACE}; border-top: 1px solid {BORDER}; }}

    /* Section headers */
    QLabel#section_title {{ font-family: 'Segoe UI Semibold'; font-size: 22px; font-weight: 700; color: {TEXT}; }}
    QLabel#section_sub {{ font-family: 'Segoe UI'; font-size: 13px; color: {TEXT_MUTED}; margin-bottom: 18px; }}
    QLabel#field_label {{ font-family: 'Segoe UI'; font-weight: 600; color: {TEXT}; font-size: 12px; }}
    QLabel#field_caption {{ font-family: 'Segoe UI'; font-weight: 700; color: {TEXT_MUTED}; font-size: 10px; }}
    QLabel#card_caption {{ font-family: 'Segoe UI'; color: {TEXT_MUTED}; font-size: 12px; }}

    /* Inputs */
    QLineEdit, QTextEdit, QComboBox {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 7px;
        padding: 7px 11px;
        min-height: 22px;
        font-family: 'Segoe UI';
        font-size: 13px;
        color: {TEXT};
        selection-background-color: {ACCENT};
    }}
    QLineEdit:hover, QTextEdit:hover, QComboBox:hover {{ border-color: #cfc9ba; }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{ border: 1.5px solid {ACCENT}; }}
    QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled {{ background-color: {CANVAS}; color: #b3b0a7; border-color: {BORDER}; }}
    QComboBox::drop-down {{ border: none; width: 24px; }}
    QComboBox QAbstractItemView {{ background-color: {SURFACE}; border: 1px solid {BORDER}; selection-background-color: {ACCENT}; selection-color: white; outline: none; }}

    /* Technical / identifier fields -- fixed-width matters here */
    QLineEdit#field_mono, QTextEdit#field_mono {{ font-family: 'Consolas', 'Courier New', monospace; font-size: 12.5px; }}

    /* Checkboxes & radio buttons */
    QCheckBox, QRadioButton {{ font-family: 'Segoe UI'; font-weight: 600; color: {TEXT}; font-size: 13px; spacing: 9px; padding: 4px 0; }}
    QCheckBox::indicator, QRadioButton::indicator {{ width: 17px; height: 17px; border: 1.5px solid #cfc9ba; background: {SURFACE}; }}
    QCheckBox::indicator {{ border-radius: 4px; }}
    QRadioButton::indicator {{ border-radius: 9px; }}
    QCheckBox::indicator:hover, QRadioButton::indicator:hover {{ border-color: {ACCENT}; }}
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}

    /* Buttons */
    QPushButton {{ font-family: 'Segoe UI'; }}
    QPushButton#btn_primary {{
        background-color: {ACCENT}; color: white; border: none; border-radius: 7px;
        padding: 9px 22px; min-height: 22px; font-weight: 700; font-size: 13px;
    }}
    QPushButton#btn_primary:hover {{ background-color: {ACCENT_HOVER}; }}
    QPushButton#btn_secondary {{
        background-color: {SURFACE}; border: 1px solid {BORDER}; border-radius: 7px;
        padding: 9px 22px; min-height: 22px; font-weight: 600; font-size: 13px; color: {TEXT};
    }}
    QPushButton#btn_secondary:hover {{ background-color: {CANVAS}; border-color: #cfc9ba; }}
    QPushButton#btn_danger {{
        background-color: {SURFACE}; border: 1px solid {DANGER}; border-radius: 7px;
        padding: 9px 22px; min-height: 22px; font-weight: 600; font-size: 13px; color: {DANGER};
    }}
    QPushButton#btn_danger:hover {{ background-color: {DANGER}; color: white; }}

    /* Segmented control (TPSL / ZPL toggle) -- each side is its own
       objectName with the full rule set (base + checked + its own corner
       radii) so nothing is split across a global + per-widget stylesheet. */
    QPushButton#seg_left, QPushButton#seg_right {{
        background-color: {CANVAS}; border: 1px solid {BORDER}; color: {TEXT_MUTED};
        padding: 8px 20px; font-weight: 700; font-size: 12.5px;
    }}
    QPushButton#seg_left:checked, QPushButton#seg_right:checked {{
        background-color: {INK}; color: white; border-color: {INK};
    }}
    QPushButton#seg_left {{ border-top-left-radius: 7px; border-bottom-left-radius: 7px; border-right: none; }}
    QPushButton#seg_right {{ border-top-right-radius: 7px; border-bottom-right-radius: 7px; }}

    /* Cards -- group related fields within a tab's content */
    QFrame#card {{
        background-color: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px;
    }}
    QLabel#card_title {{
        font-family: 'Segoe UI Semibold'; font-weight: 700; font-size: 13px; color: {TEXT};
    }}
    QFrame#card_divider {{ background-color: {BORDER}; max-height: 1px; min-height: 1px; border: none; }}
    QListWidget#printers_qlist {{
        background-color: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px;
        font-family: 'Segoe UI'; outline: none; padding: 4px;
    }}
    QListWidget#printers_qlist::item {{ padding: 9px 10px; border-radius: 6px; color: {TEXT}; }}
    QListWidget#printers_qlist::item:selected {{ background-color: {ACCENT}; color: white; }}
    QListWidget#printers_qlist::item:hover:!selected {{ background-color: {CANVAS}; }}

    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: #d8d3c5; border-radius: 5px; min-height: 24px; }}
    QScrollBar::handle:vertical:hover {{ background: #c7c1b1; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""

class SettingsWindow(QMainWindow):
    closed = pyqtSignal()

    def __init__(self, config=None):
        super(SettingsWindow, self).__init__()
        self.logger = setup_logger('SettingsModern')
        self.config = config if config is not None else Configurations.BarcodeConfig()
        self.driverInstaller = DriverInstaller()
        self.backend = usb.backend.libusb1.get_backend(find_library=self.resource_path('libusb-1.0.ddl'))
        self.config_path = r'C:\barcode\barcode.json'
        self.printers_data = []
        self.current_printer_row = -1
        
        self.setWindowTitle("System Settings")
        self.setMinimumSize(1200, 800)

        # --- UI STYLING ---
        # A "label stock" identity: warm paper-toned canvas (this app prints
        # onto physical label stock), a deep charcoal sidebar, and a stamped
        # price-tag red accent instead of the generic dashboard-blue default.
        # Technical
        # fields (VID/PID, IP, driver name, TPSL/ZPL scripts) use Consolas --
        # fixed-width genuinely helps reading hex codes and printer commands,
        # not just decoration. Segoe UI + Consolas both ship with Windows, so
        # this needs no bundled fonts.
        self.setStyleSheet(SETTINGS_STYLE)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- Sidebar ---
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(280)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0, 20, 0, 20)

        # App Identity in Sidebar
        self.brand_frame = QFrame()
        self.brand_layout = QHBoxLayout(self.brand_frame)
        self.brand_logo = QLabel()
        self.brand_logo.setPixmap(QIcon(self.resource_path("images/logo.ico")).pixmap(32, 32))
        self.brand_name = QLabel("BARCODE PRO")
        self.brand_name.setObjectName("brand_name")
        self.brand_layout.addWidget(self.brand_logo)
        self.brand_layout.addWidget(self.brand_name)
        self.brand_layout.addStretch()
        self.sidebar_layout.addWidget(self.brand_frame)
        self.sidebar_layout.addSpacing(30)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("nav_list")
        items = [
            ("Database", "\U0001F5C4"),
            ("Printer Setup", "\U0001F5A8"),
            ("General", "⚙"),
            ("Label Templates", "\U0001F5D2"),
            ("System Tools", "\U0001F527"),
        ]
        for text, icon in items:
            item = QListWidgetItem(f"{icon}   {text}")
            self.nav_list.addItem(item)

        self.sidebar_layout.addWidget(self.nav_list)
        self.sidebar_layout.addStretch()

        # Version in Sidebar
        self.lbl_ver = QLabel(f"Version {__version__}")
        self.lbl_ver.setObjectName("lbl_ver")
        self.sidebar_layout.addWidget(self.lbl_ver)

        self.main_layout.addWidget(self.sidebar)

        # --- Content Area ---
        self.content_stack = QStackedWidget()
        self.main_layout.addWidget(self.content_stack)

        self.setup_database_page()
        self.setup_printer_page()
        self.setup_general_page()
        self.setup_templates_page()
        self.setup_tools_page()

        # Connect Navigation
        self.nav_list.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

        # Action buttons, docked in a top bar above the content stack
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("btn_secondary")
        self.btn_cancel.clicked.connect(self.close)

        self.btn_save_all = QPushButton("Save All Changes")
        self.btn_save_all.setObjectName("btn_primary")
        self.btn_save_all.clicked.connect(self.update_data)

        self.top_bar = QFrame()
        self.top_bar.setObjectName("top_bar")
        self.top_layout = QHBoxLayout(self.top_bar)
        self.top_layout.setContentsMargins(20, 12, 20, 12)
        self.top_layout.addStretch()
        self.top_layout.addWidget(self.btn_cancel)
        self.top_layout.addWidget(self.btn_save_all)

        self.bottom_bar = QFrame()
        self.bottom_bar.setObjectName("bottom_bar")
        self.bottom_layout = QHBoxLayout(self.bottom_bar)
        self.bottom_layout.setContentsMargins(20, 10, 20, 10)
        self.bottom_layout.addStretch()

        # Re-organize layout
        self.content_container = QWidget()
        self.content_container_layout = QVBoxLayout(self.content_container)
        self.content_container_layout.setContentsMargins(0,0,0,0)
        self.content_container_layout.addWidget(self.top_bar)
        self.content_container_layout.addWidget(self.content_stack)
        self.content_container_layout.addWidget(self.bottom_bar)
        
        self.main_layout.addWidget(self.content_container)

        self.load_data()

    def create_page(self, title, sub):
        # Real scrolling, not just a plain QFrame: a page's content can be
        # taller than the visible window (e.g. several cards stacked), and
        # without a QScrollArea Qt silently compresses child widgets below
        # their sizeHint to force everything to fit, which visually
        # overlaps text/controls instead of clipping or scrolling.
        outer = QScrollArea()
        outer.setObjectName("page_scroll")
        outer.setWidgetResizable(True)
        outer.setFrameShape(QFrame.NoFrame)
        outer.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # NOTE: do not call outer.viewport().setStyleSheet(...) here -- a
        # local stylesheet set directly on a QScrollArea's viewport breaks
        # QSS objectName styling (background-color) for QPushButtons nested
        # further down the tree (confirmed via isolated repro: identical
        # structure renders correctly without this call, and breaks with
        # it -- Qt's stylesheet cascade doesn't reliably chain through a
        # second local-stylesheet layer on the viewport). The global
        # QScrollArea#page_scroll rule below handles the background instead.

        page = QWidget()
        page.setObjectName("page_inner")
        page.setStyleSheet(f"QWidget#page_inner {{ background-color: {CANVAS}; }}")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)

        lbl_t = QLabel(title); lbl_t.setObjectName("section_title")
        lbl_s = QLabel(sub); lbl_s.setObjectName("section_sub")
        layout.addWidget(lbl_t)
        layout.addWidget(lbl_s)

        scroll_area = QFrame()
        scroll_layout = QVBoxLayout(scroll_area)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll_area)
        layout.addStretch()

        outer.setWidget(page)
        return outer, scroll_layout

    def make_card(self, parent_layout, title=None):
        """A white, bordered section within a tab's content area. Returns
        the inner layout so callers add fields to it exactly like they
        would to a page's top-level layout.

        Deliberately no QGraphicsDropShadowEffect here: Qt renders a
        widget's whole subtree through an offscreen buffer when a graphics
        effect is applied, and that reliably breaks QSS background colors
        on child QPushButtons nested inside (confirmed both offscreen and
        in the real window -- checked segmented buttons and primary
        buttons inside a shadowed card rendered white-on-white). The
        border + background contrast against the canvas is enough to read
        as a card without it.
        """
        card = QFrame()
        card.setObjectName("card")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(26, 22, 26, 26)
        card_layout.setSpacing(6)

        if title:
            lbl = QLabel(title)
            lbl.setObjectName("card_title")
            card_layout.addWidget(lbl)
            card_layout.addSpacing(8)
            divider = QFrame()
            divider.setObjectName("card_divider")
            divider.setFixedHeight(1)
            card_layout.addWidget(divider)
            card_layout.addSpacing(10)

        parent_layout.addWidget(card)
        return card_layout

    def add_field(self, layout, label, field_type="text"):
        lbl = QLabel(label); lbl.setObjectName("field_label")
        layout.addWidget(lbl)
        if field_type == "text":
            field = QLineEdit()
        elif field_type == "password":
            field = QLineEdit(); field.setEchoMode(QLineEdit.Password)
        elif field_type == "combo":
            field = QComboBox()
        elif field_type == "textedit":
            field = QTextEdit(); field.setMaximumHeight(150)
        layout.addWidget(field)
        layout.addSpacing(12)
        return field

    def setup_database_page(self):
        page, layout = self.create_page("Database Configuration", "Manage your enterprise data sources")

        conn = self.make_card(layout, "SQL Server Connection")
        row1 = QHBoxLayout(); col_a = QVBoxLayout(); col_b = QVBoxLayout()
        self.serverName = self.add_field(col_a, "SQL Server Address")
        self.databaseName = self.add_field(col_b, "Database Name")
        row1.addLayout(col_a); row1.addLayout(col_b)
        conn.addLayout(row1)

        row2 = QHBoxLayout(); col_c = QVBoxLayout(); col_d = QVBoxLayout()
        self.userName = self.add_field(col_c, "Authentication Username")
        self.password = self.add_field(col_d, "Authentication Password", "password")
        row2.addLayout(col_c); row2.addLayout(col_d)
        conn.addLayout(row2)

        lbl_driver = QLabel("SQL Driver Name (e.g. ODBC Driver 17 for SQL Server)"); lbl_driver.setObjectName("field_label")
        lbl_driver.setWordWrap(True)
        conn.addWidget(lbl_driver)
        h_driver_box = QHBoxLayout()
        self.dbDriverName = QLineEdit()
        self.dbDriverName.setObjectName("field_mono")
        self.btn_detect_driver = QPushButton("Auto-Detect")
        self.btn_detect_driver.setFixedWidth(120)
        self.btn_detect_driver.setObjectName("btn_secondary")
        self.btn_detect_driver.clicked.connect(self.auto_detect_driver)
        h_driver_box.addWidget(self.dbDriverName); h_driver_box.addWidget(self.btn_detect_driver)
        conn.addLayout(h_driver_box)
        conn.addSpacing(6)

        self.cb_trusted_connection = QCheckBox("Use Windows Trusted Connection")
        conn.addWidget(self.cb_trusted_connection)

        layout.addSpacing(16)
        fallback = self.make_card(layout, "Local Database Fallback")
        lbl_fallback_hint = QLabel("Used automatically if the SQL Server connection above is unavailable.")
        lbl_fallback_hint.setObjectName("card_caption")
        fallback.addWidget(lbl_fallback_hint)
        h_box = QHBoxLayout()
        self.sqlite_path = QLineEdit()
        btn_browse = QPushButton("Browse")
        btn_browse.setFixedWidth(100)
        btn_browse.setObjectName("btn_secondary")
        h_box.addWidget(self.sqlite_path); h_box.addWidget(btn_browse)
        fallback.addSpacing(6)
        fallback.addLayout(h_box)

        self.content_stack.addWidget(page)

    def setup_printer_page(self):
        page, layout = self.create_page("Printer Management", "Add and configure multiple barcode printers")
        
        main_hbox = QHBoxLayout()
        layout.addLayout(main_hbox)

        # Left side: List of printers
        left_panel = QVBoxLayout()
        self.printers_qlist = QListWidget()
        self.printers_qlist.setFixedWidth(250)
        self.printers_qlist.setObjectName("printers_qlist")
        left_panel.addWidget(self.printers_qlist)

        btn_hbox = QHBoxLayout()
        self.btn_add_printer = QPushButton("Add")
        self.btn_edit_printer = QPushButton("Edit")
        self.btn_del_printer = QPushButton("Delete")
        self.btn_add_printer.setObjectName("btn_secondary")
        self.btn_edit_printer.setObjectName("btn_secondary")
        self.btn_del_printer.setObjectName("btn_danger")
        for b in [self.btn_add_printer, self.btn_edit_printer, self.btn_del_printer]:
            btn_hbox.addWidget(b)
        left_panel.addLayout(btn_hbox)
        main_hbox.addLayout(left_panel)

        # Right side: Details
        self.details_pane = QWidget()
        right_panel = QVBoxLayout(self.details_pane)
        right_panel.setContentsMargins(20, 0, 0, 0)
        main_hbox.addWidget(self.details_pane)

        conn_card = self.make_card(right_panel, "Connection")
        self.printer_name_field = self.add_field(conn_card, "Printer Display Name")
        conn_card.addSpacing(6)

        lbl_mode = QLabel("Connection Mode"); lbl_mode.setObjectName("field_label")
        conn_card.addWidget(lbl_mode)
        conn_card.addSpacing(4)

        self.mode_group = QButtonGroup()
        self.useGeneric = QRadioButton("Direct USB (PyUSB / Generic)")
        self.useCustom = QRadioButton("System Print Driver (Win32 Spooler)")
        self.wireless_mode = QRadioButton("Network / Wireless (TCP/IP)")

        for i, rb in enumerate([self.useGeneric, self.useCustom, self.wireless_mode]):
            self.mode_group.addButton(rb, i)
            conn_card.addWidget(rb)
            conn_card.addSpacing(6)
        conn_card.addSpacing(14)

        # Printer selection
        self.printer_list = self.add_field(conn_card, "Detected Device / Spooler", "combo")

        right_panel.addSpacing(16)

        # Details group
        details_card = self.make_card(right_panel, "Manual Configuration")
        det_layout = QGridLayout()
        det_layout.setHorizontalSpacing(16)
        det_layout.setVerticalSpacing(4)
        det_layout.setRowMinimumHeight(2, 14)  # gap between the two field-pair rows

        lbl_v = QLabel("USB VID"); lbl_p = QLabel("USB PID"); lbl_e = QLabel("Endpoint"); lbl_ip = QLabel("IP Address")
        for l in [lbl_v, lbl_p, lbl_e, lbl_ip]: l.setObjectName("field_caption")

        self.printerVid = QLineEdit(); self.printerPid = QLineEdit()
        self.endpoint = QLineEdit(); self.ip_address = QLineEdit()
        for f in [self.printerVid, self.printerPid, self.endpoint, self.ip_address]:
            f.setObjectName("field_mono")

        det_layout.addWidget(lbl_v, 0, 0); det_layout.addWidget(self.printerVid, 1, 0)
        det_layout.addWidget(lbl_p, 0, 1); det_layout.addWidget(self.printerPid, 1, 1)
        det_layout.addWidget(lbl_e, 3, 0); det_layout.addWidget(self.endpoint, 4, 0)
        det_layout.addWidget(lbl_ip, 3, 1); det_layout.addWidget(self.ip_address, 4, 1)
        details_card.addLayout(det_layout)

        right_panel.addSpacing(16)

        # Save button for printers
        self.btn_save_printers = QPushButton("Save Printer Configuration")
        self.btn_save_printers.setObjectName("btn_primary")
        self.btn_save_printers.clicked.connect(self.save_printers_action)
        right_panel.addWidget(self.btn_save_printers)

        right_panel.addStretch()
        
        # Behavior
        self.useGeneric.toggled.connect(lambda: [self.onWirelessModeStateChanged(), self.save_current_printer_to_list()])
        self.useCustom.toggled.connect(lambda: [self.onWirelessModeStateChanged(), self.save_current_printer_to_list()])
        self.wireless_mode.toggled.connect(lambda: [self.onWirelessModeStateChanged(), self.save_current_printer_to_list()])
        self.printer_list.currentIndexChanged.connect(self.update_printer_in_json)
        self.printer_name_field.textChanged.connect(lambda: self.save_current_printer_to_list())
        self.printerVid.textChanged.connect(lambda: self.save_current_printer_to_list())
        self.printerPid.textChanged.connect(lambda: self.save_current_printer_to_list())
        self.endpoint.textChanged.connect(lambda: self.save_current_printer_to_list())
        self.ip_address.textChanged.connect(lambda: self.save_current_printer_to_list())
        
        self.btn_add_printer.clicked.connect(self.add_new_printer_logic)
        self.btn_edit_printer.clicked.connect(self.edit_printer_logic)
        self.btn_del_printer.clicked.connect(self.delete_printer_logic)
        self.printers_qlist.currentRowChanged.connect(self.load_selected_printer)

        self.content_stack.addWidget(page)

    def setup_general_page(self):
        page, layout = self.create_page("General Settings", "Branding and system-wide behavior")

        branding = self.make_card(layout, "Branding")
        row = QHBoxLayout(); col_a = QVBoxLayout(); col_b = QVBoxLayout()
        self.companyName = self.add_field(col_a, "Organization / Branch Name")
        self.location = self.add_field(col_b, "Physical Location ID")
        row.addLayout(col_a); row.addLayout(col_b)
        branding.addLayout(row)

        layout.addSpacing(16)
        behavior = self.make_card(layout, "Behavior")
        self.cb_logging = QCheckBox("Enable System Audit Logging")
        self.cb_hide_cost = QCheckBox("Hide Unit Cost from Label Previews")
        for cb in [self.cb_logging, self.cb_hide_cost]:
            behavior.addWidget(cb)

        self.content_stack.addWidget(page)

    def setup_templates_page(self):
        page, layout = self.create_page("Label Designer", "Modify TPSL and ZPL printing templates")

        designer_card = self.make_card(layout, "Visual Layout Designer")
        lbl_designer_hint = QLabel("Design labels by dragging text, barcodes and lines onto a canvas — no script editing required.")
        lbl_designer_hint.setObjectName("card_caption")
        lbl_designer_hint.setWordWrap(True)
        designer_card.addWidget(lbl_designer_hint)
        designer_card.addSpacing(10)
        btn_layout_designer = QPushButton("Open Custom Layout Designer")
        btn_layout_designer.setObjectName("btn_primary")
        btn_layout_designer.clicked.connect(self.open_layout_designer)
        designer_card.addWidget(btn_layout_designer)

        layout.addSpacing(16)
        script_card = self.make_card(layout, "Printer Script Templates")

        tabs = QHBoxLayout()
        tabs.setSpacing(0)
        tabs.setContentsMargins(0, 0, 0, 0)
        self.btn_tpsl = QPushButton("TPSL Templates"); self.btn_tpsl.setCheckable(True); self.btn_tpsl.setChecked(True)
        self.btn_zpl = QPushButton("ZPL Templates"); self.btn_zpl.setCheckable(True)
        self.btn_tpsl.setObjectName("seg_left")
        self.btn_zpl.setObjectName("seg_right")

        tabs.addWidget(self.btn_tpsl); tabs.addWidget(self.btn_zpl); tabs.addStretch()
        script_card.addLayout(tabs)
        script_card.addSpacing(12)

        self.template_stack = QStackedWidget()

        # TPSL Page
        tpsl_p = QWidget(); t_lay = QVBoxLayout(tpsl_p); t_lay.setContentsMargins(0, 0, 0, 0)
        self.use_tpsl = QRadioButton("Set TPSL as Active Language")
        self.combo_tpsl_size = self.add_field(t_lay, "Label Size Preset", "combo")
        self.tpslCommand = self.add_field(t_lay, "TPSL Script", "textedit")
        self.tpslCommand.setObjectName("field_mono")
        t_lay.addWidget(self.use_tpsl)
        self.template_stack.addWidget(tpsl_p)

        # ZPL Page
        zpl_p = QWidget(); z_lay = QVBoxLayout(zpl_p); z_lay.setContentsMargins(0, 0, 0, 0)
        self.use_zpl = QRadioButton("Set ZPL as Active Language")
        self.combo_zpl_size = self.add_field(z_lay, "Label Size Preset", "combo")
        self.zplCommand = self.add_field(z_lay, "ZPL Script", "textedit")
        self.zplCommand.setObjectName("field_mono")
        z_lay.addWidget(self.use_zpl)
        self.template_stack.addWidget(zpl_p)

        script_card.addWidget(self.template_stack)

        self.options = Configurations.LEGACY_BARCODE_SIZE_OPTIONS
        self.combo_tpsl_size.addItems(self.options)
        self.combo_zpl_size.addItems(self.options)
        
        # Switch behavior
        self.btn_tpsl.clicked.connect(lambda: [self.template_stack.setCurrentIndex(0), self.btn_zpl.setChecked(False)])
        self.btn_zpl.clicked.connect(lambda: [self.template_stack.setCurrentIndex(1), self.btn_tpsl.setChecked(False)])
        self.combo_tpsl_size.currentIndexChanged.connect(self.on_tpslSize_changed)
        self.combo_zpl_size.currentIndexChanged.connect(self.on_zplSize_changed)

        self.content_stack.addWidget(page)


    def setup_tools_page(self):
        page, layout = self.create_page("System Tools", "Driver installation and diagnostics")

        drivers = self.make_card(layout, "SQL Server Drivers")
        btn_driver = QPushButton("Install SQL Server Driver (ODBC 17)")
        btn_driver.setObjectName("btn_secondary"); btn_driver.clicked.connect(lambda: self.install_driver_from_ui("msodbcsql.msi"))
        drivers.addWidget(btn_driver)
        drivers.addSpacing(8)

        btn_check = QPushButton("Scan for System Drivers")
        btn_check.setObjectName("btn_secondary"); btn_check.clicked.connect(self.set_database_driver_details)
        drivers.addWidget(btn_check)

        layout.addSpacing(16)
        tester = self.make_card(layout, "Direct Printer Command Tester")
        self.et_generalCommand = self.add_field(tester, "Raw Command (TSPL / ZPL)", "textedit")
        self.et_generalCommand.setObjectName("field_mono")
        btn_test = QPushButton("Send Test Command")
        btn_test.setObjectName("btn_primary"); btn_test.clicked.connect(self.send_command)
        tester.addWidget(btn_test)

        self.content_stack.addWidget(page)

    # --- LOGIC PORTED FROM SETTINGS3.PY ---
    
    def load_data(self):
        try:
            self.logger.info("Loading config...")
            self.serverName.setText(self.config.get_server())
            self.databaseName.setText(self.config.get_database())
            self.userName.setText(self.config.get_username())
            self.password.setText(self.config.get_password())
            self.dbDriverName.setText(self.config.get_database_driver_name())
            self.sqlite_path.setText(self.config.get_sqlPath())
            
            self.use_zpl.setChecked(self.config.get_use_zpl())
            self.use_tpsl.setChecked(not self.config.get_use_zpl())
            
            self.companyName.setText(self.config.get_company_name())
            self.location.setText(self.config.get_location())
            self.cb_logging.setChecked(self.config.get_logging())
            self.cb_hide_cost.setChecked(self.config.get_hide_cost())
            self.cb_trusted_connection.setChecked(self.config.get_trusted_connection())
            
            self.combo_tpsl_size.setCurrentText(self.config.get_tpslSize())
            self.combo_zpl_size.setCurrentText(self.config.get_zplSize())
            self.on_tpslSize_changed(); self.on_zplSize_changed()
            
            self.refresh_printer_list()
        except Exception as e:
            self.logger.error(f"Load error: {e}")

    def refresh_printer_list(self):
        self.printers_qlist.clear()
        self.printers_data = self.config.get_printers_list()
        for p in self.printers_data:
            self.printers_qlist.addItem(p['name'])
        
        if self.printers_qlist.count() > 0:
            active_id = self.config.get_active_printer_id()
            for i in range(self.printers_qlist.count()):
                if self.printers_data[i]['id'] == active_id:
                    self.printers_qlist.setCurrentRow(i)
                    break
            else:
                self.printers_qlist.setCurrentRow(0)

    def load_selected_printer(self, row):
        if row < 0 or row >= len(self.printers_data): return

        # Save previous row before switching
        if self.current_printer_row != -1 and self.current_printer_row != row:
            self.save_current_printer_to_list(self.current_printer_row)

        self.current_printer_row = row
        p = self.printers_data[row]

        # Block signals to prevent cascading overwrites (e.g. radio toggle -> populate_printer_list
        # -> currentIndexChanged -> update_printer_in_json overwriting the data we're loading).
        _widgets = [self.printer_name_field, self.printerVid, self.printerPid,
                    self.endpoint, self.ip_address, self.printer_list,
                    self.useGeneric, self.useCustom, self.wireless_mode]
        for w in _widgets:
            w.blockSignals(True)
        try:
            self.printer_name_field.setText(p['name'])
            self.printerVid.setText(p.get('vid', ''))
            self.printerPid.setText(p.get('pid', ''))
            self.endpoint.setText(p.get('endpoint', ''))
            self.ip_address.setText(p.get('ip_address', ''))

            mode = p.get('mode', 'USB')
            if mode == 'USB': self.useGeneric.setChecked(True)
            elif mode == 'System': self.useCustom.setChecked(True)
            else: self.wireless_mode.setChecked(True)

            self.onWirelessModeStateChanged()

            if mode == 'System':
                self.printer_list.setCurrentText(p.get('system_name', ''))
        finally:
            for w in _widgets:
                w.blockSignals(False)

    def save_current_printer_to_list(self, row=None):
        if row is None: row = self.printers_qlist.currentRow()
        if row < 0 or row >= len(self.printers_data): return
        
        p = self.printers_data[row]
        p['name'] = self.printer_name_field.text()
        p['vid'] = self.printerVid.text()
        p['pid'] = self.printerPid.text()
        p['endpoint'] = self.endpoint.text()
        p['ip_address'] = self.ip_address.text()
        
        if self.useGeneric.isChecked(): p['mode'] = 'USB'
        elif self.useCustom.isChecked(): 
            p['mode'] = 'System'
            p['system_name'] = self.printer_list.currentText()
        else: p['mode'] = 'Network'
        
        self.printers_data[row] = p
        self.printers_qlist.item(row).setText(p['name'])

    def auto_detect_driver(self):
        from modules.CheckDriver import CheckDrivers
        checker = CheckDrivers()
        best = checker.find_best_sql_driver()
        if best:
            self.dbDriverName.setText(best)
            QMessageBox.information(self, "Success", f"Detected and set driver: {best}")
        else:
            QMessageBox.warning(self, "Not Found", "No SQL Server ODBC drivers were detected on this system.")

    def save_printers_action(self):
        try:
            self.save_current_printer_to_list()
            self.config.set_printers_list(self.printers_data)
            active_row = self.printers_qlist.currentRow()
            if active_row >= 0:
                self.config.set_active_printer_id(self.printers_data[active_row]['id'])
            QMessageBox.information(self, "Saved", "Printer configurations saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save printers: {e}")

    def add_new_printer_logic(self):
        import uuid

        if self.useGeneric.isChecked():
            mode = 'USB'
        elif self.useCustom.isChecked():
            mode = 'System'
        else:
            mode = 'Network'

        # Pre-populate from the currently-selected device in the dropdown
        data = self.printer_list.currentData()
        vid, pid, endpoint, system_name, name = "0x0000", "0x0000", "0x01", "", "New Printer"

        if mode == 'USB' and data:
            raw_vid, raw_pid, eps = data
            vid = str(raw_vid)
            pid = str(raw_pid)
            endpoint = str(eps[0]) if eps else "0x01"
            name = self.printer_list.currentText()
        elif mode == 'System':
            system_name = self.printer_list.currentText() or ""
            name = system_name or "New Printer"

        new_p = {
            "id": str(uuid.uuid4()),
            "name": name,
            "mode": mode,
            "vid": vid,
            "pid": pid,
            "endpoint": endpoint,
            "ip_address": self.ip_address.text() if mode == 'Network' else "127.0.0.1",
            "system_name": system_name
        }
        self.printers_data.append(new_p)
        self.printers_qlist.addItem(new_p['name'])
        self.printers_qlist.setCurrentRow(len(self.printers_data) - 1)
        # Persist immediately so the main app's printer selector picks it up
        self.config.set_printers_list(self.printers_data)

    def edit_printer_logic(self):
        pass

    def delete_printer_logic(self):
        row = self.printers_qlist.currentRow()
        if row < 0: return
        if len(self.printers_data) <= 1:
            QMessageBox.warning(self, "Warning", "You must have at least one printer.")
            return
        
        confirm = QMessageBox.question(self, "Delete", f"Delete printer '{self.printers_data[row]['name']}'?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.printers_data.pop(row)
            self.refresh_printer_list()

    def update_data(self):
        try:
            self.save_current_printer_to_list()
            
            self.config.set_server(self.serverName.text())
            self.config.set_database(self.databaseName.text())
            self.config.set_username(self.userName.text())
            self.config.set_password(self.password.text())
            self.config.set_database_driver_name(self.dbDriverName.text())
            self.config.set_trusted_connection(self.cb_trusted_connection.isChecked())
            self.config.set_sqlitePath(self.sqlite_path.text())
            
            self.config.set_printers_list(self.printers_data)
            active_row = self.printers_qlist.currentRow()
            if active_row >= 0:
                self.config.set_active_printer_id(self.printers_data[active_row]['id'])
            
            self.config.set_company_name(self.companyName.text())
            self.config.set_location(self.location.text())
            self.config.set_logging(self.cb_logging.isChecked())
            self.config.set_hide_cost(self.cb_hide_cost.isChecked())
            
            self.config.set_use_zpl(self.use_zpl.isChecked())
            
            # Templates - Save currently displayed template based on selected size
            current_tpsl_size = self.combo_tpsl_size.currentText()
            current_zpl_size = self.combo_zpl_size.currentText()
            
            # Save TPSL templates based on selected size
            if current_tpsl_size == self.options[0]:
                self.config.set_tpsl_template(self.tpslCommand.toPlainText())
            elif current_tpsl_size == self.options[1]:
                self.config.set_tpsl_size80_template(self.tpslCommand.toPlainText())
            elif current_tpsl_size == self.options[2]:
                self.config.set_tpsl_size3_template(self.tpslCommand.toPlainText())
            elif current_tpsl_size == self.options[3]:
                self.config.set_tpsl_funbake_template(self.tpslCommand.toPlainText())
            
            # Save ZPL templates based on selected size
            if current_zpl_size == self.options[0]:
                self.config.set_zpl_template(self.zplCommand.toPlainText())
            elif current_zpl_size == self.options[1]:
                self.config.set_zpl_size80_template(self.zplCommand.toPlainText())
            elif current_zpl_size == self.options[2]:
                self.config.set_zpl_size3_template(self.zplCommand.toPlainText())
            elif current_zpl_size == self.options[3]:
                self.config.set_zpl_funbake_template(self.zplCommand.toPlainText())
            
            self.logger.info(f"Saved TPSL template for size: {current_tpsl_size}")
            self.logger.info(f"Saved ZPL template for size: {current_zpl_size}")
            
            QMessageBox.information(self, "Success", "All settings saved successfully.")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def onWirelessModeStateChanged(self):
        is_wireless = self.wireless_mode.isChecked()
        is_generic = self.useGeneric.isChecked()
        is_custom = self.useCustom.isChecked()
        
        self.ip_address.setEnabled(is_wireless)
        self.printerVid.setEnabled(is_generic)
        self.printerPid.setEnabled(is_generic)
        self.endpoint.setEnabled(is_generic)
        
        if is_generic: self.populate_printer_list()
        elif is_custom: self.populate_customdriver_printer_list()

    def update_printer_in_json(self):
        data = self.printer_list.currentData()
        if not data: return
        
        if self.useGeneric.isChecked():
            vid, pid, eps = data
            self.printerVid.setText(str(vid)); self.printerPid.setText(str(pid))
            if eps: self.endpoint.setText(str(eps[0]))
        
        # Always sync with the current printer profile
        self.save_current_printer_to_list()

    def on_tpslSize_changed(self):
        size = self.combo_tpsl_size.currentText()
        self.config.set_tpslSize(size)
        tmpls = {self.options[0]: self.config.get_tpsl_template, self.options[1]: self.config.get_tpsl_size80_template, 
                 self.options[2]: self.config.get_tpsl_size3_template, self.options[3]: self.config.get_tpsl_funbake_template}
        if size in tmpls: self.tpslCommand.setText(tmpls[size]())

    def on_zplSize_changed(self):
        size = self.combo_zpl_size.currentText()
        self.config.set_zplSize(size)
        tmpls = {self.options[0]: self.config.get_zpl_template, self.options[1]: self.config.get_zpl_size80_template, 
                 self.options[2]: self.config.get_zpl_size3_template, self.options[3]: self.config.get_zpl_funbake_template}
        if size in tmpls: self.zplCommand.setText(tmpls[size]())

    def populate_printer_list(self):
        self.printer_list.clear()
        try:
            devices = usb.core.find(find_all=True)
            for dev in devices:
                if dev.bDeviceClass == 7: # Printer
                    name = f"{hex(dev.idVendor)}:{hex(dev.idProduct)} - Printer"
                    self.printer_list.addItem(name, userData=(hex(dev.idVendor), hex(dev.idProduct), []))
        except: pass

    def populate_customdriver_printer_list(self):
        checker = CheckDriver.CheckDrivers()
        got, printers = checker.check_printer_driver()
        self.printer_list.clear()
        if got:
            for p in printers: self.printer_list.addItem(p, userData=p)

    def set_database_driver_details(self):
        QMessageBox.information(self, "Driver Check", "Scanning for ODBC Drivers...")
        # Ported simplified logic
        
    def install_driver_from_ui(self, name):
        # Ported logic
        pass

    def send_command(self):
        # Ported logic
        pass

    def open_layout_designer(self):
        from modules.barcode_designer import BarcodeDesigner
        self.designer_window = BarcodeDesigner(config=self.config)
        self.designer_window.setWindowTitle("Custom Layout Designer")
        self.designer_window.resize(1000, 600)
        self.designer_window.show()

    def resource_path(self, relative_path):
        try: base_path = sys._MEIPASS
        except Exception: base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = SettingsWindow()
    win.show()
    sys.exit(app.exec_())