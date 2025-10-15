#!/usr/bin/env python3
"""
KS MetaMaker - Main GUI Application
AI-assisted local utility for tagging, renaming, and organizing visual assets
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QProgressBar, QTextEdit, QFileDialog,
        QSplitter, QTreeWidget, QTreeWidgetItem, QStatusBar, QMessageBox
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont, QIcon, QDragEnterEvent, QDropEvent, QPalette, QColor
except ImportError as e:
    print(f"Missing required packages. Please install dependencies: {e}")
    sys.exit(1)

from ks_metamaker.utils.config import Config
from ks_metamaker.ingest import ImageIngester
from ks_metamaker.tagger import ImageTagger
from ks_metamaker.rename import FileRenamer
from ks_metamaker.organize import FileOrganizer
from ks_metamaker.export import DatasetExporter


class ProcessingWorker(QThread):
    """Worker thread for processing images"""
    progress = pyqtSignal(int, str)  # progress percentage, status message
    finished = pyqtSignal(dict)  # results
    error = pyqtSignal(str)

    def __init__(self, input_dir: Path, output_dir: Path, config: Config):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.config = config

    def run(self):
        try:
            # Initialize components
            ingester = ImageIngester(enable_quality_filter=True, enable_duplicate_detection=True)
            tagger = ImageTagger(self.config)
            renamer = FileRenamer(self.config)
            organizer = FileOrganizer(self.config, self.output_dir)
            exporter = DatasetExporter(self.config)

            # Ingest images
            self.progress.emit(10, "Ingesting images...")
            images = ingester.ingest(self.input_dir)

            # Process each image
            results = {}
            total = len(images)
            for i, image_path in enumerate(images):
                progress = 10 + (i / total) * 80
                self.progress.emit(int(progress), f"Processing {image_path.name}...")

                # Tag image
                tags = tagger.tag(image_path)

                # Rename and organize
                new_path = renamer.rename(image_path, tags)
                organized_path = organizer.organize(new_path, tags[0] if tags else "unknown")

                # Export
                exporter.export(organized_path, tags)

                results[str(image_path)] = {
                    'tags': tags,
                    'new_path': str(organized_path)
                }

            # Finalize export
            self.progress.emit(95, "Finalizing export...")
            exporter.finalize_export(self.output_dir)

            self.progress.emit(100, "Processing complete!")
            self.finished.emit(results)

        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.config = Config()
        self.processing_worker = None

        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("KS MetaMaker - Tag. Name. Organize. Simplify.")
        self.setMinimumSize(1000, 700)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)

        # Top toolbar
        toolbar_layout = QHBoxLayout()

        self.select_input_btn = QPushButton("Select Input Folder")
        self.select_input_btn.setMinimumHeight(35)
        toolbar_layout.addWidget(self.select_input_btn)

        self.select_output_btn = QPushButton("Select Output Folder")
        self.select_output_btn.setMinimumHeight(35)
        toolbar_layout.addWidget(self.select_output_btn)

        self.process_btn = QPushButton("Process Images")
        self.process_btn.setMinimumHeight(35)
        self.process_btn.setEnabled(False)
        toolbar_layout.addWidget(self.process_btn)

        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Ready. Select input and output folders to begin.")
        layout.addWidget(self.status_label)

        # Splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - File tree
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabel("Input Files")
        splitter.addWidget(self.file_tree)

        # Right panel - Results
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Processing results will appear here...")
        splitter.addWidget(self.results_text)

        splitter.setSizes([300, 700])
        layout.addWidget(splitter)

        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("KS MetaMaker v0.1.0 - Ready")

    def setup_connections(self):
        """Setup signal connections"""
        self.select_input_btn.clicked.connect(self.select_input_folder)
        self.select_output_btn.clicked.connect(self.select_output_folder)
        self.process_btn.clicked.connect(self.start_processing)

    def select_input_folder(self):
        """Select input folder containing images"""
        folder = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder:
            self.input_dir = Path(folder)
            self.update_file_tree()
            self.check_ready_to_process()

    def select_output_folder(self):
        """Select output folder for processed images"""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_dir = Path(folder)
            self.check_ready_to_process()

    def check_ready_to_process(self):
        """Check if we have both input and output folders"""
        if hasattr(self, 'input_dir') and hasattr(self, 'output_dir'):
            self.process_btn.setEnabled(True)
            self.status_label.setText(f"Ready to process images from {self.input_dir.name} to {self.output_dir.name}")
        else:
            self.process_btn.setEnabled(False)

    def update_file_tree(self):
        """Update the file tree with input directory contents"""
        self.file_tree.clear()
        if not hasattr(self, 'input_dir'):
            return

        # Add root item
        root_item = QTreeWidgetItem([self.input_dir.name])
        self.file_tree.addTopLevelItem(root_item)

        # Add image files
        image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'}
        for file_path in self.input_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                item = QTreeWidgetItem([file_path.name])
                root_item.addChild(item)

        root_item.setExpanded(True)

    def start_processing(self):
        """Start the image processing"""
        if self.processing_worker and self.processing_worker.isRunning():
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.process_btn.setEnabled(False)
        self.status_label.setText("Processing images...")

        # Start worker thread
        self.processing_worker = ProcessingWorker(self.input_dir, self.output_dir, self.config)
        self.processing_worker.progress.connect(self.update_progress)
        self.processing_worker.finished.connect(self.processing_finished)
        self.processing_worker.error.connect(self.processing_error)
        self.processing_worker.start()

    def update_progress(self, value: int, message: str):
        """Update progress bar and status"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        self.status_bar.showMessage(f"Progress: {value}% - {message}")

    def processing_finished(self, results: dict):
        """Handle processing completion"""
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        self.status_label.setText(f"Processing complete! Processed {len(results)} images.")

        # Display results
        result_text = "Processing Results:\n\n"
        for original_path, data in results.items():
            result_text += f"File: {Path(original_path).name}\n"
            result_text += f"Tags: {', '.join(data['tags'])}\n"
            result_text += f"New location: {data['new_path']}\n\n"

        self.results_text.setPlainText(result_text)

        QMessageBox.information(self, "Complete", f"Successfully processed {len(results)} images!")

    def processing_error(self, error_msg: str):
        """Handle processing error"""
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        self.status_label.setText("Error occurred during processing")
        QMessageBox.critical(self, "Error", f"Processing failed: {error_msg}")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Apply dark theme manually
    app.setStyle("Fusion")
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    app.setPalette(dark_palette)

    # Set application properties
    app.setApplicationName("KS MetaMaker")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Kalponic Studio")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()