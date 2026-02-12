"""System tray icon (pystray) integration. Opt-in; safe no-op when pystray missing."""
import threading
import logging

try:
    import pystray
    from PIL import Image, ImageDraw
except Exception:
    pystray = None


class TrayIcon:
    def __init__(self, on_capture_area, on_capture_window, on_capture_monitor, on_open_ui, on_exit):
        self.on_capture_area = on_capture_area
        self.on_capture_window = on_capture_window
        self.on_capture_monitor = on_capture_monitor
        self.on_open_ui = on_open_ui
        self.on_exit = on_exit
        self.icon = None
        self._thread = None

    def _create_image(self):
        # simple 16x16 icon
        img = Image.new('RGB', (64, 64), color=(30, 30, 30))
        d = ImageDraw.Draw(img)
        d.rectangle((8, 8, 56, 56), fill=(200, 80, 80))
        d.text((18, 18), "KS", fill=(255, 255, 255))
        return img

    def _run(self):
        if pystray is None:
            logging.info("pystray not available; tray disabled.")
            return
        img = self._create_image()
        menu = pystray.Menu(
            pystray.MenuItem('Capture Area', lambda : self.on_capture_area()),
            pystray.MenuItem('Capture Window', lambda : self.on_capture_window()),
            pystray.MenuItem('Capture Monitor', lambda : self.on_capture_monitor()),
            pystray.MenuItem('Open UI', lambda : self.on_open_ui()),
            pystray.MenuItem('Exit', lambda : self.on_exit()),
        )
        self.icon = pystray.Icon('ks_snapclip', img, 'KS SnapClip', menu)
        self.icon.run()

    def start(self):
        if pystray is None:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
