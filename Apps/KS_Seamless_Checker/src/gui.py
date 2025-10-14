from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QFileDialog, QMessageBox, QScrollArea, QProgressBar, QFrame
from PySide6.QtGui import QPalette, QColor, QFont, QPixmap
from PySide6.QtCore import Qt, QThread, Signal
import cv2
import os
import json
import sys
from .batch_processor import BatchProcessor
from .image_checker import ImageChecker

class BatchWorker(QThread):
    progress = Signal(int)
    finished = Signal(list)

    def __init__(self, processor, folder):
        super().__init__()
        self.processor = processor
        self.folder = folder

    def run(self):
        results = []
        files = [f for f in os.listdir(self.folder) if any(f.lower().endswith(ext) for ext in self.processor.supported_formats)]
        total = len(files)
        for i, file in enumerate(files):
            img_path = os.path.join(self.folder, file)
            img = cv2.imread(img_path)  # Assuming cv2 imported in processor
            if img is not None:
                seamless = self.processor.checker.is_seamless(img)
                preview = self.processor.checker.create_tiled_preview(img)
                preview_path = os.path.join(self.processor.preview_folder, f"tiled_{file}")
                preview.save(preview_path)
                results.append({
                    'file': file,
                    'seamless': seamless,
                    'preview_path': preview_path
                })
            self.progress.emit(int((i + 1) / total * 100))
        self.finished.emit(results)

class SeamlessCheckerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KS Seamless Checker")
        self.setGeometry(100, 100, 800, 600)
        self.config = self.load_config()
        self.checker = ImageChecker(self.config['seam_threshold'])
        self.processor = BatchProcessor(self.checker, self.config['supported_formats'], self.config['preview_folder'])
        self.setup_dark_theme()
        self.setup_ui()
        self.worker = None

    def load_config(self):
        with open('config.json', 'r') as f:
            return json.load(f)

    def setup_dark_theme(self):
        palette = QPalette()
        # Muted dark palette with softened text (avoid harsh pure white)
        palette.setColor(QPalette.Window, QColor(40, 42, 45))        # main window
        palette.setColor(QPalette.WindowText, QColor(230, 230, 230))  # soft off-white for labels
        palette.setColor(QPalette.Base, QColor(50, 52, 56))          # input/text background
        palette.setColor(QPalette.AlternateBase, QColor(43, 45, 48))
        palette.setColor(QPalette.ToolTipBase, QColor(230, 230, 230))
        palette.setColor(QPalette.ToolTipText, QColor(20, 20, 20))
        palette.setColor(QPalette.Text, QColor(225, 225, 225))        # textarea text
        palette.setColor(QPalette.Button, QColor(60, 62, 66))         # muted button background
        palette.setColor(QPalette.ButtonText, QColor(230, 230, 230))  # muted button text
        palette.setColor(QPalette.BrightText, QColor(220, 80, 80))
        # Accent: slightly desaturated teal/blue for links and highlights
        palette.setColor(QPalette.Link, QColor(88, 173, 212))
        palette.setColor(QPalette.Highlight, QColor(88, 173, 212))
        palette.setColor(QPalette.HighlightedText, QColor(20, 20, 20))
        self.setPalette(palette)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

    title_label = QLabel("KS Seamless Checker")
    title_font = QFont("Segoe UI", 16, QFont.Bold)
    title_label.setFont(title_font)
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setStyleSheet('color: #e6e6e6;')
    layout.addWidget(title_label)

    folder_layout = QHBoxLayout()
        folder_label = QLabel("Select Folder:")
    folder_label.setStyleSheet('color: #dcdcdc;')
    folder_layout.addWidget(folder_label)
        self.folder_entry = QLineEdit()
        self.folder_entry.setPlaceholderText("Enter or browse folder path")
        self.folder_entry.setToolTip("Path to folder containing images")
    self.folder_entry.setStyleSheet("background: #35363a; color: #e6e6e6; padding:6px; border-radius:4px;")
    folder_layout.addWidget(self.folder_entry)
    browse_button = QPushButton("Browse")
    browse_button.setToolTip("Open folder dialog")
    browse_button.clicked.connect(self.browse_folder)
    browse_button.setCursor(Qt.PointingHandCursor)
    browse_button.setStyleSheet("QPushButton{background:#4b5056;color:#e6e6e6;padding:6px 10px;border-radius:6px;} QPushButton:hover{background:#5a6066}")
    folder_layout.addWidget(browse_button)
        layout.addLayout(folder_layout)

        process_button = QPushButton("Process Batch")
        process_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        process_button.setToolTip("Start batch processing")
        process_button.clicked.connect(self.process_batch)
        process_button.setCursor(Qt.PointingHandCursor)
        process_button.setStyleSheet(
            "QPushButton{background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #5a9abf, stop:1 #4f88ad); color:#0f1416; padding:8px 12px; border-radius:8px;}"
            "QPushButton:hover{background:#68a9d4;}"
        )
        layout.addWidget(process_button)

    self.progress_bar = QProgressBar()
    self.progress_bar.setVisible(False)
    self.progress_bar.setStyleSheet("QProgressBar{background:#3b3b3b; color:#e6e6e6; border-radius:6px; height:12px;} QProgressBar::chunk{background:#58add0; border-radius:6px}")
    layout.addWidget(self.progress_bar)

    results_layout = QHBoxLayout()

    left_frame = QFrame()
    left_layout = QVBoxLayout(left_frame)
    results_label = QLabel("Results:")
    results_label.setStyleSheet('color: #dcdcdc;')
    left_layout.addWidget(results_label)
    self.results_text = QTextEdit()
    self.results_text.setReadOnly(True)
    self.results_text.setToolTip("Processing results")
    self.results_text.setStyleSheet("background:#2f3134;color:#e6e6e6;padding:8px;border-radius:6px;")
    left_layout.addWidget(self.results_text)

    right_frame = QFrame()
    right_layout = QVBoxLayout(right_frame)
    preview_label = QLabel("Preview:")
    preview_label.setStyleSheet('color: #dcdcdc;')
    right_layout.addWidget(preview_label)
    self.preview_label = QLabel()
    self.preview_label.setFixedSize(220, 220)
    self.preview_label.setStyleSheet("background:#35363a;border:1px solid #505357;border-radius:6px;")
    self.preview_label.setToolTip("Tiled preview of last processed image")
    right_layout.addWidget(self.preview_label, alignment=Qt.AlignTop)

    results_layout.addWidget(left_frame, stretch=3)
    results_layout.addWidget(right_frame, stretch=1)
    layout.addLayout(results_layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_entry.setText(folder)

    def process_batch(self):
        folder = self.folder_entry.text()
        if not os.path.isdir(folder):
            QMessageBox.critical(self, "Error", "Invalid folder path")
            return
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.worker = BatchWorker(self.processor, folder)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_batch_finished)
        self.worker.start()

    def on_batch_finished(self, results):
        self.progress_bar.setVisible(False)
        self.results_text.clear()
        for res in results:
            status = "Seamless" if res['seamless'] else "Not Seamless"
            self.results_text.append(f"{res['file']}: {status}\nPreview: {res['preview_path']}\n")
            # Show last preview
            if res['preview_path']:
                pixmap = QPixmap(res['preview_path'])
                self.preview_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
        QMessageBox.information(self, "Done", f"Processed {len(results)} images. Previews saved.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SeamlessCheckerGUI()
    window.show()
    sys.exit(app.exec())