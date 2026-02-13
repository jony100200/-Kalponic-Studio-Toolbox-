import threading
import time
from types import SimpleNamespace
from ui import startup_sequence


class DummyApp(SimpleNamespace):
    def __init__(self):
        super().__init__()
        self.withdrawn = False
    def withdraw(self):
        self.withdrawn = True
    def deiconify(self):
        self.withdrawn = False


class DummySettings:
    def __init__(self):
        self.hotkey_area = '<ctrl>+<shift>+1'
        self.hotkey_window = '<ctrl>+<shift>+2'
        self.hotkey_monitor = '<ctrl>+<shift>+3'
        self.first_run = True


def test_startup_sequence_runs_and_minimizes(tmp_path, monkeypatch):
    app = DummyApp()
    settings = DummySettings()
    called = {'tray': False}

    def start_tray():
        called['tray'] = True

    # speed up timer
    startup_sequence(app, settings, start_tray, delay_sec=0.05)
    time.sleep(0.1)

    assert called['tray'] is True
    assert app.withdrawn is True
    assert settings.first_run is False
