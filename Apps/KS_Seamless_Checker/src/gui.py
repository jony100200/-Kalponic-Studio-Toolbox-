from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QLineEdit, QFileDialog, QMessageBox,
                               QProgressBar, QFrame, QDialog, QFormLayout, QSpinBox, QDialogButtonBox,
                               QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView)
from PySide6.QtGui import QPalette, QColor, QFont, QPixmap, QIcon
from PySide6.QtCore import Qt, QThread, Signal, QSize
import cv2
import os
import json
import sys
from .batch_processor import BatchProcessor
from .image_checker import ImageChecker


class BatchWorker(QThread):
    progress = Signal(int)
    finished = Signal(list)

    def __init__(self, processor, path):
        super().__init__()
        self.processor = processor
        # path may be a folder or a single file
        self.path = path

    def run(self):
        results = []
        # If path is a file, process single file
        if os.path.isfile(self.path):
            r = self.processor.process_file(self.path)
            if r:
                results.append(r)
            self.progress.emit(100)
            self.finished.emit(results)
            return

        # Otherwise treat as folder
        try:
            files = [f for f in os.listdir(self.path) if any(f.lower().endswith(ext) for ext in self.processor.supported_formats)]
        except Exception:
            files = []
        total = len(files)
        for i, file in enumerate(files):
            img_path = os.path.join(self.path, file)
            r = self.processor.process_file(img_path)
            if r:
                results.append(r)
            if total:
                self.progress.emit(int((i + 1) / total * 100))
        self.finished.emit(results)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        if not os.path.exists(config_path):
            self.config = {}
        else:
            with open(config_path, 'r') as f:
                self.config = json.load(f)

        layout = QFormLayout(self)
        self.spin = QSpinBox()
        self.spin.setRange(0, 100000)
        self.spin.setValue(self.config.get('seam_threshold', 10))
        layout.addRow('Seam threshold', self.spin)

        self.preview_line = QLineEdit()
        self.preview_line.setText(self.config.get('preview_folder', 'previews'))
        layout.addRow('Preview folder', self.preview_line)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def save(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        self.config['seam_threshold'] = int(self.spin.value())
        self.config['preview_folder'] = self.preview_line.text()
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        self.accept()


class HeaderBar(QWidget):
    """Custom header bar for frameless window with drag-to-move and window controls."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(40)
        self.setObjectName('HeaderBar')
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 8, 4)
        layout.setSpacing(8)

        # Title label
        self.title = QLabel('KS Seamless Checker')
        self.title.setStyleSheet('color: #e6e6e6;')
        title_font = QFont('Segoe UI', 12, QFont.Bold)
        self.title.setFont(title_font)
        layout.addWidget(self.title, stretch=1)

        # Window control buttons
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icons')
        self.min_btn = QPushButton()
        self.min_btn.setIcon(QIcon(os.path.join(base, 'minimize.svg')))
        self.min_btn.setFixedSize(32, 28)
        self.min_btn.setFlat(True)
        self.min_btn.setToolTip('Minimize')
        layout.addWidget(self.min_btn)

        self.max_btn = QPushButton()
        self.max_btn.setIcon(QIcon(os.path.join(base, 'maximize.svg')))
        self.max_btn.setFixedSize(32, 28)
        self.max_btn.setFlat(True)
        self.max_btn.setToolTip('Maximize')
        layout.addWidget(self.max_btn)

        self.close_btn = QPushButton()
        self.close_btn.setIcon(QIcon(os.path.join(base, 'close.svg')))
        self.close_btn.setFixedSize(32, 28)
        self.close_btn.setFlat(True)
        self.close_btn.setToolTip('Close')
        layout.addWidget(self.close_btn)

        # Connect signals (parent should be main window)
        if self.parent_window is not None:
            self.min_btn.clicked.connect(self.parent_window.showMinimized)
            self.max_btn.clicked.connect(self._toggle_max_restore)
            self.close_btn.clicked.connect(self.parent_window.close)

        # Dragging state
        self._mouse_pressed = False
        self._drag_pos = None

    def _toggle_max_restore(self):
        if not self.parent_window:
            return
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
        else:
            self.parent_window.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._mouse_pressed = True
            self._drag_pos = event.globalPos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._mouse_pressed and self.parent_window and not self.parent_window.isMaximized():
            delta = event.globalPos() - self._drag_pos
            self.parent_window.move(self.parent_window.pos() + delta)
            self._drag_pos = event.globalPos()
            event.accept()

    def mouseReleaseEvent(self, event):
        self._mouse_pressed = False
        event.accept()

    def mouseDoubleClickEvent(self, event):
        # Double click toggles maximize/restore
        self._toggle_max_restore()
        event.accept()


class SeamlessCheckerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('KS Seamless Checker')
        self.setGeometry(100, 100, 920, 640)
        # Accept drops for files/folders
        self.setAcceptDrops(True)
        # Use a frameless window so we can draw a custom header
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.config = self.load_config()
        self.checker = ImageChecker(self.config.get('seam_threshold', 10))
        self.processor = BatchProcessor(self.checker, self.config.get('supported_formats', ['.png', '.jpg', '.jpeg']), self.config.get('preview_folder', 'previews'))
        self.worker = None
        self.last_results = []
        self.setup_dark_theme()
        self.setup_ui()

    def load_config(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {
            'seam_threshold': 10,
            'supported_formats': ['.png', '.jpg', '.jpeg'],
            'preview_folder': 'previews',
            'accent_color': '#C49A6C'
        }

    def setup_dark_theme(self):
        palette = QPalette()
        accent = self.config.get('accent_color', '#C49A6C')
        palette.setColor(QPalette.Window, QColor(40, 42, 45))
        palette.setColor(QPalette.WindowText, QColor(230, 230, 230))
        palette.setColor(QPalette.Base, QColor(50, 52, 56))
        palette.setColor(QPalette.AlternateBase, QColor(43, 45, 48))
        palette.setColor(QPalette.ToolTipBase, QColor(230, 230, 230))
        palette.setColor(QPalette.ToolTipText, QColor(20, 20, 20))
        palette.setColor(QPalette.Text, QColor(225, 225, 225))
        palette.setColor(QPalette.Button, QColor(60, 62, 66))
        palette.setColor(QPalette.ButtonText, QColor(230, 230, 230))
        palette.setColor(QPalette.BrightText, QColor(220, 80, 80))
        try:
            r = int(accent[1:3], 16)
            g = int(accent[3:5], 16)
            b = int(accent[5:7], 16)
            palette.setColor(QPalette.Link, QColor(r, g, b))
            palette.setColor(QPalette.Highlight, QColor(r, g, b))
            palette.setColor(QPalette.HighlightedText, QColor(20, 20, 20))
        except Exception:
            pass
        self.setPalette(palette)
        # Apply dark background to ensure no light border shows
        self.setStyleSheet("QMainWindow{background-color: #28282D;}")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        # tighten margins to reduce visible top border
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(12)

        # Add custom header bar
        header = HeaderBar(self)
        header.setStyleSheet('QWidget#HeaderBar{background: transparent;}')
        layout.addWidget(header)

        folder_layout = QHBoxLayout()
        folder_label = QLabel('Select Folder:')
        folder_label.setStyleSheet('color: #dcdcdc;')
        folder_layout.addWidget(folder_label)

        self.folder_entry = QLineEdit()
        self.folder_entry.setPlaceholderText('Enter or browse folder path')
        self.folder_entry.setToolTip('Path to folder containing images')
        self.folder_entry.setStyleSheet('background: #35363a; color: #e6e6e6; padding:6px; border-radius:6px;')
        folder_layout.addWidget(self.folder_entry)

        browse_btn = QPushButton()
        browse_btn.setToolTip('Open folder dialog')
        browse_btn.setFixedSize(36, 28)
        browse_icon = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icons', 'browse.svg')
        browse_btn.setIcon(QIcon(browse_icon))
        browse_btn.clicked.connect(self.browse_folder)
        browse_btn.setStyleSheet("QPushButton{background:#4b5056;color:#e6e6e6;border-radius:6px;} QPushButton:hover{background:#5a6066}")
        folder_layout.addWidget(browse_btn)

        layout.addLayout(folder_layout)

        actions_layout = QHBoxLayout()
        process_button = QPushButton()
        process_button.setCursor(Qt.PointingHandCursor)
        process_button.setFixedSize(180, 40)
        proc_icon = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icons', 'process.svg')
        process_button.setIcon(QIcon(proc_icon))
        process_button.setText('  Process Batch')
        process_button.clicked.connect(self.process_batch)
        accent = self.config.get('accent_color', '#C49A6C')
        process_button.setStyleSheet(f"QPushButton{{background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {accent}, stop:1 {accent}); color:#0f1416; padding:8px 12px; border-radius:8px;}} QPushButton:hover{{opacity:0.95;}}")
        actions_layout.addWidget(process_button)

        export_button = QPushButton('Export CSV')
        export_button.setToolTip('Export last batch results to CSV')
        export_button.clicked.connect(self.export_csv)
        export_button.setStyleSheet("QPushButton{background:#4b5056;color:#e6e6e6;padding:8px;border-radius:6px;} QPushButton:hover{background:#5a6066}")
        actions_layout.addWidget(export_button)

        layout.addLayout(actions_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"QProgressBar{{background:#3b3b3b; color:#e6e6e6; border-radius:6px; height:12px;}} QProgressBar::chunk{{background:{accent}; border-radius:6px}}")
        layout.addWidget(self.progress_bar)

        results_layout = QHBoxLayout()

        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        results_label = QLabel('Results:')
        results_label.setStyleSheet('color: #dcdcdc;')
        left_layout.addWidget(results_label)
        # Results table: thumbnail, filename, status
        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(['Preview', 'File', 'Status'])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setShowGrid(False)
        self.results_table.setStyleSheet('QTableWidget{background:#2f3134;color:#e6e6e6;border-radius:6px;} QHeaderView::section{background:#35363a;color:#dcdcdc;border:0px;}')
        self.results_table.setIconSize(QSize(64, 64))
        left_layout.addWidget(self.results_table)
        # Connect click to preview
        self.results_table.cellClicked.connect(self._on_table_click)

        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        preview_label = QLabel('Preview:')
        preview_label.setStyleSheet('color: #dcdcdc;')
        right_layout.addWidget(preview_label)
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(240, 240)
        self.preview_label.setStyleSheet('background:#35363a;border:1px solid #505357;border-radius:6px;')
        self.preview_label.setToolTip('Tiled preview of last processed image')
        right_layout.addWidget(self.preview_label, alignment=Qt.AlignTop)

        results_layout.addWidget(left_frame, stretch=3)
        results_layout.addWidget(right_frame, stretch=1)
        layout.addLayout(results_layout)

        settings_btn = QPushButton()
        settings_btn.setFixedSize(36, 28)
        settings_icon = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icons', 'settings.svg')
        settings_btn.setIcon(QIcon(settings_icon))
        settings_btn.setToolTip('Open settings')
        settings_btn.clicked.connect(self.open_settings)
        settings_btn.setStyleSheet("QPushButton{background:#3b3b3b;border-radius:6px;} QPushButton:hover{background:#47494b}")
        layout.addWidget(settings_btn, alignment=Qt.AlignRight)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            self.folder_entry.setText(folder)

    # Drag & drop support
    def dragEnterEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        mime = event.mimeData()
        urls = mime.urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        # If a file was dropped, set it; if a folder, set folder
        self.folder_entry.setText(path)
        # Auto-start processing for convenience
        self.process_batch()

    def process_batch(self):
        path = self.folder_entry.text()
        if not (os.path.isdir(path) or os.path.isfile(path)):
            QMessageBox.critical(self, 'Error', 'Invalid folder or file path')
            return
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.worker = BatchWorker(self.processor, path)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_batch_finished)
        self.worker.start()

    def on_batch_finished(self, results):
        self.progress_bar.setVisible(False)
        self.last_results = results
        # populate results table
        self.results_table.clearContents()
        self.results_table.setRowCount(len(results))
        for row, res in enumerate(results):
            status = 'Seamless' if res.get('seamless') else 'Not Seamless'
            filename = res.get('file')
            preview_path = res.get('preview_path')

            # Thumbnail cell
            thumb_item = QTableWidgetItem()
            if preview_path and os.path.exists(preview_path):
                pix = QPixmap(preview_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                thumb_item.setIcon(QIcon(pix))
            thumb_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.results_table.setItem(row, 0, thumb_item)

            # Filename cell (store preview_path in UserRole)
            file_item = QTableWidgetItem(filename)
            file_item.setData(Qt.UserRole, preview_path)
            file_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.results_table.setItem(row, 1, file_item)

            # Status cell
            status_item = QTableWidgetItem(status)
            status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.results_table.setItem(row, 2, status_item)

            # adjust row height
            self.results_table.setRowHeight(row, 72)

        QMessageBox.information(self, 'Done', f'Processed {len(results)} images. Previews saved.')

    def _on_table_click(self, row, column):
        # get preview_path stored in filename cell's UserRole
        item = self.results_table.item(row, 1)
        if not item:
            return
        preview_path = item.data(Qt.UserRole)
        if preview_path and os.path.exists(preview_path):
            pixmap = QPixmap(preview_path)
            self.preview_label.setPixmap(pixmap.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def export_csv(self):
        if not self.last_results:
            QMessageBox.warning(self, 'No results', 'No batch results to export. Run a batch first.')
            return
        default = os.path.join(self.processor.preview_folder, 'results.csv')
        path, _ = QFileDialog.getSaveFileName(self, 'Save CSV', default, 'CSV Files (*.csv)')
        if path:
            csv_path = self.processor.save_results_csv(self.last_results, csv_path=path)
            QMessageBox.information(self, 'Exported', f'Results saved to {csv_path}')

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.config = self.load_config()
            self.checker = ImageChecker(self.config.get('seam_threshold', 10))
            self.processor.preview_folder = self.config.get('preview_folder', 'previews')
            self.setup_dark_theme()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SeamlessCheckerGUI()
    window.show()
    sys.exit(app.exec())