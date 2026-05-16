import json
import os
import uuid
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QGraphicsView, QGraphicsScene, QGraphicsTextItem, 
                             QGraphicsRectItem, QGraphicsLineItem, QGraphicsItem,
                             QFormLayout, QLineEdit, QSpinBox, QSplitter, QGroupBox, QComboBox)
from PyQt5.QtGui import QFont, QColor, QPen, QBrush, QPainter
from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QPointF

class BaseElement:
    def __init__(self, element_type):
        self.element_type = element_type
        self.element_id = str(uuid.uuid4())

    def to_dict(self):
        pos = self.pos()
        return {
            "id": self.element_id,
            "type": self.element_type,
            "x": pos.x(),
            "y": pos.y()
        }

    def load_dict(self, data):
        self.element_id = data.get("id", self.element_id)
        self.setPos(data.get("x", 0), data.get("y", 0))

class CustomTextItem(QGraphicsTextItem, BaseElement):
    def __init__(self, text="Text", pos=(0,0)):
        QGraphicsTextItem.__init__(self, text)
        BaseElement.__init__(self, "text")
        self.setPos(pos[0], pos[1])
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.font_size = 14
        self.is_bold = False
        self.text_value = text
        self._update_font()

    def _update_font(self):
        font = QFont("Arial", self.font_size)
        font.setBold(self.is_bold)
        self.setFont(font)
        self.setPlainText(self.text_value)

    def to_dict(self):
        d = super().to_dict()
        d.update({
            "value": self.text_value,
            "font_size": self.font_size,
            "bold": self.is_bold
        })
        return d

    def load_dict(self, data):
        super().load_dict(data)
        self.text_value = data.get("value", "Text")
        self.font_size = data.get("font_size", 14)
        self.is_bold = data.get("bold", False)
        self._update_font()

class CustomRectItem(QGraphicsRectItem, BaseElement):
    def __init__(self, width=100, height=50, pos=(0,0), e_type="block"):
        QGraphicsRectItem.__init__(self, 0, 0, width, height)
        BaseElement.__init__(self, e_type)
        self.setPos(pos[0], pos[1])
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.box_width = width
        self.box_height = height
        self._update_rect()
        
        if e_type == "barcode":
            self.setPen(QPen(Qt.blue, 2, Qt.DashLine))
            self.setBrush(QBrush(QColor(0, 0, 255, 30)))
        else:
            self.setPen(QPen(Qt.black, 1))
            self.setBrush(QBrush(Qt.black))

    def _update_rect(self):
        self.setRect(0, 0, self.box_width, self.box_height)

    def to_dict(self):
        d = super().to_dict()
        d.update({"width": self.box_width, "height": self.box_height})
        if self.element_type == "barcode":
            d.update({"value": "{{barcode_value}}"})
        return d

    def load_dict(self, data):
        super().load_dict(data)
        self.box_width = data.get("width", 100)
        self.box_height = data.get("height", 50)
        self._update_rect()

class CustomLineItem(QGraphicsLineItem, BaseElement):
    def __init__(self, length=100, pos=(0,0)):
        QGraphicsLineItem.__init__(self, 0, 0, length, 0)
        BaseElement.__init__(self, "line")
        self.setPos(pos[0], pos[1])
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.length = length
        self.thickness = 2
        self.is_vertical = False
        self._update_line()

    def _update_line(self):
        pen = QPen(Qt.black, self.thickness)
        self.setPen(pen)
        if self.is_vertical:
            self.setLine(0, 0, 0, self.length)
        else:
            self.setLine(0, 0, self.length, 0)

    def to_dict(self):
        d = super().to_dict()
        d.update({
            "length": self.length,
            "thickness": self.thickness,
            "vertical": self.is_vertical
        })
        return d

    def load_dict(self, data):
        super().load_dict(data)
        self.length = data.get("length", 100)
        self.thickness = data.get("thickness", 2)
        self.is_vertical = data.get("vertical", False)
        self._update_line()

class CanvasView(QGraphicsView):
    selection_changed = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(0, 0, 800, 300) # Default canvas size approx 75x50
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.scene.selectionChanged.connect(self.on_selection_changed)

        # Boundary
        self.boundary = QGraphicsRectItem(0, 0, 800, 300)
        self.boundary.setPen(QPen(QColor("#cbd5e1"), 2, Qt.DashLine))
        self.scene.addItem(self.boundary)

    def on_selection_changed(self):
        items = self.scene.selectedItems()
        if items:
            self.selection_changed.emit(items[0])
        else:
            self.selection_changed.emit(None)

