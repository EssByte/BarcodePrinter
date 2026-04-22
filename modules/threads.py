import pyodbc
import sqlite3
from PyQt5.QtCore import QThread, pyqtSignal
from bisect import bisect_left
from modules.Configurations import BarcodeConfig

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

    def __init__(self, db_source, location, use_sqlite):
        super().__init__()
        self.config = BarcodeConfig()
        self.db_source = db_source  
        self.location = location
        self.use_sqlite = use_sqlite

    def run(self):
        if not self.use_sqlite:
            # SQL Server (pyodbc)
            cursor = None
            try:
                connection = self.db_source 
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
                self.error_occurred.emit(f"Error fetching from SQL: {e}")
            finally:
                if cursor: cursor.close()
        else:
            # SQLite
            cursor = None
            connection = None
            try:
                connection = sqlite3.connect(self.db_source)
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
