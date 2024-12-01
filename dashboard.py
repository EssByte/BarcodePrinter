import sys
from PyQt5.QtCore import QTimer, QDateTime
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5 import QtWidgets, uic
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
        
        self.logger = setup_logger('DashboardLogger')  # Use a logger specific to the DashboardWindow
        self.logger.info("Initializing DashboardWindow...")
        self.backend = usb.backend.libusb1.get_backend(find_library=self.resource_path('libusb-1.0.ddl'))
        self.config_path = r'C:\barcode\barcode.json'
        # Load the UI file first
        uic.loadUi(self.resource_path("ui/dashboard.ui"), self)
        self.setWindowIcon(QIcon(self.resource_path("images/logo.ico")))
        self.setWindowTitle("Dashboard")
        self.setFixedSize(1212, 760)

        # Alternatively, set the maximum size equal to the minimum size to prevent maximizing
        self.setMaximumSize(1212, 760)
        self.setMinimumSize(1212, 760)

        background = QPixmap(self.resource_path("images/background.jpg"))

        #Initialize widgets
        self.lbl_bg = self.findChild(QtWidgets.QLabel, "lbl_background")
        self.lbl_bg.setPixmap(background)
        self.lbl_dashboardIcon = self.findChild(QtWidgets.QLabel, "dashboard_icon")
        self.lbl_dashboardIcon.setPixmap(QPixmap(self.resource_path("images/dashboard.png")))
        self.lbl_resultConnectedDevice = self.findChild(QtWidgets.QLabel, "lbl_connectedDevicesResult")
        self.lbl_resultConnectivity = self.findChild(QtWidgets.QLabel, "lbl_connectivityResult")
        self.lbl_resultDatabase = self.findChild(QtWidgets.QLabel, "lbl_databaseResult")
        self.lbl_resultConfiguration = self.findChild(QtWidgets.QLabel, "lbl_configurationFileResult")
        self.lbl_loggingResult = self.findChild(QtWidgets.QLabel, "lbl_loggingResult")
        self.lbl_datetime = self.findChild(QtWidgets.QLabel, "lbl_datetime")
        self.lbl_version = self.findChild(QtWidgets.QLabel, "lbl_version")
        self.lbl_version.setText(f"Version {__version__}")
        self.btn_checkConnectedDevices = self.findChild(QtWidgets.QPushButton, "btn_checkConnectedDevices")
        self.btn_checkConnectedDevices.clicked.connect(self.count_connected_printers)
        self.btn_ping = self.findChild(QtWidgets.QPushButton, "btn_ping")
        self.btn_ping.clicked.connect(self.is_connected)
        self.btn_reloadDatabase = self.findChild(QtWidgets.QPushButton, "btn_reloadDatabase")
        self.btn_reloadDatabase.clicked.connect(self.can_connect_to_database)
        self.btn_checkConfiguration = self.findChild(QtWidgets.QPushButton, "btn_checkConfiguration")
        self.btn_checkConfiguration.clicked.connect(self.check_config_file)
        self.btn_checkLogging = self.findChild(QtWidgets.QPushButton, "btn_checkLogging")
        self.btn_checkLogging.clicked.connect(self.check_logging_enabled)
        self.btn_reloadTableView = self.findChild(QtWidgets.QPushButton, "btn_reloadTableView")
        self.btn_reloadTableView.clicked.connect(self.reload_tableview)
        self.btn_reloadPrinterInformation = self.findChild(QtWidgets.QPushButton, "btn_reloadPrinterInformation")
        self.btn_reloadPrinterInformation.clicked.connect(self.reload_current_printer_info)
        self.et_enterToSearch = self.findChild(QtWidgets.QLineEdit, "et_enterToSearch")
        self.et_itemCount = self.findChild(QtWidgets.QLineEdit, "et_itemCount")
        self.et_printerVid = self.findChild(QtWidgets.QLineEdit, "et_printerVid")
        self.et_printerPid = self.findChild(QtWidgets.QLineEdit, "et_printerPid")
        self.btn_close = self.findChild(QtWidgets.QPushButton, "btn_close")
        self.btn_close.clicked.connect(self.close)
        self.btn_reload = self.findChild(QtWidgets.QPushButton, "btn_reload")
        self.btn_reload.clicked.connect(self.load_data)
        self.btn_about = self.findChild(QtWidgets.QPushButton, "btn_about")

        #Icon section
        self.logo_icon = self.findChild(QtWidgets.QLabel, "lbl_iconLogo")
        logoIcon = QPixmap(self.resource_path("images/logo.jpeg"))
        databaseIcon = QPixmap(self.resource_path("images/database.png"))
        printerIcon = QPixmap(self.resource_path("images/printer.png"))
        otherSettingsIcon = QPixmap(self.resource_path("images/settings.png"))
        loggingIcon = QPixmap(self.resource_path("images/log.png"))
        connectivityIcon = QPixmap(self.resource_path("images/connect.png"))
        tableIcon  = QPixmap(self.resource_path("images/table.png"))
        self.logo_icon.setPixmap(logoIcon)

        self.icon_database = self.findChild(QtWidgets.QLabel, "lbl_iconDatabase")
        self.icon_printer = self.findChild(QtWidgets.QLabel, "lbl_iconPrinter")
        self.icon_other_settings = self.findChild(QtWidgets.QLabel, "lbl_iconOtherSettings")
        self.icon_logging = self.findChild(QtWidgets.QLabel, "lbl_iconLogging")
        self.icon_connectivity = self.findChild(QtWidgets.QLabel, "lbl_iconConnectivity")
        self.icon_table = self.findChild(QtWidgets.QLabel, "lbl_iconTable")
        self.icon_printer2 = self.findChild(QtWidgets.QLabel, "lbl_iconPrinter_2")
        
        self.icon_database.setPixmap(databaseIcon)
        self.icon_printer.setPixmap(printerIcon)
        self.icon_other_settings.setPixmap(otherSettingsIcon)
        self.icon_logging.setPixmap(loggingIcon)
        self.icon_connectivity.setPixmap(connectivityIcon)
        self.icon_table.setPixmap(tableIcon)
        self.icon_printer2.setPixmap(printerIcon)

        self.load_data()

        self.update_datetime()

        # Set up a QTimer to update the datetime every 60 seconds (or as needed)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(60000)  # Update every 60 seconds

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