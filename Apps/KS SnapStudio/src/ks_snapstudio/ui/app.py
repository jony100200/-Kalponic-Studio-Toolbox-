"""
Desktop GUI application for KS SnapStudio.
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QProgressBar, QTextEdit, QFileDialog, QSplitter,
    QFrame, QSizePolicy, QMessageBox, QSystemTrayIcon, QMenu
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QRect, QSize
from PySide6.QtGui import QPixmap, QIcon, QFont, QAction, QPainter, QColor

# Import core modules
from ks_snapstudio.core.capture import ScreenCapture
from ks_snapstudio.core.mask import CircleMask
from ks_snapstudio.core.watermark import WatermarkEngine
from ks_snapstudio.core.composer import BackgroundComposer
from ks_snapstudio.core.exporter import PreviewExporter
from ks_snapstudio.presets.manager import PresetManager

logger = logging.getLogger(__name__)


class DarkTheme:
    """Dark theme colors and styles for KS SnapStudio."""

    COLORS = {
        'bg_primary': '#1e1e1e',
        'bg_secondary': '#2d2d2d',
        'bg_tertiary': '#3a3a3a',
        'fg_primary': '#ffffff',
        'fg_secondary': '#cccccc',
        'fg_tertiary': '#999999',
        'accent': '#007acc',
        'accent_hover': '#0098ff',
        'success': '#28a745',
        'warning': '#ffc107',
        'error': '#dc3545',
        'border': '#404040',
        'button_bg': '#3a3a3a',
        'button_hover': '#454545',
    }

    @staticmethod
    def get_stylesheet():
        return f"""
        QMainWindow {{
            background-color: {DarkTheme.COLORS['bg_primary']};
            color: {DarkTheme.COLORS['fg_primary']};
        }}

        QWidget {{
            background-color: {DarkTheme.COLORS['bg_primary']};
            color: {DarkTheme.COLORS['fg_primary']};
            font-family: 'Segoe UI', Arial, sans-serif;
        }}

        QGroupBox {{
            font-weight: bold;
            border: 1px solid {DarkTheme.COLORS['border']};
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: {DarkTheme.COLORS['accent']};
        }}

        QPushButton {{
            background-color: {DarkTheme.COLORS['button_bg']};
            border: 1px solid {DarkTheme.COLORS['border']};
            border-radius: 4px;
            padding: 8px 16px;
            color: {DarkTheme.COLORS['fg_primary']};
            font-weight: 500;
        }}

        QPushButton:hover {{
            background-color: {DarkTheme.COLORS['button_hover']};
            border-color: {DarkTheme.COLORS['accent']};
        }}

        QPushButton:pressed {{
            background-color: {DarkTheme.COLORS['accent']};
        }}

        QPushButton#captureBtn {{
            background-color: {DarkTheme.COLORS['success']};
            font-size: 14px;
            font-weight: bold;
            padding: 12px 24px;
        }}

        QPushButton#captureBtn:hover {{
            background-color: #34d058;
        }}

        QComboBox {{
            background-color: {DarkTheme.COLORS['bg_secondary']};
            border: 1px solid {DarkTheme.COLORS['border']};
            border-radius: 4px;
            padding: 4px 8px;
            color: {DarkTheme.COLORS['fg_primary']};
            min-width: 120px;
        }}

        QComboBox:hover {{
            border-color: {DarkTheme.COLORS['accent']};
        }}

        QComboBox::drop-down {{
            border: none;
        }}

        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid {DarkTheme.COLORS['fg_secondary']};
            margin-right: 8px;
        }}

        QSpinBox {{
            background-color: {DarkTheme.COLORS['bg_secondary']};
            border: 1px solid {DarkTheme.COLORS['border']};
            border-radius: 4px;
            padding: 4px;
            color: {DarkTheme.COLORS['fg_primary']};
        }}

        QCheckBox {{
            spacing: 8px;
        }}

        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {DarkTheme.COLORS['border']};
            border-radius: 3px;
            background-color: {DarkTheme.COLORS['bg_secondary']};
        }}

        QCheckBox::indicator:checked {{
            background-color: {DarkTheme.COLORS['accent']};
            border-color: {DarkTheme.COLORS['accent']};
        }}

        QLabel {{
            color: {DarkTheme.COLORS['fg_primary']};
        }}

        QLabel#titleLabel {{
            font-size: 18px;
            font-weight: bold;
            color: {DarkTheme.COLORS['accent']};
            margin-bottom: 10px;
        }}

        QProgressBar {{
            border: 1px solid {DarkTheme.COLORS['border']};
            border-radius: 4px;
            text-align: center;
        }}

        QProgressBar::chunk {{
            background-color: {DarkTheme.COLORS['accent']};
        }}

        QTextEdit {{
            background-color: {DarkTheme.COLORS['bg_secondary']};
            border: 1px solid {DarkTheme.COLORS['border']};
            border-radius: 4px;
            color: {DarkTheme.COLORS['fg_primary']};
            font-family: 'Consolas', 'Monaco', monospace;
        }}
        """


class ProcessingWorker(QThread):
    """Worker thread for image processing to keep UI responsive."""

    finished = Signal(object, dict)  # (processed_image, metadata)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, image, preset_config):
        super().__init__()
        self.image = image
        self.preset_config = preset_config

    def run(self):
        try:
            self.progress.emit("Initializing processing...")

            # Initialize tools
            mask_tool = CircleMask()
            watermark_tool = WatermarkEngine()
            composer = BackgroundComposer()

            self.progress.emit("Detecting circle...")

            # Detect and mask circle
            circle_info = mask_tool.detect_circle(self.image)
            if circle_info:
                cropped, circle_info = mask_tool.auto_crop_circle(self.image, circle_info)
                mask = mask_tool.create_circular_mask(cropped, circle_info['center'], circle_info['radius'])
                masked = mask_tool.apply_mask(cropped, mask)
                self.progress.emit(f"Circle detected (confidence: {circle_info['confidence']:.2f})")
            else:
                # Fallback to center crop
                height, width = self.image.shape[:2]
                size = min(width, height)
                x = (width - size) // 2
                y = (height - size) // 2
                masked = self.image[y:y+size, x:x+size]
                circle_info = {'center': (size//2, size//2), 'radius': size//2}
                self.progress.emit("No circle detected, using center crop")

            # Apply branding
            if self.preset_config.get('brand_ring', True):
                self.progress.emit("Adding brand ring...")
                masked = watermark_tool.add_brand_ring(masked, circle_info)

            if self.preset_config.get('watermark', True):
                self.progress.emit("Adding watermark...")
                masked = watermark_tool.add_watermark_text(masked, "KS SnapStudio")

            # Compose background
            self.progress.emit("Composing background...")
            final = composer.compose_background(
                masked,
                self.preset_config.get('background', 'solid'),
                self.preset_config.get('palette', 'neutral')
            )

            metadata = {
                'circle_detected': circle_info['confidence'] > 0,
                'circle_confidence': circle_info['confidence'],
                'size': f"{final.shape[1]}x{final.shape[0]}",
                'preset': self.preset_config.get('name', 'Unknown')
            }

            self.progress.emit("Processing complete")
            self.finished.emit(final, metadata)

        except Exception as e:
            self.error.emit(str(e))


class SnapStudioMainWindow(QMainWindow):
    """Main application window for KS SnapStudio."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("KS SnapStudio - Material Preview Capture")
        self.setMinimumSize(1000, 700)

        # Initialize components
        self.capture_tool = ScreenCapture()
        self.preset_manager = PresetManager()
        self.current_image = None
        self.processing_worker = None

        # Setup UI
        self.setup_ui()
        self.setup_tray_icon()
        self.apply_theme()

        # Load presets
        self.load_presets()

        logger.info("KS SnapStudio GUI initialized")

    def setup_ui(self):
        """Setup the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - Controls
        self.setup_control_panel(splitter)

        # Right panel - Preview
        self.setup_preview_panel(splitter)

        # Set splitter proportions
        splitter.setSizes([400, 600])

    def setup_control_panel(self, parent):
        """Setup the control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Title
        title = QLabel("KS SnapStudio")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        # Capture section
        capture_group = QGroupBox("Screen Capture")
        capture_layout = QVBoxLayout(capture_group)

        # Monitor selection
        monitor_layout = QHBoxLayout()
        monitor_layout.addWidget(QLabel("Monitor:"))
        self.monitor_combo = QComboBox()
        self.update_monitor_list()
        monitor_layout.addWidget(self.monitor_combo)
        capture_layout.addLayout(monitor_layout)

        # Area selection
        area_layout = QHBoxLayout()
        self.area_checkbox = QCheckBox("Custom Area")
        self.area_checkbox.stateChanged.connect(self.toggle_area_selection)
        area_layout.addWidget(self.area_checkbox)

        self.area_label = QLabel("x,y,width,height")
        self.area_label.setEnabled(False)
        area_layout.addWidget(self.area_label)
        capture_layout.addLayout(area_layout)

        # Capture button
        self.capture_btn = QPushButton("📸 Capture Screen")
        self.capture_btn.setObjectName("captureBtn")
        self.capture_btn.clicked.connect(self.capture_screen)
        capture_layout.addWidget(self.capture_btn)

        layout.addWidget(capture_group)

        # Processing section
        processing_group = QGroupBox("Processing Options")
        processing_layout = QVBoxLayout(processing_group)

        # Preset selection
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))
        self.preset_combo = QComboBox()
        preset_layout.addWidget(self.preset_combo)
        processing_layout.addLayout(preset_layout)

        # Options
        self.watermark_checkbox = QCheckBox("Add Watermark")
        self.watermark_checkbox.setChecked(True)
        processing_layout.addWidget(self.watermark_checkbox)

        self.brand_ring_checkbox = QCheckBox("Add Brand Ring")
        self.brand_ring_checkbox.setChecked(True)
        processing_layout.addWidget(self.brand_ring_checkbox)

        # Background options
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("Background:"))
        self.bg_combo = QComboBox()
        self.bg_combo.addItems(["solid", "gradient", "noise", "pattern", "random"])
        self.bg_combo.setCurrentText("random")
        bg_layout.addWidget(self.bg_combo)
        processing_layout.addLayout(bg_layout)

        # Process button
        self.process_btn = QPushButton("⚙️ Process Image")
        self.process_btn.clicked.connect(self.process_image)
        self.process_btn.setEnabled(False)
        processing_layout.addWidget(self.process_btn)

        layout.addWidget(processing_group)

        # Export section
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout(export_group)

        # Quality
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(95)
        quality_layout.addWidget(self.quality_spin)
        export_layout.addLayout(quality_layout)

        # Export buttons
        export_btn_layout = QHBoxLayout()

        self.save_btn = QPushButton("💾 Save As...")
        self.save_btn.clicked.connect(self.save_image)
        self.save_btn.setEnabled(False)
        export_btn_layout.addWidget(self.save_btn)

        self.clipboard_btn = QPushButton("📋 Copy to Clipboard")
        self.clipboard_btn.clicked.connect(self.copy_to_clipboard)
        self.clipboard_btn.setEnabled(False)
        export_btn_layout.addWidget(self.clipboard_btn)

        export_layout.addLayout(export_btn_layout)

        layout.addWidget(export_group)

        # Progress and log
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setPlainText("Ready to capture...")
        layout.addWidget(self.log_text)

        # Add stretch to push everything up
        layout.addStretch()

        parent.addWidget(panel)

    def setup_preview_panel(self, parent):
        """Setup the preview panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Preview label
        preview_label = QLabel("Preview")
        preview_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(preview_label)

        # Image preview
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 400)
        self.preview_label.setStyleSheet(f"""
            QLabel {{
                border: 2px dashed {DarkTheme.COLORS['border']};
                background-color: {DarkTheme.COLORS['bg_secondary']};
            }}
        """)
        layout.addWidget(self.preview_label)

        # Metadata display
        self.metadata_label = QLabel("No image captured")
        self.metadata_label.setAlignment(Qt.AlignCenter)
        self.metadata_label.setStyleSheet(f"color: {DarkTheme.COLORS['fg_tertiary']};")
        layout.addWidget(self.metadata_label)

        parent.addWidget(panel)

    def setup_tray_icon(self):
        """Setup system tray icon."""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

            # Create tray menu
            tray_menu = QMenu()
            show_action = QAction("Show", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)

            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(QApplication.quit)
            tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()

    def apply_theme(self):
        """Apply dark theme to the application."""
        self.setStyleSheet(DarkTheme.get_stylesheet())

    def update_monitor_list(self):
        """Update the monitor selection combo box."""
        self.monitor_combo.clear()
        monitor_info = self.capture_tool.get_monitor_info()

        for monitor in monitor_info['monitors']:
            text = f"Monitor {monitor['id']}"
            if monitor['is_primary']:
                text += " (Primary)"
            text += f" - {monitor['width']}x{monitor['height']}"
            self.monitor_combo.addItem(text, monitor['id'])

    def load_presets(self):
        """Load presets into the combo box."""
        self.preset_combo.clear()
        presets = self.preset_manager.get_all_presets()

        for name, config in presets.items():
            display_name = config.get('name', name)
            self.preset_combo.addItem(display_name, name)

    def toggle_area_selection(self, state):
        """Toggle custom area selection."""
        self.area_label.setEnabled(state)

    def capture_screen(self):
        """Capture the screen."""
        try:
            monitor_id = self.monitor_combo.currentData()
            self.log_message("Capturing screen...")

            if self.area_checkbox.isChecked():
                # Would implement area selection dialog here
                self.log_message("Area selection not implemented yet, capturing full screen")
                image = self.capture_tool.capture_fullscreen(monitor_id)
            else:
                image = self.capture_tool.capture_fullscreen(monitor_id)

            self.current_image = image
            self.display_preview(image)
            self.process_btn.setEnabled(True)
            self.log_message(f"Screen captured: {image.shape}")

        except Exception as e:
            self.log_message(f"Capture failed: {e}")
            QMessageBox.critical(self, "Capture Error", str(e))

    def display_preview(self, image):
        """Display image in preview area."""
        # Convert numpy array to QPixmap
        height, width = image.shape[:2]

        # Convert RGB to RGBA if needed
        if image.shape[2] == 3:
            # Add alpha channel
            alpha = np.full((height, width, 1), 255, dtype=np.uint8)
            image = np.concatenate([image, alpha], axis=2)

        # Create QImage from numpy array
        from PySide6.QtGui import QImage
        qimage = QImage(image.data, width, height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)

        # Scale to fit preview area while maintaining aspect ratio
        preview_size = self.preview_label.size()
        scaled_pixmap = pixmap.scaled(
            preview_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.preview_label.setPixmap(scaled_pixmap)

    def process_image(self):
        """Process the captured image."""
        if self.current_image is None:
            return

        # Get preset configuration
        preset_name = self.preset_combo.currentData()
        preset_config = self.preset_manager.get_preset(preset_name)

        if not preset_config:
            self.log_message("Invalid preset selected")
            return

        # Override with UI settings
        preset_config = preset_config.copy()
        preset_config['watermark'] = self.watermark_checkbox.isChecked()
        preset_config['brand_ring'] = self.brand_ring_checkbox.isChecked()
        preset_config['background'] = self.bg_combo.currentText()

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        # Disable buttons during processing
        self.process_btn.setEnabled(False)
        self.capture_btn.setEnabled(False)

        # Start processing in background thread
        self.processing_worker = ProcessingWorker(self.current_image, preset_config)
        self.processing_worker.progress.connect(self.log_message)
        self.processing_worker.finished.connect(self.on_processing_finished)
        self.processing_worker.error.connect(self.on_processing_error)
        self.processing_worker.start()

    def on_processing_finished(self, processed_image, metadata):
        """Handle processing completion."""
        self.current_image = processed_image
        self.display_preview(processed_image)

        # Update metadata display
        metadata_text = f"Size: {metadata['size']} | Preset: {metadata['preset']}"
        if metadata['circle_detected']:
            metadata_text += ".2f"        else:
            metadata_text += " | Circle: Manual crop"

        self.metadata_label.setText(metadata_text)

        # Enable export buttons
        self.save_btn.setEnabled(True)
        self.clipboard_btn.setEnabled(True)

        # Hide progress
        self.progress_bar.setVisible(False)

        # Re-enable buttons
        self.process_btn.setEnabled(True)
        self.capture_btn.setEnabled(True)

        self.log_message("Processing complete!")

    def on_processing_error(self, error_msg):
        """Handle processing error."""
        self.log_message(f"Processing error: {error_msg}")
        QMessageBox.critical(self, "Processing Error", error_msg)

        # Hide progress and re-enable buttons
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        self.capture_btn.setEnabled(True)

    def save_image(self):
        """Save the processed image."""
        if self.current_image is None:
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Preview",
            "preview.png",
            "Images (*.png *.jpg *.jpeg *.webp *.tiff)"
        )

        if filename:
            try:
                from ks_snapstudio.core.exporter import PreviewExporter
                exporter = PreviewExporter()
                success = exporter.export_preview(
                    self.current_image,
                    Path(filename),
                    quality=self.quality_spin.value()
                )

                if success:
                    self.log_message(f"Image saved to {filename}")
                else:
                    self.log_message("Failed to save image")

            except Exception as e:
                self.log_message(f"Save error: {e}")
                QMessageBox.critical(self, "Save Error", str(e))

    def copy_to_clipboard(self):
        """Copy image to clipboard."""
        if self.current_image is None:
            return

        try:
            # Convert to QPixmap and copy to clipboard
            height, width = self.current_image.shape[:2]

            if self.current_image.shape[2] == 3:
                alpha = np.full((height, width, 1), 255, dtype=np.uint8)
                image = np.concatenate([self.current_image, alpha], axis=2)
            else:
                image = self.current_image

            from PySide6.QtGui import QImage
            qimage = QImage(image.data, width, height, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)

            clipboard = QApplication.clipboard()
            clipboard.setPixmap(pixmap)

            self.log_message("Image copied to clipboard")

        except Exception as e:
            self.log_message(f"Clipboard error: {e}")
            QMessageBox.critical(self, "Clipboard Error", str(e))

    def log_message(self, message):
        """Add message to log."""
        current_text = self.log_text.toPlainText()
        self.log_text.setPlainText(f"{current_text}\n{message}")
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def closeEvent(self, event):
        """Handle application close."""
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        event.accept()


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("KS SnapStudio")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Kalponic Studio")

    # Set application icon
    # app.setWindowIcon(QIcon("path/to/icon.png"))

    # Create and show main window
    window = SnapStudioMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()</content>
<parameter name="filePath">E:\__Kalponic Studio Repositories\-Kalponic-Studio-Toolbox-\Apps\KS SnapStudio\src\ks_snapstudio\ui\app.py