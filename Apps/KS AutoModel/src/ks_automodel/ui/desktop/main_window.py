"""PySide6 desktop UI for KS AutoModel aligned with KS design language."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QRadioButton,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...core import (
    AppProfiler,
    ConfigManager,
    HardwareProfiler,
    ModelDownloader,
    ModelFinder,
    PipelineComposer,
    ScoringEngine,
    SearchFilters,
    TaskMapper,
)
from ...core.pipeline import PipelineConfig
from ...core.scoring import ScoringPreferences
from ...core.utils import setup_logging
from ...data import AppProfile, HardwareInfo, ModelCandidate, ModelRegistry
from ...providers import HuggingFaceProvider
from ..theme import KS_TOKENS, build_qss

logger = setup_logging()


@dataclass
class AnalysisRecord:
    project: Path
    hardware_tier: str
    tasks: List[str]
    pipeline_id: str


class MainWindow(QMainWindow):
    """Main PySide window following the KS UI blueprint."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("KS AutoModel – Intelligent Model Finder")
        self.resize(1200, 760)

        self.config_path = Path.home() / ".ks_automodel" / "config.json"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self.config = ConfigManager(self.config_path)
        registry_path = Path(__file__).resolve().parents[4] / "data" / "registries" / "curated_models.json"
        self.registry = ModelRegistry(registry_paths=[registry_path])
        self.provider = HuggingFaceProvider(registry=self.registry, online_enabled=False)
        self.finder = ModelFinder([self.provider])
        self.scorer = ScoringEngine(
            ScoringPreferences(
                favor_quality=self.config.favor_quality,
                license_allow_list=tuple(self.config.get_license_preferences()),
            )
        )
        self.composer = PipelineComposer()

        self.hardware: Optional[HardwareInfo] = None
        self.profile: Optional[AppProfile] = None
        self.candidates_by_task: Dict[str, List[ModelCandidate]] = {}
        self.pipeline: Optional[PipelineConfig] = None
        self.history: List[AnalysisRecord] = []

        self._build_ui()
        self.setStyleSheet(build_qss())

    # ------------------------------------------------------------------ UI builders

    def _build_ui(self) -> None:
        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(KS_TOKENS["spacing.unit"] * 2)

        header = QLabel("KS AutoModel")
        header.setObjectName("Heading")
        sub = QLabel("Analyze any project, detect ML needs, and assemble optimized model pipelines.")
        sub.setObjectName("SubHeading")
        layout.addWidget(header)
        layout.addWidget(sub)

        self.tabs = QTabWidget()
        self.tabs.setTabBarAutoHide(False)
        layout.addWidget(self.tabs, 1)

        self.tabs.addTab(self._build_home_tab(), "Home")
        self.tabs.addTab(self._build_results_tab(), "Results")
        self.tabs.addTab(self._build_pipeline_tab(), "Pipeline")
        self.tabs.addTab(self._build_download_tab(), "Download")
        self.tabs.addTab(self._build_history_tab(), "History")

        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)
        self.tabs.setTabEnabled(3, False)

        self.setCentralWidget(central)

    # --- Home tab -----------------------------------------------------

    def _build_home_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(KS_TOKENS["spacing.unit"] * 2)

        primary_panel = self._panel()
        grid = QGridLayout(primary_panel)
        grid.setHorizontalSpacing(KS_TOKENS["spacing.unit"] * 2)
        grid.setVerticalSpacing(KS_TOKENS["spacing.unit"] * 1)

        self.project_path_edit = QLineEdit(str(Path.cwd()))
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._choose_project)
        self.analyze_btn = QPushButton("Analyze Application")
        self.analyze_btn.setObjectName("PrimaryButton")
        self.analyze_btn.clicked.connect(self._analyze_project)

        self.hardware_label = QLabel("Hardware tier: —")
        self.hardware_label.setObjectName("SubHeading")
        self.hardware_details = QLabel("Run analysis to detect hardware profile.")
        self.hardware_details.setWordWrap(True)

        grid.addWidget(QLabel("Project Path"), 0, 0)
        grid.addWidget(self.project_path_edit, 0, 1)
        grid.addWidget(browse, 0, 2)
        grid.addWidget(self.analyze_btn, 1, 0, 1, 3)
        grid.addWidget(self.hardware_label, 2, 0, 1, 3)
        grid.addWidget(self.hardware_details, 3, 0, 1, 3)
        layout.addWidget(primary_panel)

        prefs_panel = self._panel()
        prefs_layout = QVBoxLayout(prefs_panel)
        prefs_layout.setSpacing(KS_TOKENS["spacing.unit"])
        prefs_layout.addWidget(self._build_preferences_group())
        layout.addWidget(prefs_panel)

        summary_panel = self._panel()
        summary_layout = QVBoxLayout(summary_panel)
        summary_layout.addWidget(QLabel("Analysis Summary"))
        self.summary_card = QTextEdit()
        self.summary_card.setReadOnly(True)
        self.summary_card.setPlaceholderText("Run an analysis to see detected tasks and hints.")
        summary_layout.addWidget(self.summary_card)
        layout.addWidget(summary_panel, 1)

        return tab

    def _build_preferences_group(self) -> QGroupBox:
        group = QGroupBox("Preferences")
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(KS_TOKENS["spacing.unit"] * 2)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Auto", "Dark", "Light"])
        self.theme_combo.setCurrentIndex(0)

        self.favor_small_radio = QRadioButton("Favor smaller models")
        self.favor_quality_radio = QRadioButton("Favor quality")
        if self.config.favor_quality:
            self.favor_quality_radio.setChecked(True)
        else:
            self.favor_small_radio.setChecked(True)

        self.license_edit = QLineEdit(", ".join(self.config.get_license_preferences()))
        self.max_size_edit = QLineEdit("500")

        layout.addWidget(QLabel("Theme"), 0, 0)
        layout.addWidget(self.theme_combo, 0, 1)
        layout.addWidget(self.favor_small_radio, 1, 0, 1, 2)
        layout.addWidget(self.favor_quality_radio, 2, 0, 1, 2)
        layout.addWidget(QLabel("Preferred licenses (comma separated)"), 3, 0, 1, 2)
        layout.addWidget(self.license_edit, 4, 0, 1, 2)
        layout.addWidget(QLabel("Maximum model size (MB)"), 5, 0, 1, 2)
        layout.addWidget(self.max_size_edit, 6, 0, 1, 2)

        return group

    # --- Results tab --------------------------------------------------

    def _build_results_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(KS_TOKENS["spacing.unit"] * 2)

        header = QLabel("Task Recommendations")
        header.setObjectName("SubHeading")
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        wrapper = QWidget()
        self.results_layout = QVBoxLayout(wrapper)
        self.results_layout.setSpacing(KS_TOKENS["spacing.unit"] * 2)
        scroll.setWidget(wrapper)
        layout.addWidget(scroll, 1)

        return tab

    # --- Pipeline tab -------------------------------------------------

    def _build_pipeline_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(KS_TOKENS["spacing.unit"] * 2)

        toggle_panel = self._panel()
        toggle_layout = QHBoxLayout(toggle_panel)
        toggle_layout.addWidget(QLabel("Pipeline preference:"))
        self.pipeline_small_radio = QRadioButton("Favor smaller models")
        self.pipeline_quality_radio = QRadioButton("Favor quality")
        if self.config.favor_quality:
            self.pipeline_quality_radio.setChecked(True)
        else:
            self.pipeline_small_radio.setChecked(True)
        self.pipeline_small_radio.toggled.connect(self._recompose_pipeline)
        self.pipeline_quality_radio.toggled.connect(self._recompose_pipeline)
        toggle_layout.addWidget(self.pipeline_small_radio)
        toggle_layout.addWidget(self.pipeline_quality_radio)
        toggle_layout.addStretch()
        layout.addWidget(toggle_panel)

        summary_panel = self._panel()
        summary_layout = QVBoxLayout(summary_panel)
        summary_layout.setSpacing(KS_TOKENS["spacing.unit"])

        self.pipeline_metrics = QLabel("Pipeline metrics will appear here after analysis.")
        self.pipeline_metrics.setWordWrap(True)
        summary_layout.addWidget(self.pipeline_metrics)

        self.pipeline_chain = QListWidget()
        summary_layout.addWidget(self.pipeline_chain)

        self.pipeline_notes = QTextEdit()
        self.pipeline_notes.setReadOnly(True)
        summary_layout.addWidget(self.pipeline_notes)

        layout.addWidget(summary_panel, 1)
        return tab

    # --- Download tab -------------------------------------------------

    def _build_download_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(KS_TOKENS["spacing.unit"] * 2)

        panel = self._panel()
        grid = QGridLayout(panel)
        grid.setHorizontalSpacing(KS_TOKENS["spacing.unit"] * 2)
        grid.setVerticalSpacing(KS_TOKENS["spacing.unit"])

        self.download_summary = QTextEdit()
        self.download_summary.setReadOnly(True)
        self.download_summary.setPlaceholderText("Generate a pipeline to review the summary.")

        self.target_dir_edit = QLineEdit(str(self.config.download_dir))
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._choose_download_dir)

        self.write_config_checkbox = QCheckBox("Write project config (.ks/automodel.yml)")
        self.write_config_checkbox.setChecked(True)

        self.download_btn = QPushButton("Download Pipeline (simulated)")
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self._download_pipeline)

        self.download_progress = QProgressBar()
        self.download_status = QLabel("Status: idle")

        grid.addWidget(QLabel("Summary"), 0, 0, 1, 3)
        grid.addWidget(self.download_summary, 1, 0, 1, 3)
        grid.addWidget(QLabel("Target directory"), 2, 0)
        grid.addWidget(self.target_dir_edit, 2, 1)
        grid.addWidget(browse, 2, 2)
        grid.addWidget(self.write_config_checkbox, 3, 0, 1, 3)
        grid.addWidget(self.download_btn, 4, 0, 1, 3)
        grid.addWidget(self.download_progress, 5, 0, 1, 3)
        grid.addWidget(self.download_status, 6, 0, 1, 3)

        layout.addWidget(panel)
        return tab

    # --- History tab --------------------------------------------------

    def _build_history_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(KS_TOKENS["spacing.unit"])

        self.history_list = QListWidget()
        self.history_list.setSelectionMode(QListWidget.NoSelection)
        layout.addWidget(self.history_list, 1)

        note = QLabel("History is session-based. Future versions will persist recent analyses.")
        note.setWordWrap(True)
        layout.addWidget(note)
        return tab

    # ------------------------------------------------------------------ Actions

    def _choose_project(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select project directory", self.project_path_edit.text())
        if directory:
            self.project_path_edit.setText(directory)

    def _collect_preferences(self) -> None:
        favor_quality = self.favor_quality_radio.isChecked() or self.pipeline_quality_radio.isChecked()
        licenses = [part.strip() for part in self.license_edit.text().split(",") if part.strip()]
        self.config.update(
            favor_quality=favor_quality,
            license_preferences=licenses or self.config.get_license_preferences(),
        )
        self.scorer.prefs.favor_quality = favor_quality
        self.scorer.prefs.license_allow_list = tuple(licenses)
        try:
            self.scorer.prefs.max_size_mb = float(self.max_size_edit.text() or 500)
        except ValueError:
            self.scorer.prefs.max_size_mb = 500.0

    def _analyze_project(self) -> None:
        project_path = Path(self.project_path_edit.text()).expanduser()
        if not project_path.exists():
            QMessageBox.warning(self, "Invalid Path", "The selected project directory does not exist.")
            return

        self._collect_preferences()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.hardware = HardwareProfiler().detect()
            self.profile = AppProfiler().analyse(project_path)
            directives = TaskMapper().map(self.profile)
            self.candidates_by_task = {}

            for directive in directives:
                filters = SearchFilters(
                    task=directive.task,
                    preferred_formats=directive.preferred_formats,
                    license_allow_list=self.config.get_license_preferences(),
                    tags=directive.recommended_tags,
                    limit=6,
                )
                candidates = self.finder.search(filters)
                scored = self.scorer.score(self.hardware, self.profile, candidates)
                self.candidates_by_task[directive.task] = scored

            self.pipeline = self.composer.compose(
                candidates_by_task=self.candidates_by_task,
                target_dir=self.config.download_dir,
                favor_quality=self.config.favor_quality,
            )

        except Exception as exc:
            logger.exception("Analysis failed")
            QMessageBox.critical(self, "Analysis Error", str(exc))
            return
        finally:
            QApplication.restoreOverrideCursor()

        self._update_home_summary()
        self._populate_results_tab()
        self._populate_pipeline_tab()
        self._populate_download_tab()
        self._append_history(project_path)

        self.tabs.setTabEnabled(1, True)
        self.tabs.setTabEnabled(2, True)
        self.tabs.setTabEnabled(3, True)
        self.tabs.setCurrentIndex(1)

    def _update_home_summary(self) -> None:
        if not (self.hardware and self.profile):
            return
        self.hardware_label.setText(f"Hardware tier: {self.hardware.tier}")
        gpu_info = self.hardware.gpu_name or "None"
        self.hardware_details.setText(
            f"CPU: {self.hardware.cpu_name} ({self.hardware.cpu_cores} cores) • "
            f"RAM: {self.hardware.ram_gb:.1f} GB • GPU: {gpu_info}"
        )
        summary_lines = [
            f"Project: {self.profile.project_path}",
            f"Tasks: {', '.join(self.profile.tasks)}",
            f"Summary: {self.profile.summary}",
            "",
            "Hints:",
        ]
        for key, value in self.profile.hints.items():
            summary_lines.append(f"- {key}: {value}")
        self.summary_card.setPlainText("\n".join(summary_lines))

    def _populate_results_tab(self) -> None:
        # Clear existing cards
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not self.candidates_by_task:
            placeholder = QLabel("No candidates found for the detected tasks.")
            placeholder.setWordWrap(True)
            self.results_layout.addWidget(placeholder)
            return

        for task, candidates in self.candidates_by_task.items():
            card = self._panel()
            card_layout = QVBoxLayout(card)
            title = QLabel(task.replace("_", " ").title())
            title.setObjectName("SubHeading")
            card_layout.addWidget(title)

            top_candidates = candidates[:3] if candidates else []
            if not top_candidates:
                card_layout.addWidget(QLabel("No models available for this task."))
            else:
                for candidate in top_candidates:
                    detail = QLabel(
                        f"{candidate.display_name} • {candidate.format.upper()} • "
                        f"{candidate.size_mb:.1f} MB • score {candidate.score:.1f}"
                    )
                    detail.setWordWrap(True)
                    card_layout.addWidget(detail)
                    bullet = QLabel(
                        f"↳ VRAM est.: {self._estimate_vram(candidate):.1f} GB • "
                        f"Quantization: {candidate.quantization or 'n/a'} • "
                        f"License: {candidate.license}"
                    )
                    bullet.setWordWrap(True)
                    card_layout.addWidget(bullet)
            self.results_layout.addWidget(card)

        self.results_layout.addStretch()

    def _populate_pipeline_tab(self) -> None:
        if not self.pipeline:
            return
        self.pipeline_chain.clear()
        for stage in self.pipeline.stages:
            item = QListWidgetItem(
                f"{stage.task}: {stage.candidate.display_name} ({stage.candidate.format}, "
                f"{stage.candidate.size_mb:.1f} MB)"
            )
            self.pipeline_chain.addItem(item)

        self.pipeline_metrics.setText(
            f"Pipeline ID: {self.pipeline.pipeline_id} • Models: {self.pipeline.total_models}\n"
            f"Estimated disk: {self.pipeline.estimated_disk_mb:.1f} MB | "
            f"VRAM: {self.pipeline.estimated_vram_gb:.1f} GB | "
            f"Latency: {self.pipeline.estimated_latency_ms:.1f} ms"
        )
        self.pipeline_notes.setPlainText("\n".join(self.pipeline.notes))
        self.pipeline_small_radio.setChecked(not self.pipeline.favor_quality)
        self.pipeline_quality_radio.setChecked(self.pipeline.favor_quality)

    def _populate_download_tab(self) -> None:
        if not self.pipeline:
            return
        summary_lines = [
            f"Pipeline ID: {self.pipeline.pipeline_id}",
            f"Tasks: {', '.join(self.pipeline.tasks)}",
            f"Total models: {self.pipeline.total_models}",
            f"Estimated disk: {self.pipeline.estimated_disk_mb:.1f} MB",
            f"Estimated VRAM: {self.pipeline.estimated_vram_gb:.1f} GB",
            "",
            "Stages:",
        ]
        for stage in self.pipeline.stages:
            summary_lines.append(
                f"- {stage.task}: {stage.candidate.display_name} "
                f"({stage.candidate.format.upper()}, {stage.candidate.size_mb:.1f} MB)"
            )
        self.download_summary.setPlainText("\n".join(summary_lines))
        self.download_btn.setEnabled(True)
        self.download_progress.setValue(0)
        self.download_status.setText("Status: ready")

    def _append_history(self, project_path: Path) -> None:
        if not (self.pipeline and self.hardware and self.profile):
            return
        record = AnalysisRecord(
            project=project_path,
            hardware_tier=self.hardware.tier,
            tasks=self.profile.tasks,
            pipeline_id=self.pipeline.pipeline_id,
        )
        self.history.append(record)
        item = QListWidgetItem(
            f"{project_path} | tier {record.hardware_tier} | tasks {', '.join(record.tasks)} "
            f"| pipeline {record.pipeline_id}"
        )
        self.history_list.addItem(item)

    def _choose_download_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select download directory", self.target_dir_edit.text())
        if directory:
            self.target_dir_edit.setText(directory)

    def _download_pipeline(self) -> None:
        if not self.pipeline:
            return
        self.download_btn.setEnabled(False)
        self.download_status.setText("Status: downloading…")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            pipeline = PipelineConfig(
                pipeline_id=self.pipeline.pipeline_id,
                stages=self.pipeline.stages,
                estimated_disk_mb=self.pipeline.estimated_disk_mb,
                estimated_vram_gb=self.pipeline.estimated_vram_gb,
                estimated_latency_ms=self.pipeline.estimated_latency_ms,
                favor_quality=self.pipeline.favor_quality,
                target_dir=Path(self.target_dir_edit.text()).expanduser(),
                notes=self.pipeline.notes,
            )
            downloader = ModelDownloader(simulate=True)
            total = len(pipeline.stages)
            for index, _result in enumerate(downloader.download_pipeline(pipeline), start=1):
                self.download_progress.setValue(int(index / max(total, 1) * 100))
            self.download_status.setText(f"Status: completed (saved to {pipeline.target_dir})")
            if self.write_config_checkbox.isChecked():
                self._write_project_config(pipeline)
        except Exception as exc:
            logger.exception("Download failed")
            QMessageBox.critical(self, "Download Error", str(exc))
            self.download_status.setText("Status: failed")
        finally:
            QApplication.restoreOverrideCursor()
            self.download_btn.setEnabled(True)

    def _write_project_config(self, pipeline: PipelineConfig) -> None:
        project_root = self.profile.project_path if self.profile else Path.cwd()
        config_dir = project_root / ".ks"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "automodel.yml"
        lines = [
            f"pipeline_id: {pipeline.pipeline_id}",
            f"target_dir: {pipeline.target_dir}",
            "tasks:",
        ] + [f"  - {task}" for task in pipeline.tasks]
        config_file.write_text("\n".join(lines), encoding="utf-8")
        self.download_status.setText(f"Status: completed (config written to {config_file})")

    def _recompose_pipeline(self) -> None:
        if not self.candidates_by_task:
            return
        favor_quality = self.pipeline_quality_radio.isChecked()
        self.pipeline = self.composer.compose(
            candidates_by_task=self.candidates_by_task,
            target_dir=Path(self.target_dir_edit.text()).expanduser(),
            favor_quality=favor_quality,
        )
        self._populate_pipeline_tab()
        self._populate_download_tab()

    # ------------------------------------------------------------------

    def _panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        return panel

    def _estimate_vram(self, candidate: ModelCandidate) -> float:
        baseline = 1.0 if candidate.format.lower() in {"onnx", "int8"} else 1.5
        if candidate.quantization and candidate.quantization.lower() == "fp16":
            baseline *= 0.6
        if candidate.quantization and candidate.quantization.lower() == "int8":
            baseline *= 0.4
        return max(0.5, baseline)


def create_main_window() -> MainWindow:
    return MainWindow()
