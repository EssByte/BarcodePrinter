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
            font_huge = ImageFont.truetype(font_path, 60)
        except:
            font_small = font_medium = font_large = font_price = font_huge = ImageFont.load_default()

        # DEBUG LAYOUT 2: Shifted and Huge
        description = data.get('description', 'TEST')
        
        # Huge markers at corners
        draw.line([(0,0), (60,60)], fill=0, width=10)
        draw.line([(width_px,0), (width_px-60, 60)], fill=0, width=10)
        draw.line([(0, height_px), (60, height_px-60)], fill=0, width=10)
        draw.line([(width_px, height_px), (width_px-60, height_px-60)], fill=0, width=10)
        
        # Top Text (No anchor)
        draw.text((150, 10), "TOP START", fill=0, font=font_huge)
        
        # Barcode shifted right
        barcode_value = data.get('barcode_value', '12345678')
        try:
            from barcode import Code128
            from barcode.writer import ImageWriter
            import io
            rv = io.BytesIO()
            Code128(barcode_value, writer=ImageWriter()).write(rv, options={"write_text": False, "module_height": 10.0, "quiet_zone": 1.0, "background": "white", "foreground": "black"})
            rv.seek(0)
            bc_img = Image.open(rv).convert('1')
            bc_img = bc_img.resize((400, 150))
            image.paste(bc_img, (200, 100)) # Shifted Right
        except:
            draw.text((150, 150), "[ERROR]", fill=0, font=font_huge)

        # Bottom Text
        draw.text((150, 270), f"BC: {barcode_value}", fill=0, font=font_huge)
        draw.text((150, 340), "BOTTOM END", fill=0, font=font_large)

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
