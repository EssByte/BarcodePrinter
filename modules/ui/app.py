import os
import sys
import usb
import usb.core
import usb.util
import usb.backend.libusb1
import requests
import pyodbc
import sqlite3
import subprocess
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox, QGridLayout, QHBoxLayout, QAction, QProgressBar, QComboBox, QCheckBox, QHeaderView, QFrame, QVBoxLayout, QSpinBox
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtGui import QIcon, QBrush, QColor

from modules import Configurations
from modules.logger_config import setup_logger
from modules.SendCommand import SendCommand
from modules.Configurations import BarcodeConfig
from modules.ImagePrinter import ImagePrinter
from modules.label_details_dialog import LabelDetailsDialog
from modules.threads import FetchItemsThread, FilterItemsBinaryThread
from modules.utils import resource_path, split_description, replace_placeholders
from remark import RemarkDialog
from dashboard import DashboardWindow
from check_password import PasswordCheck
from version import __version__

class BarcodeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = setup_logger('BarcodeApp')
        self.logger.info("Initializing BarcodeApp...")
        self.config = BarcodeConfig()

        self.current_page = 1
        self.items_per_page = 100  
        self.total_pages = 1
        self.current_displayed_items = []
        self.items = []
        self.all_items = []
        self.loading_overlay = None
    
        self.initUI()
        self.input_timer = QTimer()
        self.input_timer.setSingleShot(True)
        self.input_timer.timeout.connect(self.filter_items_binary)
        self.config.setting_changed.connect(self.handle_config_change)
        
        # Load local backend
        backend_lib = resource_path('libusb-1.0.ddl', self.logger)
        self.backend = usb.backend.libusb1.get_backend(find_library=backend_lib)
        
        self.setWindowIcon(QIcon(resource_path("images/logo.ico")))
        self.db_connected = False # Kept for UI legacy checks if any
        self.settings = QSettings("MyCompany", "MyApp")
        self.restore_column_widths() 
        self.loadStylesheet()
        self.showMaximized()
        self.fetch_items_thread = None

        # Initial background scan
        self.handle_config_change() 

    def update_logging(self):
        self.logger = setup_logger('BarcodeApp')
        self.logger.info("Logging configuration updated.")
    
    def start_timer(self):
        self.input_timer.start(400)

    def handle_config_change(self, key=None, value=None):
        self.logger.info(f"Config change detected ({key}). Initializing necessary updates...")
        try:
            if key in [None, "server", "database", "location", "useSqlite"]:
                self.show_loading("SCANNING DATABASE...")
                self.update_logging()
                self.check_version()
                self.start_fetch_items()
            
            if key in [None, "printers_list", "active_printer_id"]:
                self.populate_printers()
        except Exception as e:
            self.hide_loading()
            self.logger.error(f"Failed to reload: {e}")
            QMessageBox.critical(self, 'Error', f"Failed to reload: {e}")

    def start_fetch_items(self):
        # Entirely background now
        self.fetch_items_thread = FetchItemsThread(self.config.get_location(), self.config.get_useSqlite())
        self.fetch_items_thread.items_fetched.connect(self.handle_items_fetched)
        self.fetch_items_thread.error_occurred.connect(self.handle_fetch_error)
        self.fetch_items_thread.start()

    def handle_fetch_error(self, err_msg):
        self.hide_loading()
        self.logger.error(err_msg)
        QMessageBox.critical(self, 'Database Error', err_msg)

    def handle_items_fetched(self, items):
        self.hide_loading()
        self.items = items
        key_idx = 0 if self.config.get_useSqlite() else 5
        self.all_items = sorted(self.items, key=lambda x: str(x[key_idx]).lower())
        self.display_items(self.all_items)
            
    def runUpdater(self):
        try:
            self.logger.info("Starting updater...")
            current_dir = os.path.dirname(os.path.abspath(__file__))
            updater_script = os.path.join(os.path.dirname(current_dir), "..", "updater.py")
            
            if os.path.exists(updater_script):
                self.close()
                subprocess.Popen([sys.executable, updater_script])
            else:
                updater_exe = os.path.join(os.getcwd(), "Updater.exe")
                if os.path.exists(updater_exe):
                    self.close()
                    subprocess.Popen([updater_exe])
                else:
                    subprocess.Popen([r"C:\barcode\Updater.exe"])
                    self.close()
        except Exception as e:
            self.logger.error(f"Failed to start updater: {e}")
            QMessageBox.critical(self, "Updater Error", f"Failed to start updater: {e}")
            
    def initUI(self):
        self.setWindowTitle('Barcode Printer')
        self.setGeometry(200, 200, 1400, 600)

        central_widget = QWidget(self)
        central_widget.setObjectName("central_widget")
        self.setCentralWidget(central_widget)

        grid_layout = QGridLayout(central_widget)
        menu_bar = self.menuBar()

        dashboard_menu = menu_bar.addMenu("Dashboard")
        dashboard_action = QAction("Open Dashboard", self)
        dashboard_action.triggered.connect(self.open_dashboard)
        dashboard_menu.addAction(dashboard_action)

        file_menu = menu_bar.addMenu('Settings')
        settings_action = QAction('Open Settings', self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)

        layout_menu = menu_bar.addMenu('Layout Designer')
        layout_action = QAction('Open Custom Layout Designer', self)
        layout_action.triggered.connect(self.open_layout_designer)
        layout_menu.addAction(layout_action)

        # Search UI
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.item_code_input = QLineEdit(self)
        self.item_code_input.setPlaceholderText('Enter Item Code')
        self.item_code_input.textChanged.connect(self.start_timer)
        self.item_code_input.returnPressed.connect(lambda: self.filter_items(False))

        self.search_for_uom = QPushButton("Get UOM", self)
        self.search_for_uom.setCursor(Qt.PointingHandCursor)
        self.search_for_uom.clicked.connect(lambda: self.filter_items(True))
        
        self.search_by_description = QPushButton("Search", self)
        self.search_by_description.setObjectName("btn_search")
        self.search_by_description.setCursor(Qt.PointingHandCursor)
        self.search_by_description.clicked.connect(lambda: self.filter_items(False))

        self.barcode_size = QComboBox(self)
        self.options = ["Size 1 (35x25 Graphic)", "Size 2", "Size 3", "75x55 (Graphic)"]
        self.barcode_size.addItems(self.options)
        self.barcode_size.currentIndexChanged.connect(self.handle_barcode_size)
        
        self.printer_selector = QComboBox(self)
        self.printer_selector.setMinimumWidth(150)
        self.printers_data = []
        self.populate_printers()
        self.printer_selector.currentIndexChanged.connect(self.handle_printer_selection)
        
        self.btn_refresh_printers = QPushButton("🔄", self)
        self.btn_refresh_printers.setFixedWidth(40)
        self.btn_refresh_printers.clicked.connect(self.populate_printers)
        
        self.sqlite_switch = QCheckBox("Use SQLite")
        self.sqlite_switch.setChecked(self.config.get_useSqlite())
        self.sqlite_switch.stateChanged.connect(self.toggle_database_mode)

        if self.config.get_use_zpl():
            self.barcode_size.setCurrentText(self.config.get_zplSize())
        else:
            self.barcode_size.setCurrentText(self.config.get_tpslSize())
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.item_code_input)
        search_layout.addWidget(self.sqlite_switch)
        search_layout.addWidget(QLabel("Printer:"))
        search_layout.addWidget(self.printer_selector)
        search_layout.addWidget(self.btn_refresh_printers)
        search_layout.addWidget(QLabel("Size:"))
        search_layout.addWidget(self.barcode_size)
        search_layout.addWidget(QLabel("X:"))
        self.x_offset_spin = QSpinBox()
        self.x_offset_spin.setRange(0, 200)
        self.x_offset_spin.setValue(int(self.settings.value("label_x_offset", 30)))
        self.x_offset_spin.setFixedWidth(50)
        self.x_offset_spin.valueChanged.connect(lambda v: self.settings.setValue("label_x_offset", v))
        search_layout.addWidget(self.x_offset_spin)
        search_layout.addWidget(self.search_for_uom)
        search_layout.addWidget(self.search_by_description)
        grid_layout.addLayout(search_layout, 0, 0, 1, 3)

        # Table UI
        self.item_table = QTableWidget(self)
        self.item_table.setColumnCount(11)
        self.item_table.setHorizontalHeaderLabels(["*", "Remark", "Copies", "Item Code", "Description", "UOM", "Unit Price", "Unit Cost", "Barcode", "Location", "Price"])
        self.item_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.item_table.setSelectionMode(QTableWidget.NoSelection)
        self.item_table.verticalHeader().setDefaultSectionSize(60)
        self.item_table.setColumnWidth(0, 50)
        self.item_table.setColumnWidth(1, 150) # Remark
        self.item_table.setColumnWidth(2, 80) # Copies
        self.item_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        grid_layout.addWidget(self.item_table, 1, 0, 1, 3)

        # Pagination & Action Buttons
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton('Previous', self)
        self.prev_button.clicked.connect(self.previous_page)
        self.page_label = QLabel('Page 1 of 1')
        self.next_button = QPushButton('Next', self)
        self.next_button.clicked.connect(self.next_page)
        
        self.items_per_page_combo = QComboBox(self)
        self.items_per_page_combo.addItems(['50', '100', '200', '500'])
        self.items_per_page_combo.setCurrentText(str(self.items_per_page))
        self.items_per_page_combo.currentTextChanged.connect(self.change_items_per_page)

        self.reload_button = QPushButton('Reload Database', self)
        self.reload_button.clicked.connect(self.handle_config_change)
        self.print_button = QPushButton('Print Barcode', self)
        self.print_button.setObjectName("btn_print")
        self.print_button.clicked.connect(self.print_barcode)

        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addStretch(1)
        pagination_layout.addWidget(QLabel('Items per page:'))
        pagination_layout.addWidget(self.items_per_page_combo)
        pagination_layout.addSpacing(20)
        pagination_layout.addWidget(self.reload_button)
        pagination_layout.addWidget(self.print_button)
        grid_layout.addLayout(pagination_layout, 2, 0, 1, 3)

        # Bottom Bar
        buttons_layout = QHBoxLayout()
        self.update_button = QPushButton('Update', self)
        self.update_button.clicked.connect(self.runUpdater)
        buttons_layout.addWidget(self.update_button)
        buttons_layout.addStretch(1)
        grid_layout.addLayout(buttons_layout, 3, 0, 1, 3)

        self.check_version()
        self.update_pagination_buttons()

    def setup_loading_overlay(self, msg="SCANNING DATABASE..."):
        if not self.loading_overlay:
            self.loading_overlay = QFrame(self)
            self.loading_overlay.setStyleSheet("background-color: rgba(15, 23, 42, 0.9); border-radius: 20px; border: 2px solid #3b82f6;")
            self.loading_overlay.setFixedSize(400, 120)
            
            overlay_layout = QVBoxLayout(self.loading_overlay)
            self.lbl_loading_msg = QLabel(msg)
            self.lbl_loading_msg.setStyleSheet("color: white; font-weight: 800; font-size: 14px; letter-spacing: 1px; border: none;")
            self.lbl_loading_msg.setAlignment(Qt.AlignCenter)
            
            self.loading_pbar = QProgressBar()
            self.loading_pbar.setRange(0, 0)
            self.loading_pbar.setTextVisible(False)
            self.loading_pbar.setStyleSheet("""
                QProgressBar { border: 1px solid #334155; border-radius: 5px; height: 8px; background: #1e293b; }
                QProgressBar::chunk { background-color: #3b82f6; border-radius: 4px; }
            """)
            overlay_layout.addStretch()
            overlay_layout.addWidget(self.lbl_loading_msg)
            overlay_layout.addWidget(self.loading_pbar)
            overlay_layout.addStretch()

    def show_loading(self, msg="SCANNING DATABASE..."):
        self.setup_loading_overlay(msg)
        self.lbl_loading_msg.setText(msg)
        self.loading_overlay.move(
            (self.width() - self.loading_overlay.width()) // 2,
            (self.height() - self.loading_overlay.height()) // 2
        )
        self.loading_overlay.show()
        self.loading_overlay.raise_()

    def hide_loading(self):
        if self.loading_overlay:
            self.loading_overlay.hide()

    def loadStylesheet(self):
        try:
            stylesheet = """
            QMainWindow { background-color: #f0f2f5; }
            QWidget#central_widget { background-color: #f0f2f5; }
            QLabel { font-family: 'Segoe UI'; color: #2c3e50; font-size: 14px; font-weight: 500; }
            QLineEdit { background-color: #ffffff; border: 2px solid #e0e6ed; border-radius: 8px; padding: 10px 15px; font-size: 14px; }
            QLineEdit:focus { border: 2px solid #3498db; }
            QTableWidget { background-color: #ffffff; border: 1px solid #e0e6ed; border-radius: 12px; gridline-color: transparent; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #f1f3f5; }
            QHeaderView::section { background-color: #f8fafc; padding: 12px; border: none; border-bottom: 2px solid #3498db; font-weight: bold; }
            QHeaderView::section:vertical { border-right: 2px solid #3498db; padding: 5px; }
            QPushButton { background-color: #ffffff; border: 1px solid #d1d5db; border-radius: 8px; padding: 8px 16px; font-weight: 600; }
            QPushButton:hover { background-color: #f9fafb; border-color: #3498db; color: #3498db; }
            QPushButton#btn_print { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3498db, stop:1 #2980b9); color: white; border: none; }
            QPushButton#btn_search { background-color: #2ecc71; color: white; border: none; }
            QComboBox { background-color: #ffffff; border: 1px solid #d1d5db; border-radius: 8px; padding: 8px; }
            QProgressBar { border: 1px solid #d1d5db; border-radius: 5px; text-align: center; }
            QProgressBar::chunk { background-color: #3498db; border-radius: 4px; }
            QMenuBar { background-color: #ffffff; border-bottom: 1px solid #e0e6ed; padding: 5px; }
            """
            self.setStyleSheet(stylesheet)
        except Exception as e:
            self.logger.error(f"Failed to apply stylesheet: {e}")

    def change_items_per_page(self, new_value):
        self.items_per_page = int(new_value)
        self.current_page = 1
        if hasattr(self, 'current_displayed_items'):
            self.display_items(self.current_displayed_items)

    def update_pagination_buttons(self):
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < self.total_pages)
        self.page_label.setText(f'Page {self.current_page} of {self.total_pages}')

    def previous_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.display_items(self.current_displayed_items)

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.display_items(self.current_displayed_items)
                
    def toggle_database_mode(self):
        self.config.set_useSqlite(self.sqlite_switch.isChecked())

    def handle_barcode_size(self):
        selected_item = self.barcode_size.currentText()
        if not self.config.get_use_zpl():
            self.config.set_tpslSize(selected_item)
        else:
            self.config.set_zplSize(selected_item)

    def populate_printers(self):
        self.printer_selector.blockSignals(True)
        self.printer_selector.clear()
        self.printers_data = self.config.get_printers_list()
        active_id = self.config.get_active_printer_id()
        for i, p in enumerate(self.printers_data):
            self.printer_selector.addItem(p['name'], p['id'])
            if p['id'] == active_id:
                self.printer_selector.setCurrentIndex(i)
        self.printer_selector.blockSignals(False)

    def handle_printer_selection(self, index):
        if index < 0: return
        printer_id = self.printer_selector.itemData(index)
        self.config.set_active_printer_id(printer_id)
    
    def check_version(self):
        repo_owner = "PersonX-46"
        repo_name = "BarcodePrinter"
        api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            tag_name = response.json()["tag_name"]
            self.update_button.setVisible(tag_name > __version__)
        except Exception as e:
            self.logger.error(f"Version check failed: {e}")

    def display_items(self, items):
        self.current_displayed_items = items
        total_items = len(items)
        self.total_pages = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)
        start_index = (self.current_page - 1) * self.items_per_page
        page_items = items[start_index:start_index + self.items_per_page]
        
        self.item_table.setRowCount(len(page_items))
        barcode_config = Configurations.BarcodeConfig()

        for row, item in enumerate(page_items):
            cb = QTableWidgetItem(); cb.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled); cb.setCheckState(Qt.Unchecked)
            self.item_table.setItem(row, 0, cb)

            if self.config.get_useSqlite():
                bc, name, p = item; item_code = "-"; uom = "-"; unit_price = p; unit_cost = 0; loc = "-"; loc_p = p
            else:
                item_code, name, uom, unit_price, unit_cost, barcode, loc, loc_p = item
                bc = item_code if barcode is None else barcode

            safe_float = lambda x: float(x) if x not in (None, "") else 0.0
            values = [item_code, name, uom, f"RM {safe_float(unit_price):.2f}", '***' if barcode_config.get_hide_cost() else f"RM {safe_float(unit_cost):.2f}", bc, loc, f"RM {safe_float(loc_p):.2f}"]
            
            rmk = QTableWidgetItem(""); rmk.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled); rmk.setTextAlignment(Qt.AlignCenter)
            self.item_table.setItem(row, 1, rmk)

            cp = QTableWidgetItem("1"); cp.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled); cp.setTextAlignment(Qt.AlignCenter)
            self.item_table.setItem(row, 2, cp)

            for col, val in enumerate(values, start=3):
                ti = QTableWidgetItem(str(val)); ti.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled); ti.setTextAlignment(Qt.AlignCenter)
                self.item_table.setItem(row, col, ti)
            if row % 2 == 0:
                for c in range(11): self.item_table.item(row, c).setBackground(QBrush(QColor(248, 250, 252)))

        self.update_pagination_buttons()
        self.restore_column_widths()

    def filter_items_binary(self):
        search_text = self.item_code_input.text().strip().lower()
        self.current_page = 1
        if not search_text: self.display_items(self.all_items); return
        self.display_items([item for item in self.all_items if search_text in str(item).lower()])

    def filter_items(self, isUOM):
        search_text = self.item_code_input.text().strip().lower()
        self.current_page = 1
        keywords = search_text.split()
        idx = 0 if self.config.get_useSqlite() else (0 if isUOM else 1)
        filtered = [item for item in self.all_items if all(kw in str(item[idx]).lower() for kw in keywords)]
        self.display_items(filtered)

    def print_barcode(self):
        selected_rows = [r for r in range(self.item_table.rowCount()) if self.item_table.item(r, 0).checkState() == Qt.Checked]
        if not selected_rows: 
            QMessageBox.warning(self, 'Selection Error', 'No items selected for printing.')
            return

        details_dialog = LabelDetailsDialog(self)
        if details_dialog.exec_() != LabelDetailsDialog.Accepted: return

        meta = details_dialog.get_data()
        net_weight_val = meta['weight']
        batch_val = meta['batch']
        
        send_command = SendCommand()
        printer_config = self.config.get_active_printer_config()
        if not printer_config:
            QMessageBox.critical(self, 'Error', 'No active printer configuration found.')
            return

        mode = printer_config.get('mode', 'USB')
        usb_printer = None
        
        try:
            if mode == 'USB':
                vid = int(printer_config['vid'], 16) if '0x' in printer_config['vid'] else int(printer_config['vid'])
                pid = int(printer_config['pid'], 16) if '0x' in printer_config['pid'] else int(printer_config['pid'])
                usb_printer = usb.core.find(idVendor=vid, idProduct=pid, backend=self.backend)
                if usb_printer is None:
                    QMessageBox.warning(self, 'Printer Error', f'Printer {printer_config["name"]} not found via USB.')
                    return
                usb_printer.set_configuration()
            elif mode == 'Network':
                ip_full = printer_config.get('ip_address', '127.0.0.1:9100')
                if ":" in ip_full:
                    ip, port = ip_full.split(":")
                else:
                    ip, port = ip_full, "9100"

            for row in selected_rows:
                desc = self.item_table.item(row, 4).text().replace('"', '')
                price = self.item_table.item(row, 10).text()
                bc = self.item_table.item(row, 8).text()
                remark_text = self.item_table.item(row, 1).text()
                qty = self.item_table.item(row, 2).text()
                
                d1, d2 = split_description(desc)
                sz = self.barcode_size.currentText()
                printer_clear = "CLS"
                print_data = ""
                
                if "Graphic" in sz:
                    image_printer = ImagePrinter()
                    if "35x25" in sz or "Size 1" in sz:
                        item_code = self.item_table.item(row, 3).text()
                        remark = self.item_table.item(row, 1).text()
                        im = image_printer.render_35x25_label({
                            'company_name': self.config.get_company_name(),
                            'item_code': item_code,
                            'description': desc, 
                            'remark': remark,
                            'barcode_value': bc, 
                            'unit_price_integer': price
                        }, x_offset=self.x_offset_spin.value())
                        print_data = image_printer.get_full_command(im, copies=int(qty), width_mm=35, height_mm=25)
                    else: # Assume Fun Bake 75x55
                        im = image_printer.render_fun_bake_label({
                            'description': desc, 'barcode_value': bc, 'remark': remark_text, 
                            'unit_price_integer': price, 'net_weight': net_weight_val, 'batch': batch_val
                        })
                        print_data = image_printer.get_full_command(im, copies=int(qty), width_mm=75, height_mm=50)
                    printer_clear = b""
                else:
                    tmpl = self.get_current_template()
                    print_data = replace_placeholders(
                        tmpl, self.logger, 
                        companyName=self.config.get_company_name(), description=desc, description_1=d1, description_2=d2, 
                        remark=remark_text, barcode_value=bc, unit_price_integer=price, weight=net_weight_val, batch=batch_val, copies=qty
                    )
                    if self.config.get_use_zpl(): printer_clear = "^XA^CLS^XZ"

                if mode == 'USB':
                    payload = print_data.encode('utf-8') if isinstance(print_data, str) else print_data
                    usb_printer.write(int(printer_config.get('endpoint', '0x01'), 16), payload)
                elif mode == 'Network':
                    send_command.send_wireless_command(ip, port, printer_clear, print_data)
                else: # System
                    sys_name = printer_config.get('system_name', '')
                    send_command.send_win32print(sys_name, printer_clear)
                    send_command.send_win32print(sys_name, print_data)

            QMessageBox.information(self, 'Success', f'Successfully sent all items to {printer_config["name"]}!')
        except Exception as e:
            QMessageBox.critical(self, 'Printing Error', f"An error occurred: {e}")
        finally:
            if usb_printer: usb.util.dispose_resources(usb_printer)

    def get_current_template(self):
        sz = self.barcode_size.currentText()
        if self.config.get_use_zpl():
            if "Graphic" in sz: return self.config.get_zpl_funbake_template()
            return self.config.get_zpl_template()
        else:
            if "Graphic" in sz: return self.config.get_tpsl_funbake_template()
            return self.config.get_tpsl_template()

    def save_column_widths(self):
        for i in range(self.item_table.columnCount()):
            self.settings.setValue(f"column_width_{i}", self.item_table.columnWidth(i))

    def restore_column_widths(self):
        for i in range(self.item_table.columnCount()):
            w = self.settings.value(f"column_width_{i}", type=int)
            if w: self.item_table.setColumnWidth(i, w)
            
    def open_settings(self):
        self.settings_window = PasswordCheck(self.config)
        self.settings_window.show()

    def open_dashboard(self): 
        self.dashboard_window = DashboardWindow()
        self.dashboard_window.show()

    def open_layout_designer(self):
        from modules.barcode_designer import BarcodeDesigner
        # Open the widget as a standalone window
        self.designer_window = BarcodeDesigner()
        self.designer_window.setWindowTitle("Custom Layout Designer")
        self.designer_window.resize(1000, 600)
        self.designer_window.show()

    def closeEvent(self, e): 
        self.save_column_widths()
        super().closeEvent(e)
