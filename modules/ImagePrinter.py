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
        
        # Create a white 1-bit image
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
                    font_main = ImageFont.truetype(font_path, 40)
                    break
            except:
                pass

        if not font_main:
            font_main = ImageFont.load_default()

        # Draw centered description
        description = data.get('description', '')
        center_x = width_px // 2
        center_y = height_px // 2
        
        draw.text((center_x, center_y), description, fill=0, anchor="mm", font=font_main)
        
        return image

    def to_tpsl_bitmap(self, image, x=0, y=0):
        """
        Converts a Pillow image to a TPSL BITMAP command string.
        Format: BITMAP x,y,width_bytes,height,mode,data
        """
        # Ensure image is monochrome (1-bit)
        image = image.convert('1')
        
        # By default, PIL '1' mode: 0=Black, 1=White
        # TSPL expects: 1=Black, 0=White
        # If it was printing solid black, it means the 1s (background) were firing.
        # Let's try WITHOUT the inversion first to see if that fixes the background.
        
        width, height = image.size
        width_bytes = (width + 7) // 8
        
        # Get raw data from Pillow
        data = image.tobytes()
        
        # BITMAP command header
        # Using mode 0 (Overwrite)
        # Note: No space after the comma before the binary data
        header = f"BITMAP {x},{y},{width_bytes},{height},0,".encode('utf-8')
        
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
