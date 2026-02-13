from datetime import datetime
import re


def _sanitize_window_title(title: str) -> str:
    if not title:
        return ""
    # remove problematic characters
    s = re.sub(r'[\\/:*?"<>|]', '', title)
    s = s.strip().replace(' ', '_')
    return s[:64]


def generate_filename(prefix: str, window_title: str, timestamp: datetime) -> str:
    ts = timestamp.strftime('%Y%m%d_%H%M%S')
    w = _sanitize_window_title(window_title)
    if w:
        return f"{prefix}_{w}_{ts}.png"
    return f"{prefix}_{ts}.png"


def instant_paste(timeout: float = 0.2) -> bool:
    """Simulate Ctrl+V (paste) using pynput. Returns True on success."""
    try:
        from pynput.keyboard import Controller, Key
        kb = Controller()
        kb.press(Key.ctrl)
        kb.press('v')
        kb.release('v')
        kb.release(Key.ctrl)
        return True
    except Exception:
        return False


def optimize_image(img, max_width: int = 1024, convert_to_png: bool = True):
    """Simple AI optimization: resize if wider than max_width and convert mode if requested."""
    try:
        from PIL import Image
        out = img.copy()
        w, h = out.size
        if w > max_width:
            new_h = int(max_width * h / w)
            out = out.resize((max_width, new_h), Image.LANCZOS)
        if convert_to_png:
            out = out.convert("RGBA")
        return out
    except Exception:
        # on error, return original
        return img


def validate_hotkeys(hotkeys: dict) -> (bool, str):
    """Validate a mapping of name->hotkey_string.

    Returns (True, '') if valid. If invalid returns (False, 'message').
    Checks for empties and duplicates.
    """
    seen = {}
    for name, val in hotkeys.items():
        if not val or not isinstance(val, str) or not val.strip():
            return False, f"Hotkey for {name} is empty or invalid"
        norm = val.strip().lower()
        if norm in seen:
            return False, f"Hotkey conflict: {name} and {seen[norm]} both use '{val}'"
        seen[norm] = name
    return True, ""
