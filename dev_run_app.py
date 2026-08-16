"""
Dev-only launcher: runs the main window with fake item data, bypassing the
real SQL Server/SQLite fetch, so it can be visually tested on Linux (the
real DB fetch, USB printing, and win32 printing all need Windows).
"""
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox

app = QApplication(sys.argv)

# The background fetch thread will fail immediately (no real DB reachable
# here) and try to pop a modal error dialog -- suppress it so it doesn't
# block, then inject mock data below instead.
QMessageBox.critical = staticmethod(lambda *a, **k: None)

from modules.ui.app import BarcodeApp

# (item_code, name, uom, unit_price, unit_cost, barcode, location, loc_price)
MOCK_ITEMS = [
    ("SKU-1001", "Kaya Butter Toast Loaf 400g", "PKT", 8.90, 5.20, "9556001234561", "HQ", 8.90),
    ("SKU-1002", "Chocolate Chip Cookies 250g", "PKT", 12.50, 7.80, "9556001234578", "HQ", 12.50),
    ("SKU-1003", "Sourdough Bread Loaf", "PC", 15.00, 9.00, "9556001234585", "HQ", 15.00),
    ("SKU-1004", "Croissant Butter Plain", "PC", 4.50, 2.10, "9556001234592", "HQ", 4.50),
    ("SKU-1005", "Red Velvet Cupcake Box of 6", "BOX", 28.00, 16.00, "9556001234608", "HQ", 28.00),
    ("SKU-1006", "Wholemeal Bread 600g", "PKT", 9.80, 5.90, "9556001234615", "HQ", 9.80),
    ("SKU-1007", "Banana Cake Slice", "PC", 6.50, 3.20, "9556001234622", "HQ", 6.50),
    ("SKU-1008", "Pandan Chiffon Cake Whole", "PC", 32.00, 18.50, "9556001234639", "HQ", 32.00),
    ("SKU-1009", "Butter Cream Birthday Cake 6in", "PC", 55.00, 30.00, "9556001234646", "HQ", 55.00),
    ("SKU-1010", "Garlic Cheese Bread", "PC", 7.20, 3.90, "9556001234653", "HQ", 7.20),
]

window = BarcodeApp()
window.handle_items_fetched(MOCK_ITEMS)
window.show()
sys.exit(app.exec_())
