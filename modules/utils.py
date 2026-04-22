import os
import sys
import re

def resource_path(relative_path, logger=None):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Fall back to the current working directory in development mode
        base_path = os.path.abspath(".")

    absolute_path = os.path.join(base_path, relative_path)
    if logger:
        logger.debug(f"Resolved absolute path: {absolute_path}")

    return absolute_path

def split_description(description, max_chars=25):
    """Split description into two lines for printer labels."""
    if len(description) <= max_chars:
        return description, ""
    
    split_pos = description.rfind(' ', 0, max_chars + 1)
    if split_pos == -1:
        split_pos = max_chars
        
    return description[:split_pos].strip(), description[split_pos:].strip()

def replace_placeholders(template, logger=None, **kwargs):
    """Replace {{placeholder}} with actual data in the template."""
    def replace(match):
        key = match.group(1)
        if key not in kwargs:
            if logger:
                logger.warning(f"Missing placeholder for: {key}")
            return f"{{{{{key}}}}}"
        return str(kwargs[key])
    return re.sub(r'{{(.*?)}}', replace, template)
