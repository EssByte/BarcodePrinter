import json
import os
import uuid
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QGraphicsView, QGraphicsScene, QGraphicsTextItem, 
                             QGraphicsRectItem, QGraphicsLineItem, QGraphicsItem,
                             QFormLayout, QLineEdit, QSpinBox, QSplitter, QGroupBox, QComboBox, QCheckBox, QMessageBox)
from PyQt5.QtGui import QFont, QColor, QPen, QBrush, QPainter
from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QPointF

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

    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(0, 0, 750, 550) # Canvas size for 75x55mm label
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.scene.selectionChanged.connect(self.on_selection_changed)

        # Boundary
        self.boundary = QGraphicsRectItem(0, 0, 750, 550)
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
        btn_text.clicked.connect(lambda *args: self.add_element(CustomTextItem("New Text", (20, 20))))
        
        btn_barcode = QPushButton("Add Barcode")
        btn_barcode.clicked.connect(lambda *args: self.add_element(CustomRectItem(200, 50, (20, 20), "barcode")))
        
        btn_line = QPushButton("Add Line")
        btn_line.clicked.connect(lambda *args: self.add_element(CustomLineItem(150, (20, 20))))
        
        btn_block = QPushButton("Add Block")
        btn_block.clicked.connect(lambda *args: self.add_element(CustomRectItem(100, 100, (20, 20), "block")))
        
        btn_delete = QPushButton("Delete Selected")
        btn_delete.setStyleSheet("background-color: #ef4444; color: white;")
        btn_delete.clicked.connect(self.delete_selected)

        btn_save = QPushButton("Save Layout")
        btn_save.setStyleSheet("background-color: #10b981; color: white;")
        btn_save.clicked.connect(self.save_design)

        for btn in [btn_text, btn_barcode, btn_line, btn_block, btn_delete, btn_save]:
            tool_layout.addWidget(btn)
        
        # Printing Section
        tool_layout.addSpacing(20)
        tool_layout.addWidget(QLabel("<b>Printer</b>"))
        
        self.printer_combo = QComboBox()
        self.load_printers()
        tool_layout.addWidget(self.printer_combo)
        
        btn_print = QPushButton("Print Layout")
        btn_print.setStyleSheet("background-color: #3b82f6; color: white; padding: 10px; font-weight: bold;")
        btn_print.clicked.connect(self.print_layout)
        tool_layout.addWidget(btn_print)
        
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
            
            if item.element_type == "barcode":
                self.val_edit = QLineEdit(item.barcode_value)
                self.val_edit.textChanged.connect(self.apply_properties)
                self.prop_layout.addRow("Value:", self.val_edit)

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

    def load_printers(self):
        from modules.Configurations import BarcodeConfig
        self.config = BarcodeConfig()
        printers = self.config.get_printers_list()
        for p in printers:
            self.printer_combo.addItem(p.get("name", "Unknown"), p)

    def print_layout(self):
        printer_data = self.printer_combo.currentData()
        if not printer_data:
            QMessageBox.warning(self, "No Printer", "Please select a printer first.")
            return
            
        from modules.ImagePrinter import ImagePrinter
        from modules.SendCommand import SendCommand
        import usb.core
        import usb.backend.libusb1
        import sys
        
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
            
            img = ip.render_custom_label(test_data, layout_dict, W=750, H=550)
            print_data = ip.get_full_command(img, copies=1, width_mm=75, height_mm=55)

            # 2. Send Command
            sc = SendCommand()
            mode = printer_data.get('mode', 'USB')
            
            if mode == 'USB':
                vid = int(printer_data['vid'], 16) if '0x' in printer_data['vid'] else int(printer_data['vid'])
                pid = int(printer_data['pid'], 16) if '0x' in printer_data['pid'] else int(printer_data['pid'])
                
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
                ep = int(printer_data.get('endpoint', '0x01'), 16)
                usb_printer.write(ep, print_data)
                usb.util.dispose_resources(usb_printer)
                
            elif mode == 'Network':
                ip_full = printer_data.get('ip_address', '127.0.0.1:9100')
                ip_addr, port = ip_full.split(":") if ":" in ip_full else (ip_full, "9100")
                sc.send_wireless_command(ip_addr, port, b"CLS", print_data)
            else: # System
                sys_name = printer_data.get('system_name', '')
                sc.send_win32print(sys_name, b"CLS")
                sc.send_win32print(sys_name, print_data)

            QMessageBox.information(self, "Success", "Custom layout sent to printer successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Failed to print: {e}")
