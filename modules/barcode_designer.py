"""
Barcode Label Designer - Visual layout editor for barcode printing.
Supports multiple sticker sizes with WYSIWYG editing and mm-based grid.
"""
import os
import uuid
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                             QGraphicsView, QGraphicsScene, QGraphicsTextItem,
                             QGraphicsRectItem, QGraphicsLineItem, QGraphicsItem,
                             QFormLayout, QLineEdit, QSpinBox, QSplitter, QGroupBox, QComboBox, QCheckBox, QMessageBox,
                             QInputDialog)
from PyQt5.QtGui import QFont, QColor, QPen, QBrush, QPainter
from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QPointF

from modules.Configurations import BarcodeConfig

try:
    from .size_converter import SizeConverter
except ImportError:
    SizeConverter = None

class BaseElement:
    def init_element(self, element_type):
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
        super().__init__(text)
        self.init_element("text")
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
        super().__init__(0, 0, width, height)
        self.init_element(e_type)
        self.setPos(pos[0], pos[1])
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.box_width = width
        self.box_height = height
        self.barcode_value = "{{barcode_value}}"
        self._update_rect()

    def _update_rect(self):
        self.setRect(0, 0, self.box_width, self.box_height)
        if self.element_type == "barcode":
            self.update_barcode_pixmap()
        else:
            self.setPen(QPen(Qt.black, 1))
            self.setBrush(QBrush(Qt.black))

    def update_barcode_pixmap(self):
        try:
            from barcode import Code128
            from barcode.writer import ImageWriter
            import io
            from PyQt5.QtGui import QImage
            
            rv = io.BytesIO()
            Code128(self.barcode_value, writer=ImageWriter()).write(rv, options={
                "write_text": False, "module_height": 5.0, "module_width": 0.22,
                "quiet_zone": 1.0, "background": "white", "foreground": "black"
            })
            rv.seek(0)
            
            img = QImage()
            img.loadFromData(rv.read())
            img = img.scaled(int(self.box_width), int(self.box_height), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            
            self.setBrush(QBrush(img))
            self.setPen(QPen(Qt.transparent))
        except Exception as e:
            print("Barcode preview error:", e)
            self.setPen(QPen(Qt.blue, 2, Qt.DashLine))
            self.setBrush(QBrush(QColor(0, 0, 255, 30)))

    def to_dict(self):
        d = super().to_dict()
        d.update({"width": self.box_width, "height": self.box_height})
        if self.element_type == "barcode":
            d.update({"value": self.barcode_value})
        return d

    def load_dict(self, data):
        super().load_dict(data)
        self.box_width = data.get("width", 100)
        self.box_height = data.get("height", 50)
        if self.element_type == "barcode":
            self.barcode_value = data.get("value", "{{barcode_value}}")
        self._update_rect()

class CustomLineItem(QGraphicsLineItem, BaseElement):
    def __init__(self, length=100, pos=(0,0)):
        super().__init__(0, 0, length, 0)
        self.init_element("line")
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

    def __init__(self, size_converter=None):
        super().__init__()
        self.size_converter = size_converter
        
        # Calculate canvas size based on label size (default 75x50mm placeholder;
        # BarcodeDesigner resizes this immediately to the selected profile's size)
        if size_converter and SizeConverter:
            width_px, height_px = size_converter.mm_to_pixels(75), size_converter.mm_to_pixels(50)
        else:
            width_px, height_px = 750, 500
        
        self.scene = QGraphicsScene(0, 0, width_px, height_px)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setStyleSheet("QGraphicsView { border: none; background: #f1f5f9; }")
        self.scene.selectionChanged.connect(self.on_selection_changed)

        # Professional boundary
        self.boundary = QGraphicsRectItem(0, 0, width_px, height_px)
        self.boundary.setPen(QPen(QColor("#3b82f6"), 2))
        self.boundary.setBrush(QBrush(QColor(255, 255, 255)))
        self.scene.addItem(self.boundary)

        self.grid_lines = []

        # Draw grid if size converter available
        if size_converter and SizeConverter:
            self._draw_grid(width_px, height_px)

    def _draw_grid(self, width, height):
        """Draw mm grid for visual reference (every 5mm)."""
        if not self.size_converter or not SizeConverter:
            return

        # Clear any grid lines left over from a previous size
        for line in self.grid_lines:
            self.scene.removeItem(line)
        self.grid_lines = []

        grid_pen = QPen(QColor("#e2e8f0"), 0.5)
        step = self.size_converter.mm_to_pixels(5)

        # Vertical lines
        x = 0
        while x <= width:
            line = self.scene.addLine(x, 0, x, height, grid_pen)
            line.setZValue(-1)
            self.grid_lines.append(line)
            x += step

        # Horizontal lines
        y = 0
        while y <= height:
            line = self.scene.addLine(0, y, width, y, grid_pen)
            line.setZValue(-1)
            self.grid_lines.append(line)
            y += step

    def on_selection_changed(self):
        items = self.scene.selectedItems()
        if items:
            self.selection_changed.emit(items[0])
        else:
            self.selection_changed.emit(None)
    
    def set_label_size_mm(self, width_mm, height_mm):
        """Resize canvas to arbitrary mm dimensions using the current size_converter's dpi."""
        if not self.size_converter or not SizeConverter:
            return

        width_px = self.size_converter.mm_to_pixels(width_mm)
        height_px = self.size_converter.mm_to_pixels(height_mm)
        self.scene.setSceneRect(0, 0, width_px, height_px)
        self.boundary.setRect(0, 0, width_px, height_px)
        self._draw_grid(width_px, height_px)

DESIGNER_STYLE = """
QWidget#toolboxPanel {
    background: #f8fafc;
}
QGroupBox {
    font-weight: 600;
    color: #334155;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 12px;
    background: white;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QPushButton#toolBtn {
    background: white;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 10px;
    text-align: left;
    color: #1e293b;
}
QPushButton#toolBtn:hover {
    background: #eff6ff;
    border-color: #3b82f6;
    color: #1d4ed8;
}
QPushButton#toolBtn:pressed {
    background: #dbeafe;
}
QPushButton#dangerBtn {
    background: #ef4444;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 10px;
    font-weight: 600;
}
QPushButton#dangerBtn:hover { background: #dc2626; }
QPushButton#successBtn {
    background: #10b981;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 10px;
    font-weight: 600;
}
QPushButton#successBtn:hover { background: #059669; }
QPushButton#primaryBtn {
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px;
    font-weight: 700;
}
QPushButton#primaryBtn:hover { background: #2563eb; }
QPushButton#iconBtn {
    background: white;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
}
QPushButton#iconBtn:hover { border-color: #3b82f6; }
QComboBox, QLineEdit, QSpinBox {
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 4px 6px;
    background: white;
}
QComboBox:hover, QLineEdit:hover, QSpinBox:hover {
    border-color: #94a3b8;
}
QSplitter::handle {
    background: #e2e8f0;
}
QSplitter::handle:hover {
    background: #cbd5e1;
}
"""

class BarcodeDesigner(QWidget):
    def __init__(self):
        super().__init__()
        self.config = BarcodeConfig()
        self.current_profile_id = None
        self.size_converter = SizeConverter(dpi=SizeConverter.PRINTER_DPI) if SizeConverter else None
        self.setStyleSheet(DESIGNER_STYLE)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)

        # Splitter for adjustable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 1. Toolbox Panel (Left)
        toolbox = QWidget()
        toolbox.setObjectName("toolboxPanel")
        tool_layout = QVBoxLayout(toolbox)
        tool_layout.setContentsMargins(10, 10, 10, 10)
        tool_layout.setSpacing(4)

        # Label size
        size_group = QGroupBox("Label Size")
        size_layout = QVBoxLayout(size_group)
        self.size_combo = QComboBox()
        self.size_combo.currentIndexChanged.connect(self.handle_size_change)
        size_layout.addWidget(self.size_combo)

        size_btn_row = QHBoxLayout()
        btn_new_size = QPushButton("+ New")
        btn_new_size.setObjectName("toolBtn")
        btn_new_size.clicked.connect(self.create_new_size)
        btn_rename_size = QPushButton("Rename")
        btn_rename_size.setObjectName("toolBtn")
        btn_rename_size.clicked.connect(self.rename_current_size)
        btn_delete_size = QPushButton("Delete")
        btn_delete_size.setObjectName("dangerBtn")
        btn_delete_size.clicked.connect(self.delete_current_size)
        size_btn_row.addWidget(btn_new_size)
        size_btn_row.addWidget(btn_rename_size)
        size_btn_row.addWidget(btn_delete_size)
        size_layout.addLayout(size_btn_row)
        tool_layout.addWidget(size_group)

        # Elements
        elements_group = QGroupBox("Elements")
        elements_layout = QVBoxLayout(elements_group)

        btn_text = QPushButton("🔤  Add Text")
        btn_text.setObjectName("toolBtn")
        btn_text.clicked.connect(lambda *args: self.add_element(CustomTextItem("New Text", (20, 20))))

        btn_barcode = QPushButton("▤  Add Barcode")
        btn_barcode.setObjectName("toolBtn")
        btn_barcode.clicked.connect(lambda *args: self.add_element(CustomRectItem(200, 50, (20, 20), "barcode")))

        btn_line = QPushButton("╱  Add Line")
        btn_line.setObjectName("toolBtn")
        btn_line.clicked.connect(lambda *args: self.add_element(CustomLineItem(150, (20, 20))))

        btn_block = QPushButton("▭  Add Block")
        btn_block.setObjectName("toolBtn")
        btn_block.clicked.connect(lambda *args: self.add_element(CustomRectItem(100, 100, (20, 20), "block")))

        for btn in [btn_text, btn_barcode, btn_line, btn_block]:
            elements_layout.addWidget(btn)
        tool_layout.addWidget(elements_group)

        # Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)

        btn_delete = QPushButton("Delete Selected")
        btn_delete.setObjectName("dangerBtn")
        btn_delete.clicked.connect(self.delete_selected)

        btn_save = QPushButton("Save Layout")
        btn_save.setObjectName("successBtn")
        btn_save.clicked.connect(self.save_design)

        actions_layout.addWidget(btn_delete)
        actions_layout.addWidget(btn_save)
        tool_layout.addWidget(actions_group)

        # Printing Section
        printer_group = QGroupBox("Printer")
        printer_group_layout = QVBoxLayout(printer_group)

        printer_layout = QHBoxLayout()
        self.printer_combo = QComboBox()
        self.load_printers()
        self.printer_combo.currentIndexChanged.connect(self.handle_printer_selection)

        self.btn_refresh_printers = QPushButton("🔄")
        self.btn_refresh_printers.setObjectName("iconBtn")
        self.btn_refresh_printers.setFixedWidth(36)
        self.btn_refresh_printers.clicked.connect(self.load_printers)

        printer_layout.addWidget(self.printer_combo)
        printer_layout.addWidget(self.btn_refresh_printers)
        printer_group_layout.addLayout(printer_layout)

        btn_print = QPushButton("Print Layout")
        btn_print.setObjectName("primaryBtn")
        btn_print.clicked.connect(self.print_layout)
        printer_group_layout.addWidget(btn_print)
        tool_layout.addWidget(printer_group)

        tool_layout.addStretch()

        # 2. Canvas (Center)
        self.canvas = CanvasView(self.size_converter)
        self.canvas.selection_changed.connect(self.update_properties_panel)

        # 3. Properties Panel (Right)
        self.prop_panel = QGroupBox("Properties")
        self.prop_layout = QFormLayout(self.prop_panel)
        self.current_item = None
        self.update_properties_panel(None)

        splitter.addWidget(toolbox)
        splitter.addWidget(self.canvas)
        splitter.addWidget(self.prop_panel)
        splitter.setSizes([150, 600, 250])

        self.populate_size_combo()

    def populate_size_combo(self):
        self.size_combo.blockSignals(True)
        self.size_combo.clear()
        profiles = self.config.get_custom_label_sizes()
        for p in profiles:
            self.size_combo.addItem(p["name"], p["id"])
        self.size_combo.blockSignals(False)
        if profiles:
            self.size_combo.setCurrentIndex(0)
            self.load_profile(profiles[0])

    def get_profile_by_id(self, profile_id):
        for p in self.config.get_custom_label_sizes():
            if p["id"] == profile_id:
                return p
        return None

    def load_profile(self, profile):
        self.current_profile_id = profile["id"]
        for item in list(self.canvas.scene.items()):
            if isinstance(item, BaseElement):
                self.canvas.scene.removeItem(item)
        self.canvas.set_label_size_mm(profile["width_mm"], profile["height_mm"])
        for item_data in profile.get("elements", []):
            e_type = item_data.get("type")
            if e_type == "text":
                item = CustomTextItem()
            elif e_type in ("barcode", "block"):
                item = CustomRectItem(e_type=e_type)
            elif e_type == "line":
                item = CustomLineItem()
            else:
                continue
            item.load_dict(item_data)
            self.canvas.scene.addItem(item)

    def handle_size_change(self, index):
        if index < 0:
            return
        profile_id = self.size_combo.itemData(index)
        profile = self.get_profile_by_id(profile_id)
        if profile:
            self.load_profile(profile)

    def create_new_size(self):
        name, ok = QInputDialog.getText(self, "New Label Size", "Name:")
        if not ok or not name.strip():
            return
        width_mm, ok = QInputDialog.getDouble(self, "New Label Size", "Width (mm):", 50.0, 1.0, 500.0, 1)
        if not ok:
            return
        height_mm, ok = QInputDialog.getDouble(self, "New Label Size", "Height (mm):", 30.0, 1.0, 500.0, 1)
        if not ok:
            return

        profiles = self.config.get_custom_label_sizes()
        new_profile = {
            "id": str(uuid.uuid4()),
            "name": name.strip(),
            "width_mm": width_mm,
            "height_mm": height_mm,
            "elements": []
        }
        profiles.append(new_profile)
        self.config.set_custom_label_sizes(profiles)
        self.populate_size_combo()
        idx = self.size_combo.findData(new_profile["id"])
        if idx >= 0:
            self.size_combo.setCurrentIndex(idx)

    def rename_current_size(self):
        if not self.current_profile_id:
            return
        target_id = self.current_profile_id
        profile = self.get_profile_by_id(target_id)
        if not profile:
            return
        new_name, ok = QInputDialog.getText(self, "Rename Label Size", "Name:", text=profile["name"])
        if not ok or not new_name.strip():
            return

        profiles = self.config.get_custom_label_sizes()
        for p in profiles:
            if p["id"] == target_id:
                p["name"] = new_name.strip()
        self.config.set_custom_label_sizes(profiles)
        self.populate_size_combo()
        idx = self.size_combo.findData(target_id)
        if idx >= 0:
            self.size_combo.setCurrentIndex(idx)

    def delete_current_size(self):
        if not self.current_profile_id:
            return
        profiles = self.config.get_custom_label_sizes()
        if len(profiles) <= 1:
            QMessageBox.warning(self, "Cannot Delete", "At least one label size must exist.")
            return
        reply = QMessageBox.question(self, "Delete Size", "Delete this label size and its design?")
        if reply != QMessageBox.Yes:
            return

        profiles = [p for p in profiles if p["id"] != self.current_profile_id]
        self.config.set_custom_label_sizes(profiles)
        self.current_profile_id = None
        self.populate_size_combo()

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

        if not item:
            placeholder = QLabel("Select an element on the canvas to edit its properties.")
            placeholder.setWordWrap(True)
            placeholder.setStyleSheet("color: #94a3b8; padding: 8px 0;")
            self.prop_layout.addRow(placeholder)
            return

        self.x_edit = QSpinBox(); self.x_edit.setRange(-2000, 4000); self.x_edit.setValue(int(item.pos().x()))
        self.y_edit = QSpinBox(); self.y_edit.setRange(-2000, 4000); self.y_edit.setValue(int(item.pos().y()))
        self.x_edit.valueChanged.connect(self.apply_properties)
        self.y_edit.valueChanged.connect(self.apply_properties)
        self.prop_layout.addRow("X:", self.x_edit)
        self.prop_layout.addRow("Y:", self.y_edit)

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
            self.w_edit = QSpinBox(); self.w_edit.setRange(10, 4000); self.w_edit.setValue(item.box_width)
            self.h_edit = QSpinBox(); self.h_edit.setRange(5, 4000); self.h_edit.setValue(item.box_height)
            
            self.w_edit.valueChanged.connect(self.apply_properties)
            self.h_edit.valueChanged.connect(self.apply_properties)

            self.prop_layout.addRow("Width:", self.w_edit)
            self.prop_layout.addRow("Height:", self.h_edit)
            
            if item.element_type == "barcode":
                self.val_edit = QLineEdit(item.barcode_value)
                self.val_edit.textChanged.connect(self.apply_properties)
                self.prop_layout.addRow("Value:", self.val_edit)

        elif isinstance(item, CustomLineItem):
            self.l_edit = QSpinBox(); self.l_edit.setRange(10, 4000); self.l_edit.setValue(item.length)
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

        if hasattr(self, 'x_edit') and hasattr(self, 'y_edit'):
            item.setPos(self.x_edit.value(), self.y_edit.value())

        if isinstance(item, CustomTextItem):
            item.text_value = self.val_edit.text()
            item.font_size = self.size_edit.value()
            item.is_bold = self.bold_check.isChecked()
            item._update_font()
        elif isinstance(item, CustomRectItem):
            item.box_width = self.w_edit.value()
            item.box_height = self.h_edit.value()
            if item.element_type == "barcode" and hasattr(self, 'val_edit'):
                item.barcode_value = self.val_edit.text()
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
        if not self.current_profile_id:
            return
        elements = [item.to_dict() for item in self.canvas.scene.items() if isinstance(item, BaseElement)]
        profiles = self.config.get_custom_label_sizes()
        for p in profiles:
            if p["id"] == self.current_profile_id:
                p["elements"] = elements
        self.config.set_custom_label_sizes(profiles)

    def load_printers(self):
        self.printer_combo.blockSignals(True)
        self.printer_combo.clear()
        printers = self.config.get_printers_list()
        active_id = self.config.get_active_printer_id()
        
        for i, p in enumerate(printers):
            self.printer_combo.addItem(p.get("name", "Unknown"), p.get("id"))
            if p.get("id") == active_id:
                self.printer_combo.setCurrentIndex(i)
        self.printer_combo.blockSignals(False)

    def handle_printer_selection(self, index):
        if index < 0: return
        printer_id = self.printer_combo.itemData(index)
        self.config.set_active_printer_id(printer_id)

    def print_layout(self):
        printer_config = self.config.get_active_printer_config()
        if not printer_config:
            QMessageBox.warning(self, "No Printer", "Please select a printer first.")
            return
            
        from modules.ImagePrinter import ImagePrinter
        from modules.SendCommand import SendCommand
        import usb.core
        import usb.backend.libusb1
        import sys
        
        profile = self.get_profile_by_id(self.current_profile_id)
        if not profile:
            QMessageBox.warning(self, "No Size", "Please select a label size first.")
            return

        try:
            # 1. Render Image
            ip = ImagePrinter()
            layout_dict = self.get_design_dict()

            # Create some dummy data or grab real data. Here we can use generic placeholders for a test print
            test_data = {
                "barcode_value": "1234567890",
                "description": "Custom Print Test",
                "unit_price_integer": "99.90",
                "remark": "Test Remark"
            }

            W = self.size_converter.mm_to_pixels(profile["width_mm"])
            H = self.size_converter.mm_to_pixels(profile["height_mm"])
            img = ip.render_custom_label(test_data, layout_dict, W=W, H=H)
            print_data = ip.get_full_command(img, copies=1, width_mm=profile["width_mm"], height_mm=profile["height_mm"])

            # 2. Send Command
            sc = SendCommand()
            mode = printer_config.get('mode', 'USB')
            
            if mode == 'USB':
                vid = int(printer_config['vid'], 16) if '0x' in printer_config['vid'] else int(printer_config['vid'])
                pid = int(printer_config['pid'], 16) if '0x' in printer_config['pid'] else int(printer_config['pid'])
                
                def resource_path(relative_path):
                    try:
                        base_path = sys._MEIPASS
                    except Exception:
                        base_path = os.path.abspath(".")
                    return os.path.join(base_path, relative_path)

                backend = usb.backend.libusb1.get_backend(find_library=resource_path('libusb-1.0.ddl'))
                usb_printer = usb.core.find(idVendor=vid, idProduct=pid, backend=backend)
                
                if not usb_printer:
                    QMessageBox.warning(self, "Printer Error", "Could not find USB printer.")
                    return
                
                usb_printer.set_configuration()
                ep = int(printer_config.get('endpoint', '0x01'), 16)
                usb_printer.write(ep, print_data)
                usb.util.dispose_resources(usb_printer)

            elif mode == 'Network':
                ip_full = printer_config.get('ip_address', '127.0.0.1:9100')
                ip_addr, port = ip_full.split(":") if ":" in ip_full else (ip_full, "9100")
                sc.send_wireless_command(ip_addr, port, b"CLS", print_data)
            else: # System
                sys_name = printer_config.get('system_name', '')
                sc.send_win32print(sys_name, b"CLS")
                sc.send_win32print(sys_name, print_data)

            QMessageBox.information(self, "Success", "Custom layout sent to printer successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Failed to print: {e}")
