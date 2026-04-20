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
        Renders the Fun Bake label (75mm x 50mm) as a monochrome image.
        data = {
            'description': '...',
            'barcode_value': '...',
            'remark': '...',
            'unit_price_integer': '...'
        }
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
        
        font_small = font_large = font_extra_large = None
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    font_small = ImageFont.truetype(font_path, 16)
                    font_large = ImageFont.truetype(font_path, 24)
                    font_extra_large = ImageFont.truetype(font_path, 32)
                    break
            except Exception as e:
                print(f"Failed to load font {font_path}: {e}")

        if not font_small:
            print("No Chinese-compatible font found. Falling back to default.")
            font_small = ImageFont.load_default()
            font_large = ImageFont.load_default()
            font_extra_large = ImageFont.load_default()

        # Layout Constants (based on the aggressive shift logic)
        left_margin = 80
        center_x = width_px // 2 + 30 # slight right bias
        
        # 1. Header: "nama produk / product name"
        draw.text((center_x, 20), "nama produk / product name", fill=0, anchor="mt", font=font_small)
        
        # 2. Description
        # Use extra large for Chinese characters to be readable
        draw.text((center_x, 50), data.get('description', ''), fill=0, anchor="mt", font=font_extra_large)
        
        # 3. Horizontal Bar
        draw.rectangle([60, 95, 590, 97], fill=0)
        
        # 4. Vertical Bar
        draw.rectangle([440, 95, 442, 240], fill=0)
        
        # 5. Right Border Bar
        draw.rectangle([590, 95, 592, 240], fill=0)
        
        # 6. Left side: "kod produk / product code"
        draw.text((80, 115), "kod produk / product code", fill=0, font=font_small)
        
        # 7. Generate Barcode (Code128)
        code_class = barcode.get_barcode_class('code128')
        rv = io.BytesIO()
        # module_width 0.2mm is approx 1.6 dots at 8dpmm. 
        code_obj = code_class(data.get('barcode_value', '0000000'), writer=ImageWriter())
        # Disable text as we draw it manually
        code_obj.write(rv, options={
            "module_width": 0.25, 
            "module_height": 10.0, 
            "font_size": 0, 
            "text_distance": 0,
            "quiet_zone": 1.0,
            "write_text": False
        })
        
        barcode_img = Image.open(rv).convert('1')
        # Resize/Crop barcode to fit our area (approx 350px wide, 60px high)
        max_barcode_w = 340
        max_barcode_h = 60
        
        # Calculate aspect ratio
        w_ratio = max_barcode_w / barcode_img.width
        h_ratio = max_barcode_h / barcode_img.height
        ratio = min(w_ratio, h_ratio)
        new_size = (int(barcode_img.width * ratio), int(barcode_img.height * ratio))
        barcode_img = barcode_img.resize(new_size, Image.NEAREST)
        
        # Paste barcode
        image.paste(barcode_img, (80, 140))
        
        # Value below barcode
        draw.text((80, 205), data.get('barcode_value', ''), fill=0, font=font_small)
        
        # 8. Right side: "harga / price"
        draw.text((455, 115), "harga / price", fill=0, font=font_small)
        draw.text((455, 160), f"RM {data.get('unit_price_integer', '0')}", fill=0, font=font_large)
        
        # 9. Bottom Horizontal Bar
        draw.rectangle([60, 240, 590, 242], fill=0)
        
        # 10. Bottom: "expire date" and Remark
        draw.text((80, 260), "expire date", fill=0, font=font_small)
        draw.text((80, 290), data.get('remark', ''), fill=0, font=font_large)
        
        return image

    def to_tpsl_bitmap(self, image, x=0, y=0):
        """
        Converts a Pillow image to a TPSL BITMAP command string.
        Format: BITMAP x,y,width_bytes,height,mode,data
        """
        # Ensure image is monochrome
        image = image.convert('1')
        
        # IMPORTANT: Pillow '1' mode uses 0 for Black and 1 for White.
        # TSC printers use 1 for Black (Heat) and 0 for White.
        # We must invert the image bits.
        image = Image.eval(image, lambda x: 0 if x == 1 else 1)
        
        width, height = image.size
        width_bytes = (width + 7) // 8
        
        # Get raw data from Pillow
        data = image.tobytes()
        
        # BITMAP command header
        # Using mode 0 (Overwrite)
        header = f"BITMAP {x},{y},{width_bytes},{height},0,".encode('utf-8')
        footer = b"\r\n"
        
        return header + data + footer

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
