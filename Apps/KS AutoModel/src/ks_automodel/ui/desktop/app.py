"""Application bootstrap for KS AutoModel desktop UI."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .main_window import create_main_window


def run() -> None:
    app = QApplication(sys.argv)
    window = create_main_window()
    window.show()
    sys.exit(app.exec())


__all__ = ["run"]
