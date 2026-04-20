import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io
import os

class ImagePrinter:
    def __init__(self, dpi=203):
        self.dpi = dpi
        # dots per mm: 203 DPI / 25.4 mm/in approx 8 dots/mm
        self.dpmm = dpi / 25.4
        
    def render_fun_bake_label(self, data):
        """
        Renders a smaller test image (200x200) to verify transmission.
        75mm x 50mm label area.
        """
        width_px, height_px = 200, 200 # Smaller test size
        
        # Create a white 1-bit image (1 = White)
        image = Image.new('1', (width_px, height_px), 1)
        draw = ImageDraw.Draw(image)
        
        # Test Pattern: Big black box
        draw.rectangle([10, 10, 190, 190], fill=0) # Black box

        # Find font
        font_path = "/usr/share/fonts/google-noto-sans-cjk-vf-fonts/NotoSansCJK-VF.ttc"
        try:
            font_main = ImageFont.truetype(font_path, 30)
        except:
            font_main = ImageFont.load_default()

        # Text in the middle
        draw.text((100, 100), data.get('description', 'TEST'), fill=1, anchor="mm", font=font_main) # White text on black box
        
        return image

    def to_tpsl_bitmap(self, image, x=50, y=50):
        """
        Converts a Pillow image to a GW (Graphic Write) command.
        GW x, y, width_bytes, height, data
        """
        image = image.convert('1')
        
        # PIL '1' mode: 0=Black, 1=White
        # TSPL 'GW' expects: 1=Black, 0=White (Heat on)
        # So we MUST invert.
        image = Image.eval(image, lambda x: 0 if x == 1 else 1)
        
        width, height = image.size
        width_bytes = (width + 7) // 8
        data = image.tobytes()
        
        # GW Command Header
        header = f"GW {x},{y},{width_bytes},{height},".encode('utf-8')
        
        return header + data + b"\r\n"

    def get_full_command(self, image, copies=1):
        """Wraps the bitmap in standard TPSL start/end commands"""
        bitmap_data = self.to_tpsl_bitmap(image, 0, 0)
        
        header = (
            "SPEED 2.0\r\n"
            "DENSITY 7\r\n"
            "DIRECTION 0\r\n"
            "SIZE 75MM, 50MM\r\n"
            "REFERENCE 0,0\r\n"
            "CLS\r\n"
        ).encode('utf-8')
        
        footer = f"PRINT {copies}\r\n".encode('utf-8')
        
        return header + bitmap_data + footer
