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