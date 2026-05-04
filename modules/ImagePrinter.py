import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io
import os
import json
import textwrap

class ImagePrinter:
    def __init__(self, dpi=203):
        self.dpi = dpi
        # dots per mm: 203 DPI / 25.4 mm/in approx 8 dots/mm
        self.dpmm = dpi / 25.4
        
    def render_fun_bake_label(self, data):
        """
        Renders the variable-data portion of the Fun Bake label (75mm x 50mm).
        The top section (company header) is pre-printed on the sticker stock,
        so this image leaves the top blank and only draws the data rows below.

        Layout (top-to-bottom):
          [blank — pre-printed header area]
          ─────────────────────────────────
          NAMA PRODUK  产品名称  PRODUCT NAME
          <description line 1 & 2 — large bold>
          ─────────────────────────────────────────────────────
          KOD PRODUK 产品编号  PRODUCT CODE │ HARGA  价格  PRICE
          [barcode]                         │ RM xx.xx / <weight>
          <barcode value>                   │
          ─────────────────────────────────────────────────────
          GUNA SBL  期满  EXP.   LOT  厂家编号  BATCH
          <remark / expiry>                    <batch>
        """
        import platform

        W, H = 750, 400

        # The pre-printed header occupies roughly the top 27% of the label.
        # We leave that area blank (white = no heat = pre-print shows through).
        HEADER_SKIP = 108   # px of blank space at top matching the header height
        COL          = 370  # x of vertical divider between barcode and price columns
        PAD          = 8    # inner horizontal padding

        NAME_Y = HEADER_SKIP
        MID_Y  = NAME_Y + 108
        BOT_Y  = MID_Y  + 118

        image = Image.new('1', (W, H), 1)
        draw  = ImageDraw.Draw(image)

        # ── fonts ──────────────────────────────────────────────────────────
        if platform.system() == "Windows":
            fp = "C:\\Windows\\Fonts\\msyh.ttc"   if os.path.exists("C:\\Windows\\Fonts\\msyh.ttc")   else "arial.ttf"
            fb = "C:\\Windows\\Fonts\\msyhbd.ttc"  if os.path.exists("C:\\Windows\\Fonts\\msyhbd.ttc") else fp
        else:
            fp = "/usr/share/fonts/google-droid-sans-fonts/DroidSansFallbackFull.ttf"
            fb = fp

        try:
            f_label  = ImageFont.truetype(fp, 13)   # section header labels
            f_name   = ImageFont.truetype(fb, 26)   # product name (large bold)
            f_med    = ImageFont.truetype(fp, 17)   # barcode value / secondary text
            f_price  = ImageFont.truetype(fb, 22)   # price
            f_bot    = ImageFont.truetype(fb, 28)   # expiry / batch value
        except:
            d = ImageFont.load_default()
            f_label = f_name = f_med = f_price = f_bot = d

        # ── 1. PRODUCT NAME SECTION ────────────────────────────────────────
        draw.text((PAD, NAME_Y + 4), "NAMA PRODUK  产品名称  PRODUCT NAME", fill=0, font=f_label)

        description = data.get('description', '')
        for i, line in enumerate(textwrap.wrap(description, width=26)[:2]):
            draw.text((PAD, NAME_Y + 24 + i * 32), line, fill=0, font=f_name)

        # ── 2. MIDDLE SECTION — barcode (left) + price (right) ────────────
        draw.line([(0, MID_Y), (W, MID_Y)], fill=0, width=2)
        draw.line([(COL, MID_Y), (COL, BOT_Y)], fill=0, width=2)

        # Left: product code + barcode
        draw.text((PAD, MID_Y + 4), "KOD PRODUK  产品编号  PRODUCT CODE", fill=0, font=f_label)

        barcode_value = data.get('barcode_value', '000000')
        try:
            from barcode import Code128
            rv = io.BytesIO()
            Code128(barcode_value, writer=ImageWriter()).write(rv, options={
                "write_text": False, "module_height": 5.0, "module_width": 0.22,
                "quiet_zone": 1.0, "background": "white", "foreground": "black"
            })
            rv.seek(0)
            bc = Image.open(rv).convert('1')
            bw, bh = bc.size
            th = 60
            tw = min(int(bw * th / bh), COL - PAD * 2)
            bc = bc.resize((tw, th))
            image.paste(bc, (PAD, MID_Y + 22))
            draw.text((PAD, MID_Y + 22 + th + 2), barcode_value, fill=0, font=f_med)
        except Exception as e:
            print(f"Barcode render error: {e}")
            draw.text((PAD, MID_Y + 30), barcode_value, fill=0, font=f_med)

        # Right: price
        rx = COL + PAD
        draw.text((rx, MID_Y + 4), "HARGA  价格  PRICE", fill=0, font=f_label)
        price      = data.get('unit_price_integer', '0.00')
        net_weight = data.get('net_weight', '')
        price_line = f"RM {price}"
        if net_weight:
            price_line += f" / {net_weight}"
        draw.text((rx, MID_Y + 30), price_line, fill=0, font=f_price)

        # ── 3. BOTTOM SECTION — expiry + batch ────────────────────────────
        draw.line([(0, BOT_Y), (W, BOT_Y)], fill=0, width=2)
        draw.text((PAD, BOT_Y + 4),
                  "GUNA SBL  期满  EXP.     LOT  厂家编号  BATCH",
                  fill=0, font=f_label)

        remark = data.get('remark', '')
        batch  = data.get('batch', '')
        draw.text((PAD, BOT_Y + 22), remark, fill=0, font=f_bot)
        if batch:
            draw.text((COL + PAD, BOT_Y + 22), batch, fill=0, font=f_bot)

        # ── outer border (full label) ──────────────────────────────────────
        draw.rectangle([(0, 0), (W - 1, H - 1)], outline=0)

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
