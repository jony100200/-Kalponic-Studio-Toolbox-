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


class ModernDarkTheme:
    """
    Modern Dark Theme System for KS Seamless Checker
    Implements sci-fi aesthetics with proper contrast and visual hierarchy
    """

    # Core Color Palette (60-30-10 Rule)
    COLORS = {
        # Primary (60%): Deep space background
        'bg_primary': '#0f0f0f',      # Main background
        'bg_secondary': '#1a1a1a',    # Secondary surfaces
        'bg_tertiary': '#2d2d2d',     # Cards, panels

        # Accent (10%): Cyberpunk neon
        'accent_primary': '#00d4aa',  # Main accent (teal/cyan)
        'accent_secondary': '#ff6b6b', # Error/warning
        'accent_success': '#4ecdc4',   # Success states
        'accent_info': '#45b7d1',     # Info states

        # Text Hierarchy
        'text_primary': '#ffffff',    # Primary text (high contrast)
        'text_secondary': '#b0b0b0',  # Secondary text
        'text_tertiary': '#808080',   # Tertiary/disabled text

        # Interactive States
        'hover': '#333333',           # Hover backgrounds
        'pressed': '#404040',         # Pressed states
        'selected': '#2d5016',        # Selected items
        'focus': '#00d4aa',           # Focus rings

        # Borders & Dividers
        'border_light': '#404040',    # Subtle borders
        'border_medium': '#555555',   # Medium borders
        'border_strong': '#777777',   # Strong borders

        # Special Effects
        'glow_primary': 'rgba(0, 212, 170, 0.3)',
        'glow_error': 'rgba(255, 107, 107, 0.3)',
        'shadow': 'rgba(0, 0, 0, 0.5)',
    }

    @classmethod
    def get_main_window_style(cls):
        """Main window stylesheet with modern dark theme"""
        return f"""
            QMainWindow {{
                background-color: {cls.COLORS['bg_primary']};
                color: {cls.COLORS['text_primary']};
                border: none;
            }}

            /* Remove any default margins/padding */
            QMainWindow QWidget {{
                font-family: 'Segoe UI', 'Consolas', monospace;
                font-size: 10pt;
            }}
        """

    @classmethod
    def get_button_style(cls, variant='primary'):
        """Modern button styling with variants"""
        base_style = f"""
            QPushButton {{
                background-color: {cls.COLORS['bg_tertiary']};
                color: {cls.COLORS['text_primary']};
                border: 1px solid {cls.COLORS['border_light']};
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                min-height: 14px;
            }}

            QPushButton:hover {{
                background-color: {cls.COLORS['hover']};
                border-color: {cls.COLORS['accent_primary']};
            }}

            QPushButton:pressed {{
                background-color: {cls.COLORS['pressed']};
                border-color: {cls.COLORS['accent_primary']};
            }}

            QPushButton:disabled {{
                background-color: {cls.COLORS['bg_secondary']};
                color: {cls.COLORS['text_tertiary']};
                border-color: {cls.COLORS['border_light']};
            }}
        """

        if variant == 'accent':
            return base_style.replace(
                f"background-color: {cls.COLORS['bg_tertiary']};",
                f"background-color: {cls.COLORS['accent_primary']};"
            ).replace(
                "color: {cls.COLORS['text_primary']};",
                "color: #0f0f0f;"
            )
        elif variant == 'danger':
            return base_style.replace(
                f"border-color: {cls.COLORS['border_light']};",
                f"border-color: {cls.COLORS['accent_secondary']};"
            )

        return base_style

    @classmethod
    def get_input_style(cls):
        """Modern input field styling"""
        return f"""
            QLineEdit, QTextEdit, QSpinBox, QComboBox {{
                background-color: {cls.COLORS['bg_secondary']};
                color: {cls.COLORS['text_primary']};
                border: 1px solid {cls.COLORS['border_light']};
                border-radius: 6px;
                padding: 8px 12px;
                selection-background-color: {cls.COLORS['accent_primary']};
                selection-color: #0f0f0f;
            }}

            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border-color: {cls.COLORS['focus']};
            }}

            QLineEdit:hover, QTextEdit:hover, QSpinBox:hover, QComboBox:hover {{
                border-color: {cls.COLORS['border_medium']};
            }}

            /* Placeholder text */
            QLineEdit::placeholder {{
                color: {cls.COLORS['text_tertiary']};
            }}

            /* Dropdown arrow */
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}

            QComboBox::down-arrow {{
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }}
        """

    @classmethod
    def get_table_style(cls):
        """Modern table styling"""
        return f"""
            QTableWidget {{
                background-color: {cls.COLORS['bg_secondary']};
                color: {cls.COLORS['text_primary']};
                border: 1px solid {cls.COLORS['border_light']};
                border-radius: 8px;
                gridline-color: {cls.COLORS['border_light']};
                selection-background-color: {cls.COLORS['selected']};
                selection-color: {cls.COLORS['text_primary']};
            }}

            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {cls.COLORS['border_light']};
            }}

            QTableWidget::item:selected {{
                background-color: {cls.COLORS['selected']};
            }}

            QTableWidget::item:hover {{
                background-color: {cls.COLORS['hover']};
            }}

            QHeaderView::section {{
                background-color: {cls.COLORS['bg_tertiary']};
                color: {cls.COLORS['text_primary']};
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid {cls.COLORS['accent_primary']};
                font-weight: 600;
            }}

            QHeaderView::section:hover {{
                background-color: {cls.COLORS['hover']};
            }}
        """

    @classmethod
    def get_label_style(cls):
        """Modern label styling"""
        return f"""
            QLabel {{
                color: {cls.COLORS['text_primary']};
                font-size: 11pt;
            }}

            QLabel[secondary="true"] {{
                color: {cls.COLORS['text_secondary']};
                font-size: 10pt;
            }}

            QLabel[tertiary="true"] {{
                color: {cls.COLORS['text_tertiary']};
                font-size: 9pt;
            }}
        """

    @classmethod
    def get_progress_style(cls):
        """Modern progress bar styling"""
        return f"""
            QProgressBar {{
                background-color: {cls.COLORS['bg_secondary']};
                color: {cls.COLORS['text_primary']};
                border: 1px solid {cls.COLORS['border_light']};
                border-radius: 6px;
                text-align: center;
                font-size: 9pt;
                font-weight: 500;
            }}

            QProgressBar::chunk {{
                background-color: {cls.COLORS['accent_primary']};
                border-radius: 5px;
            }}
        """

    @classmethod
    def get_frame_style(cls):
        """Modern frame/panel styling"""
        return f"""
            QFrame {{
                background-color: {cls.COLORS['bg_tertiary']};
                border: 1px solid {cls.COLORS['border_light']};
                border-radius: 8px;
            }}

            QFrame[card="true"] {{
                background-color: {cls.COLORS['bg_secondary']};
                border: 1px solid {cls.COLORS['border_medium']};
                border-radius: 10px;
            }}
        """

    @classmethod
    def get_scrollbar_style(cls):
        """Modern scrollbar styling"""
        return f"""
            QScrollBar:vertical {{
                background-color: {cls.COLORS['bg_secondary']};
                width: 12px;
                border-radius: 6px;
            }}

            QScrollBar::handle:vertical {{
                background-color: {cls.COLORS['border_medium']};
                border-radius: 6px;
                min-height: 30px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {cls.COLORS['accent_primary']};
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}

            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
                background: none;
            }}
        """

    @classmethod
    def apply_theme_to_app(cls, app):
        """Apply the complete modern dark theme to QApplication"""
        app.setStyleSheet(f"""
            {cls.get_main_window_style()}
            {cls.get_button_style()}
            {cls.get_input_style()}
            {cls.get_table_style()}
            {cls.get_label_style()}
            {cls.get_progress_style()}
            {cls.get_frame_style()}
            {cls.get_scrollbar_style()}

            /* Dialog styling */
            QDialog {{
                background-color: {cls.COLORS['bg_primary']};
                color: {cls.COLORS['text_primary']};
                border-radius: 10px;
            }}

            /* Message box styling */
            QMessageBox {{
                background-color: {cls.COLORS['bg_primary']};
                color: {cls.COLORS['text_primary']};
            }}

            QMessageBox QLabel {{
                color: {cls.COLORS['text_primary']};
            }}

            /* Tooltips */
            QToolTip {{
                background-color: {cls.COLORS['bg_tertiary']};
                color: {cls.COLORS['text_primary']};
                border: 1px solid {cls.COLORS['border_medium']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
        """)

        # Set application-wide font
        font = QFont('Segoe UI', 10)
        font.setStyleHint(QFont.System)
        app.setFont(font)


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
        """Apply modern dark theme to settings dialog"""
        # Apply the comprehensive modern theme
        ModernDarkTheme.apply_theme_to_app(QApplication.instance())

        # Set dialog-specific styling
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ModernDarkTheme.COLORS['bg_primary']};
                color: {ModernDarkTheme.COLORS['text_primary']};
                border-radius: 12px;
                border: 1px solid {ModernDarkTheme.COLORS['border_light']};
            }}

            QDialog QGroupBox {{
                font-weight: bold;
                border: 2px solid {ModernDarkTheme.COLORS['accent_primary']};
                border-radius: 8px;
                margin-top: 1ex;
                color: {ModernDarkTheme.COLORS['text_primary']};
            }}

            QDialog QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: {ModernDarkTheme.COLORS['accent_primary']};
                font-weight: bold;
            }}
        """)

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
    """Modern header bar for frameless window with drag-to-move and window controls."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(50)
        self.setObjectName('ModernHeaderBar')

        # Modern gradient background
        self.setStyleSheet(f"""
            QWidget#ModernHeaderBar {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {ModernDarkTheme.COLORS['bg_tertiary']},
                    stop:1 {ModernDarkTheme.COLORS['bg_secondary']});
                border-bottom: 1px solid {ModernDarkTheme.COLORS['border_light']};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # App icon and title section
        title_section = QHBoxLayout()
        title_section.setSpacing(12)

        # App icon placeholder (you can add a real icon later)
        icon_label = QLabel("🔍")
        icon_label.setStyleSheet(f"color: {ModernDarkTheme.COLORS['accent_primary']}; font-size: 18pt;")
        title_section.addWidget(icon_label)

        # Title label (removed version suffix)
        self.title = QLabel('KS Seamless Checker')
        self.title.setStyleSheet(f"""
            color: {ModernDarkTheme.COLORS['text_primary']};
            background: transparent;
            padding: 4px 8px;
            font-size: 14pt;
            font-weight: 700;
            font-family: 'Segoe UI', sans-serif;
        """)
        title_section.addWidget(self.title)
        title_section.addStretch()

        layout.addLayout(title_section, stretch=1)

        # Window control buttons with modern styling
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        # icons directory
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icons')

        # Minimize button (use SVG icon)
        self.min_btn = QPushButton()
        self.min_btn.setFixedSize(36, 36)
        self.min_btn.setToolTip('Minimize')
        self.min_btn.setFlat(False)
        self.min_btn.setFocusPolicy(Qt.NoFocus)
        # Make icon visible by default: semi-opaque background and white icon
        self.min_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.06);
                color: {ModernDarkTheme.COLORS['text_primary']};
                border: 1px solid rgba(255,255,255,0.04);
                border-radius: 6px;
                padding: 6px;
            }}
            QPushButton:hover {{
                background: {ModernDarkTheme.COLORS['hover']};
                border-color: {ModernDarkTheme.COLORS['accent_primary']};
            }}
            QPushButton:pressed {{
                background: {ModernDarkTheme.COLORS['pressed']};
            }}
        """)
        min_icon_path = os.path.join(icons_dir, 'minimize.svg')
        if os.path.exists(min_icon_path):
            self.min_btn.setIcon(QIcon(min_icon_path))
            self.min_btn.setIconSize(QSize(18, 18))
        controls_layout.addWidget(self.min_btn)

        # Maximize / Restore button (icon toggles tooltip and icon if available)
        self.max_btn = QPushButton()
        self.max_btn.setFixedSize(36, 36)
        self.max_btn.setToolTip('Maximize')
        self.max_btn.setFlat(False)
        self.max_btn.setFocusPolicy(Qt.NoFocus)
        self.max_btn.setStyleSheet(self.min_btn.styleSheet())
        max_icon_path = os.path.join(icons_dir, 'maximize.svg')
        if os.path.exists(max_icon_path):
            self.max_btn.setIcon(QIcon(max_icon_path))
            self.max_btn.setIconSize(QSize(18, 18))
        controls_layout.addWidget(self.max_btn)

        # Close button with danger styling (use SVG icon)
        self.close_btn = QPushButton()
        self.close_btn.setFixedSize(36, 36)
        self.close_btn.setToolTip('Close')
        self.close_btn.setFlat(False)
        self.close_btn.setFocusPolicy(Qt.NoFocus)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.06);
                color: {ModernDarkTheme.COLORS['text_primary']};
                border: 1px solid rgba(255,255,255,0.04);
                border-radius: 6px;
                padding: 6px;
            }}
            QPushButton:hover {{
                background: {ModernDarkTheme.COLORS['accent_secondary']};
                border-color: {ModernDarkTheme.COLORS['accent_secondary']};
            }}
            QPushButton:pressed {{
                background: {ModernDarkTheme.COLORS['pressed']};
            }}
        """)
        close_icon_path = os.path.join(icons_dir, 'close.svg')
        if os.path.exists(close_icon_path):
            self.close_btn.setIcon(QIcon(close_icon_path))
            self.close_btn.setIconSize(QSize(18, 18))
        controls_layout.addWidget(self.close_btn)

        layout.addLayout(controls_layout)

        # Connect signals
        if self.parent_window is not None:
            self.min_btn.clicked.connect(self.parent_window.showMinimized)
            self.max_btn.clicked.connect(self._toggle_max_restore)
            self.close_btn.clicked.connect(self.parent_window.close)
            # Install event filter to detect window state changes
            self.parent_window.installEventFilter(self)

        # Initial button state update
        self._update_max_button_text()

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
        self._update_max_button_text()

    def _update_max_button_text(self):
        """Update maximize button text based on window state"""
        if not self.parent_window:
            return
        if self.parent_window.isMaximized():
            self.max_btn.setText('🗗')  # Restore down symbol
            self.max_btn.setToolTip('Restore Down')
        else:
            self.max_btn.setText('🗖')  # Maximize symbol
            self.max_btn.setToolTip('Maximize')

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

    def resizeEvent(self, event):
        """Update button states when window is resized externally"""
        super().resizeEvent(event)
        self._update_max_button_text()

    def eventFilter(self, obj, event):
        """Filter events from parent window to detect state changes"""
        if obj == self.parent_window and event.type() == event.Type.WindowStateChange:
            self._update_max_button_text()
        return super().eventFilter(obj, event)


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

        # Apply modern dark theme
        self.setup_dark_theme()

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

    def setup_dark_theme(self):
        """Apply modern dark theme to preview window"""
        # Apply the comprehensive modern theme
        ModernDarkTheme.apply_theme_to_app(QApplication.instance())

        # Set window-specific styling
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ModernDarkTheme.COLORS['bg_primary']};
                color: {ModernDarkTheme.COLORS['text_primary']};
                border-radius: 12px;
                border: 1px solid {ModernDarkTheme.COLORS['border_light']};
            }}

            QLabel {{
                color: {ModernDarkTheme.COLORS['text_primary']};
                font-size: 12px;
            }}

            QPushButton {{
                background-color: {ModernDarkTheme.COLORS['bg_secondary']};
                color: {ModernDarkTheme.COLORS['text_primary']};
                border: 1px solid {ModernDarkTheme.COLORS['border_light']};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: {ModernDarkTheme.COLORS['hover']};
                border-color: {ModernDarkTheme.COLORS['accent_primary']};
            }}

            QPushButton:pressed {{
                background-color: {ModernDarkTheme.COLORS['pressed']};
            }}
        """)


