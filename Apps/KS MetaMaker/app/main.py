#!/usr/bin/env python3
"""
KS MetaMaker - Main GUI Application
AI-assisted local utility for tagging, renaming, and organizing visual assets
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

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
from ks_metamaker.context_metadata import ContextMetadataGenerator
from ks_metamaker.review_dialog import ReviewDialog
from ks_metamaker.hardware_setup_dialog import HardwareSetupDialog


class ProcessingWorker(QThread):
    """Worker thread for processing images"""
    progress = pyqtSignal(int, str)  # progress percentage, status message
    finished = pyqtSignal(dict)  # results
    error = pyqtSignal(str)

    def __init__(self, input_dir: Path, output_dir: Path, config: Config, hardware_detector=None):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.config = config
        self.hardware_detector = hardware_detector

    def run(self):
        try:
            # Initialize components
            ingester = ImageIngester(enable_quality_filter=True, enable_duplicate_detection=True)
            tagger = ImageTagger(self.config, hardware_detector=self.hardware_detector)
            renamer = FileRenamer(self.config)
            organizer = FileOrganizer(self.config, self.output_dir)
            exporter = DatasetExporter(self.config)

            # Initialize context metadata generator if enabled
            metadata_generator = None
            if self.config.export.get('write_context_json', False):
                metadata_generator = ContextMetadataGenerator(self.output_dir)

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

                # Generate context metadata if enabled
                if metadata_generator:
                    try:
                        metadata_path = metadata_generator.generate_context_metadata(
                            image_path=image_path,
                            processed_path=organized_path,
                            tags=tags,
                            profile_name=self.config.profile_name,
                            hardware_profile=getattr(self.hardware_detector, 'profile', 'unknown') if self.hardware_detector else 'unknown',
                            models_used=self.config.models.keys() if self.config.models else []
                        )
                        logger.info(f"Generated context metadata: {metadata_path}")
                    except Exception as e:
                        logger.warning(f"Failed to generate context metadata for {image_path}: {e}")

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
        self.hardware_detector = None
        self.processing_worker = None
        self.processing_results = {}  # Store results for review

        # Initialize hardware detection
        self.init_hardware_detection()

        self.init_ui()
        self.setup_connections()

    def init_hardware_detection(self):
        """Initialize hardware detection and show setup dialog if needed"""
        try:
            from ks_metamaker.hardware_detector import HardwareDetector
            self.hardware_detector = HardwareDetector()

            # Show hardware setup dialog
            setup_dialog = HardwareSetupDialog(self.hardware_detector, self)
            if setup_dialog.exec():
                logger.info("Hardware setup completed")
            else:
                logger.warning("Hardware setup cancelled or failed")

        except Exception as e:
            logger.error(f"Hardware detection initialization failed: {e}")
            # Continue without hardware detection
            self.hardware_detector = None

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("KS MetaMaker - Tag. Name. Organize. Simplify.")
        self.setMinimumSize(1000, 700)

        # Create menu bar
        self.create_menu_bar()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)

        # Top toolbar
        toolbar_layout = QHBoxLayout()

        # Profile selection
        toolbar_layout.addWidget(QLabel("Profile:"))
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(150)
        self.populate_profile_combo()
        toolbar_layout.addWidget(self.profile_combo)

        toolbar_layout.addSpacing(20)

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

        self.review_btn = QPushButton("Review Tags")
        self.review_btn.setMinimumHeight(35)
        self.review_btn.setEnabled(False)
        self.review_btn.setVisible(False)  # Hidden until processing is done
        toolbar_layout.addWidget(self.review_btn)

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

    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()

        # Setup menu
        setup_menu = menubar.addMenu('Setup')

        # Hardware setup action
        hardware_action = setup_menu.addAction('🖥️ Hardware & AI Models')
        hardware_action.triggered.connect(self.show_hardware_setup)

        # Separator
        setup_menu.addSeparator()

        # Exit action
        exit_action = setup_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)

    def show_hardware_setup(self):
        """Show the hardware setup dialog"""
        models_dir = project_root / "models"
        dialog = HardwareSetupDialog(models_dir, self)
        dialog.exec()

    def setup_connections(self):
        """Setup signal connections"""
        self.select_input_btn.clicked.connect(self.select_input_folder)
        self.select_output_btn.clicked.connect(self.select_output_folder)
        self.process_btn.clicked.connect(self.start_processing)
        self.review_btn.clicked.connect(self.show_review_dialog)
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)

    def populate_profile_combo(self):
        """Populate the profile selection combo box"""
        self.profile_combo.clear()
        profiles = self.config.get_available_profiles()

        for profile in profiles:
            self.profile_combo.addItem(profile)

        # Set current profile
        current_profile = self.config.profile_name
        index = self.profile_combo.findText(current_profile)
        if index >= 0:
            self.profile_combo.setCurrentIndex(index)

    def show_review_dialog(self):
        """Show the tag review dialog"""
        if not self.processing_results:
            QMessageBox.warning(self, "No Results", "No processing results available for review.")
            return

        # Prepare data for review dialog
        review_data = []
        for original_path, data in self.processing_results.items():
            review_data.append({
                'path': data['new_path'],  # Use the processed path
                'tags': data['tags'],
                'metadata': {}  # Could be enhanced to include confidence scores
            })

        # Show review dialog
        review_dialog = ReviewDialog(review_data, self.config, self)
        review_dialog.tags_approved.connect(self.on_tags_approved)
        review_dialog.tags_rejected.connect(self.on_tags_rejected)
        review_dialog.tags_modified.connect(self.on_tags_modified)

        review_dialog.exec()

    def on_tags_approved(self, approved_data: list):
        """Handle approved tags from review dialog"""
        self.status_bar.showMessage(f"Approved {len(approved_data)} images with reviewed tags")
        logger.info(f"Approved {len(approved_data)} images from review")

    def on_tags_rejected(self, rejected_paths: list):
        """Handle rejected images from review dialog"""
        self.status_bar.showMessage(f"Rejected {len(rejected_paths)} images")
        logger.info(f"Rejected {len(rejected_paths)} images from review")

    def on_tags_modified(self, modified_tags: dict):
        """Handle modified tags from review dialog"""
        # Here you could update the exported files with the modified tags
        self.status_bar.showMessage(f"Updated tags for {len(modified_tags)} images")
        logger.info(f"Modified tags for {len(modified_tags)} images")

    def select_input_folder(self):
        """Select input folder containing images"""
        # Start from last used directory if available
        start_dir = self.config.last_input_dir if self.config.last_input_dir else ""
        folder = QFileDialog.getExistingDirectory(self, "Select Input Folder", start_dir)
        if folder:
            self.input_dir = Path(folder)
            self.config.last_input_dir = str(self.input_dir)
            self.config.save()  # Save the preference
            self.status_bar.showMessage(f"Input folder set: {self.input_dir.name} (remembered for next session)")
            self.update_file_tree()
            self.check_ready_to_process()

    def select_output_folder(self):
        """Select output folder for processed images"""
        # Start from last used directory if available
        start_dir = self.config.last_output_dir if self.config.last_output_dir else ""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", start_dir)
        if folder:
            self.output_dir = Path(folder)
            self.config.last_output_dir = str(self.output_dir)
            self.config.save()  # Save the preference
            self.status_bar.showMessage(f"Output folder set: {self.output_dir.name} (remembered for next session)")
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
        self.processing_worker = ProcessingWorker(self.input_dir, self.output_dir, self.config, self.hardware_detector)
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

        # Store results for review
        self.processing_results = results

        # Show review button if review UI is enabled in profile
        if self.config.ui_features.get('review_ui', True):
            self.review_btn.setVisible(True)
            self.review_btn.setEnabled(True)

        # Display results
        result_text = "Processing Results:\n\n"
        for original_path, data in results.items():
            result_text += f"File: {Path(original_path).name}\n"
            result_text += f"Tags: {', '.join(data['tags'])}\n"
            result_text += f"New location: {data['new_path']}\n\n"

        self.results_text.setPlainText(result_text)

        QMessageBox.information(self, "Complete", f"Successfully processed {len(results)} images!\n\nThe output folder will now open in File Explorer.\n\nUse 'Review Tags' to manually validate and edit the generated tags.")

        # Open output folder in file explorer
        try:
            if hasattr(self, 'output_dir'):
                os.startfile(str(self.output_dir))
                logger.info(f"Opened output folder: {self.output_dir}")
        except Exception as e:
            logger.warning(f"Could not open output folder: {e}")

    def processing_error(self, error_msg: str):
        """Handle processing error"""
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        self.status_label.setText("Error occurred during processing")
        QMessageBox.critical(self, "Error", f"Processing failed: {error_msg}")

    def undo_action(self):
        """Perform undo action"""
        # TODO: Implement undo functionality
        QMessageBox.information(self, "Undo", "Undo action not implemented yet.")

    def redo_action(self):
        """Perform redo action"""
        # TODO: Implement redo functionality
        QMessageBox.information(self, "Redo", "Redo action not implemented yet.")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About KS MetaMaker",
            "<h2>KS MetaMaker v0.1.0</h2>"
            "<p>AI-assisted local utility for tagging, renaming, and organizing visual assets.</p>"
            "<p>Copyright &copy; 2023 Kalponic Studio. All rights reserved.</p>"
        )


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