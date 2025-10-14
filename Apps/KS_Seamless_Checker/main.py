from src.gui import SeamlessCheckerGUI
from PySide6.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SeamlessCheckerGUI()
    window.show()
    sys.exit(app.exec())