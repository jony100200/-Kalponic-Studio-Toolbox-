"""Typer CLI entrypoint for KS AutoModel."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from ..core import (
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
from ..core.scoring import ScoringPreferences
from ..data import ModelRegistry
from ..providers import HuggingFaceProvider

app = typer.Typer(help="KS AutoModel - intelligent model recommendation engine.")


def _build_services(config_path: Path) -> tuple:
    config = ConfigManager(config_path)
    registry_root = Path(__file__).resolve().parents[4] / "data" / "registries" / "curated_models.json"
    registry = ModelRegistry(registry_paths=[registry_root])
    provider = HuggingFaceProvider(registry=registry, online_enabled=False)
    finder = ModelFinder(providers=[provider])
    prefs = ScoringPreferences(
        favor_quality=config.favor_quality,
        license_allow_list=tuple(config.get_license_preferences()),
    )
    scorer = ScoringEngine(prefs)
    return config, finder, scorer


@app.command()
def analyze(
    project: Optional[Path] = typer.Argument(None, help="Path to the target project directory."),
    favor_quality: bool = typer.Option(False, "--favor-quality", help="Prefer higher quality models."),
    download: bool = typer.Option(False, "--download", help="Download recommended models immediately."),
) -> None:
    """Analyse a project, recommend models, and optionally download them."""
    config_path = Path.home() / ".ks_automodel" / "config.json"
    config, finder, scorer = _build_services(config_path)
    if favor_quality != config.favor_quality:
        config.update(favor_quality=favor_quality)

    hardware = HardwareProfiler().detect()
    profile = AppProfiler().analyse(project or Path.cwd())
    directives = TaskMapper().map(profile)

    candidates_by_task = {}
    for directive in directives:
        filters = SearchFilters(
            task=directive.task,
            preferred_formats=directive.preferred_formats,
            license_allow_list=config.get_license_preferences(),
            limit=5,
            tags=directive.recommended_tags,
        )
        candidates = finder.search(filters)
        scored = scorer.score(hardware, profile, candidates)
        candidates_by_task[directive.task] = scored

    pipeline = PipelineComposer().compose(
        candidates_by_task=candidates_by_task,
        target_dir=config.download_dir,
        favor_quality=favor_quality,
    )

    typer.echo("Hardware Tier: " + hardware.tier)
    typer.echo("Detected Tasks: " + ", ".join(profile.tasks))
    typer.echo("Recommended pipeline:")
    for stage in pipeline.stages:
        typer.echo(
            f"  - {stage.task}: {stage.candidate.display_name} ({stage.candidate.format}, "
            f"{stage.candidate.size_mb:.1f}MB) score={stage.candidate.score}"
        )
    typer.echo(f"Estimated disk: {pipeline.estimated_disk_mb:.1f} MB | VRAM: {pipeline.estimated_vram_gb:.1f} GB")

    if download:
        typer.echo("Downloading models...")
        downloader = ModelDownloader()
        for result in downloader.download_pipeline(pipeline):
            typer.echo(f"  - Downloaded {result.candidate.display_name} -> {result.path}")
        typer.echo("Download complete.")


@app.command()
def hardware():
    """Display detected hardware information."""
    try:
        profiler = HardwareProfiler()
        hardware = profiler.detect()

        typer.echo("🖥️  Hardware Profile:")
        typer.echo(f"   CPU: {hardware.cpu_name}")
        typer.echo(f"   Cores: {hardware.cpu_cores}")
        typer.echo(f"   RAM: {hardware.ram_gb:.1f} GB")
        if hardware.gpu_name:
            typer.echo(f"   GPU: {hardware.gpu_vendor} {hardware.gpu_name}")
            typer.echo(f"   VRAM: {hardware.vram_gb:.1f} GB")
        typer.echo(f"   OS: {hardware.os_name}")
        typer.echo(f"   Tier: {hardware.tier}")
        if hardware.notes:
            typer.echo(f"   Notes: {', '.join(hardware.notes)}")

    except Exception as e:
        typer.echo(f"❌ Error detecting hardware: {e}", err=True)
        raise typer.Exit(1)
