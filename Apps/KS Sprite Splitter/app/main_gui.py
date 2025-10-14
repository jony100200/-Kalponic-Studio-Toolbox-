"""
KS Sprite Splitter - PySide6 GUI Application

A modern, user-friendly interface for AI-powered 2D sprite separation.
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QProgressBar, QTextEdit,
    QFileDialog, QGroupBox, QFormLayout, QSplitter, QTabWidget,
    QListWidget, QCheckBox, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QPixmap, QImage, QIcon

import qdarkstyle

# Import qdarkstyle for better theme support
import qdarkstyle

# Import our pipeline
from ks_splitter.pipeline import PipelineRunner
from ks_splitter.parts import load_template


class ProcessingThread(QThread):
    """Background thread for sprite processing."""

    progress_updated = Signal(int, str)  # progress, message
    processing_finished = Signal(dict)   # results
    error_occurred = Signal(str)         # error message

    def __init__(self, input_path: str, output_dir: str, category: str, config: dict):
        super().__init__()
        self.input_path = input_path
        self.output_dir = output_dir
        self.category = category
        self.config = config

    def run(self):
        """Run the processing pipeline in background thread."""
        try:
            self.progress_updated.emit(10, "Initializing pipeline...")

            runner = PipelineRunner(self.config)
            self.progress_updated.emit(30, "Processing sprite...")

            run_dir = runner.run(self.input_path, self.output_dir, self.category)
            self.progress_updated.emit(100, f"Processing complete! Results in: {run_dir}")

            # Return results info
            results = {
                'run_dir': run_dir,
                'input_path': self.input_path,
                'category': self.category
            }
            self.processing_finished.emit(results)

        except Exception as e:
            self.error_occurred.emit(str(e))


class SpriteSplitterGUI(QMainWindow):
    """Main GUI application for KS Sprite Splitter."""

    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.processing_thread = None
        self.current_theme = self.load_theme_preference()  # Load saved theme preference

        self.init_ui()
        self.load_stylesheet()

        # Set up keyboard shortcuts
        self.setup_shortcuts()

    def setup_shortcuts(self):
        """Set up global keyboard shortcuts."""
        from PySide6.QtGui import QShortcut, QKeySequence

        # Theme toggle shortcut (Ctrl+T)
        theme_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        theme_shortcut.activated.connect(self.toggle_theme)

        # Focus shortcuts for accessibility
        focus_input_shortcut = QShortcut(QKeySequence("Alt+I"), self)
        focus_input_shortcut.activated.connect(lambda: self.input_path_label.setFocus())

        focus_output_shortcut = QShortcut(QKeySequence("Alt+O"), self)
        focus_output_shortcut.activated.connect(lambda: self.output_dir_label.setFocus())

        focus_process_shortcut = QShortcut(QKeySequence("Alt+P"), self)
        focus_process_shortcut.activated.connect(lambda: self.process_btn.setFocus())

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("KS Sprite Splitter v1.0")
        self.setMinimumSize(1000, 700)
        self.setAccessibleName("KS Sprite Splitter Main Window")
        self.setAccessibleDescription("AI-powered 2D sprite separation tool with dark theme interface")

        # Set application icon
        icon_path = Path(__file__).parent / "icons" / "app_icon.svg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - Controls
        self.create_control_panel(splitter)

        # Right panel - Preview/Results
        self.create_preview_panel(splitter)

        # Set splitter proportions
        splitter.setSizes([400, 600])

        # Status bar
        self.statusBar().showMessage("Ready")

        # Menu bar
        self.create_menu_bar()

    def create_control_panel(self, parent):
        """Create the control panel with input/output settings."""
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)

        # Input/Output group
        io_group = QGroupBox("Input & Output")
        io_layout = QFormLayout(io_group)

        # Input file selection
        self.input_path_label = QLabel("No file selected")
        self.input_path_label.setObjectName("input_path_label")
        self.input_path_label.setAccessibleName("Input file path")
        self.input_path_label.setAccessibleDescription("Shows the currently selected sprite image file path")
        select_input_btn = QPushButton("Select Sprite Image")
        select_input_btn.setToolTip("Click to browse and select a sprite image file (PNG, JPG, BMP, TIFF)")
        select_input_btn.setAccessibleName("Select input sprite image")
        select_input_btn.setShortcut("Ctrl+O")
        select_input_btn.clicked.connect(self.select_input_file)

        # Output directory selection
        self.output_dir_label = QLabel("No directory selected")
        self.output_dir_label.setObjectName("output_dir_label")
        self.output_dir_label.setAccessibleName("Output directory path")
        self.output_dir_label.setAccessibleDescription("Shows the currently selected output directory path")
        select_output_btn = QPushButton("Select Output Directory")
        select_output_btn.setToolTip("Click to browse and select an output directory for processed results")
        select_output_btn.setAccessibleName("Select output directory")
        select_output_btn.setShortcut("Ctrl+D")
        select_output_btn.clicked.connect(self.select_output_directory)

        io_layout.addRow("Input:", self.input_path_label)
        io_layout.addRow(select_input_btn)
        io_layout.addRow("Output:", self.output_dir_label)
        io_layout.addRow(select_output_btn)

        control_layout.addWidget(io_group)

        # Template selection group
        template_group = QGroupBox("Template Selection")
        template_layout = QVBoxLayout(template_group)

        self.template_combo = QComboBox()
        self.template_combo.addItems(['tree', 'flag', 'char', 'arch', 'vfx'])
        self.template_combo.setToolTip("Select the sprite category that best matches your input image")
        self.template_combo.setAccessibleName("Sprite category selection")
        self.template_combo.setAccessibleDescription("Choose the type of sprite being processed: tree, flag, character, architecture, or visual effects")
        self.template_combo.currentTextChanged.connect(self.on_template_changed)

        template_layout.addWidget(QLabel("Sprite Category:"))
        template_layout.addWidget(self.template_combo)

        # Template preview
        self.template_info = QTextEdit()
        self.template_info.setMaximumHeight(100)
        self.template_info.setReadOnly(True)
        self.template_info.setAccessibleName("Template information")
        self.template_info.setAccessibleDescription("Shows details about the selected sprite category including parts and processing parameters")
        self.on_template_changed('tree')  # Initialize with tree template

        template_layout.addWidget(QLabel("Template Info:"))
        template_layout.addWidget(self.template_info)

        control_layout.addWidget(template_group)

        # Backend selection group
        backend_group = QGroupBox("Backend Configuration")
        backend_layout = QFormLayout(backend_group)

        self.segmenter_combo = QComboBox()
        self.segmenter_combo.addItems(['mock', 'opencv'])
        self.segmenter_combo.setToolTip("Choose the segmentation algorithm for object detection")
        self.segmenter_combo.setAccessibleName("Segmentation backend")
        self.segmenter_combo.setAccessibleDescription("Select the method used to detect and separate objects in the sprite")

        self.matter_combo = QComboBox()
        self.matter_combo.addItems(['mock', 'guided'])
        self.matter_combo.setToolTip("Choose the matting algorithm for soft edges")
        self.matter_combo.setAccessibleName("Matting backend")
        self.matter_combo.setAccessibleDescription("Select the method used to create soft, anti-aliased edges around sprite parts")

        self.parts_combo = QComboBox()
        self.parts_combo.addItems(['mock', 'heuristic'])
        self.parts_combo.setToolTip("Choose the part splitting algorithm")
        self.parts_combo.setAccessibleName("Part splitting backend")
        self.parts_combo.setAccessibleDescription("Select the method used to separate the sprite into semantic parts")

        backend_layout.addRow("Segmentation:", self.segmenter_combo)
        backend_layout.addRow("Matting:", self.matter_combo)
        backend_layout.addRow("Part Splitting:", self.parts_combo)

        control_layout.addWidget(backend_group)

        # Processing controls
        process_group = QGroupBox("Processing")
        process_layout = QVBoxLayout(process_group)

        self.process_btn = QPushButton("🚀 Process Sprite")
        self.process_btn.setMinimumHeight(40)
        self.process_btn.setToolTip("Start processing the selected sprite with the chosen configuration")
        self.process_btn.setAccessibleName("Process sprite button")
        self.process_btn.setAccessibleDescription("Begins the AI-powered sprite separation process")
        self.process_btn.setShortcut("Ctrl+P")
        self.process_btn.clicked.connect(self.start_processing)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setAccessibleName("Processing progress")
        self.progress_bar.setAccessibleDescription("Shows the current progress of sprite processing")

        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        self.progress_label.setAccessibleName("Progress status")
        self.progress_label.setAccessibleDescription("Displays current processing status messages")

        process_layout.addWidget(self.process_btn)
        process_layout.addWidget(self.progress_bar)
        process_layout.addWidget(self.progress_label)

        control_layout.addWidget(process_group)

        # Add stretch to push everything to top
        control_layout.addStretch()

        parent.addWidget(control_widget)

    def create_preview_panel(self, parent):
        """Create the preview/results panel."""
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)

        # Tab widget for different views
        self.tab_widget = QTabWidget()

        # Preview tab
        preview_tab = QWidget()
        preview_layout_tab = QVBoxLayout(preview_tab)

        self.preview_image = QLabel("No preview available")
        self.preview_image.setObjectName("preview_image")
        self.preview_image.setAlignment(Qt.AlignCenter)
        self.preview_image.setMinimumSize(400, 300)
        self.preview_image.setAccessibleName("Sprite preview image")
        self.preview_image.setAccessibleDescription("Shows a preview of the selected sprite image or processing results")

        preview_layout_tab.addWidget(self.preview_image)

        # Results tab
        results_tab = QWidget()
        results_layout_tab = QVBoxLayout(results_tab)

        self.results_list = QListWidget()
        self.results_list.setAccessibleName("Processing results list")
        self.results_list.setAccessibleDescription("Lists the results and output files from sprite processing")
        results_layout_tab.addWidget(QLabel("Processing Results:"))
        results_layout_tab.addWidget(self.results_list)

        # Log tab
        log_tab = QWidget()
        log_layout_tab = QVBoxLayout(log_tab)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setAccessibleName("Processing log")
        self.log_text.setAccessibleDescription("Shows detailed log messages from the sprite processing pipeline")
        log_layout_tab.addWidget(QLabel("Processing Log:"))
        log_layout_tab.addWidget(self.log_text)

        # Add tabs
        self.tab_widget.addTab(preview_tab, "Preview")
        self.tab_widget.addTab(results_tab, "Results")
        self.tab_widget.addTab(log_tab, "Log")

        preview_layout.addWidget(self.tab_widget)

        parent.addWidget(preview_widget)

    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')

        open_action = file_menu.addAction('Open Sprite...')
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Select a sprite image file to process")
        open_action.triggered.connect(self.select_input_file)

        file_menu.addSeparator()

        exit_action = file_menu.addAction('Exit')
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)

        # View menu
        view_menu = menubar.addMenu('View')

        theme_action = view_menu.addAction('Toggle Theme (Dark/Light)')
        theme_action.setShortcut("Ctrl+T")
        theme_action.setStatusTip("Switch between dark and light themes")
        theme_action.triggered.connect(self.toggle_theme)

        # Help menu
        help_menu = menubar.addMenu('Help')

        about_action = help_menu.addAction('About')
        about_action.setShortcut("F1")
        about_action.setStatusTip("Show information about KS Sprite Splitter")
        about_action.triggered.connect(self.show_about)

    def load_config(self) -> dict:
        """Load configuration from YAML file."""
        try:
            import yaml
            config_path = Path(__file__).parent / "configs" / "config.yml"
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception:
            # Return default config
            return {
                'objects_backend': 'mock',
                'matte_backend': 'mock',
                'parts_backend': 'mock'
            }

    def load_stylesheet(self):
        """Load the application stylesheet with enhanced sci-fi dark theme."""
        try:
            # Load base qdarkstyle
            base_stylesheet = qdarkstyle.load_stylesheet_pyside6()

            # Enhanced sci-fi dark theme customizations
            custom_stylesheet = """
            /* KS Sprite Splitter - Enhanced Sci-Fi Dark Theme */

            /* Main window with subtle gradient background */
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #19232D, stop:1 #151A22);
                color: #F8FAFC;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 10pt;
            }

            /* Enhanced group boxes with sci-fi styling */
            QGroupBox {
                font-weight: 600;
                font-size: 11pt;
                border: 2px solid #475569;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2D3748, stop:1 #374151);
                color: #CBD5E0;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #00D4FF;
                font-weight: 700;
                font-size: 12pt;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            /* Enhanced buttons with neon accents */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #374151, stop:1 #4B5563);
                border: 2px solid #00D4FF;
                border-radius: 6px;
                padding: 10px 20px;
                color: #F8FAFC;
                font-weight: 600;
                font-size: 11pt;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                min-height: 16px;
            }

            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4B5563, stop:1 #6B7280);
                border-color: #00FF88;
                color: #00FF88;
            }

            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1F2937, stop:1 #374151);
                border-color: #FF6B6B;
            }

            QPushButton:disabled {
                background: #374151;
                border-color: #6B7280;
                color: #9CA3AF;
            }

            /* Enhanced combo boxes */
            QComboBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #374151, stop:1 #4B5563);
                border: 2px solid #475569;
                border-radius: 6px;
                padding: 6px 12px;
                color: #F8FAFC;
                font-size: 10pt;
                min-width: 120px;
                min-height: 20px;
            }

            QComboBox:hover {
                border-color: #00D4FF;
            }

            QComboBox:focus {
                border-color: #00FF88;
                outline: 2px solid #00FF88;
                outline-offset: 1px;
            }

            QComboBox::drop-down {
                border: none;
                width: 24px;
            }

            QComboBox QAbstractItemView {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2D3748, stop:1 #374151);
                border: 2px solid #475569;
                selection-background-color: #00D4FF;
                color: #F8FAFC;
                border-radius: 4px;
            }

            /* Enhanced progress bar with sci-fi styling */
            QProgressBar {
                border: 2px solid #475569;
                border-radius: 8px;
                text-align: center;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1F2937, stop:1 #374151);
                height: 20px;
            }

            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00D4FF, stop:1 #00FF88);
                border-radius: 6px;
            }

            /* Enhanced text areas */
            QTextEdit, QListWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2D3748, stop:1 #374151);
                border: 2px solid #475569;
                border-radius: 6px;
                color: #F8FAFC;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9pt;
            }

            QTextEdit:focus, QListWidget:focus {
                border-color: #00FF88;
                outline: 2px solid #00FF88;
                outline-offset: 1px;
            }

            /* Enhanced tabs */
            QTabWidget::pane {
                border: 2px solid #475569;
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2D3748, stop:1 #374151);
            }

            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #374151, stop:1 #4B5563);
                border: 2px solid #475569;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 20px;
                margin-right: 4px;
                color: #CBD5E0;
                font-weight: 600;
                font-size: 10pt;
            }

            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00D4FF, stop:1 #00FF88);
                border-bottom: 3px solid #00FF88;
                color: #1F2937;
                font-weight: 700;
            }

            QTabBar::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4B5563, stop:1 #6B7280);
                border-color: #00D4FF;
                color: #00D4FF;
            }

            /* Enhanced status bar */
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00D4FF, stop:1 #00FF88);
                color: #1F2937;
                border-top: 2px solid #00FF88;
                font-weight: 600;
                padding: 4px 8px;
            }

            /* Enhanced menu bar */
            QMenuBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2D3748, stop:1 #374151);
                border-bottom: 2px solid #475569;
                color: #F8FAFC;
                padding: 4px;
            }

            QMenuBar::item {
                background: transparent;
                padding: 6px 12px;
                border-radius: 4px;
                color: #CBD5E0;
                font-weight: 500;
            }

            QMenuBar::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00D4FF, stop:1 #00FF88);
                color: #1F2937;
            }

            /* Enhanced preview image area */
            QLabel#preview_image {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1F2937, stop:1 #374151);
                border: 2px dashed #475569;
                border-radius: 8px;
                color: #9CA3AF;
                font-style: italic;
                font-size: 11pt;
            }

            /* Enhanced splitter */
            QSplitter::handle {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #475569, stop:1 #6B7280);
                border-radius: 2px;
            }

            QSplitter::handle:horizontal {
                width: 4px;
            }

            QSplitter::handle:vertical {
                height: 4px;
            }

            /* Enhanced scrollbars */
            QScrollBar:vertical {
                background: #2D3748;
                width: 14px;
                border-radius: 7px;
            }

            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6B7280, stop:1 #9CA3AF);
                border-radius: 7px;
                min-height: 24px;
            }

            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00D4FF, stop:1 #00FF88);
            }

            /* Form labels */
            QLabel {
                color: #F8FAFC;
                font-weight: 500;
                font-size: 10pt;
            }

            /* Special styling for input path labels */
            QLabel[objectName*="path_label"] {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #374151, stop:1 #4B5563);
                border: 2px solid #475569;
                border-radius: 6px;
                padding: 6px 12px;
                color: #CBD5E0;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9pt;
                min-height: 16px;
            }
            """

            # Combine base stylesheet with custom enhancements
            full_stylesheet = base_stylesheet + custom_stylesheet
            self.setStyleSheet(full_stylesheet)

        except Exception as e:
            print(f"Warning: Could not load enhanced stylesheet: {e}")
            # Fallback to basic qdarkstyle
            try:
                fallback_stylesheet = qdarkstyle.load_stylesheet_pyside6()
                self.setStyleSheet(fallback_stylesheet)
            except Exception as e2:
                print(f"Warning: Could not load fallback stylesheet: {e2}")

    def toggle_theme(self):
        """Toggle between dark and light themes."""
        if self.current_theme == "dark":
            self.current_theme = "light"
        else:
            self.current_theme = "dark"
        self.load_stylesheet()
        # Save theme preference
        self.save_theme_preference()

    def load_theme_preference(self) -> str:
        """Load theme preference from settings."""
        try:
            from PySide6.QtCore import QSettings
            settings = QSettings("Kalponic Studio", "KS Sprite Splitter")
            theme = settings.value("theme", "dark")  # Default to dark
            return theme
        except Exception:
            return "dark"

    def save_theme_preference(self):
        """Save current theme preference to settings."""
        try:
            from PySide6.QtCore import QSettings
            settings = QSettings("Kalponic Studio", "KS Sprite Splitter")
            settings.setValue("theme", self.current_theme)
        except Exception:
            pass

    def select_input_file(self):
        """Open file dialog to select input sprite image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Sprite Image",
            str(Path.home()),
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )

        if file_path:
            self.input_path = file_path
            self.input_path_label.setText(Path(file_path).name)

            # Load and display preview
            self.load_image_preview(file_path)

    def select_output_directory(self):
        """Open directory dialog to select output directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory",
            str(Path.home())
        )

        if dir_path:
            self.output_dir = dir_path
            self.output_dir_label.setText(Path(dir_path).name)

    def load_image_preview(self, image_path: str):
        """Load and display image preview."""
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale to fit preview area while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.preview_image.setPixmap(scaled_pixmap)
            else:
                self.preview_image.setText("Failed to load image")
        except Exception as e:
            self.preview_image.setText(f"Error loading preview: {e}")

    def on_template_changed(self, template_name: str):
        """Update template information when selection changes."""
        try:
            template = load_template(template_name)
            info_text = f"Category: {template['name']}\n"
            info_text += f"Parts: {', '.join(template['parts'])}\n"
            info_text += f"Clustering: k={template['heuristics']['kmeans_k']}\n"
            info_text += f"Band width: {template['matting']['band_px']}px"

            if 'extras' in template:
                extras = template['extras']
                if extras:
                    info_text += f"\nExtras: {', '.join(extras.keys())}"

            self.template_info.setPlainText(info_text)
        except Exception as e:
            self.template_info.setPlainText(f"Error loading template: {e}")

    def start_processing(self):
        """Start the sprite processing pipeline."""
        if not hasattr(self, 'input_path') or not hasattr(self, 'output_dir'):
            self.statusBar().showMessage("Please select input file and output directory")
            return

        # Update config with selected backends
        self.config['objects_backend'] = self.segmenter_combo.currentText()
        self.config['matte_backend'] = self.matter_combo.currentText()
        self.config['parts_backend'] = self.parts_combo.currentText()

        # Disable processing button
        self.process_btn.setEnabled(False)
        self.process_btn.setText("Processing...")

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting...")

        # Clear previous results
        self.results_list.clear()
        self.log_text.clear()

        # Start processing thread
        self.processing_thread = ProcessingThread(
            self.input_path,
            self.output_dir,
            self.template_combo.currentText(),
            self.config
        )

        self.processing_thread.progress_updated.connect(self.on_progress_updated)
        self.processing_thread.processing_finished.connect(self.on_processing_finished)
        self.processing_thread.error_occurred.connect(self.on_error_occurred)

        self.processing_thread.start()

    def on_progress_updated(self, progress: int, message: str):
        """Handle progress updates from processing thread."""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
        self.log_text.append(f"[{progress}%] {message}")

    def on_processing_finished(self, results: dict):
        """Handle successful processing completion."""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.process_btn.setEnabled(True)
        self.process_btn.setText("🚀 Process Sprite")

        # Update results list
        self.results_list.addItem(f"Input: {Path(results['input_path']).name}")
        self.results_list.addItem(f"Category: {results['category']}")
        self.results_list.addItem(f"Output: {results['run_dir']}")

        # Try to load result preview
        run_dir = Path(results['run_dir'])
        preview_dir = run_dir / "Preview"
        if preview_dir.exists():
            preview_files = list(preview_dir.glob("*.png"))
            if preview_files:
                self.load_image_preview(str(preview_files[0]))

        self.statusBar().showMessage("Processing completed successfully!")

    def on_error_occurred(self, error_msg: str):
        """Handle processing errors."""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.process_btn.setEnabled(True)
        self.process_btn.setText("🚀 Process Sprite")

        self.log_text.append(f"ERROR: {error_msg}")
        self.statusBar().showMessage(f"Processing failed: {error_msg}")

    def show_about(self):
        """Show about dialog."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(
            self, "About KS Sprite Splitter",
            "KS Sprite Splitter v1.0\n\n"
            "AI-powered 2D sprite separation tool\n"
            "Built with PySide6 and OpenCV\n\n"
            "© 2025 Kalponic Studio"
        )


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("KS Sprite Splitter")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Kalponic Studio")

    # Set application icon if available
    icon_path = Path(__file__).parent / "app" / "icons" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = SpriteSplitterGUI()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())