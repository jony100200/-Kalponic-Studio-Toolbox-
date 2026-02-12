"""KS SnapClip clipboard helpers for Windows (fallback saves to temp file if no win32 libs).

This module provides a simple `copy_image` function that attempts to copy a PIL image
into the Windows clipboard using `pywin32`. If pywin32 isn't available, it falls back
to saving the image to a temporary file and returning its path (so UI can notify the user).
"""

from PIL import Image
import tempfile
import os


class ClipboardProvider:
    def copy(self, img: Image.Image) -> dict:
        raise NotImplementedError()


class WindowsClipboard(ClipboardProvider):
    def copy(self, img: Image.Image) -> dict:
        try:
            import win32clipboard
            import win32con
            import io

            output = io.BytesIO()
            img.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]  # BMP file header adjustment for CF_DIB
            output.close()

            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_DIB, data)
            finally:
                win32clipboard.CloseClipboard()
            return {"success": True, "message": "Image copied to clipboard"}
        except Exception as e:
            # fallback: save to temp file
            fd, path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            img.save(path)
            return {"success": False, "message": f"pywin32 not available or failed: {e}. Saved to {path}", "path": path}


# Provide a default provider for imports
default_provider = WindowsClipboard()
