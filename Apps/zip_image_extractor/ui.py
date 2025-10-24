"""
Kalponic Studio Zip Image Extractor UI

Implements a PySide6 interface that follows the KS Universal UI System blueprint.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, List, Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSizePolicy,
    QCheckBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QFrame,
)

try:
    # When executed via `python -m zip_image_extractor.ui`
    from .main import extract_first_image
except ImportError:  # pragma: no cover - direct script execution
    from main import extract_first_image


KS_TOKENS = {
    "color.bg.base": "#1C1F2A",
    "color.bg.panel": "#262E38",
    "color.text.primary": "#D9D8D8",
    "color.text.secondary": "#A0A0A0",
    "color.accent.primary": "#00C2FF",
    "color.accent.success": "#32CD32",
    "color.accent.error": "#E45757",
    "color.shadow.base": "rgba(0,0,0,0.25)",
    "color.glow.accent": "rgba(0,194,255,0.35)",
    "radius.panel": "8px",
    "spacing.unit": "8px",
}


APP_STYLE = f"""
QWidget {{
    background-color: {KS_TOKENS["color.bg.base"]};
    color: {KS_TOKENS["color.text.primary"]};
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 13px;
}}
QLabel#title {{
    font-size: 18px;
    font-weight: 700;
}}
QLabel#subtitle {{
    font-size: 14px;
    color: {KS_TOKENS["color.text.secondary"]};
}}
QFrame#panel {{
    background-color: {KS_TOKENS["color.bg.panel"]};
    border-radius: {KS_TOKENS["radius.panel"]};
    border: 1px solid rgba(255, 255, 255, 0.05);
}}
QLabel#section {{
    font-weight: 600;
    color: {KS_TOKENS["color.text.secondary"]};
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}
QLineEdit, QTextEdit {{
    background-color: {KS_TOKENS["color.bg.base"]};
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 8px 10px;
    selection-background-color: {KS_TOKENS["color.accent.primary"]};
}}
QLineEdit:focus, QTextEdit:focus {{
    border: 1px solid {KS_TOKENS["color.accent.primary"]};
    box-shadow: 0 0 0 1px {KS_TOKENS["color.accent.primary"]};
}}
QPushButton {{
    border-radius: 6px;
    padding: 10px 16px;
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
}}
QPushButton:hover {{
    border-color: {KS_TOKENS["color.accent.primary"]};
}}
QPushButton:disabled {{
    color: rgba(255, 255, 255, 0.4);
    background-color: rgba(255, 255, 255, 0.05);
}}
QPushButton[class="ks-primary"] {{
    background-color: {KS_TOKENS["color.accent.primary"]};
    color: {KS_TOKENS["color.bg.base"]};
    border: none;
    font-weight: 600;
}}
QPushButton[class="ks-primary"]:hover {{
    background-color: rgba(0, 194, 255, 0.85);
}}
QPushButton[class="ks-primary"]:pressed {{
    background-color: {KS_TOKENS["color.accent.primary"]};
}}
QCheckBox {{
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    background-color: rgba(255, 255, 255, 0.05);
}}
QCheckBox::indicator:checked {{
    background-color: {KS_TOKENS["color.accent.primary"]};
    border: 1px solid {KS_TOKENS["color.accent.primary"]};
}}
QProgressBar {{
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    background-color: rgba(255, 255, 255, 0.05);
    height: 12px;
}}
QProgressBar::chunk {{
    border-radius: 6px;
    background-color: {KS_TOKENS["color.accent.primary"]};
}}
"""


class ExtractionWorker(QThread):
    """Background worker for sequential zip processing."""

    progress = Signal(str)
    step_changed = Signal(int, int)
    finished = Signal(int, int)
    failed = Signal(str)

    def __init__(self, zip_paths: Iterable[Path], output_dir: Optional[Path] = None):
        super().__init__()
        self._zip_paths: List[Path] = list(zip_paths)
        self._output_dir = output_dir

    def run(self) -> None:  # type: ignore[override]
        total = len(self._zip_paths)
        success_count = 0

        for index, zip_path in enumerate(self._zip_paths, start=1):
            if self.isInterruptionRequested():
                break

            self.progress.emit(f"Processing '{zip_path.name}'")
            try:
                result = extract_first_image(zip_path, self._output_dir, reporter=self.progress.emit)
                if result is not None:
                    success_count += 1
            except Exception as exc:  # pragma: no cover - defensive path
                self.failed.emit(f"Error processing '{zip_path}': {exc}")
            finally:
                self.step_changed.emit(index, total)

        self.finished.emit(success_count, total)


class KSZipImageExtractor(QWidget):
    """High-level UI container."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("KS Zip Image Extractor")
        self.resize(840, 620)

        self._worker: Optional[ExtractionWorker] = None

        self._build_ui()
        self._apply_palette()
        self._wire_events()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        title = QLabel("KS Zip Image Extractor")
        title.setObjectName("title")
        subtitle = QLabel("Extract the leading image from zip archives with the KS universal interface.")
        subtitle.setObjectName("subtitle")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        controls_frame = QFrame()
        controls_frame.setObjectName("panel")
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(20, 20, 20, 20)
        controls_layout.setSpacing(18)

        section_label = QLabel("Source & Output")
        section_label.setObjectName("section")
        controls_layout.addWidget(section_label)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(14)

        self.source_label = QLabel("Zip File")
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("Select a .zip archive to process…")
        self.source_browse = QPushButton("Browse…")

        grid.addWidget(self.source_label, 0, 0)
        grid.addWidget(self.source_edit, 0, 1)
        grid.addWidget(self.source_browse, 0, 2)

        self.process_folder_cb = QCheckBox("Process entire folder")
        self.include_subdirs_cb = QCheckBox("Include sub-folders")
        self.include_subdirs_cb.setEnabled(False)

        grid.addWidget(self.process_folder_cb, 1, 1, 1, 1)
        grid.addWidget(self.include_subdirs_cb, 1, 2, 1, 1)

        output_label = QLabel("Output Directory")
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Optional. Defaults to each zip's folder.")
        self.output_browse = QPushButton("Browse…")

        grid.addWidget(output_label, 2, 0)
        grid.addWidget(self.output_edit, 2, 1)
        grid.addWidget(self.output_browse, 2, 2)

        controls_layout.addLayout(grid)

        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        self.status_label = QLabel("Ready")
        action_row.addWidget(self.status_label)
        action_row.addStretch()

        self.extract_button = QPushButton("Extract Images")
        self.extract_button.setProperty("class", "ks-primary")
        action_row.addWidget(self.extract_button)

        controls_layout.addLayout(action_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        controls_layout.addWidget(self.progress_bar)

        log_frame = QFrame()
        log_frame.setObjectName("panel")
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(20, 20, 20, 20)
        log_layout.setSpacing(12)

        log_label = QLabel("Activity Log")
        log_label.setObjectName("section")
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        mono_font = QFont("JetBrains Mono")
        mono_font.setPointSize(11)
        self.log_view.setFont(mono_font)
        self.log_view.setLineWrapMode(QTextEdit.NoWrap)

        log_layout.addWidget(log_label)
        log_layout.addWidget(self.log_view)

        layout.addWidget(header_frame)
        layout.addWidget(controls_frame)
        layout.addWidget(log_frame, stretch=1)

        footer = QLabel("Kalponic Studio Tools • Adaptive • Consistent • Accessible")
        footer.setObjectName("subtitle")
        footer.setAlignment(Qt.AlignCenter)
        footer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(footer)

    def _apply_palette(self) -> None:
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(KS_TOKENS["color.bg.base"]))
        palette.setColor(QPalette.Base, QColor(KS_TOKENS["color.bg.base"]))
        palette.setColor(QPalette.AlternateBase, QColor(KS_TOKENS["color.bg.panel"]))
        palette.setColor(QPalette.WindowText, QColor(KS_TOKENS["color.text.primary"]))
        palette.setColor(QPalette.Text, QColor(KS_TOKENS["color.text.primary"]))
        palette.setColor(QPalette.ButtonText, QColor(KS_TOKENS["color.text.primary"]))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def _wire_events(self) -> None:
        self.process_folder_cb.toggled.connect(self._on_mode_changed)
        self.source_browse.clicked.connect(self._browse_source)
        self.output_browse.clicked.connect(self._browse_output_dir)
        self.extract_button.clicked.connect(self._start_extraction)

    def _on_mode_changed(self, checked: bool) -> None:
        if checked:
            self.source_label.setText("Source Folder")
            self.source_edit.setPlaceholderText("Select a folder containing .zip archives…")
            self.include_subdirs_cb.setEnabled(True)
        else:
            self.source_label.setText("Zip File")
            self.source_edit.setPlaceholderText("Select a .zip archive to process…")
            self.include_subdirs_cb.setChecked(False)
            self.include_subdirs_cb.setEnabled(False)

    def _browse_source(self) -> None:
        if self.process_folder_cb.isChecked():
            directory = QFileDialog.getExistingDirectory(self, "Select Folder")
            if directory:
                self.source_edit.setText(directory)
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Zip Archive",
                "",
                "Zip Files (*.zip);;All Files (*)",
            )
            if file_path:
                self.source_edit.setText(file_path)

    def _browse_output_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_edit.setText(directory)

    def _start_extraction(self) -> None:
        if self._worker and self._worker.isRunning():
            QMessageBox.warning(self, "Extraction Running", "Please wait for the current extraction to finish.")
            return

        source_text = self.source_edit.text().strip()
        if not source_text:
            QMessageBox.warning(self, "Missing Source", "Please select a zip file or folder to process.")
            return

        source_path = Path(source_text).expanduser().resolve()
        if self.process_folder_cb.isChecked():
            if not source_path.is_dir():
                QMessageBox.warning(self, "Invalid Folder", "The selected source must be an existing directory.")
                return
            zip_paths = self._collect_folder_zips(source_path, self.include_subdirs_cb.isChecked())
            if not zip_paths:
                QMessageBox.information(self, "No Archives Found", "No .zip files were found in the selected folder.")
                return
        else:
            if not source_path.is_file() or source_path.suffix.lower() != ".zip":
                QMessageBox.warning(self, "Invalid Zip File", "Please choose a valid .zip file to extract.")
                return
            zip_paths = [source_path]

        output_text = self.output_edit.text().strip()
        output_dir = Path(output_text).expanduser().resolve() if output_text else None
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)

        self._set_ui_busy(True, len(zip_paths))
        self.log_view.clear()

        self._worker = ExtractionWorker(zip_paths, output_dir)
        self._worker.progress.connect(self._append_log)
        self._worker.failed.connect(self._append_error)
        self._worker.step_changed.connect(self._update_progress)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _collect_folder_zips(self, folder: Path, include_subdirs: bool) -> List[Path]:
        pattern = "**/*.zip" if include_subdirs else "*.zip"
        zip_iter = folder.rglob("*.zip") if include_subdirs else folder.glob("*.zip")
        return sorted(path.resolve() for path in zip_iter if path.is_file())

    def _append_log(self, message: str) -> None:
        self.log_view.append(message)
        self.log_view.ensureCursorVisible()
        self.status_label.setText(message)

    def _append_error(self, message: str) -> None:
        self.log_view.append(f"<span style='color:{KS_TOKENS['color.accent.error']}'>{message}</span>")
        self.status_label.setText(message)

    def _update_progress(self, index: int, total: int) -> None:
        if total == 0:
            self.progress_bar.setRange(0, 0)
            return
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(int((index / total) * 100))

    def _on_worker_finished(self, success: int, total: int) -> None:
        summary = f"Completed extraction • {success} of {total} archive(s) produced images."
        if success == 0:
            summary = f"No images extracted from {total} archive(s)."
        self._append_log(summary)
        self._set_ui_busy(False, total)

    def _set_ui_busy(self, busy: bool, total: int) -> None:
        self.extract_button.setEnabled(not busy)
        self.source_browse.setEnabled(not busy)
        self.output_browse.setEnabled(not busy)
        self.process_folder_cb.setEnabled(not busy)
        self.include_subdirs_cb.setEnabled(not busy and self.process_folder_cb.isChecked())
        self.progress_bar.setVisible(busy)
        if busy:
            self.progress_bar.setRange(0, 0 if total == 0 else 100)
            self.status_label.setText("Extracting images…")
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.status_label.setText("Ready")

    def closeEvent(self, event) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.wait(2000)
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)
    window = KSZipImageExtractor()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
