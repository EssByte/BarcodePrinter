"""
Size Converter: Handle millimeter to pixel conversions for label printing.

Standard label sizes supported:
- 35 x 25 mm
- 75 x 50 mm
- 60 x 40 mm
- Custom sizes

Uses 72 DPI (standard screen DPI) for conversion.
"""

class SizeConverter:
    """Convert between millimeters and pixels for label design."""
    
    # Standard label sizes (width x height in mm)
    LABEL_SIZES = {
        "35 x 25 mm": (35, 25),
        "75 x 50 mm": (75, 50),
        "60 x 40 mm": (60, 40),
    }
    
    # DPI settings
    DEFAULT_DPI = 72  # Screen DPI
    PRINTER_DPI = 203  # Typical thermal printer DPI (actual printing)
    
    def __init__(self, dpi=DEFAULT_DPI):
        """Initialize converter with specified DPI."""
        self.dpi = dpi
        self.pixels_per_mm = dpi / 25.4  # 25.4 mm = 1 inch
    
    def mm_to_pixels(self, mm):
        """Convert millimeters to pixels."""
        return int(mm * self.pixels_per_mm)
    
    def pixels_to_mm(self, pixels):
        """Convert pixels back to millimeters."""
        return pixels / self.pixels_per_mm
    
    def get_label_size_pixels(self, label_size_name):
        """Get label dimensions in pixels.
        
        Args:
            label_size_name: Key from LABEL_SIZES dict, e.g., "75 x 50 mm"
        
        Returns:
            (width_px, height_px) tuple
        """
        if label_size_name not in self.LABEL_SIZES:
            return None
        
        width_mm, height_mm = self.LABEL_SIZES[label_size_name]
        width_px = self.mm_to_pixels(width_mm)
        height_px = self.mm_to_pixels(height_mm)
        
        return (width_px, height_px)
    
    def get_all_sizes(self):
        """Return list of available label size names."""
        return list(self.LABEL_SIZES.keys())
    
    def get_canvas_margin_pixels(self, margin_mm=3):
        """Get margin in pixels (default 3mm on each side)."""
        return self.mm_to_pixels(margin_mm)
    
    def validate_position(self, x_px, y_px, width_px, height_px, canvas_width_px, canvas_height_px):
        """Check if element fits within canvas."""
        return (x_px >= 0 and y_px >= 0 and 
                x_px + width_px <= canvas_width_px and
                y_px + height_px <= canvas_height_px)
