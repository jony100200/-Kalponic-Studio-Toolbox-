"""Maps abstract tasks to model families and search directives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from ..data import AppProfile


@dataclass(slots=True)
class TaskDirective:
    task: str
    preferred_formats: List[str]
    recommended_tags: List[str]
    notes: str


TASK_LIBRARY: Dict[str, TaskDirective] = {
    "object_detection": TaskDirective(
        task="object_detection",
        preferred_formats=["onnx", "fp16"],
        recommended_tags=["detector", "small"],
        notes="Focus on ONNX exports for easy deployment. YOLO family for speed.",
    ),
    "segmentation": TaskDirective(
        task="segmentation",
        preferred_formats=["onnx"],
        recommended_tags=["segmentation", "foreground"],
        notes="Prefer U^2-Net or MODNet derivatives for light footprint.",
    ),
    "captioning": TaskDirective(
        task="captioning",
        preferred_formats=["fp16", "int8"],
        recommended_tags=["caption", "multimodal"],
        notes="CLIP/BLIP-based captioning pipelines, choose small variant when possible.",
    ),
    "classification": TaskDirective(
        task="classification",
        preferred_formats=["onnx", "int8"],
        recommended_tags=["classifier"],
        notes="EfficientNet or MobileNet variants fit most hardware tiers.",
    ),
    "super_resolution": TaskDirective(
        task="super_resolution",
        preferred_formats=["onnx", "fp16"],
        recommended_tags=["sr", "upscale"],
        notes="Real-ESRGAN family provides good trade-off between quality and size.",
    ),
    "ocr": TaskDirective(
        task="ocr",
        preferred_formats=["onnx"],
        recommended_tags=["ocr"],
        notes="EasyOCR and PaddleOCR have lightweight ONNX exports.",
    ),
    "speech_to_text": TaskDirective(
        task="speech_to_text",
        preferred_formats=["int8", "onnx"],
        recommended_tags=["whisper", "asr"],
        notes="Whisper small/medium INT8 models for CPU-friendly inference.",
    ),
}


class TaskMapper:
    """Convert inferred tasks into actionable search directives."""

    def map(self, profile: AppProfile) -> List[TaskDirective]:
        directives: List[TaskDirective] = []
        for task in profile.tasks:
            directive = TASK_LIBRARY.get(task)
            if directive:
                directives.append(directive)
        if not directives:
            directives.append(TASK_LIBRARY["classification"])
        return directives
