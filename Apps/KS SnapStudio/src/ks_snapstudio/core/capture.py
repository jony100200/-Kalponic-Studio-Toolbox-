"""
Screen capture functionality for KS SnapStudio.
"""

import time
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import mss
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ScreenCapture:
    """Handles screen capture operations with area selection and optimization."""

    def __init__(self):
        self.sct = mss.mss()
        self._last_capture: Optional[np.ndarray] = None
        self._capture_time: float = 0.0

    def capture_fullscreen(self, monitor: int = 1) -> np.ndarray:
        """Capture the full screen of specified monitor."""
        try:
            monitor_info = self.sct.monitors[monitor]
            screenshot = self.sct.grab(monitor_info)

            # Convert to numpy array
            img_array = np.frombuffer(screenshot.bgra, dtype=np.uint8)
            img_array = img_array.reshape((screenshot.height, screenshot.width, 4))

            # Convert BGRA to RGB
            img_array = img_array[:, :, [2, 1, 0, 3]]  # BGR to RGB, keep alpha

            self._last_capture = img_array
            self._capture_time = time.time()

            logger.info(f"Captured fullscreen: {img_array.shape}")
            return img_array

        except Exception as e:
            logger.error(f"Fullscreen capture failed: {e}")
            raise

    def capture_area(self, x: int, y: int, width: int, height: int, monitor: int = 1) -> np.ndarray:
        """Capture a specific area of the screen."""
        try:
            monitor_info = self.sct.monitors[monitor]

            # Ensure coordinates are within monitor bounds
            x = max(monitor_info["left"], min(x, monitor_info["left"] + monitor_info["width"] - width))
            y = max(monitor_info["top"], min(y, monitor_info["top"] + monitor_info["height"] - height))

            capture_area = {
                "left": x,
                "top": y,
                "width": width,
                "height": height
            }

            screenshot = self.sct.grab(capture_area)

            # Convert to numpy array
            img_array = np.frombuffer(screenshot.bgra, dtype=np.uint8)
            img_array = img_array.reshape((screenshot.height, screenshot.width, 4))

            # Convert BGRA to RGB
            img_array = img_array[:, :, [2, 1, 0, 3]]

            self._last_capture = img_array
            self._capture_time = time.time()

            logger.info(f"Captured area: {x},{y} {width}x{height} -> {img_array.shape}")
            return img_array

        except Exception as e:
            logger.error(f"Area capture failed: {e}")
            raise

    def get_monitor_info(self) -> Dict[str, Any]:
        """Get information about available monitors."""
        monitors = []
        for i, monitor in enumerate(self.sct.monitors[1:], 1):  # Skip index 0 (all monitors)
            monitors.append({
                "id": i,
                "left": monitor["left"],
                "top": monitor["top"],
                "width": monitor["width"],
                "height": monitor["height"],
                "is_primary": i == 1
            })

        return {
            "count": len(monitors),
            "monitors": monitors
        }

    def get_last_capture(self) -> Optional[np.ndarray]:
        """Get the last captured image."""
        return self._last_capture

    def get_capture_age(self) -> float:
        """Get how old the last capture is in seconds."""
        if self._capture_time == 0.0:
            return float('inf')
        return time.time() - self._capture_time

    def save_capture(self, filepath: Path, quality: int = 95) -> bool:
        """Save the last capture to file."""
        if self._last_capture is None:
            logger.warning("No capture to save")
            return False

        try:
            # Convert to PIL Image (remove alpha channel for JPEG)
            if self._last_capture.shape[2] == 4:
                # Convert BGRA to RGB
                rgb_array = self._last_capture[:, :, :3]
            else:
                rgb_array = self._last_capture

            img = Image.fromarray(rgb_array)

            # Save with quality setting
            if filepath.suffix.lower() in ['.jpg', '.jpeg']:
                img.save(filepath, quality=quality, optimize=True)
            else:
                img.save(filepath)

            logger.info(f"Saved capture to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save capture: {e}")
            return False

    def __del__(self):
        """Clean up mss instance."""
        if hasattr(self, 'sct'):
            self.sct.close()</content>
<parameter name="filePath">E:\__Kalponic Studio Repositories\-Kalponic-Studio-Toolbox-\Apps\KS SnapStudio\src\ks_snapstudio\core\capture.py