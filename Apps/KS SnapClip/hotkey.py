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
        self._enabled = True

    def pause(self):
        self._enabled = False

    def resume(self):
        self._enabled = True

    def enabled(self) -> bool:
        return self._enabled

    def add_hotkey(self, combo: str, callback):
        """Add a hotkey combo string (pynput style) and a callback.

        The callback is wrapped so hotkeys can be paused/resumed.
        """
        def _wrapped():
            if not self._enabled:
                return
            try:
                callback()
            except Exception:
                pass
        self._hotkeys[combo] = _wrapped

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

    def update_hotkeys(self, hotkey_map: dict):
        """Replace current hotkeys with a new hotkey->callback mapping and restart listener if running."""
        # wrap callbacks to respect pause/resume state
        wrapped = {}
        for combo, cb in hotkey_map.items():
            def _make(cb_):
                def _wrapped():
                    if not self._enabled:
                        return
                    try:
                        cb_()
                    except Exception:
                        pass
                return _wrapped
            wrapped[combo] = _make(cb)
        self._hotkeys = wrapped
        # if a listener is running, restart it to pick up changes
        if self._running:
            self.stop()
            self.start()
