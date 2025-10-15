"""Application profiling to infer ML tasks from a project directory."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Set

from ..data import AppProfile
from .utils import resolve_project_path, setup_logging

logger = setup_logging()

PYTHON_IMPORT_PATTERNS = {
    "segmentation": {"semantic", "segmentation", "u2net", "deeplab", "mask"},
    "object_detection": {"yolo", "detectron", "detr", "mmdet"},
    "captioning": {"clip", "blip", "caption", "lavis"},
    "super_resolution": {"realesrgan", "srgan", "esrgan"},
    "classification": {"resnet", "efficientnet", "classifier"},
    "ocr": {"ocr", "easyocr", "tesseract"},
    "speech_to_text": {"whisper", "asr"},
}

README_HINTS = {
    "image": {"image", "picture", "photo"},
    "video": {"video", "clip"},
    "text": {"text", "document"},
    "audio": {"audio", "voice"},
}


class AppProfiler:
    """Analyse project metadata to infer tasks and hints."""

    def __init__(self, max_files: int = 200) -> None:
        self.max_files = max_files

    def analyse(self, path: str | Path) -> AppProfile:
        project_path = resolve_project_path(str(path))
        python_imports = self._scan_python_imports(project_path)
        readme_summary, readme_hints = self._scan_readme(project_path)

        tasks = self._infer_tasks(python_imports, readme_summary)
        hints = {"imports": sorted(python_imports), **readme_hints}
        summary = readme_summary or f"Inferred tasks: {', '.join(tasks) or 'unknown'}"

        logger.info("Analysed %s tasks=%s", project_path, tasks)
        return AppProfile(project_path=project_path, summary=summary, tasks=tasks, hints=hints)

    # Internal helpers -------------------------------------------------

    def _scan_python_imports(self, project_path: Path) -> Set[str]:
        imports: Set[str] = set()
        python_files = list(project_path.rglob("*.py"))[: self.max_files]
        for file_path in python_files:
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for match in re.finditer(r"^\s*(?:import|from)\s+([\w\.]+)", text, re.MULTILINE):
                root = match.group(1).split(".")[0].lower()
                imports.add(root)
        return imports

    def _scan_readme(self, project_path: Path) -> tuple[str, Dict[str, Iterable[str]]]:
        readme = next((p for p in project_path.glob("README*") if p.is_file()), None)
        if not readme:
            return "", {}
        text = readme.read_text(encoding="utf-8", errors="ignore").lower()
        summary = text.splitlines()[0].strip() if text else ""
        hints: Dict[str, List[str]] = {}
        for key, keywords in README_HINTS.items():
            hits = [word for word in keywords if word in text]
            if hits:
                hints[key] = hits
        return summary, hints

    def _infer_tasks(self, imports: Set[str], summary: str) -> List[str]:
        tasks: Set[str] = set()
        lower_summary = summary.lower()
        for task, keywords in PYTHON_IMPORT_PATTERNS.items():
            if any(keyword in imports for keyword in keywords):
                tasks.add(task)
        if "detection" in lower_summary:
            tasks.add("object_detection")
        if "caption" in lower_summary:
            tasks.add("captioning")
        if "segment" in lower_summary or "matting" in lower_summary:
            tasks.add("segmentation")
        if not tasks:
            tasks.add("classification")
        return sorted(tasks)
