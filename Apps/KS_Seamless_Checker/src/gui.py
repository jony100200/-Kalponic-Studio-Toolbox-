from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QLineEdit, QFileDialog, QMessageBox,
                               QProgressBar, QFrame, QDialog, QFormLayout, QSpinBox, QDialogButtonBox, QComboBox,
                               QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QDialogButtonBox, QSizePolicy,
                               QCheckBox)
from PySide6.QtGui import QPalette, QColor, QFont, QPixmap, QIcon, QKeySequence
from PySide6.QtCore import Qt, QThread, Signal, QSize
import cv2
import os
import json
import sys
# Add parent directory to sys.path for relative imports when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
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
        self.setModal(True)

        # Apply dark theme
        self.setup_dark_theme()

        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        if not os.path.exists(config_path):
            self.config = {}
        else:
            with open(config_path, 'r') as f:
                self.config = json.load(f)

        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Seam threshold
        self.spin = QSpinBox()
        self.spin.setRange(0, 100000)
        self.spin.setValue(self.config.get('seam_threshold', 10))
        self.spin.setStyleSheet('background: #35363a; color: #e6e6e6; padding:6px; border-radius:6px;')
        layout.addRow(self.create_label('Seam threshold'), self.spin)

        # Preview folder
        self.preview_line = QLineEdit()
        self.preview_line.setText(self.config.get('preview_folder', 'previews'))
        self.preview_line.setStyleSheet('background: #35363a; color: #e6e6e6; padding:6px; border-radius:6px;')
        layout.addRow(self.create_label('Preview folder'), self.preview_line)

        # Preview mode
        self.preview_mode_combo = QComboBox()
        self.preview_mode_combo.addItems(['memory', 'disk'])
        self.preview_mode_combo.setCurrentText(self.config.get('preview_mode', 'memory'))
        self.preview_mode_combo.setStyleSheet('background: #35363a; color: #e6e6e6; padding:6px; border-radius:6px;')
        layout.addRow(self.create_label('Preview mode'), self.preview_mode_combo)

        # Auto-start on drop
        self.auto_start_cb = QCheckBox('Auto-start when file/folder dropped')
        self.auto_start_cb.setChecked(self.config.get('auto_start_on_drop', True))
        self.auto_start_cb.setStyleSheet('color: #e6e6e6;')
        layout.addRow(self.auto_start_cb)

        # Thumbnail settings
        self.thumb_only_cb = QCheckBox('Keep only thumbnails in memory (save RAM)')
        self.thumb_only_cb.setChecked(self.config.get('thumbnail_only_in_memory', True))
        self.thumb_only_cb.setStyleSheet('color: #e6e6e6;')
        layout.addRow(self.thumb_only_cb)

        self.thumb_size_spin = QSpinBox()
        self.thumb_size_spin.setRange(32, 2048)
        self.thumb_size_spin.setValue(int(self.config.get('thumbnail_max_size', 256)))
        self.thumb_size_spin.setStyleSheet('background: #35363a; color: #e6e6e6; padding:6px; border-radius:6px;')
        layout.addRow(self.create_label('Thumbnail max size (px)'), self.thumb_size_spin)

        # AI seam detection
        self.ai_seam_cb = QCheckBox('Use AI for seam detection (requires PyTorch)')
        self.ai_seam_cb.setChecked(self.config.get('use_ai_seam_detection', False))
        self.ai_seam_cb.setStyleSheet('color: #e6e6e6;')
        layout.addRow(self.ai_seam_cb)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        buttons.setStyleSheet("""
            QPushButton {
                background: #4b5056;
                color: #e6e6e6;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background: #5a6066;
            }
        """)
        layout.addRow(buttons)

    def create_label(self, text):
        """Create a styled label for form rows."""
        label = QLabel(text)
        label.setStyleSheet('color: #dcdcdc; font-weight: bold;')
        return label

    def setup_dark_theme(self):
        """Apply the same dark theme as the main window."""
        palette = QPalette()
        accent = self.parent().config.get('accent_color', '#C49A6C') if self.parent() else '#C49A6C'
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
        self.setStyleSheet("QDialog{background-color: #28282D;}")

    def save(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        self.config['seam_threshold'] = int(self.spin.value())
        self.config['preview_folder'] = self.preview_line.text()
        self.config['preview_mode'] = self.preview_mode_combo.currentText()
        self.config['auto_start_on_drop'] = bool(self.auto_start_cb.isChecked())
        self.config['thumbnail_only_in_memory'] = bool(self.thumb_only_cb.isChecked())
        self.config['thumbnail_max_size'] = int(self.thumb_size_spin.value())
        self.config['use_ai_seam_detection'] = bool(self.ai_seam_cb.isChecked())
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


class PreviewWindow(QDialog):
    """Floating, resizable preview window with next/previous navigation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Preview')
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self.setMinimumSize(480, 480)
        self.results = []
        self.current_index = 0
        self._scale = 1.0
        self._dragging = False
        self._last_pos = None

        layout = QVBoxLayout(self)
        nav = QHBoxLayout()
        self.prev_btn = QPushButton('\u25C0')
        self.next_btn = QPushButton('\u25B6')
        nav.addWidget(self.prev_btn)
        nav.addStretch()
        nav.addWidget(self.next_btn)
        layout.addLayout(nav)

        # Scroll area for zooming and panning
        from PySide6.QtWidgets import QScrollArea
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet('background:#2f3134;border:1px solid #505357;border-radius:6px;')
        self.image_label.setBackgroundRole(QPalette.Base)
        self.image_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.scroll.setWidget(self.image_label)
        layout.addWidget(self.scroll, stretch=1)

        self.prev_btn.clicked.connect(self.show_prev)
        self.next_btn.clicked.connect(self.show_next)

        # Bind mouse events for dragging on the image_label
        self.image_label.mousePressEvent = self._on_mouse_press
        self.image_label.mouseMoveEvent = self._on_mouse_move
        self.image_label.mouseReleaseEvent = self._on_mouse_release

    def set_results(self, results):
        self.results = results or []

    def show_index(self, idx):
        if not self.results:
            return
        if idx < 0:
            idx = 0
        if idx >= len(self.results):
            idx = len(self.results) - 1
        self.current_index = idx
        self._update_image()
        self.show()

    def _update_image(self):
        if not self.results:
            self.image_label.clear()
            return
        preview_bytes = self.results[self.current_index].get('preview_bytes', b'')
        thumb_bytes = self.results[self.current_index].get('thumb_bytes', b'')
        use_bytes = preview_bytes if preview_bytes else thumb_bytes
        if use_bytes:
            pix = QPixmap()
            pix.loadFromData(use_bytes, format='PNG')
            self._orig_pixmap = pix
            self._scale = 1.0
            self._apply_scale()
        else:
            self.image_label.clear()

    def _apply_scale(self):
        if not hasattr(self, '_orig_pixmap') or self._orig_pixmap.isNull():
            return
        old_h = self.scroll.horizontalScrollBar().value()
        old_v = self.scroll.verticalScrollBar().value()
        vp_w = self.scroll.viewport().width()
        vp_h = self.scroll.viewport().height()

        # center before scale
        center_x = old_h + vp_w / 2
        center_y = old_v + vp_h / 2

        new_w = max(1, int(self._orig_pixmap.width() * self._scale))
        new_h = max(1, int(self._orig_pixmap.height() * self._scale))
        scaled = self._orig_pixmap.scaled(new_w, new_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        self.image_label.resize(scaled.size())

        # adjust scrollbars to keep same center
        ratio = (self._scale)
        new_center_x = center_x * ratio
        new_center_y = center_y * ratio
        hbar = self.scroll.horizontalScrollBar()
        vbar = self.scroll.verticalScrollBar()
        hbar.setValue(int(new_center_x - vp_w / 2))
        vbar.setValue(int(new_center_y - vp_h / 2))

    def wheelEvent(self, event):
        # Zoom in/out with wheel
        delta = event.angleDelta().y()
        if delta == 0:
            return
        factor = 1.15 if delta > 0 else 0.85
        new_scale = self._scale * factor
        # clamp
        new_scale = max(0.05, min(8.0, new_scale))
        self._scale = new_scale
        self._apply_scale()

    def _on_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._last_pos = event.globalPos()
            event.accept()

    def _on_mouse_move(self, event):
        if not self._dragging:
            return
        delta = event.globalPos() - self._last_pos
        self._last_pos = event.globalPos()
        hbar = self.scroll.horizontalScrollBar()
        vbar = self.scroll.verticalScrollBar()
        hbar.setValue(hbar.value() - delta.x())
        vbar.setValue(vbar.value() - delta.y())
        event.accept()

    def _on_mouse_release(self, event):
        self._dragging = False
        event.accept()

    def show_prev(self):
        if not self.results:
            return
        self.current_index = max(0, self.current_index - 1)
        self._update_image()

    def show_next(self):
        if not self.results:
            return
        self.current_index = min(len(self.results) - 1, self.current_index + 1)
        self._update_image()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.show_prev()
        elif event.key() == Qt.Key_Right:
            self.show_next()
        elif event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Rescale current image to new size
        self._update_image()


class SeamlessCheckerGUI(QMainWindow):
    """
    Main GUI application for KS Seamless Checker.

    Provides a dark-themed interface for seamless texture detection with:
    - Drag & drop file/folder support
    - Batch processing capabilities
    - Real-time preview with zoom controls
    - CSV export functionality
    - Customizable settings
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle('KS Seamless Checker')
        self.setGeometry(100, 100, 920, 640)
        # Accept drops for files/folders
        self.setAcceptDrops(True)
        # Use a frameless window so we can draw a custom header
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        self.config = self.load_config()
        self.checker = ImageChecker(
            threshold=self.config.get('threshold', 20.0),
            use_ai=self.config.get('use_ai', False)
        )
        self.processor = BatchProcessor(self.checker, self.config.get('supported_formats', ['.png', '.jpg', '.jpeg']), self.config.get('preview_folder', 'previews'))
        # Apply preview_mode from config (memory or disk)
        self.processor.preview_mode = self.config.get('preview_mode', 'memory')
        # Thumbnail settings
        self.processor.thumbnail_only_in_memory = self.config.get('thumbnail_only_in_memory', True)
        self.processor.thumbnail_max_size = int(self.config.get('thumbnail_max_size', 256))
        self.worker = None
        self.last_results = []
        self.footer_label = None
        self.footer_progress = None
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

    def save_last_path(self, path):
        """Save the last used folder/file path to config."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        self.config['last_folder_path'] = path
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

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
        # Enable drag and drop on the folder entry
        self.folder_entry.setAcceptDrops(True)
        self.folder_entry.dragEnterEvent = self._folder_drag_enter
        self.folder_entry.dropEvent = self._folder_drop
        # Load last folder path
        last_path = self.config.get('last_folder_path', '')
        if last_path:
            self.folder_entry.setText(last_path)
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

        layout.addLayout(actions_layout)

        # Remove old progress_bar and export_button, they will be in footer

        results_layout = QHBoxLayout()

        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        results_label = QLabel('Results:')
        results_label.setStyleSheet('color: #dcdcdc;')
        left_layout.addWidget(results_label)
        # Results table: thumbnail, filename, status
        self.results_table = QTableWidget(0, 4)
        self.results_table.setHorizontalHeaderLabels(['Preview', 'File', 'Status', 'Details'])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
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

        # Floating preview window (initially hidden)
        self.preview_window = PreviewWindow(parent=self)

        results_layout.addWidget(left_frame, stretch=3)
        results_layout.addWidget(right_frame, stretch=1)
        layout.addLayout(results_layout)

        # Footer bar
        footer_layout = QHBoxLayout()
        self.footer_label = QLabel('Ready')
        self.footer_label.setStyleSheet('color: #dcdcdc;')
        footer_layout.addWidget(self.footer_label)
        footer_layout.addStretch()
        self.footer_progress = QProgressBar()
        self.footer_progress.setVisible(False)
        self.footer_progress.setStyleSheet(f"QProgressBar{{background:#3b3b3b; color:#e6e6e6; border-radius:6px; height:12px;}} QProgressBar::chunk{{background:{accent}; border-radius:6px}}")
        footer_layout.addWidget(self.footer_progress)
        export_btn = QPushButton('Export CSV')
        export_btn.setToolTip('Export last batch results to CSV')
        export_btn.clicked.connect(self.export_csv)
        export_btn.setStyleSheet("QPushButton{background:#4b5056;color:#e6e6e6;padding:8px;border-radius:6px;} QPushButton:hover{background:#5a6066}")
        footer_layout.addWidget(export_btn)
        footer_widget = QWidget()
        footer_widget.setLayout(footer_layout)
        layout.addWidget(footer_widget)

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
            self.save_last_path(folder)

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
        self.save_last_path(path)
        # Auto-start processing for convenience only if enabled in settings
        # reload config in case settings changed externally
        self.config = self.load_config()
        if self.config.get('auto_start_on_drop', True):
            self.process_batch()

    def save_last_path(self, path):
        """Save the last used path to config.json"""
        try:
            config = self.load_config()
            config['last_folder_path'] = path
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            pass  # Silently ignore config save errors

    def _folder_drag_enter(self, event):
        """Handle drag enter event for folder_entry"""
        mime = event.mimeData()
        if mime.hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def _folder_drop(self, event):
        """Handle drop event for folder_entry"""
        mime = event.mimeData()
        urls = mime.urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        self.folder_entry.setText(path)
        self.save_last_path(path)
        # Auto-start processing for convenience only if enabled in settings
        self.config = self.load_config()
        if self.config.get('auto_start_on_drop', True):
            self.process_batch()

    def process_batch(self):
        path = self.folder_entry.text()
        if not (os.path.isdir(path) or os.path.isfile(path)):
            QMessageBox.critical(self, 'Error', 'Invalid folder or file path')
            return
        self.footer_progress.setVisible(True)
        self.footer_progress.setValue(0)
        self.footer_label.setText('Processing...')
        self.worker = BatchWorker(self.processor, path)
        self.worker.progress.connect(self.footer_progress.setValue)
        self.worker.finished.connect(self.on_batch_finished)
        self.worker.start()

    def on_batch_finished(self, results):
        self.footer_progress.setVisible(False)
        self.footer_label.setText(f'Processed {len(results)} images')
        self.last_results = results
        # populate results table
        self.results_table.clearContents()
        self.results_table.setRowCount(len(results))
        for row, res in enumerate(results):
            status = 'Seamless' if res.get('seamless') else 'Not Seamless'
            filename = res.get('file')
            preview_bytes = res.get('preview_bytes', b'')
            thumb_bytes = res.get('thumb_bytes', b'')

            # Thumbnail cell (use in-memory bytes if available)
            thumb_item = QTableWidgetItem()
            # Use thumbnail bytes for table (smaller)
            if thumb_bytes:
                pix = QPixmap()
                pix.loadFromData(thumb_bytes, format='PNG')
                thumb_item.setIcon(QIcon(pix.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
            elif preview_bytes:
                pix = QPixmap()
                pix.loadFromData(preview_bytes, format='PNG')
                thumb_item.setIcon(QIcon(pix.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
            thumb_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.results_table.setItem(row, 0, thumb_item)

            # Filename cell (store preview_bytes in UserRole)
            file_item = QTableWidgetItem(filename)
            # store both bytes in UserRole as a small dict-like tuple (thumb, preview)
            file_item.setData(Qt.UserRole, (thumb_bytes, preview_bytes))
            file_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.results_table.setItem(row, 1, file_item)

            # Status cell
            status_item = QTableWidgetItem(status)
            status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.results_table.setItem(row, 2, status_item)

            # Details cell - show seamless type
            seamless_type = res.get('seamless_type', 'unknown')
            type_display = {
                'fully_seamless': 'Fully Seamless',
                'horizontal_only': 'X-Axis Only',
                'vertical_only': 'Y-Axis Only',
                'not_seamless': 'Not Seamless'
            }.get(seamless_type, seamless_type.title())

            details_item = QTableWidgetItem(type_display)
            details_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.results_table.setItem(row, 3, details_item)

            # adjust row height
            self.results_table.setRowHeight(row, 72)

        QMessageBox.information(self, 'Done', f'Processed {len(results)} images.')

    def _on_table_click(self, row, column):
        # get preview_path stored in filename cell's UserRole
        item = self.results_table.item(row, 1)
        if not item:
            return
        data = item.data(Qt.UserRole)
        if not data:
            return
        # data is (thumb_bytes, preview_bytes)
        thumb_bytes, preview_bytes = data if isinstance(data, tuple) else (b'', data)
        use_bytes = preview_bytes if preview_bytes else thumb_bytes
        if use_bytes:
            pixmap = QPixmap()
            pixmap.loadFromData(use_bytes, format='PNG')
            self.preview_label.setPixmap(pixmap.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            # also open/refresh floating preview window at selected index
            self.preview_window.set_results(self.last_results)
            self.preview_window.show_index(row)

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
            self.checker = ImageChecker(
                threshold=self.config.get('seam_threshold', 10),
                use_ai=self.config.get('use_ai_seam_detection', False)
            )
            self.processor.preview_folder = self.config.get('preview_folder', 'previews')
            self.processor.preview_mode = self.config.get('preview_mode', 'memory')
            # apply thumbnail settings
            self.processor.thumbnail_only_in_memory = self.config.get('thumbnail_only_in_memory', True)
            self.processor.thumbnail_max_size = int(self.config.get('thumbnail_max_size', 256))
            self.setup_dark_theme()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SeamlessCheckerGUI()
    window.show()
    sys.exit(app.exec())