class SeamlessCheckerGUI(QMainWindow):
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
            threshold=self.config.get('seam_threshold', 10),
            use_ai=self.config.get('use_ai_seam_detection', False)
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
        """Apply modern dark theme with sci-fi aesthetics"""
        # Apply the comprehensive modern theme
        ModernDarkTheme.apply_theme_to_app(QApplication.instance())

        # Set window properties for modern look
        self.setWindowTitle("KS Seamless Checker v2.0")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        # Remove window frame for custom title bar
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)

        # Optional: Add subtle drop shadow effect
        # Note: This requires additional setup for proper shadow rendering

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Add custom header bar with modern styling
        header = HeaderBar(self)
        header.setProperty("card", True)  # Apply card styling
        layout.addWidget(header)

        # Main content area with card styling
        main_card = QFrame()
        main_card.setProperty("card", True)
        main_layout = QVBoxLayout(main_card)
        results_layout = QHBoxLayout()
        results_layout.setSpacing(16)

        # Left panel - Results table
        left_panel = QFrame()
        left_panel.setProperty("card", True)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)

        results_header = QHBoxLayout()
        results_label = QLabel('📊 Results:')
        results_label.setProperty("secondary", True)
        results_header.addWidget(results_label)
        results_header.addStretch()
        left_layout.addLayout(results_header)

        # Results table with modern styling
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
        self.results_table.setIconSize(QSize(64, 64))
        # Connect click to preview
        self.results_table.cellClicked.connect(self._on_table_click)
        left_layout.addWidget(self.results_table)

        # Right panel - Preview
        right_panel = QFrame()
        right_panel.setProperty("card", True)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)

        preview_label = QLabel('👁️ Preview:')
        preview_label.setProperty("secondary", True)
        right_layout.addWidget(preview_label)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(280, 280)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setToolTip('Tiled preview of last processed image')
        right_layout.addWidget(self.preview_label, alignment=Qt.AlignTop)
        right_layout.addStretch()

        results_layout.addWidget(left_panel, stretch=3)
        results_layout.addWidget(right_panel, stretch=1)
        main_layout.addLayout(results_layout)

        layout.addWidget(main_card)

        # Footer bar with modern styling
        footer_card = QFrame()
        footer_card.setProperty("card", True)
        footer_layout = QHBoxLayout(footer_card)
        footer_layout.setContentsMargins(16, 12, 16, 12)

        self.footer_label = QLabel('✨ Ready to process images')
        self.footer_label.setProperty("secondary", True)
        footer_layout.addWidget(self.footer_label)

        footer_layout.addStretch()

        self.footer_progress = QProgressBar()
        self.footer_progress.setVisible(False)
        self.footer_progress.setFixedWidth(200)
        footer_layout.addWidget(self.footer_progress)

        export_btn = QPushButton('💾 Export CSV')
        export_btn.setToolTip('Export last batch results to CSV file')
        export_btn.clicked.connect(self.export_csv)
        footer_layout.addWidget(export_btn)

        settings_btn = QPushButton()
        settings_btn.setFixedSize(40, 32)
        settings_icon = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icons', 'settings.svg')
        if os.path.exists(settings_icon):
            settings_btn.setIcon(QIcon(settings_icon))
        else:
            settings_btn.setText('⚙️')
        settings_btn.setToolTip('Open settings')
        settings_btn.clicked.connect(self.open_settings)
        footer_layout.addWidget(settings_btn)

        layout.addWidget(footer_card)

        # Floating preview window (initially hidden)
        self.preview_window = PreviewWindow(parent=self)

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
            print(f"Error saving last path: {e}")

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