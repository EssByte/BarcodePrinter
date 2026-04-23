import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame, QPushButton, QGraphicsDropShadowEffect
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
        # Fixed naming to match logic methods:
        # lbl_resultConnectivity, lbl_resultDatabase, lbl_resultConnectedDevice, lbl_resultConfiguration, lbl_loggingResult
        
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(30)
        
        # Connectivity Card (Vibrant Orange Border)
        self.card_net = self.create_status_card("CONNECTIVITY", "Public Network Access", "lbl_resultConnectivity", "#f59e0b")
        self.grid_layout.addWidget(self.card_net, 0, 0)
        
        # Database Card (Vibrant Purple Border)
        self.card_db = self.create_status_card("DATABASE", "SQL Server Status", "lbl_resultDatabase", "#8b5cf6")
        self.grid_layout.addWidget(self.card_db, 0, 1)
        
        # Printer Card (Vibrant Green Border)
        self.card_printer = self.create_status_card("HARDWARE", "Connected Printers", "lbl_resultConnectedDevice", "#10b981")
        self.grid_layout.addWidget(self.card_printer, 1, 0)
        
        # Configuration Card (Vibrant Blue Border)
        self.card_config = self.create_status_card("CONFIG FILE", "Schema Integrity", "lbl_resultConfiguration", "#3b82f6")
        self.grid_layout.addWidget(self.card_config, 1, 1)
        
        # Logging Card (Vibrant Pink Border)
        self.card_log = self.create_status_card("LOGGING", "Audit Trail Status", "lbl_loggingResult", "#ec4899")
        self.grid_layout.addWidget(self.card_log, 2, 0)

        # Security Card
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

        # Timer setup
        self.update_datetime()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)

        # Load initial diagnostics
        QTimer.singleShot(800, self.load_data)

    def create_status_card(self, title, subtitle, result_name, accent_color):
        card = QFrame()
        card.setObjectName("status_card")
        # GLASSMORPHISM STYLE
        card.setStyleSheet(f"""
            QFrame#status_card {{ 
                background-color: rgba(255, 255, 255, 0.95); 
                border-left: 8px solid {accent_color};
                border-radius: 15px; 
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 80))
        card.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(30, 30, 30, 30)
        
        text_layout = QVBoxLayout()
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet(f"font-size: 18px; font-weight: 800; color: #1e293b; letter-spacing: 1px;")
        lbl_s = QLabel(subtitle)
        lbl_s.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748b;")
        text_layout.addWidget(lbl_t)
        text_layout.addWidget(lbl_s)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        if result_name:
            lbl_res = QLabel("SCAN")
            setattr(self, result_name, lbl_res)
            lbl_res.setStyleSheet(f"font-size: 28px; color: {accent_color}; font-weight: 900;")
            layout.addWidget(lbl_res)
        else:
            lbl_res = QLabel("✅")
            lbl_res.setStyleSheet("font-size: 32px;")
            layout.addWidget(lbl_res)
            
        return card

    def update_datetime(self):
        # Get the current date and time in the desired format
        current_datetime = QDateTime.currentDateTime().toString('dd/MM/yyyy hh:mm AP')
        
        # Update the label text with the formatted date and time
        self.lbl_datetime.setText(current_datetime)

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # Log the attempt to resolve the resource path
            self.logger.debug(f"Attempting to resolve resource path for: {relative_path}")
            
            # Try to get the PyInstaller base path
            base_path = sys._MEIPASS
            self.logger.debug(f"PyInstaller base path resolved: {base_path}")
        except AttributeError:
            # Fall back to the current working directory in development mode
            base_path = os.path.abspath(".")
            self.logger.debug(f"Development mode detected. Base path resolved to: {base_path}")
        except Exception as e:
            self.logger.exception(f"Unexpected error while resolving base path: {e}")
            raise  # Re-raise the exception if it cannot be handled

        # Construct the absolute path to the resource
        absolute_path = os.path.join(base_path, relative_path)
        self.logger.debug(f"Absolute resource path resolved: {absolute_path}")
        return absolute_path

    def is_connected(self):
        try:
            # Try to connect to a public DNS server (Google's DNS: 8.8.8.8) over port 53 (DNS port)
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            
            # Log success if connected
            self.logger.info("Successfully connected to the internet (8.8.8.8:53).")
            
            # Update the UI to reflect successful connection
            self.lbl_resultConnectivity.setText("✅️")
        except (socket.timeout, OSError) as e:
            # Log failure if not connected
            self.logger.error(f"Failed to connect to the internet: {e}")
            
            # Update the UI to reflect the failure
            self.lbl_resultConnectivity.setText("❌")

    def can_connect_to_database(self):
        try:
            # Load configuration
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # Prepare the connection string
            connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={config['server']};"
                f"DATABASE={config['database']};"
                f"UID={config['username']};"
                f"PWD={config['password']};"
            )

            # Try to establish a connection to the database
            with pyodbc.connect(connection_string, timeout=5) as connection:
                # Connection successful
                self.logger.info("Successfully connected to the database.")
                self.lbl_resultDatabase.setText("✅️")

        except FileNotFoundError:
            self.logger.error(f"Configuration file not found at {self.config_path}")
            QMessageBox.critical(self, 'Config Error', f'Configuration file not found at {self.config_path}')

        except json.JSONDecodeError:
            self.logger.error("Error parsing the configuration file.")
            QMessageBox.critical(self, 'Config Error', 'Error parsing the configuration file.')

        except KeyError as e:
            self.logger.error(f"Missing key in configuration file: {e}")
            QMessageBox.critical(self, 'Config Error', f'Missing key in configuration file: {e}')
            
        except pyodbc.Error as e:
            self.logger.error(f"Database connection failed: {e}")
            print(f"Connection failed: {e}")
            self.lbl_resultDatabase.setText("❌")

    def check_config_file(self):
        # Log the start of the configuration file check
        self.logger.info("Checking configuration file...")

        # List of required keys in the config file
        required_keys = [
            "server",
            "database",
            "username",
            "password",
            "vid",
            "pid",
            "endpoint",
            "companyName",
            "location",
            "useZPL",
            "ip_address",
            "wireless_mode",
            "zplTemplate",
            "tpslTemplate",
            "logging"
        ]

        # Check if the file exists
        if not os.path.isfile(self.config_path):
            error_message = f"Configuration file not found at {self.config_path}"
            self.logger.error(error_message)  # Log the error
            print(f"Error: {error_message}")
            self.lbl_resultConfiguration.setText("❌")
            return

        try:
            # Load and parse the JSON file
            with open(self.config_path, "r") as file:
                config = json.load(file)
            self.logger.info(f"Configuration file loaded successfully from {self.config_path}")
        except json.JSONDecodeError:
            error_message = "Configuration file is not a valid JSON."
            self.logger.error(error_message)  # Log the error
            print(error_message)
            self.lbl_resultConfiguration.setText("❌")
            return

        # Check for all required keys
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            error_message = f"Missing required keys: {', '.join(missing_keys)}"
            self.logger.error(error_message)  # Log the missing keys
            print(f"Error: {error_message}")
            self.lbl_resultConfiguration.setText("❌")
        else:
            self.logger.info("All required keys are present in the configuration file.")
            self.lbl_resultConfiguration.setText("✅️")
    
    def count_connected_printers(self):
        self.logger.info("Starting to count connected printers...")

        try:
            # Find all USB devices
            devices = usb.core.find(find_all=True)
            printer_count = 0

            # Iterate over devices and check if any have the printer class (0x07)
            for device in devices:
                # The bDeviceClass is 7 for printers or can be 0 if the interface specifies it
                if device.bDeviceClass == 7:
                    printer_count += 1
                    self.logger.debug(f"Printer found!")
                else:
                    # Check each configuration for interfaces specifying the printer class
                    for config in device:
                        for interface in config:
                            if interface.bInterfaceClass == 7:
                                printer_count += 1
                                self.logger.debug(f"Printer found via interface")
                                break  # Found a printer, exit loop

            self.logger.info(f"Total connected printers: {printer_count}")
            self.lbl_resultConnectedDevice.setText(str(printer_count))
            
        except usb.core.USBError as e:
            error_message = f"USB Error: {e}"
            self.logger.error(error_message)  # Log the error
            print(error_message)
            self.lbl_resultConnectedDevice.setText("-1")  # Indicate error

        except Exception as e:
            error_message = f"Error: {e}"
            self.logger.error(error_message)  # Log the error
            print(error_message)
            self.lbl_resultConnectedDevice.setText("-1")  # Indicate error

    def check_logging_enabled(self):
        self.logger.info("Checking if logging is enabled...")

        try:
            # Load the JSON file
            with open(self.config_path, 'r') as file:
                config = json.load(file)

            # Check if 'logging' key exists
            if 'logging' not in config:
                error_message = "Error: 'logging' key is missing in the configuration file."
                self.logger.error(error_message)  # Log the error
                return error_message

            # Check if 'logging' value is a boolean
            if isinstance(config['logging'], bool):
                if config['logging']:
                    self.lbl_loggingResult.setText("✅️")
                    self.btn_checkLogging.setText("Enabled")
                    self.logger.info("Logging is enabled.")
                else:
                    self.lbl_loggingResult.setText("❌")
                    self.btn_checkLogging.setText("Disabled")
                    self.logger.info("Logging is disabled.")
            else:
                error_message = "Error: 'logging' key must be a boolean (true or false)."
                self.logger.error(error_message)  # Log the error
                return error_message

        except FileNotFoundError:
            error_message = f"Error: Configuration file not found at {self.config_path}."
            self.logger.error(error_message)  # Log the error
            return error_message
        except json.JSONDecodeError:
            error_message = "Error: Configuration file is not a valid JSON."
            self.logger.error(error_message)  # Log the error
            return error_message
        
    def reload_tableview(self):
        self.logger.info("Reloading table view with configuration data.")

        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

                # Update UI elements with the configuration values
                self.et_enterToSearch.setText(str(config["enterToSearch"]))
                self.et_itemCount.setText(config['itemCount'])

                self.logger.info("Table view reloaded successfully with config data.")

        except FileNotFoundError:
            error_message = f"Configuration file not found at {self.config_path}"
            self.logger.error(error_message)  # Log the error
            QMessageBox.critical(self, 'Config Error', error_message)

        except json.JSONDecodeError:
            error_message = "Error parsing the configuration file."
            self.logger.error(error_message)  # Log the error
            QMessageBox.critical(self, 'Config Error', error_message)

        except KeyError as e:
            error_message = f"Missing key in configuration file: {e}"
            self.logger.error(error_message)  # Log the error
            QMessageBox.critical(self, 'Config Error', error_message)

    def reload_current_printer_info(self):
        self.logger.info("Reloading current printer information from the configuration file.")

        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

                # Update UI elements with the configuration values for printer VID and PID
                self.et_printerVid.setText(config["vid"])
                self.et_printerPid.setText(config['pid'])

                self.logger.info("Printer information reloaded successfully: VID and PID set in UI.")

        except FileNotFoundError:
            error_message = f"Configuration file not found at {self.config_path}"
            self.logger.error(error_message)  # Log the error
            QMessageBox.critical(self, 'Config Error', error_message)

        except json.JSONDecodeError:
            error_message = "Error parsing the configuration file."
            self.logger.error(error_message)  # Log the error
            QMessageBox.critical(self, 'Config Error', error_message)

        except KeyError as e:
            error_message = f"Missing key in configuration file: {e}"
            self.logger.error(error_message)  # Log the error
            QMessageBox.critical(self, 'Config Error', error_message)
    
    def load_data(self):
        self.logger.info("Loading data... Starting to perform various checks and reload UI components.")

        try:
            # Count connected printers
            self.logger.info("Counting connected printers...")
            self.count_connected_printers()

            # Check network connectivity
            self.logger.info("Checking network connectivity...")
            self.is_connected()

            # Check database connection
            self.logger.info("Checking database connectivity...")
            self.can_connect_to_database()

            # Check configuration file
            self.logger.info("Checking configuration file...")
            self.check_config_file()

            # Check if logging is enabled
            self.logger.info("Checking if logging is enabled...")
            self.check_logging_enabled()

            # Reload the table view data
            self.logger.info("Reloading table view...")
            self.reload_tableview()

            # Reload current printer information
            self.logger.info("Reloading current printer information...")
            self.reload_current_printer_info()

            self.logger.info("Data loading process completed successfully.")

        except Exception as e:
            self.logger.error(f"Error occurred during data loading: {e}")
            QMessageBox.critical(self, 'Error', f"An error occurred while loading data: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DashboardWindow()
    window.show()
    sys.exit(app.exec_())