"""Hotkey manager using pynput. Opt-in; safe when pynput missing (no-op).
"""
import threading
import logging

try:
    from pynput import keyboard
except Exception:
    keyboard = None


class HotkeyManager:
    def __init__(self):
        self._hotkeys = {}
        self._listener = None
        self._thread = None
        self._running = False

    def add_hotkey(self, combo: str, callback):
        """Add a hotkey combo string (pynput style) and a callback."""
        self._hotkeys[combo] = callback

    def _run_listener(self):
        if keyboard is None:
            logging.info("pynput not available; hotkeys disabled.")
            return

        hotkey_map = {}
        for combo, cb in self._hotkeys.items():
            hotkey_map[combo] = cb

        # Use GlobalHotKeys
        with keyboard.GlobalHotKeys(hotkey_map) as h:
            self._listener = h
            h.join()

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_listener, daemon=True)
        self._thread.start()

    def stop(self):
        if keyboard and self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
        self._running = False
