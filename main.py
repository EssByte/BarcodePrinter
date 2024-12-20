import os
import re
import sys
import pyodbc
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox, QGridLayout, QHBoxLayout, QAction, QMainWindow
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QFileSystemWatcher, QTimer
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtGui import QIcon, QBrush, QColor
import usb
import usb.core
import usb.util
import usb.backend.libusb1
import requests
import json
from bisect import bisect_left
from check_password import PasswordCheck
from dashboard import DashboardWindow
from modules import Configurations
from modules.logger_config import setup_logger
from modules.SendCommand import SendCommand
from version import __version__
import subprocess


class FilterItemsBinaryThread(QThread):
    items_filtered = pyqtSignal(list)  # Signal to emit filtered items

    def __init__(self, all_items, search_text, sort_by='barcode'):
        super().__init__()
        self.all_items = all_items
        self.search_text = search_text.lower()
        self.sort_by = sort_by

    def binary_search(self, items, target: str):
        """Perform binary search for the target on pre-sorted items."""
        if self.sort_by == 'description':
            item_codes = [str(item[1]).lower() for item in items]
        elif self.sort_by == 'barcode':
            item_codes = [str(item[4]).lower() for item in items]

        index = bisect_left(item_codes, target)

        if index < len(item_codes) and item_codes[index] == target:
            return [items[index]]  # Return found item as a single-item list for uniform display
        return []

    def run(self):
        # Sort items before binary search
        if self.sort_by == "description":
            sorted_items = sorted(self.all_items, key=lambda x: x[1].lower())
        elif self.sort_by == 'barcode':
            sorted_items = sorted(self.all_items, key=lambda x: x[4].lower())

        # Apply binary search if there is search text; otherwise return all items
        if self.search_text:
            filtered_items = self.binary_search(sorted_items, self.search_text)
        else:
            filtered_items = sorted_items

        # Emit the filtered items
        self.items_filtered.emit(filtered_items)

class FetchItemsThread(QThread):
    items_fetched = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, connection, location):
        super().__init__()
        self.connection = connection
        self.location = location

    def run(self):
        try:
            cursor = self.connection.cursor()
            query = f"""
            WITH BaseItems AS (
                SELECT
                    u.ItemCode,
                    i.Description,
                    u.Price AS DefaultUnitPrice,
                    u.Cost,
                    ISNULL(NULLIF(u.BarCode, ''), i.ItemCode) as Barcode,
                    ISNULL(p.Location, 'HQ') as Location,
                    ISNULL(p.Price, u.Price) AS PosUnitPrice
                FROM dbo.ItemUOM u
                LEFT JOIN dbo.Item i ON u.ItemCode = i.ItemCode
                LEFT JOIN dbo.PosPricePlan p ON u.ItemCode = p.ItemCode AND p.Location = '{self.location}'
            )
            SELECT * FROM BaseItems;
            """
            cursor.execute(query)
            items = cursor.fetchall()
            # Sort items (assuming index 4 is the barcode or description for sorting)
            self.items_fetched.emit(items)  # Emit sorted items
        except pyodbc.Error as e:
            self.error_occurred.emit("Error fetching items from the database.")  # Emit error message
        except Exception as e:
            self.error_occurred.emit("Unexpected error occurred while fetching items.")
        finally:
            if cursor is not None:
                try:
                    cursor.close()  # Safely close the cursor
                except Exception as e:
                    # Log or handle issues with closing the cursor if needed
                    print(f"Error closing cursor: {e}")

class BarcodeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = setup_logger('BarcodeApp')  # Use a logger specific to the DashboardWindow
        self.logger.info("Initializing BarcodeApp...")
        self.initUI()
        self.config_path = r'C:\barcode\barcode.json'
        self.input_timer = QTimer()
        self.input_timer.setSingleShot(True)
        self.input_timer.timeout.connect(self.filter_items_binary)
        self.file_watcher = QFileSystemWatcher()
        self.file_watcher.addPath(self.config_path)
        self.file_watcher.fileChanged.connect(self.handle_config_change)
        self.load_config()
        self.backend = usb.backend.libusb1.get_backend(find_library=self.resource_path('libusb-1.0.ddl'))
        self.setWindowIcon(QIcon(self.resource_path(("images/logo.ico"))))
        self.db_connected = False
        self.connection = None
        self.warning_shown = False
        self.connect_to_database()
        self.loadStylesheet()
        self.showMaximized()
        self.fetch_items_thread = None
        self.items = []

        # Start fetching items on a separate thread
        self.start_fetch_items()

    def update_logging(self):
        """ This method will update logging based on the config setting """
        self.logger = setup_logger('BarcodeApp')  # Reinitialize the logger
        self.logger.info("Logging configuration updated.")
    
    def start_timer(self):
        self.input_timer.start(400)

    def handle_config_change(self):
        """
        Handle changes in the JSON config file.
        """
        self.logger.info("Configuration file changed. Reloading...")

        try:
            self.update_logging()
            self.logger.info("Attempting to reload configuration...")
            self.load_config()  # Reload configuration
            self.logger.info("Checking for updates...")
            self.check_version()

            if self.db_connected:
                self.logger.info("Closing existing database connection...")
                self.connection.close()

            self.logger.info("Reconnecting to the database...")
            self.connect_to_database()  # Reconnect to the database

            self.logger.info("Refreshing items after config reload...")
            self.start_fetch_items()  # Refresh items

            self.logger.info("Configuration reloaded and items refreshed successfully.")

        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")
            QMessageBox.critical(self, 'Error', f"Failed to reload configuration: {e}")
    
    def load_config(self):
        self.logger.info("Attempting to load configuration...")

        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.logger.info("Configuration file loaded successfully.")

                # Log the loaded values (or specific values you're interested in)
                self.logger.debug(f"Server: {config['server']}, Database: {config['database']}")
                self.logger.debug(f"Username: {config['username']}, IP Address: {config['ip_address']}")

                self.server = config['server']
                self.database = config['database']
                self.username = config['username']
                self.password = config['password']
                self.vid = int(config['vid'], 16)
                self.pid = int(config['pid'], 16)
                self.endpoint = int(config['endpoint'], 16)
                self.companyName = config['companyName']
                self.location = config.get('location') 
                self.useZPL: bool = config['useZPL']
                self.zpl_template: str = config['zplTemplate']
                self.tpsl_template: str = config['tpslTemplate']
                self.ip_address: str = config['ip_address']
                self.wireless_mode: bool = config['wireless_mode']

                self.logger.info("Configuration values loaded into instance variables.")

        except FileNotFoundError:
            self.logger.error(f"Configuration file not found at {self.config_path}")
            QMessageBox.critical(self, 'Config Error', f'Configuration file not found at {self.config_path}')
            
        except json.JSONDecodeError:
            self.logger.error("Error parsing the configuration file.")
            QMessageBox.critical(self, 'Config Error', 'Error parsing the configuration file.')
            
        except KeyError as e:
            self.logger.error(f"Missing key in configuration file: {e}")
            QMessageBox.critical(self, 'Config Error', f'Missing key in configuration file: {e}')


    def resource_path(self, relative_path):
        #Get absolute path to resource, works for dev and for PyInstaller
        self.logger.info(f"Attempting to resolve resource path for: {relative_path}")

        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
            self.logger.debug(f"PyInstaller environment detected. Using base path: {base_path}")
        except Exception as e:
            # Fall back to the current working directory in development mode
            base_path = os.path.abspath(".")
            self.logger.debug(f"Development mode detected. Base path resolved to: {base_path}")
            self.logger.exception(f"Unexpected error while checking PyInstaller path: {e}")

        # Construct the absolute path to the resource
        absolute_path = os.path.join(base_path, relative_path)
        self.logger.debug(f"Resolved absolute path: {absolute_path}")

        return absolute_path
    
    def runUpdater(self):
        subprocess.Popen([r"C:\barcode\Updater.exe"])
        self.close()

    def initUI(self):
        # Initialize logger for UI actions
        self.logger.info("Initializing the UI components.")

        # Set the window properties
        self.setWindowTitle('Barcode Printer')
        self.setGeometry(200, 200, 1400, 600)
        self.setWindowIcon(QIcon(self.resource_path("logo.ico")))

        self.logger.debug("Window title and geometry set.")

        # Create a central widget to hold the main layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)  # Set central widget

        # Main layout for the widget
        grid_layout = QGridLayout(central_widget)

        # === Menu Bar Section ===
        menu_bar = self.menuBar()  # Use QMainWindow's menuBar method

        self.logger.debug("Menu bar created.")

        # Dashboard menu action
        dashboard_menu = menu_bar.addMenu("Dashboard")
        dashboard_action = QAction("Open Dashboard", self)
        dashboard_action.triggered.connect(self.open_dashboard)
        dashboard_menu.addAction(dashboard_action)
        self.logger.debug("Dashboard menu and action added.")

        # Settings menu action
        file_menu = menu_bar.addMenu('Settings')
        settings_action = QAction('Open Settings', self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        self.logger.debug("Settings menu and action added.")

        # === Search Bar Section ===
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.item_code_input = QLineEdit(self)
        self.item_code_input.setPlaceholderText('Enter Item Code')
        self.item_code_input.textChanged.connect(self.start_timer)
        self.item_code_input.returnPressed.connect(self.filter_items)

        # Search button
        self.search_by_description = QPushButton("Search", self)
        self.search_by_description.setCursor(Qt.PointingHandCursor)
        self.search_by_description.setStyleSheet("""
        QPushButton {
            background: qlineargradient(spread:pad, x1:0.148, y1:1, x2:1, y2:1, stop:0.233503 rgba(53, 132, 228, 255), stop:1 rgba(26, 95, 180, 255));
            color: white;
            border-top-left-radius: 8px;
            border-bottom-right-radius: 8px;
            font-style: italic;
            font-weight: bold;
            qproperty-cursor: pointingHandCursor;
        }
        QPushButton:hover {
            background: white;
            border: 2px solid rgb(53, 132, 228);
            color: black;
        }
        """)
        self.search_by_description.clicked.connect(self.filter_items)

        # Add widgets to the search layout
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.item_code_input)
        search_layout.addWidget(self.search_by_description)

        # Add search layout to the grid layout
        grid_layout.addLayout(search_layout, 0, 0, 1, 3)

        self.logger.debug("Search bar section initialized.")

        # === Item Table Section ===
        self.item_table = QTableWidget(self)
        self.item_table.setColumnCount(9)
        self.item_table.setHorizontalHeaderLabels([
            "Select", "Item Code", "Description", "Unit Price", "Unit Cost",
            "Barcode", "Location", "Location Price", "Number of Copies"
        ])
        self.item_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.item_table.setSelectionMode(QTableWidget.NoSelection)

        # Add table to the grid layout
        grid_layout.addWidget(self.item_table, 1, 0, 1, 3)
        self.logger.debug("Item table added to layout.")

        # === Buttons Section ===
        print_layout = QHBoxLayout()

        # Print Button
        self.print_button = QPushButton('Print Barcode', self)
        self.print_button.setStyleSheet("""
        QPushButton {
            background: white;
            border: 2px solid rgb(53, 132, 228);
            color: black;
            border-top-left-radius: 8px;
            border-bottom-right-radius: 8px;
            font-style: italic;
            font-weight: bold;
            qproperty-cursor: pointingHandCursor;
        }
        QPushButton:hover {
            background: qlineargradient(spread:pad, x1:0.148, y1:1, x2:1, y2:1, stop:0.233503 rgba(53, 132, 228, 255), stop:1 rgba(26, 95, 180, 255));
            color: white;
        }
        """)
        self.reload_button = QPushButton('Reload Database', self)
        self.reload_button.setStyleSheet("""
        QPushButton {
            background: white;
            border: 2px solid rgb(53, 132, 228);
            color: black;
            border-top-left-radius: 8px;
            border-bottom-right-radius: 8px;
            font-style: italic;
            font-weight: bold;
            qproperty-cursor: pointingHandCursor;
        }
        QPushButton:hover {
            background: qlineargradient(spread:pad, x1:0.148, y1:1, x2:1, y2:1, stop:0.233503 rgba(53, 132, 228, 255), stop:1 rgba(26, 95, 180, 255));
            color: white;
        }
        """)
        self.print_button.setCursor(Qt.PointingHandCursor)
        self.reload_button.setCursor(Qt.PointingHandCursor)
        self.print_button.clicked.connect(self.print_barcode)
        self.reload_button.clicked.connect(self.handle_config_change)

        # Add the print and reload buttons to the layout, centered
        print_layout.addStretch(1)
        print_layout.addWidget(self.reload_button)
        print_layout.addWidget(self.print_button)

        # Create a new layout for the "Update Database" button to align it to the right
        update_layout = QHBoxLayout()
        self.update_button = QPushButton('Update', self)
        self.update_button.setStyleSheet("""
        QPushButton {
            background: white;
            border: 2px solid rgb(53, 132, 228);
            color: black;
            border-top-left-radius: 8px;
            border-bottom-right-radius: 8px;
            font-style: italic;
            font-weight: bold;
            qproperty-cursor: pointingHandCursor;
        }
        QPushButton:hover {
            background: qlineargradient(spread:pad, x1:0.148, y1:1, x2:1, y2:1, stop:0.233503 rgba(53, 132, 228, 255), stop:1 rgba(26, 95, 180, 255));
            color: white;
        }
        """)
        self.update_button.setCursor(Qt.PointingHandCursor)
        self.check_version()
        self.update_button.clicked.connect(self.runUpdater)

        # Add the update button to the new layout and align it to the right
        update_layout.addWidget(self.update_button)

        # Add both the centered buttons and the right-aligned update button to the grid layout
       # Add print_layout to the grid, aligning it to the right
        grid_layout.addLayout(print_layout, 2, 1, 1, 1, alignment=Qt.AlignRight)  # Right-aligned print button

        # Add update_layout to the grid, aligning it to the left
        grid_layout.addLayout(update_layout, 2, 0, 2, 1, alignment=Qt.AlignLeft)  # Left-aligned update button


        self.logger.debug("Print and reload buttons section initialized.")
        self.logger.debug("Update button section initialized.")

        # Final log for UI initialization complete
        self.logger.info("UI components initialization complete.")

    def check_version(self):

        self.repo_owner = "PersonX-46"
        self.repo_name = "BarcodePrinter"
        self.download_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/releases/latest/download/BarcodePrinter.exe"
        self.api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
        try:
            self.logger.info("Fetching version details from GitHub...")
            response = requests.get(self.api_url)
            response.raise_for_status()

            release_data = response.json()
            self.logger.info("Fetched version details from GitHub...")
            tag_name = release_data["tag_name"]
            if tag_name > __version__:
                self.update_button.setVisible(True)
                self.logger.info("Update Available, update button is visible")
            else:   
                self.update_button.setVisible(False)
                self.logger.info("Update is not available, update button is not visible")

        except requests.RequestException as e:
            error_message = f"Failed to fetch version details:\n{e}"
            self.logger.error(error_message)
            QMessageBox.critical(self, "Version Check Error", error_message)

    def loadStylesheet(self):
        try:
            # Define the stylesheet for the application
            stylesheet = """
            QLabel { font-size: 20px; font-weight: bold; }
            QLineEdit { font-size: 18px; padding: 8px; border: 2px solid rgb(53, 132, 228);border-radius: 10px; }
            QTableWidget { font-size: 16px; padding: 4px; border: 1px solid black; border-radius: 12px; }
            QPushButton { padding: 10px 20px; font-size: 20px; margin: 10px; }
            QPushButton:hover { background-color: rgb(0, 106, 255); }
            QPushButton:pressed { background-color: #000099; }
            QHeaderView::section { font-size: 16px; font-weight: bold; padding: 10px; }
            """
            
            # Applying the stylesheet to the application
            self.setStyleSheet(stylesheet)
            
            # Log successful application of the stylesheet
            self.logger.info("Stylesheet applied successfully.")
        except Exception as e:
            # Log if there was an error while applying the stylesheet
            self.logger.error(f"Failed to apply stylesheet: {e}")
            QMessageBox.critical(self, 'Stylesheet Error', f"Failed to apply stylesheet: {e}")

    def connect_to_database(self):
        try:
            # Log the attempt to connect to the database
            self.logger.info("Attempting to connect to the database.")
            
            # Try to establish the connection
            self.connection = pyodbc.connect(
                f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password}'
            )
            
            # Check if the connection was successful
            if self.connection:
                self.db_connected = True
                self.logger.info("Successfully connected to the database.")
                print('Success: Connected to Database')
        except pyodbc.Error as e:
            # Log the error if the connection fails
            self.logger.error(f"Error connecting to the database: {e}")
            print(f"Error connecting to database: {e}")

    def replace_placeholders(self, template, **kwargs):
        def replace(match):
            key = match.group(1)
            if key not in kwargs:
                self.logger.warning(f"Missing placeholder for: {key}")
                return f"{{{{{key}}}}}"  # Or raise an exception if needed
            return str(kwargs[key])
        return re.sub(r'{{(.*?)}}', replace, template)

    def start_fetch_items(self):
        if not self.db_connected:
            self.logger.error('Database is not connected. Items will not be shown.')
            QMessageBox.critical(self, 'Database Error', 'Database is not connected. Items will not be shown.')
            return

        self.logger.info(f"Fetching items for location: {self.location}")
        
        self.fetch_items_thread = FetchItemsThread(self.connection, self.location)
        self.fetch_items_thread.items_fetched.connect(self.handle_items_fetched)
        self.fetch_items_thread.start()

    def handle_items_fetched(self, items):
        if items:
            # Log the number of items fetched
            self.logger.info(f"Fetched {len(items)} items.")
            
            # Sort the items by the 5th element (index 4), assuming it's a barcode or description
            self.items = items
            self.all_items = sorted(self.items, key=lambda x: x[4].lower())

            
            # Display the items (you can call your display logic here)
            self.display_items(self.all_items)
            
            # Optionally, update UI elements like the item count or display a success message
            self.logger.info("Items successfully displayed.")
        else:
            # Handle the case when no items were fetched
            self.logger.warning("No items fetched from the database.")
            QMessageBox.warning(self, "No items", "No items were fetched from the database.")

    def open_settings(self):
        try:
            self.logger.info("Attempting to open the Settings window.")
            self.settings_window = PasswordCheck()  # Create instance of Settings window
            self.settings_window.show()  # Show the window
            self.logger.info("Settings window opened successfully.")
        except Exception as e:
            # Log any errors that occur while opening the Settings window
            self.logger.error(f"Error opening the Settings window: {e}")
            QMessageBox.critical(self, 'Error', f"Failed to open Settings window: {e}")

    def open_dashboard(self):
        try:
            self.logger.info("Attempting to open the Dashboard window.")
            self.dashboard_window = DashboardWindow()  # Create instance of Dashboard window
            self.dashboard_window.show()  # Show the window
            self.logger.info("Dashboard window opened successfully.")
        except Exception as e:
            # Log any errors that occur while opening the Dashboard window
            self.logger.error(f"Error opening the Dashboard window: {e}")
            QMessageBox.critical(self, 'Error', f"Failed to open Dashboard window: {e}")
    
    def display_items(self, items):
        try:
            self.logger.info(f"Displaying {len(items[:100])} items.")

            self.item_table.setRowCount(len(items[:100]))

            # Set column resize modes for headers
            self.item_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Select column
            self.item_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)           # Item Code
            self.item_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)           # Description
            self.item_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Unit Price
            self.item_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Unit Cost
            self.item_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)           # Barcode
            self.item_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Location

            # Manually adjust column widths after applying resize modes for more control
            self.item_table.setColumnWidth(0, 50)   # Select column, smallest
            self.item_table.setColumnWidth(1, 150)  # Item Code column, medium
            self.item_table.setColumnWidth(2, 300)  # Description column, largest
            self.item_table.setColumnWidth(3, 100)  # Unit Price column
            self.item_table.setColumnWidth(4, 150)  # Unit Cost column
            self.item_table.setColumnWidth(5, 100)  # Barcode column, adjusted for consistency
            self.item_table.setColumnWidth(6, 100)  # Location column

            barcode_config = Configurations.BarcodeConfig()

            # Add rows of items to the table
            for row_number, item in enumerate(items[:100]):
                checkbox_item = QTableWidgetItem()
                checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox_item.setCheckState(Qt.Unchecked)
                self.item_table.setItem(row_number, 0, checkbox_item)
                self.item_table.item(row_number, 0).setTextAlignment(Qt.AlignLeft)

                # Extract item details
                item_code, description, unit_price, unit_cost, barcode, location, location_price = item
                barcode_value = item_code if barcode is None else barcode  # Fallback to item_code if barcode is None

                try:
                    # Format currency values
                    formatted_unit_price = f"RM {float(unit_price):.2f}" if unit_price is not None else "RM 0.00"
                    if not barcode_config.get_hide_cost():
                        formatted_unit_cost = f"RM {float(unit_cost):.2f}" if unit_cost is not None else "RM 0.00"
                    if barcode_config.get_hide_cost():
                        formatted_unit_cost = '***'
                    formatted_location_price = f"RM {float(location_price):.2f}" if location_price is not None else "RM 0.00"
                except ValueError as e:
                    formatted_unit_price = "RM 0.00"
                    self.logger.warning(f"ValueError while formatting price values: {e}")

                # Set the data for each row
                for col_number, value in enumerate([item_code, description, formatted_unit_price, formatted_unit_cost, barcode_value, location, formatted_location_price], start=1):
                    table_item = QTableWidgetItem(str(value))
                    table_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    table_item.setTextAlignment(Qt.AlignCenter)
                    self.item_table.setItem(row_number, col_number, table_item)

                # Add copies column (editable)
                copies_item = QTableWidgetItem("1")
                copies_item.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled)
                copies_item.setTextAlignment(Qt.AlignCenter)
                self.item_table.setItem(row_number, 8, copies_item)

                # Set background color for every even row (index 0, 2, 4, etc.)
                if row_number % 2 == 0:
                    for col_number in range(self.item_table.columnCount()):
                        item = self.item_table.item(row_number, col_number)
                        item.setBackground(QBrush(QColor(230, 238, 255)))  # Set light gray background color for even rows

            # Adjust column sizes after filling in data
            self.item_table.resizeColumnsToContents()

            # Add padding to each column
            padding = 20
            for column in range(self.item_table.columnCount()):
                current_width = self.item_table.columnWidth(column)
                self.item_table.setColumnWidth(column, current_width + padding)

            self.logger.info("Finished displaying items.")
        
        except Exception as e:
            self.logger.error(f"Error displaying items: {e}")
            QMessageBox.critical(self, 'Error', f"Error displaying items: {e}")


    def start_filter_items_thread(self):
        try:
            # Ensure database is connected
            if not self.db_connected or not hasattr(self, 'all_items'):
                if not self.warning_shown:
                    QMessageBox.warning(self, 'Database Error', 'Database is not connected. Searched items will not be shown.')
                    self.warning_shown = True
                self.logger.warning("Database is not connected or 'all_items' is not available.")
                return

            # Get the current text and selected sortBy option
            search_text = self.item_code_input.text().strip().lower()
            sort_by = 'barcode'

            self.logger.info(f"Starting filter for items with search text: {search_text}, sorted by: {sort_by}")

            # Terminate any running thread to prevent overlap
            if hasattr(self, 'filter_items_thread') and self.filter_items_thread.isRunning():
                self.logger.info("Terminating any running filter thread.")
                self.filter_items_thread.terminate()

            # Start a new thread for filtering items
            self.filter_items_thread = FilterItemsBinaryThread(self.all_items, search_text, sort_by)
            self.filter_items_thread.items_filtered.connect(self.display_items)
            self.filter_items_thread.start()

            self.logger.info("Started new filter thread for items.")
        
        except Exception as e:
            self.logger.error(f"Error in start_filter_items_thread: {e}")
            QMessageBox.critical(self, 'Error', f"Error filtering items: {e}")

    def binary_search(self, items, target: str):
        try:
            # Prepare item codes for search
            item_codes = [str(item[4]).lower() for item in items]
            self.logger.info(f"Performing binary search for target: '{target}'")

            # Perform binary search
            index = bisect_left(item_codes, target.lower())
            self.logger.debug(f"Binary search index found: {index}")

            # Check if the target is found
            if index < len(item_codes) and item_codes[index] == target.lower():
                self.logger.info(f"Item found at index {index}: {items[index]}")
                return items[index]

            # If not found
            self.logger.info(f"Item '{target}' not found.")
            return None
        except Exception as e:
            self.logger.error(f"Error during binary search: {e}")
            return None

    def filter_items_binary(self):
        if not self.db_connected or not hasattr(self, 'all_items'):
            if not self.warning_shown:
                QMessageBox.warning(self, 'Database Error', 'Database is not connected. Searched items will not be shown.')
                self.warning_shown = True
            return  

        search_text = self.item_code_input.text().strip().lower()
        
        # Log search query
        self.logger.info(f"Searching for items with code: {search_text}")

        if not search_text:
            self.logger.info("No search text provided, displaying first 100 items.")
            self.display_items(self.all_items[:100])
            return

        # Perform binary search for the item
        found_item = self.binary_search(self.all_items, search_text)
        
        if found_item:
            self.logger.info(f"Item found: {found_item}")
            self.display_items([found_item])
        else:
            self.logger.warning(f"No items found for search text: {search_text}")
            self.display_items([])
            # Uncomment to display a message box if no item is found
            #QMessageBox.information(self, "Item Not Found", 'No items match the search criteria!')

    def filter_items(self):
        if not self.db_connected or not hasattr(self, 'all_items'):
            if not self.warning_shown:
                QMessageBox.warning(self, 'Database Error', 'Database is not connected. Searched items will not be shown.')
                self.warning_shown = True
            return

        search_text = self.item_code_input.text().strip().lower()
        
        # Log the search text being processed
        self.logger.info(f"Filtering items with search text: {search_text}")

        # Extract keywords by splitting the search text
        keywords = search_text.split()
        
        # Log the keywords
        self.logger.info(f"Keywords extracted: {keywords}")

        # Filter items by checking if both ItemCode and Description contain each keyword
        filtered_items = [
            item for item in self.all_items
            if all(
                keyword in item[1].lower()  # Ensure the keyword is in the description (item[1])
                for keyword in keywords
            )
        ]
        
        # Log the number of filtered items
        self.logger.info(f"Found {len(filtered_items)} items matching the search criteria.")
        
        # Display the filtered items
        self.display_items(filtered_items)

    def print_barcode(self):
        selected_rows = []
        barcode_config = Configurations.BarcodeConfig()
        send_command = SendCommand()
        for row in range(self.item_table.rowCount()):
            if self.item_table.item(row, 0).checkState() == Qt.Checked:
                selected_rows.append(row)

        if not selected_rows:
            self.logger.warning("No items selected for printing.")
            QMessageBox.warning(self, 'Selection Error', 'No items selected for printing.')
            return

        printer = None  # Ensure we initialize the printer variable
        try:
            self.logger.info("USB mode selected. Checking printer connection...")

            if barcode_config.get_use_generic_driver():
                printer = usb.core.find(idVendor=self.vid, idProduct=self.pid, backend=self.backend)

                if printer is None:
                    self.logger.error(f"Printer not found (Vendor ID: {self.vid}, Product ID: {self.pid}).")
                    QMessageBox.warning(self, 'Printer Error', 'Printer not found. Check your device and USB permissions.')
                    return

                try:
                    printer.set_configuration()
                    self.logger.info("Printer connected via USB.")
                except usb.core.USBError as e:
                    self.logger.error(f"Failed to configure USB printer: {e}")
                    QMessageBox.warning(self, 'Printer Error', f"Failed to configure USB printer: {e}")
                    return

            else:
                self.logger.info("Wireless mode selected. Validating IP and port...")
                try:
                    ip, port = self.ip_address.split(":")
                except ValueError as e:
                    self.logger.error(f"Invalid IP or port: {e}")
                    QMessageBox.warning(self, 'Printer Error', f"Invalid IP or port: {e}")
                    return

            # Process selected items
            for row in selected_rows:
                description = self.item_table.item(row, 2).text()
                unit_price_integer = self.item_table.item(row, 7).text()
                barcode_value = self.item_table.item(row, 5).text() or self.item_table.item(row, 5).text()
                copies = self.item_table.item(row, 8).text()

                self.logger.info(f"Preparing to print item: {description} (Barcode: {barcode_value})")
            
                printer_clear = ""
                print_data = ""
                if not self.useZPL:
                    printer_clear = "CLS"
                    print_data = self.replace_placeholders(
                        self.tpsl_template,
                        companyName=self.companyName,
                        description=description,
                        barcode_value=barcode_value,
                        unit_price_integer=unit_price_integer,
                        copies=copies,
                    )
                else:
                    printer_clear = "^XA^CLS^XZ"
                    print_data = self.replace_placeholders(
                        self.zpl_template,
                        companyName=self.companyName,
                        description=description,
                        barcode_value=barcode_value,
                        unit_price_integer=unit_price_integer,
                        copies=copies,
                    )

                if barcode_config.get_use_generic_driver():
                    if printer is not None:
                        printer.write(self.endpoint, print_data.encode('utf-8'))
                        self.logger.info(f"Barcode print command sent successfully for item: {barcode_value}")
                    else:
                        self.logger.error("Printer is not available.")
                elif barcode_config.get_wireless_mode():
                    send_command.send_wireless_command(ip_address=ip, port=port, command=printer_clear)
                    send_command.send_wireless_command(ip_address=ip, port=port, command=print_data)
                    self.logger.info(f"Wireless print command sent to {ip}:{port} for item: {barcode_value}")
                elif not barcode_config.get_use_generic_driver():
                    send_command.send_win32print(barcode_config.get_printer_name(), printer_clear)
                    send_command.send_win32print(barcode_config.get_printer_name(), print_data)

        except usb.core.USBError as e:
            self.logger.error(f"USB Error: {e}")
            QMessageBox.information(self, 'Error', f'{e}')
        except ValueError as e:
            self.logger.error(f"Value Error: {e}")
            QMessageBox.information(self, 'Error', f'{e}')
        finally:
            # Show success message once after all items are printed
            if not self.wireless_mode and barcode_config.get_use_generic_driver():
                self.logger.info('All selected items have been successfully sent to the printer (USB).')
                QMessageBox.information(self, 'Success', 'All selected items have been successfully sent to the printer!')
                usb.util.dispose_resources(printer)

            elif not self.wireless_mode and not barcode_config.get_use_generic_driver():
                self.logger.info('All selected items have been successfully sent to the printer (win32print).')
                QMessageBox.information(self, 'Success', 'All selected items have been successfully sent to the printer!')

            else:
                self.logger.info('All selected items have been successfully sent to the printer (wireless).')
                QMessageBox.information(self, 'Success', 'All selected items have been successfully sent to the printer!')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BarcodeApp()
    window.showMaximized()
    sys.exit(app.exec_())