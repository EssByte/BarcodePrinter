import json
import os
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsTextItem, 
                             QGraphicsItem, QGraphicsRectItem, QMenu, QAction)
from PyQt5.QtGui import QFont, QColor, QPen, QBrush, QPainter
from PyQt5.QtCore import Qt, QRectF, pyqtSignal

class DraggableItem(QGraphicsTextItem):
    item_moved = pyqtSignal()

    def __init__(self, text, key, initial_pos=(0, 0)):
        super().__init__(text)
        self.key = key
        self.setPos(initial_pos[0], initial_pos[1])
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setFont(QFont("Segoe UI", 10))
        
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.item_moved.emit()
        return super().itemChange(change, value)

class BarcodeDesigner(QGraphicsView):
    def __init__(self, config_path=os.path.join(os.path.expanduser("~"), ".barcode_design.json")):
        super().__init__()
        self.config_path = config_path
        self.scene = QGraphicsScene(0, 0, 800, 300) # 75mm x 50mm approx
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        
        # Draw Label Boundary
        self.boundary = QGraphicsRectItem(0, 0, 800, 300)
        self.boundary.setPen(QPen(QColor("#cbd5e1"), 2, Qt.DashLine))
        self.scene.addItem(self.boundary)
        
        self.items = {}
        self.init_default_items()
        self.load_design()

    def init_default_items(self):
        default_elements = {
            "product_name": ("PRODUCT NAME", (20, 20)),
            "product_code": ("PRODUCT CODE", (20, 180)),
            "price": ("PRICE: RM 0.00", (500, 20)),
            "expiry": ("EXP: 01/01/2025", (500, 80)),
            "weight": ("NET WT: 500g", (500, 140)),
            "batch": ("BATCH: LOT123", (500, 200)),
            "barcode": ("[ BARCODE AREA ]", (20, 220))
        }
        
        for key, (text, pos) in default_elements.items():
            item = DraggableItem(text, key, pos)
            if key == "product_name": item.setFont(QFont("Segoe UI", 16, QFont.Bold))
            elif key == "barcode": 
                item.setFont(QFont("Courier New", 14, QFont.Bold))
                item.setDefaultTextColor(QColor("#3b82f6"))
            
            item.item_moved.connect(self.auto_save)
            self.scene.addItem(item)
            self.items[key] = item

    def load_design(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    for key, pos in data.items():
                        if key in self.items:
                            self.items[key].setPos(pos[0], pos[1])
            except: pass

    def auto_save(self):
        design_data = {}
        for key, item in self.items.items():
            design_data[key] = [item.pos().x(), item.pos().y()]
        
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(design_data, f, indent=4)
        except: pass

    def get_design(self):
        design_data = {}
        for key, item in self.items.items():
            design_data[key] = [item.pos().x(), item.pos().y()]
        return design_data
