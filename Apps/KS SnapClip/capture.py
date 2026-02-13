"""KS SnapClip capture helpers using MSS for robust multi-monitor screenshots.

Supports: fullscreen (monitor), active window, and area selection via overlay.
"""

import time
from typing import Optional, Tuple
from PIL import Image

# Use mss for reliable screen capture
try:
    import mss
    import mss.tools
except Exception:
    mss = None
    # Provide a minimal dummy context so tests can monkeypatch 'mss' without import error
    class _DummyMSS:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        @property
        def monitors(self):
            # single monitor fallback
            return [{"left": 0, "top": 0, "width": 800, "height": 600}]
        def grab(self, monitor):
            raise RuntimeError("mss not available")
    mss = _DummyMSS()

try:
    import win32gui
except Exception:
    win32gui = None

import area_overlay


def _mss_shot_region(left: int, top: int, width: int, height: int) -> Image.Image:
    with mss.mss() as s:
        monitor = {"left": left, "top": top, "width": width, "height": height}
        im = s.grab(monitor)
        # Convert to PIL Image (RGB)
        img = Image.frombytes("RGB", im.size, im.rgb)
        return img


def capture_fullscreen(monitor_index: int = 0) -> Image.Image:
    with mss.mss() as s:
        # mss.monitors[0] is the virtual full set; monitors[1:] are physical monitors
        monitors = s.monitors
        if monitor_index + 1 < len(monitors):
            mon = monitors[monitor_index + 1]
        else:
            mon = monitors[0]
        left, top, width, height = mon["left"], mon["top"], mon["width"], mon["height"]
        return _mss_shot_region(left, top, width, height)


def capture_active_window() -> Optional[Image.Image]:
    if win32gui is None:
        return None
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0:
        return None
    return _mss_shot_region(left, top, width, height)


def capture_rect(left: int, top: int, width: int, height: int) -> Optional[Image.Image]:
    """Capture the specified rectangle (absolute screen coords) and return a PIL Image."""
    if width <= 0 or height <= 0:
        return None
    try:
        return _mss_shot_region(left, top, width, height)
    except Exception:
        return None

def capture_area(delay: float = 0.0, monitor_index: int = 0) -> Optional[Image.Image]:
    """Capture an area selected by the user using the overlay.

    Returns PIL.Image or None if cancelled.
    """
    if delay > 0:
        time.sleep(delay)

    region = area_overlay.select_region(monitor_index=monitor_index)
    if not region:
        return None

    left, top, right, bottom = region
    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0:
        return None

    # small delay to ensure overlay has been destroyed and OS repainted
    time.sleep(0.05)

    try:
        return _mss_shot_region(left, top, width, height)
    except Exception:
        return None
