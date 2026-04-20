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
        Renders a simple label with just the description as a centered image.
        75mm x 50mm
        """
        width_mm, height_mm = 75, 50
        width_px = int(width_mm * self.dpmm)
        height_px = int(height_mm * self.dpmm)
        
        # Create a white 1-bit image (1 = White)
        image = Image.new('1', (width_px, height_px), 1)
        draw = ImageDraw.Draw(image)
        
        # Try to load a font that supports Chinese, fallback to default
        font_paths = [
            "/usr/share/fonts/google-noto-sans-cjk-vf-fonts/NotoSansCJK-VF.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
        ]
        
        font_main = None
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    font_main = ImageFont.truetype(font_path, 60) # Larger font
                    break
            except:
                pass

        if not font_main:
            font_main = ImageFont.load_default()

        # TEST PATTERN: Draw a small black rectangle in the top-left (0,0)
        # This confirms if BITMAP data is working at all
        draw.rectangle([10, 10, 100, 100], fill=0) # Black box

        # Draw centered description
        description = data.get('description', 'TEST IMAGE')
        center_x = width_px // 2
        center_y = height_px // 2
        
        # fill=0 is Black in PIL mode '1'
        draw.text((center_x, center_y), description, fill=0, anchor="mm", font=font_main)
        
        return image

    def to_tpsl_bitmap(self, image, x=0, y=0):
        """
        Converts a Pillow image to a BITMAP command.
        """
        # Ensure 1-bit
        image = image.convert('1')
        
        # INVERSION: Most TSPL printers need 1 for Ink (Heat)
        # PIL '1' uses 0 for Black ink. So we MUST invert.
        # If it was solid black before, maybe the header was wrong.
        image = Image.eval(image, lambda x: 0 if x == 1 else 1)
        
        width, height = image.size
        width_bytes = (width + 7) // 8
        data = image.tobytes()
        
        # Mode 0 = OVERWRITE
        # Some printers are picky about the comma and binary data
        header = f"BITMAP {x},{y},{width_bytes},{height},0,".encode('utf-8')
        
        # NO trailing \r\n after binary data - the data should be the exact size
        return header + data

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
