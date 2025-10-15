"""
🖥️ Hardware Setup Dialog for KS MetaMaker
=========================================
GUI for hardware detection, model recommendations, and downloads
"""

import sys
from pathlib import Path
from typing import Optional, Callable
import logging

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QFrame, QMessageBox, QScrollArea,
    QWidget, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon

from .hardware_detector import HardwareDetector
from .model_recommender import ModelRecommender
from .model_downloader import ModelDownloader

logger = logging.getLogger(__name__)


class DownloadWorker(QThread):
    """Worker thread for downloading models"""
    progress_updated = pyqtSignal(str, int)  # message, percentage
    download_finished = pyqtSignal(dict)  # results dict

    def __init__(self, models_dir: Path, recommendations: dict):
        super().__init__()
        self.models_dir = models_dir
        self.recommendations = recommendations
        self.downloader = ModelDownloader(models_dir)

    def run(self):
        """Execute downloads in background thread"""
        results = self.downloader.download_all_models(
            self.recommendations,
            progress_callback=self.progress_updated.emit
        )
        self.download_finished.emit(results)


class HardwareSetupDialog(QDialog):
    """Dialog for hardware detection and model setup"""

    def __init__(self, models_dir: Path, parent=None):
        super().__init__(parent)
        self.models_dir = models_dir
        self.hardware_detector = HardwareDetector()
        self.model_recommender = ModelRecommender()
        self.download_worker = None

        self.setWindowTitle("KS MetaMaker - Hardware Setup & Model Download")
        self.setModal(True)
        self.resize(700, 600)

        self._setup_ui()
        self._detect_hardware()

    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("🖥️ Hardware Detection & AI Model Setup")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Hardware info section
        self._create_hardware_section(layout)

        # Model recommendations section
        self._create_recommendations_section(layout)

        # Download section
        self._create_download_section(layout)

        # Buttons
        self._create_buttons(layout)

    def _create_hardware_section(self, layout):
        """Create hardware information display"""
        hardware_group = QGroupBox("Detected Hardware")
        hardware_layout = QVBoxLayout(hardware_group)

        self.hardware_text = QTextEdit()
        self.hardware_text.setReadOnly(True)
        self.hardware_text.setMaximumHeight(120)
        hardware_layout.addWidget(self.hardware_text)

        layout.addWidget(hardware_group)

    def _create_recommendations_section(self, layout):
        """Create model recommendations display"""
        rec_group = QGroupBox("Recommended AI Models")
        rec_layout = QVBoxLayout(rec_group)

        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        self.recommendations_text.setMaximumHeight(150)
        rec_layout.addWidget(self.recommendations_text)

        layout.addWidget(rec_group)

    def _create_download_section(self, layout):
        """Create download progress section"""
        download_group = QGroupBox("Download Progress")
        download_layout = QVBoxLayout(download_group)

        self.progress_label = QLabel("Ready to download models...")
        download_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        download_layout.addWidget(self.progress_bar)

        self.download_log = QTextEdit()
        self.download_log.setReadOnly(True)
        self.download_log.setMaximumHeight(100)
        download_layout.addWidget(self.download_log)

        layout.addWidget(download_group)

    def _create_buttons(self, layout):
        """Create action buttons"""
        button_layout = QHBoxLayout()

        self.detect_button = QPushButton("🔄 Re-detect Hardware")
        self.detect_button.clicked.connect(self._detect_hardware)
        button_layout.addWidget(self.detect_button)

        button_layout.addStretch()

        self.download_button = QPushButton("⬇️ Download Models")
        self.download_button.clicked.connect(self._start_download)
        self.download_button.setEnabled(False)
        button_layout.addWidget(self.download_button)

        self.close_button = QPushButton("❌ Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

    def _detect_hardware(self):
        """Detect and display hardware information"""
        try:
            # Get hardware info
            summary = self.hardware_detector.get_hardware_summary()
            profile = self.hardware_detector.get_system_profile()

            # Display hardware info
            hardware_info = f"""
System Profile: {profile.upper()}

CPU: {summary['system']['cpu_name']}
Cores: {summary['system']['cpu_cores']}
RAM: {summary['system']['total_ram_gb']} GB total

"""

            if summary['gpus']:
                primary_gpu = summary['gpus'][0]
                hardware_info += f"GPU: {primary_gpu['name']} ({primary_gpu['memory_gb']} GB VRAM)"
            else:
                hardware_info += "GPU: None detected (CPU-only mode)"

            self.hardware_text.setPlainText(hardware_info.strip())

            # Get recommendations
            recommendation = self.model_recommender.get_recommendation(profile)
            self.current_recommendation = recommendation

            # Display recommendations
            rec_text = f"""
Profile: {recommendation.profile.upper()}
Reasoning: {recommendation.reasoning}

Recommended Models:
• Tagging: {recommendation.tagging_model}
• Detection: {recommendation.detection_model}
• Captioning: {recommendation.captioning_model}
"""
            self.recommendations_text.setPlainText(rec_text.strip())

            # Enable download button
            self.download_button.setEnabled(True)
            self.progress_label.setText("Hardware detected successfully. Ready to download models.")

        except Exception as e:
            logger.error(f"Hardware detection failed: {e}")
            QMessageBox.critical(self, "Error", f"Hardware detection failed: {e}")

    def _start_download(self):
        """Start downloading recommended models"""
        if not hasattr(self, 'current_recommendation'):
            QMessageBox.warning(self, "Warning", "No hardware profile detected. Please detect hardware first.")
            return

        # Confirm download
        reply = QMessageBox.question(
            self, "Confirm Download",
            f"Do you want to download the recommended AI models?\n\n"
            f"This will download approximately 2-8 GB of model files.\n\n"
            f"Profile: {self.current_recommendation.profile.upper()}\n"
            f"Models: {len(self.current_recommendation.download_urls)} files",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Disable buttons during download
        self.download_button.setEnabled(False)
        self.detect_button.setEnabled(False)
        self.close_button.setEnabled(False)

        # Start download
        self.progress_bar.setValue(0)
        self.download_log.clear()
        self.progress_label.setText("Starting model downloads...")

        self.download_worker = DownloadWorker(self.models_dir, self.current_recommendation.download_urls)
        self.download_worker.progress_updated.connect(self._update_progress)
        self.download_worker.download_finished.connect(self._download_finished)
        self.download_worker.start()

    def _update_progress(self, message: str, percentage: int):
        """Update download progress"""
        self.progress_label.setText(message)
        self.progress_bar.setValue(percentage)
        self.download_log.append(f"{message} ({percentage}%)")

    def _download_finished(self, results: dict):
        """Handle download completion"""
        # Re-enable buttons
        self.detect_button.setEnabled(True)
        self.close_button.setEnabled(True)

        # Show results
        successful = sum(1 for success in results.values() if success)
        total = len(results)

        if successful == total:
            self.progress_label.setText("✅ All models downloaded successfully!")
            QMessageBox.information(
                self, "Success",
                f"All {total} AI models downloaded successfully!\n\n"
                "KS MetaMaker is now ready to use with optimal AI models for your hardware."
            )
        else:
            self.progress_label.setText(f"⚠️ Downloaded {successful}/{total} models")
            QMessageBox.warning(
                self, "Partial Success",
                f"Downloaded {successful} out of {total} models.\n\n"
                "Some models may need to be downloaded manually or you can try again."
            )

        # Log results
        self.download_log.append(f"\nDownload Results: {successful}/{total} successful")

    def closeEvent(self, event):
        """Handle dialog close"""
        if self.download_worker and self.download_worker.isRunning():
            reply = QMessageBox.question(
                self, "Downloads in Progress",
                "Model downloads are still in progress. Are you sure you want to close?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

            # Stop the download worker
            self.download_worker.terminate()
            self.download_worker.wait()

        event.accept()