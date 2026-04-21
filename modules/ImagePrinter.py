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
        Renders the full Fun Bake label (75mm x 50mm) as an image.
        Padded to 608px width (76 bytes) for perfect alignment.
        """
        width_px = 608 
        height_px = 400
        
        # Create a white 1-bit image (1 = White)
        image = Image.new('1', (width_px, height_px), 1)
        draw = ImageDraw.Draw(image)
        # Detect OS and load appropriate font
        import platform
        import os
        if platform.system() == "Windows":
            # Common Windows CJK fonts
            font_paths = [
                "C:\\Windows\\Fonts\\msyh.ttc",   # Microsoft YaHei
                "C:\\Windows\\Fonts\\msyhbd.ttc", # Microsoft YaHei Bold
                "C:\\Windows\\Fonts\\simhei.ttf", # SimHei
                "C:\\Windows\\Fonts\\arial.ttf"   # Emergency Fallback
            ]
            font_path = "arial.ttf" 
            for p in font_paths:
                if os.path.exists(p):
                    font_path = p
                    break
        else:
            font_path = "/usr/share/fonts/google-droid-sans-fonts/DroidSansFallbackFull.ttf"

        try:
            font_small = ImageFont.truetype(font_path, 20)
            font_medium = ImageFont.truetype(font_path, 30)
            font_large = ImageFont.truetype(font_path, 40)
            font_huge = ImageFont.truetype(font_path, 30)
        except:
            # Final fallback to built-in tiny font if all files fail
            font_small = font_medium = font_large = font_huge = ImageFont.load_default()

        # FRESH START: NEW GRID LAYOUT
        
        # 1. Split columns: Vertical line at 70% of width
        col_split = int(width_px * 0.70)
        draw.line([(col_split, 0), (col_split, height_px)], fill=0, width=2)

        # 2. Column A Rows (Left side): 60% / 40% split
        row_a_split = int(height_px * 0.60)
        draw.line([(0, row_a_split), (col_split, row_a_split)], fill=0, width=2)

        # 3. Column B Rows (Right side): 4 equal rows (25% each)
        for i in range(1, 4):
            row_y = int(height_px * (i * 0.25))
            draw.line([(col_split, row_y), (width_px, row_y)], fill=0, width=2)

        # 4. Content for Column A, Row A (Top Left)
        # Small Label
        draw.text((20, 20), "NAMA PRODUK / PRODUCT NAME", fill=0, font=font_small)
        # Big Description
        description = data.get('description', 'VANILLA POWDER')
        # English description (now smaller)
        draw.text((20, 50), description, fill=0, font=font_huge)
        
        # Chinese Translation (now smaller and much closer)
        draw.text((20, 90), "香草粉", fill=0, font=font_huge)

        return image

    def to_tpsl_bitmap(self, image, x=0, y=0):
        """
        Converts a Pillow image to a GW (Graphic Write) command.
        """
        image = image.convert('1')
        
        # Some printers interpret bits differently. Removing inversion to fix the black background issue.
        # image = Image.eval(image, lambda val: 0 if val == 1 else 1)
        
        width, height = image.size
        width_bytes = (width + 7) // 8
        data = image.tobytes()
        
        # GW Header: No space after comma, binary data follows immediately
        header = f"GW {x},{y},{width_bytes},{height},".encode('utf-8')
        
        return header + data

    def get_full_command(self, image, copies=1):
        """Wraps the bitmap in standard TPSL start/end commands"""
        # Automatically save a copy of the image to the images/ folder for debugging
        try:
            if not os.path.exists('images'):
                os.makedirs('images')
            import datetime
            # Use microsecond (%f) to avoid collisions if multiple labels are printed quickly
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            image.save(f"images/print_{timestamp}.png")
        except Exception as e:
            # We don't want to crash the whole print job if saving fails (e.g. permission issues)
            # but we log it to console
            print(f"Warning: Failed to save debug image to 'images/' folder: {e}")

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