class BarcodeDesigner(QWidget):
    def __init__(self, config_path=os.path.join(os.path.expanduser("~"), ".barcode_custom_layout.json")):
        super().__init__()
        self.config_path = config_path
        self.init_ui()
        self.load_design()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)

        # Splitter for adjustable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 1. Toolbox Panel (Left)
        toolbox = QWidget()
        tool_layout = QVBoxLayout(toolbox)
        tool_layout.addWidget(QLabel("<b>Tools</b>"))
        
        btn_text = QPushButton("Add Text")
        btn_text.clicked.connect(lambda: self.add_element(CustomTextItem("New Text", (20, 20))))
        
        btn_barcode = QPushButton("Add Barcode")
        btn_barcode.clicked.connect(lambda: self.add_element(CustomRectItem(200, 50, (20, 20), "barcode")))
        
        btn_line = QPushButton("Add Line")
        btn_line.clicked.connect(lambda: self.add_element(CustomLineItem(150, (20, 20))))
        
        btn_block = QPushButton("Add Block")
        btn_block.clicked.connect(lambda: self.add_element(CustomRectItem(100, 100, (20, 20), "block")))
        
        btn_delete = QPushButton("Delete Selected")
        btn_delete.setStyleSheet("background-color: #ef4444; color: white;")
        btn_delete.clicked.connect(self.delete_selected)

        btn_save = QPushButton("Save Layout")
        btn_save.setStyleSheet("background-color: #10b981; color: white;")
        btn_save.clicked.connect(self.save_design)

        for btn in [btn_text, btn_barcode, btn_line, btn_block, btn_delete, btn_save]:
            tool_layout.addWidget(btn)
        tool_layout.addStretch()

        # 2. Canvas (Center)
        self.canvas = CanvasView()
        self.canvas.selection_changed.connect(self.update_properties_panel)

        # 3. Properties Panel (Right)
        self.prop_panel = QGroupBox("Properties")
        self.prop_layout = QFormLayout(self.prop_panel)
        self.current_item = None

        splitter.addWidget(toolbox)
        splitter.addWidget(self.canvas)
        splitter.addWidget(self.prop_panel)
        splitter.setSizes([150, 600, 250])

    def add_element(self, item):
        self.canvas.scene.addItem(item)
        self.save_design()

    def delete_selected(self):
        items = self.canvas.scene.selectedItems()
        for item in items:
            self.canvas.scene.removeItem(item)
        self.save_design()

    def update_properties_panel(self, item):
        self.current_item = item
        # Clear layout
        while self.prop_layout.count():
            child = self.prop_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        if not item: return

        if isinstance(item, CustomTextItem):
            self.val_edit = QLineEdit(item.text_value)
            self.size_edit = QSpinBox(); self.size_edit.setRange(8, 72); self.size_edit.setValue(item.font_size)
            self.bold_check = QCheckBox("Bold"); self.bold_check.setChecked(item.is_bold)
            
            self.val_edit.textChanged.connect(self.apply_properties)
            self.size_edit.valueChanged.connect(self.apply_properties)
            self.bold_check.stateChanged.connect(self.apply_properties)

            self.prop_layout.addRow("Value:", self.val_edit)
            self.prop_layout.addRow("Size:", self.size_edit)
            self.prop_layout.addRow("", self.bold_check)

        elif isinstance(item, CustomRectItem):
            self.w_edit = QSpinBox(); self.w_edit.setRange(10, 800); self.w_edit.setValue(item.box_width)
            self.h_edit = QSpinBox(); self.h_edit.setRange(5, 800); self.h_edit.setValue(item.box_height)
            
            self.w_edit.valueChanged.connect(self.apply_properties)
            self.h_edit.valueChanged.connect(self.apply_properties)

            self.prop_layout.addRow("Width:", self.w_edit)
            self.prop_layout.addRow("Height:", self.h_edit)

        elif isinstance(item, CustomLineItem):
            self.l_edit = QSpinBox(); self.l_edit.setRange(10, 800); self.l_edit.setValue(item.length)
            self.t_edit = QSpinBox(); self.t_edit.setRange(1, 20); self.t_edit.setValue(item.thickness)
            self.v_check = QCheckBox("Vertical"); self.v_check.setChecked(item.is_vertical)

            self.l_edit.valueChanged.connect(self.apply_properties)
            self.t_edit.valueChanged.connect(self.apply_properties)
            self.v_check.stateChanged.connect(self.apply_properties)

            self.prop_layout.addRow("Length:", self.l_edit)
            self.prop_layout.addRow("Thickness:", self.t_edit)
            self.prop_layout.addRow("", self.v_check)

    def apply_properties(self):
        if not self.current_item: return
        item = self.current_item

        if isinstance(item, CustomTextItem):
            item.text_value = self.val_edit.text()
            item.font_size = self.size_edit.value()
            item.is_bold = self.bold_check.isChecked()
            item._update_font()
        elif isinstance(item, CustomRectItem):
            item.box_width = self.w_edit.value()
            item.box_height = self.h_edit.value()
            item._update_rect()
        elif isinstance(item, CustomLineItem):
            item.length = self.l_edit.value()
            item.thickness = self.t_edit.value()
            item.is_vertical = self.v_check.isChecked()
            item._update_line()
        
        self.save_design()

    def get_design_dict(self):
        elements = []
        for item in self.canvas.scene.items():
            if isinstance(item, BaseElement):
                elements.append(item.to_dict())
        return {"elements": elements}

    def save_design(self):
        data = self.get_design_dict()
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("Failed to save design:", e)

    def load_design(self):
        if not os.path.exists(self.config_path): return
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
            
            for item_data in data.get("elements", []):
                e_type = item_data.get("type")
                if e_type == "text":
                    item = CustomTextItem()
                elif e_type in ["barcode", "block"]:
                    item = CustomRectItem(e_type=e_type)
                elif e_type == "line":
                    item = CustomLineItem()
                else:
                    continue
                
                item.load_dict(item_data)
                self.canvas.scene.addItem(item)
        except Exception as e:
            print("Failed to load design:", e)
