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
        
        # Fonts
        font_path = "/usr/share/fonts/google-noto-sans-cjk-vf-fonts/NotoSansCJK-VF.ttc"
        try:
            # We use multiple scales for different parts of the label
            font_small = ImageFont.truetype(font_path, 18)
            font_medium = ImageFont.truetype(font_path, 24)
            font_large = ImageFont.truetype(font_path, 35)
            font_price = ImageFont.truetype(font_path, 40)
        except:
            font_small = font_medium = font_large = font_price = ImageFont.load_default()

        # Draw Headers
        draw.text((width_px//2, 25), "nama produk / product name", fill=0, anchor="mm", font=font_small)
        description = data.get('description', '')
        draw.text((width_px//2, 60), description, fill=0, anchor="mm", font=font_large)

        # Draw Box (60, 95) to (590, 240)
        draw.line([(60, 95), (590, 95)], fill=0, width=2)   # Top
        draw.line([(60, 240), (590, 240)], fill=0, width=2) # Bottom
        draw.line([(60, 95), (60, 240)], fill=0, width=2)   # Left
        draw.line([(440, 95), (440, 240)], fill=0, width=2) # Middle
        draw.line([(590, 95), (590, 240)], fill=0, width=2) # Right

        # Left Column: Product Code
        draw.text((80, 115), "kod produk / product code", fill=0, font=font_small)
        
        # Generate Barcode
        barcode_value = data.get('barcode_value', '12345678')
        try:
            from barcode import Code128
            from barcode.writer import ImageWriter
            import io
            
            # Create barcode image buffer
            rv = io.BytesIO()
            Code128(barcode_value, writer=ImageWriter()).write(rv, options={
                "write_text": False, 
                "module_height": 10.0, 
                "quiet_zone": 1.0,
                "background": "white",
                "foreground": "black"
            })
            rv.seek(0)
            bc_img = Image.open(rv).convert('1')
            
            # Scale barcode to fit the allocated space
            bc_img = bc_img.resize((300, 50))
            image.paste(bc_img, (80, 140))
        except Exception as e:
            draw.text((80, 140), f"[Barcode: {barcode_value}]", fill=0, font=font_small)

        draw.text((80, 205), barcode_value, fill=0, font=font_medium)

        # Right Column: Price
        draw.text((455, 115), "harga / price", fill=0, font=font_small)
        price = data.get('unit_price_integer', '0.00')
        draw.text((455, 165), f"RM {price}", fill=0, font=font_price)

        # Footer: Expire Date / Remark
        draw.text((80, 260), "expire date", fill=0, font=font_small)
        remark = data.get('remark', '')
        draw.text((80, 295), remark, fill=0, font=font_large)

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
