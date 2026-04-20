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
        Renders the full label (75mm x 50mm) as an image.
        Padded to 608px width (76 bytes) for perfect alignment.
        """
        width_px = 608 
        height_px = 400
        
        # Create a white 1-bit image (1 = White)
        image = Image.new('1', (width_px, height_px), 1)
        draw = ImageDraw.Draw(image)
        
        # Find font
        font_path = "/usr/share/fonts/google-noto-sans-cjk-vf-fonts/NotoSansCJK-VF.ttc"
        try:
            # We use a large font for the description
            font_main = ImageFont.truetype(font_path, 50)
        except:
            font_main = ImageFont.load_default()

        # Draw centered description
        description = data.get('description', 'TEST IMAGE')
        center_x = width_px // 2
        center_y = height_px // 2
        
        # Draw text (fill=0 is black)
        draw.text((center_x, center_y), description, fill=0, anchor="mm", font=font_main)
        
        return image

    def to_tpsl_bitmap(self, image, x=0, y=0):
        """
        Converts a Pillow image to a GW (Graphic Write) command.
        """
        image = image.convert('1')
        
        # Invert: 0 (Black in PIL) -> 1 (Ink in TSPL)
        image = Image.eval(image, lambda val: 0 if val == 1 else 1)
        
        width, height = image.size
        width_bytes = (width + 7) // 8
        data = image.tobytes()
        
        # GW Header: No space after comma, binary data follows immediately
        header = f"GW {x},{y},{width_bytes},{height},".encode('utf-8')
        
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
        
        footer = f"\r\nPRINT {copies}\r\n".encode('utf-8')
        
        return header + bitmap_data + footer
