"""UI components for KS AutoModel."""

from .desktop.app import run
from .desktop.main_window import MainWindow, create_main_window

__all__ = ["MainWindow", "create_main_window", "run"]
