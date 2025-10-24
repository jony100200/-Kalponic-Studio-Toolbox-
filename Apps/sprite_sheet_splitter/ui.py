"""
Kalponic Studio Sprite Sheet Splitter UI

PySide6 interface that implements the KS Universal UI System blueprint.
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
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QCheckBox,
)

try:
    from .main import IMAGE_EXTENSIONS, iter_sprite_sheets, split_sprite_sheet
except ImportError:  # pragma: no cover - direct script execution
    from main import IMAGE_EXTENSIONS, iter_sprite_sheets, split_sprite_sheet


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
QSpinBox {{
    background-color: {KS_TOKENS["color.bg.base"]};
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 6px 8px;
}}
QSpinBox:focus {{
    border: 1px solid {KS_TOKENS["color.accent.primary"]};
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


class SpriteSplitWorker(QThread):
    """Background worker for sprite sheet splitting."""

    progress = Signal(str)
    failed = Signal(str)
    step_changed = Signal(int, int)
    finished = Signal(int, int, int)

    def __init__(self, sprite_paths: Iterable[Path], output_dir: Path, rows: int, cols: int):
        super().__init__()
        self._sprite_paths = list(sprite_paths)
        self._output_dir = output_dir
        self._rows = rows
        self._cols = cols

    def run(self) -> None:  # type: ignore[override]
        total = len(self._sprite_paths)
        success = 0
        frames_total = 0

        for index, sprite_path in enumerate(self._sprite_paths, start=1):
            if self.isInterruptionRequested():
                break

            self.progress.emit(f"Processing '{sprite_path.name}'")
            try:
                frames = split_sprite_sheet(
                    sprite_path,
                    self._output_dir,
                    self._rows,
                    self._cols,
                    reporter=self.progress.emit,
                )
                if frames:
                    success += 1
                    frames_total += len(frames)
            except Exception as exc:  # pragma: no cover - defensive path
                self.failed.emit(f"Unexpected error on '{sprite_path.name}': {exc}")

            self.step_changed.emit(index, total)

        self.finished.emit(success, total, frames_total)


class KSSpriteSheetSplitter(QWidget):
    """Primary KS UI surface."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("KS Sprite Sheet Splitter")
        self.resize(880, 640)

        self._worker: Optional[SpriteSplitWorker] = None

        self._build_ui()
        self._apply_palette()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QFrame()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        title = QLabel("KS Sprite Sheet Splitter")
        title.setObjectName("title")
        subtitle = QLabel("Slice sprite grids into production-ready frames with Kalponic Studio styling.")
        subtitle.setObjectName("subtitle")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        controls_frame = QFrame()
        controls_frame.setObjectName("panel")
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(20, 20, 20, 20)
        controls_layout.setSpacing(18)

        section_label = QLabel("Source & Layout")
        section_label.setObjectName("section")
        controls_layout.addWidget(section_label)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(14)

        self.source_label = QLabel("Sprite Sheet")
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("Select a sprite sheet image…")
        self.source_browse = QPushButton("Browse…")
        grid.addWidget(self.source_label, 0, 0)
        grid.addWidget(self.source_edit, 0, 1)
        grid.addWidget(self.source_browse, 0, 2)

        self.process_folder_cb = QCheckBox("Process entire folder")
        self.include_subdirs_cb = QCheckBox("Include sub-folders")
        self.include_subdirs_cb.setEnabled(False)
        grid.addWidget(self.process_folder_cb, 1, 1)
        grid.addWidget(self.include_subdirs_cb, 1, 2)

        output_label = QLabel("Output Directory")
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Defaults to the source location if empty.")
        self.output_browse = QPushButton("Browse…")
        grid.addWidget(output_label, 2, 0)
        grid.addWidget(self.output_edit, 2, 1)
        grid.addWidget(self.output_browse, 2, 2)

        rows_label = QLabel("Rows")
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 1000)
        self.rows_spin.setValue(4)
        cols_label = QLabel("Columns")
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 1000)
        self.cols_spin.setValue(4)

        grid.addWidget(rows_label, 3, 0)
        grid.addWidget(self.rows_spin, 3, 1)
        grid.addWidget(cols_label, 4, 0)
        grid.addWidget(self.cols_spin, 4, 1)

        controls_layout.addLayout(grid)

        action_row = QHBoxLayout()
        action_row.setSpacing(12)
        self.status_label = QLabel("Ready")
        action_row.addWidget(self.status_label)
        action_row.addStretch()

        self.split_button = QPushButton("Split Frames")
        self.split_button.setProperty("class", "ks-primary")
        action_row.addWidget(self.split_button)

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

        layout.addWidget(header)
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

    def _connect_signals(self) -> None:
        self.source_browse.clicked.connect(self._browse_source)
        self.output_browse.clicked.connect(self._browse_output)
        self.split_button.clicked.connect(self._start_split)
        self.process_folder_cb.toggled.connect(self._toggle_folder_mode)

    def _toggle_folder_mode(self, checked: bool) -> None:
        if checked:
            self.source_label.setText("Source Folder")
            self.source_edit.setPlaceholderText("Select a folder containing sprite sheets…")
            self.include_subdirs_cb.setEnabled(True)
        else:
            self.source_label.setText("Sprite Sheet")
            self.source_edit.setPlaceholderText("Select a sprite sheet image…")
            self.include_subdirs_cb.setChecked(False)
            self.include_subdirs_cb.setEnabled(False)

    def _browse_source(self) -> None:
        if self.process_folder_cb.isChecked():
            directory = QFileDialog.getExistingDirectory(self, "Select Source Folder")
            if directory:
                self.source_edit.setText(directory)
        else:
            filter_mask = "Image Files (" + " ".join(f"*{ext}" for ext in sorted(IMAGE_EXTENSIONS)) + ");;All Files (*)"
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Sprite Sheet", "", filter_mask)
            if file_path:
                self.source_edit.setText(file_path)

    def _browse_output(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if directory:
            self.output_edit.setText(directory)

    def _start_split(self) -> None:
        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "Processing", "Sprite splitting is already running.")
            return

        source_text = self.source_edit.text().strip()
        if not source_text:
            QMessageBox.warning(self, "Missing Source", "Please select a sprite sheet or folder to process.")
            return

        rows = self.rows_spin.value()
        cols = self.cols_spin.value()

        source_path = Path(source_text).expanduser().resolve()
        sprite_paths: List[Path]
        if self.process_folder_cb.isChecked():
            if not source_path.is_dir():
                QMessageBox.warning(self, "Invalid Folder", "Source must be an existing folder.")
                return
            sprite_paths = self._collect_from_folder(source_path, self.include_subdirs_cb.isChecked())
            if not sprite_paths:
                QMessageBox.information(self, "No Images Found", "No sprite sheet images were located in the folder.")
                return
        else:
            if not source_path.is_file() or source_path.suffix.lower() not in IMAGE_EXTENSIONS:
                QMessageBox.warning(self, "Invalid Sprite Sheet", "Please choose a valid sprite sheet image.")
                return
            sprite_paths = [source_path]

        output_text = self.output_edit.text().strip()
        if output_text:
            output_dir = Path(output_text).expanduser().resolve()
        else:
            output_dir = source_path.parent if not self.process_folder_cb.isChecked() else source_path
        output_dir.mkdir(parents=True, exist_ok=True)

        self._set_busy(True, len(sprite_paths))
        self.log_view.clear()

        self._worker = SpriteSplitWorker(sprite_paths, output_dir, rows, cols)
        self._worker.progress.connect(self._log_info)
        self._worker.failed.connect(self._log_error)
        self._worker.step_changed.connect(self._did_step)
        self._worker.finished.connect(self._worker_finished)
        self._worker.start()

    def _collect_from_folder(self, folder: Path, recursive: bool) -> List[Path]:
        iterator = folder.rglob("*") if recursive else folder.iterdir()
        collected: List[Path] = []
        for path in iterator:
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                collected.append(path.resolve())
        collected.sort()
        return collected

    def _set_busy(self, busy: bool, total: int) -> None:
        self.split_button.setEnabled(not busy)
        self.source_browse.setEnabled(not busy)
        self.output_browse.setEnabled(not busy)
        self.process_folder_cb.setEnabled(not busy)
        self.include_subdirs_cb.setEnabled(not busy and self.process_folder_cb.isChecked())
        self.rows_spin.setEnabled(not busy)
        self.cols_spin.setEnabled(not busy)
        self.progress_bar.setVisible(busy)

        if busy:
            self.status_label.setText("Splitting sprite sheets…")
            self.progress_bar.setRange(0, 0 if total == 0 else 100)
        else:
            self.status_label.setText("Ready")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

    def _log_info(self, message: str) -> None:
        self.log_view.append(message)
        self.log_view.ensureCursorVisible()
        self.status_label.setText(message)

    def _log_error(self, message: str) -> None:
        self.log_view.append(f"<span style='color:{KS_TOKENS['color.accent.error']}'>{message}</span>")
        self.status_label.setText(message)

    def _did_step(self, index: int, total: int) -> None:
        if total == 0:
            self.progress_bar.setRange(0, 0)
            return
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(int((index / total) * 100))

    def _worker_finished(self, success: int, total: int, frames_total: int) -> None:
        summary = f"Completed • {success}/{total} sprite sheet(s) produced {frames_total} frame(s)."
        if success == 0:
            summary = f"No frames generated from {total} sprite sheet(s)."
        self._log_info(summary)
        self._set_busy(False, total)

    def closeEvent(self, event) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.wait(2000)
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)
    window = KSSpriteSheetSplitter()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
