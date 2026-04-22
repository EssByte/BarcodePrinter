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
        width_px = 800 
        height_px = 300
        
        # Create a white 1-bit image (1 = White)
        image = Image.new('1', (width_px, height_px), 1)
        draw = ImageDraw.Draw(image)
        # Detect OS and load appropriate font
        import platform
        import os
        if platform.system() == "Windows":
            # Primary font and Bold variant
            font_path = "C:\\Windows\\Fonts\\msyh.ttc" if os.path.exists("C:\\Windows\\Fonts\\msyh.ttc") else "arial.ttf"
            font_bold_path = "C:\\Windows\\Fonts\\msyhbd.ttc" if os.path.exists("C:\\Windows\\Fonts\\msyhbd.ttc") else font_path
        else:
            font_path = "/usr/share/fonts/google-droid-sans-fonts/DroidSansFallbackFull.ttf"
            font_bold_path = font_path

        try:
            font_small = ImageFont.truetype(font_path, 12)
            font_small_bold = ImageFont.truetype(font_bold_path, 12)
            font_medium = ImageFont.truetype(font_path, 20)
            font_large = ImageFont.truetype(font_path, 30)
            font_huge = ImageFont.truetype(font_path, 24)
        except:
            # Final fallback to built-in tiny font if all files fail
            font_small = font_small_bold = font_medium = font_large = font_huge = ImageFont.load_default()

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
        draw.text((20, 20), "NAMA PRODUK / PRODUCT NAME", fill=0, font=font_small_bold)
        # Big Description
        description = data.get('description', 'VANILLA POWDER')
        # English description (now smaller)
        draw.text((20, 50), description, fill=0, font=font_huge)
        
        # Chinese Translation (now smaller and much closer)
        draw.text((20, 90), "香草粉", fill=0, font=font_huge)

        # 5. Content for Column A, Row B (Bottom Left)
        # Label (Centered vertically in the 180-300 range)
        draw.text((20, 200), "KOD PRODUK / PRODUCT CODE", fill=0, font=font_small_bold)
        
        # Generate and Paste Barcode (Height reduced to 40 for better fit)
        barcode_value = data.get('barcode_value', '12345678')
        try:
            from barcode import Code128
            from barcode.writer import ImageWriter
            import io
            rv = io.BytesIO()
            Code128(barcode_value, writer=ImageWriter()).write(rv, options={
                "write_text": False, "module_height": 10.0, "quiet_zone": 1.0, 
                "background": "white", "foreground": "black"
            })
            rv.seek(0)
            bc_img = Image.open(rv).convert('1')
            bc_img = bc_img.resize((300, 40))
            image.paste(bc_img, (20, 220))
        except:
            draw.text((20, 220), "[BARCODE ERROR]", fill=0, font=font_small)

        # Barcode Value Text (Positioned horizontally middle of Row B)
        draw.text((20, 265), barcode_value, fill=0, font=font_medium)

        # 6. Column B (Right Side) - Each row is 75px tall (300/4)
        col_b_x = col_split + 10
        
        # Row A: PRICE (0 to 75)
        draw.text((col_b_x, 10), "HARGA / PRICE (RM)", fill=0, font=font_small_bold)
        price = data.get('unit_price_integer', '0.00')
        draw.text((col_b_x, 35), price, fill=0, font=font_medium)

        # Row B: EXPIRY (75 to 150)
        draw.text((col_b_x, 85), "GUNA SBL / EXP", fill=0, font=font_small_bold)
        expiry = data.get('remark', '')
        draw.text((col_b_x, 110), expiry, fill=0, font=font_medium)

        # Row C: NET WEIGHT (150 to 225)
        draw.text((col_b_x, 160), "BERAT BERSIH / NET WT", fill=0, font=font_small_bold)
        weight = data.get('net_weight', '')
        draw.text((col_b_x, 185), weight, fill=0, font=font_medium)

        # Row D: BATCH (225 to 300)
        draw.text((col_b_x, 235), "LOT / BATCH", fill=0, font=font_small_bold)
        batch = data.get('batch', '')
        draw.text((col_b_x, 260), batch, fill=0, font=font_medium)

        # Rotate 180 degrees (correction for upside-down printing)
        image = image.rotate(180)

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
