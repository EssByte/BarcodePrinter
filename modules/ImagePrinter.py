import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io
import os
import json

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

        # --- EXPERIMENTAL: LOAD DESIGN FROM DESIGNER ---
        design_path = os.path.join(os.path.expanduser("~"), ".barcode_design.json")
        design = {}
        if os.path.exists(design_path):
            try:
                with open(design_path, 'r') as f:
                    design = json.load(f)
            except: pass

        if design:
            # RENDER FROM CUSTOM DESIGN
            # DRAW REFERENCE LINES
            col_split = int(width_px * 0.60)
            row_a_split = int(height_px * 0.60)
            
            # 1. Vertical Split
            draw.line([(col_split, 0), (col_split, height_px)], fill=0, width=2)
            # 2. Left Column Horizontal Split
            draw.line([(0, row_a_split), (col_split, row_a_split)], fill=0, width=2)
            # 3. Right Column Horizontal Splits
            for i in range(1, 4):
                draw.line([(col_split, i * 75), (width_px, i * 75)], fill=0, width=2)

            # 1. Product Name
            pos = design.get("product_name", [80, 20])
            draw.text((pos[0], pos[1]), data.get('description', 'PRODUCT NAME'), fill=0, font=font_huge)
            
            # 2. Product Code & Barcode
            pos_label = design.get("product_code", [80, 180])
            draw.text((pos_label[0], pos_label[1]), "PRODUCT CODE", fill=0, font=font_small_bold)
            
            barcode_value = data.get('barcode_value', '12345678')
            pos_bc = design.get("barcode", [80, 220])
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
                image.paste(bc_img, (int(pos_bc[0]), int(pos_bc[1])))
                # Barcode Value Text below barcode
                draw.text((int(pos_bc[0]), int(pos_bc[1]) + 45), barcode_value, fill=0, font=font_medium)
            except: pass

            # 3. Price
            pos = design.get("price", [500, 20])
            draw.text((pos[0], pos[1]), "PRICE (RM)", fill=0, font=font_small_bold)
            draw.text((pos[0], pos[1] + 25), data.get('unit_price_integer', '0.00'), fill=0, font=font_medium)

            # 4. Expiry
            pos = design.get("expiry", [500, 80])
            draw.text((pos[0], pos[1]), "EXPIRY", fill=0, font=font_small_bold)
            draw.text((pos[0], pos[1] + 25), data.get('remark', ''), fill=0, font=font_medium)

            # 5. Weight
            pos = design.get("weight", [500, 140])
            draw.text((pos[0], pos[1]), "NET WEIGHT", fill=0, font=font_small_bold)
            draw.text((pos[0], pos[1] + 25), data.get('net_weight', ''), fill=0, font=font_medium)

            # 6. Batch
            pos = design.get("batch", [500, 200])
            draw.text((pos[0], pos[1]), "BATCH", fill=0, font=font_small_bold)
            draw.text((pos[0], pos[1] + 25), data.get('batch', ''), fill=0, font=font_medium)

        else:
            # ORIGINAL GRID LAYOUT FALLBACK
            # 1. Split columns: Vertical line at 60% of width
            col_split = int(width_px * 0.60)
            draw.line([(col_split, 0), (col_split, height_px)], fill=0, width=2)
            # 2. Column A Rows (Left side): 60% / 40% split
            row_a_split = int(height_px * 0.60)
            draw.line([(0, row_a_split), (col_split, row_a_split)], fill=0, width=2)
            for i in range(1, 4):
                row_y = int(height_px * (i * 0.25))
                draw.line([(col_split, row_y), (width_px, row_y)], fill=0, width=2)

            description = data.get('description', 'NAMA PRODUK')
            draw.text((80, 20), "NAMA PRODUK / PRODUCT NAME", fill=0, font=font_small_bold)
            draw.text((80, 50), description, fill=0, font=font_huge)
            draw.text((80, 200), "KOD PRODUK / PRODUCT CODE", fill=0, font=font_small_bold)
            barcode_value = data.get('barcode_value', '12345678')
            try:
                from barcode import Code128
                rv = io.BytesIO()
                Code128(barcode_value, writer=ImageWriter()).write(rv, options={"write_text": False, "module_height": 10.0, "quiet_zone": 1.0, "background": "white", "foreground": "black"})
                rv.seek(0); bc_img = Image.open(rv).convert('1'); bc_img = bc_img.resize((300, 40)); image.paste(bc_img, (80, 220))
            except: pass
            draw.text((80, 265), barcode_value, fill=0, font=font_medium)

            col_b_x = col_split + 10
            draw.text((col_b_x, 10), "HARGA / PRICE (RM)", fill=0, font=font_small_bold)
            draw.text((col_b_x, 35), data.get('unit_price_integer', '0.00'), fill=0, font=font_medium)
            draw.text((col_b_x, 85), "GUNA SBL / EXP", fill=0, font=font_small_bold)
            draw.text((col_b_x, 110), data.get('remark', ''), fill=0, font=font_medium)
            draw.text((col_b_x, 160), "BERAT BERSIH / NET WT", fill=0, font=font_small_bold)
            draw.text((col_b_x, 185), data.get('net_weight', ''), fill=0, font=font_medium)
            draw.text((col_b_x, 235), "LOT / BATCH", fill=0, font=font_small_bold)
            draw.text((col_b_x, 260), data.get('batch', ''), fill=0, font=font_medium)

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
