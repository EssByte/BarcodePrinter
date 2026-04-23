import pyodbc
import sqlite3
import usb.core
import socket
import json
import os
from PyQt5.QtCore import QThread, pyqtSignal
from bisect import bisect_left
from modules.Configurations import BarcodeConfig

class DiagnosticThread(QThread):
    progress = pyqtSignal(str, str) # Result name, value
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, config_path, location, backend):
        super().__init__()
        self.config_path = config_path
        self.location = location
        self.backend = backend

    def run(self):
        try:
            # 1. Connectivity Check
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=3)
                self.progress.emit("lbl_resultConnectivity", "✅")
            except:
                self.progress.emit("lbl_resultConnectivity", "❌")

            # 2. Printer Check
            try:
                devices = usb.core.find(find_all=True, backend=self.backend)
                count = 0
                for dev in devices:
                    if dev.bDeviceClass == 7: count += 1
                    else:
                        for cfg in dev:
                            if any(intf.bInterfaceClass == 7 for intf in cfg):
                                count += 1; break
                self.progress.emit("lbl_resultConnectedDevice", str(count))
            except:
                self.progress.emit("lbl_resultConnectedDevice", "ERR")

            # 3. Config Check
            required = ["server", "database", "username", "password", "vid", "pid", "logging"]
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, 'r') as f:
                        conf = json.load(f)
                        missing = [k for k in required if k not in conf]
                        self.progress.emit("lbl_resultConfiguration", "✅" if not missing else "⚠️")
                        
                        # Background technical updates
                        self.progress.emit("et_printerVid", conf.get("vid", ""))
                        self.progress.emit("et_printerPid", conf.get("pid", ""))
                        self.progress.emit("et_itemCount", str(conf.get("itemCount", "0")))
                except: self.progress.emit("lbl_resultConfiguration", "❌")
            else: self.progress.emit("lbl_resultConfiguration", "❌")

            # 4. Database Check
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, 'r') as f:
                        c = json.load(f)
                        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={c['server']};DATABASE={c['database']};UID={c['username']};PWD={c['password']};"
                        with pyodbc.connect(conn_str, timeout=3) as _:
                            self.progress.emit("lbl_resultDatabase", "✅")
                except: self.progress.emit("lbl_resultDatabase", "❌")

            # 5. Logging Check
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, 'r') as f:
                        c = json.load(f)
                        is_enabled = c.get('logging', False)
                        self.progress.emit("lbl_loggingResult", "✅" if is_enabled else "❌")
                        self.progress.emit("btn_checkLogging", "Enabled" if is_enabled else "Disabled")
                except: pass

            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

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
            # Barcode index is usually 5 (SQL Server) or 0 (SQLite)
            item_codes = [str(item[5]).lower() if len(item) > 5 else str(item[0]).lower() for item in items]
        else:
            item_codes = [str(i).lower() for i in items]

        index = bisect_left(item_codes, target)

        if index < len(item_codes) and item_codes[index] == target:
            return [items[index]]  
        return []

    def run(self):
        # Implementation from main.py
        if self.sort_by == "description":
            sorted_items = sorted(self.all_items, key=lambda x: str(x[1]).lower())
        elif self.sort_by == 'barcode':
            sorted_items = sorted(self.all_items, key=lambda x: str(x[5]).lower() if len(x) > 5 else str(x[0]).lower())
        else:
            sorted_items = self.all_items

        if self.search_text:
            filtered_items = self.binary_search(sorted_items, self.search_text)
        else:
            filtered_items = sorted_items

        self.items_filtered.emit(filtered_items)

class FetchItemsThread(QThread):
    items_fetched = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, location, use_sqlite):
        super().__init__()
        self.config = BarcodeConfig()
        self.location = location
        self.use_sqlite = use_sqlite

    def run(self):
        if not self.use_sqlite:
            # SQL Server (pyodbc)
            connection = None
            cursor = None
            try:
                drv = '{ODBC Driver 17 for SQL Server}'
                c = self.config
                conn_str = f'DRIVER={drv};SERVER={c.get_server()};DATABASE={c.get_database()};UID={c.get_username()};PWD={c.get_password()};'
                if c.get_trusted_connection():
                    conn_str += 'Trusted_Connection=yes;'
                
                connection = pyodbc.connect(conn_str, timeout=5)
                cursor = connection.cursor()
                query = f"""
                WITH BaseItems AS (
                    SELECT
                        u.ItemCode,
                        i.Description AS DescriptionWithUOM,
                        u.UOM,
                        u.Price AS DefaultUnitPrice,
                        u.Cost,
                        ISNULL(NULLIF(u.BarCode, ''), i.ItemCode) AS Barcode,
                        ISNULL(p.Location, 'HQ') AS Location,
                        ISNULL(p.Price, u.Price) AS PosUnitPrice
                    FROM dbo.ItemUOM u
                    LEFT JOIN dbo.Item i ON u.ItemCode = i.ItemCode
                    LEFT JOIN dbo.PosPricePlan p ON u.ItemCode = p.ItemCode AND p.Location = '{self.location}'
                )
                SELECT * FROM BaseItems;
                """
                cursor.execute(query)
                items = cursor.fetchall()
                self.items_fetched.emit(items)
            except Exception as e:
                self.error_occurred.emit(f"SQL Error: {e}")
            finally:
                if cursor: cursor.close()
                if connection: connection.close()
        else:
            # SQLite
            connection = None
            cursor = None
            try:
                db_path = self.config.get_sqlPath()
                connection = sqlite3.connect(db_path)
                cursor = connection.cursor()
                query = "SELECT barCode, name, price FROM Tbl_Plu;"
                cursor.execute(query)
                items = cursor.fetchall()
                self.items_fetched.emit(items)
            except Exception as e:
                self.error_occurred.emit(f"SQLite error: {e}")
            finally:
                if cursor: cursor.close()
                if connection: connection.close()
