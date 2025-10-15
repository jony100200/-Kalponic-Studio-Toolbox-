"""
Context.json Metadata Generator for KS MetaMaker
Creates comprehensive metadata files for processed images
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from PIL import Image
import numpy as np

from .tag_normalizer import NormalizedTag


@dataclass
class ProcessingStep:
    """Represents a single processing step"""
    step_name: str
    timestamp: str
    duration_ms: float
    success: bool
    details: Dict[str, Any]


@dataclass
class TagMetadata:
    """Metadata for a single tag"""
    tag: str
    confidence: float
    category: str
    source: str  # 'openclip', 'yolo', 'blip', 'quality', etc.
    normalized_from: Optional[str] = None
    is_synonym: bool = False


@dataclass
class ImageMetadata:
    """Comprehensive metadata for a processed image"""
    filename: str
    original_path: str
    processed_path: str
    file_hash: str
    processing_timestamp: str
    profile_used: str

    # Image properties
    dimensions: tuple
    file_size_bytes: int
    image_format: str
    color_mode: str

    # Processing results
    tags: List[TagMetadata]
    category: str
    quality_score: float

    # Processing history
    processing_steps: List[ProcessingStep]
    total_processing_time_ms: float

    # Model information
    models_used: List[str]
    hardware_profile: str

    # Additional metadata
    custom_fields: Dict[str, Any]


class ContextMetadataGenerator:
    """Generates context.json metadata files for processed images"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.metadata_dir = output_dir / "metadata"
        self.metadata_dir.mkdir(exist_ok=True)

    def generate_context_metadata(
        self,
        image_path: Path,
        processed_path: Path,
        tags: List[str],
        normalized_tags: Optional[List[NormalizedTag]] = None,
        processing_history: Optional[List[ProcessingStep]] = None,
        profile_name: str = "default",
        hardware_profile: str = "unknown",
        models_used: Optional[List[str]] = None
    ) -> Path:
        """
        Generate comprehensive context.json metadata for an image

        Args:
            image_path: Original image path
            processed_path: Processed/final image path
            tags: Final list of tags applied
            normalized_tags: Normalized tag objects with metadata
            processing_history: List of processing steps
            profile_name: Name of the profile used
            hardware_profile: Hardware profile used
            models_used: List of AI models used

        Returns:
            Path to the generated metadata file
        """
        # Calculate file hash
        file_hash = self._calculate_file_hash(image_path)

        # Get image properties
        image_props = self._get_image_properties(image_path)

        # Convert tags to TagMetadata
        tag_metadata = self._convert_tags_to_metadata(
            tags, normalized_tags, processing_history
        )

        # Determine category
        category = self._determine_category(tag_metadata)

        # Calculate quality score
        quality_score = self._calculate_quality_score(image_props, tag_metadata)

        # Create processing history if not provided
        if processing_history is None:
            processing_history = [ProcessingStep(
                step_name="basic_processing",
                timestamp=datetime.now().isoformat(),
                duration_ms=1000.0,  # Placeholder
                success=True,
                details={"tags_generated": len(tags)}
            )]

        # Calculate total processing time
        total_time = sum(step.duration_ms for step in processing_history)

        # Create metadata object
        metadata = ImageMetadata(
            filename=processed_path.name,
            original_path=str(image_path),
            processed_path=str(processed_path),
            file_hash=file_hash,
            processing_timestamp=datetime.now().isoformat(),
            profile_used=profile_name,
            dimensions=image_props['dimensions'],
            file_size_bytes=image_props['file_size'],
            image_format=image_props['format'],
            color_mode=image_props['color_mode'],
            tags=tag_metadata,
            category=category,
            quality_score=quality_score,
            processing_steps=processing_history,
            total_processing_time_ms=total_time,
            models_used=models_used or [],
            hardware_profile=hardware_profile,
            custom_fields={}
        )

        # Generate metadata file path
        metadata_filename = f"{processed_path.stem}_context.json"
        metadata_path = self.metadata_dir / metadata_filename

        # Write metadata to file
        self._write_metadata(metadata, metadata_path)

        return metadata_path

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of the file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _get_image_properties(self, image_path: Path) -> Dict[str, Any]:
        """Extract basic image properties"""
        try:
            with Image.open(image_path) as img:
                return {
                    'dimensions': img.size,
                    'file_size': image_path.stat().st_size,
                    'format': img.format or 'unknown',
                    'color_mode': img.mode
                }
        except Exception:
            return {
                'dimensions': (0, 0),
                'file_size': 0,
                'format': 'unknown',
                'color_mode': 'unknown'
            }

    def _convert_tags_to_metadata(
        self,
        tags: List[str],
        normalized_tags: Optional[List[NormalizedTag]],
        processing_history: Optional[List[ProcessingStep]]
    ) -> List[TagMetadata]:
        """Convert tags to TagMetadata objects"""

        # Create mapping from normalized tags if available
        normalized_map = {}
        if normalized_tags:
            for norm_tag in normalized_tags:
                normalized_map[norm_tag.normalized] = norm_tag

        tag_metadata = []

        for i, tag in enumerate(tags):
            # Try to get metadata from normalized tags
            if tag in normalized_map:
                norm_tag = normalized_map[tag]
                tag_meta = TagMetadata(
                    tag=tag,
                    confidence=norm_tag.confidence,
                    category=norm_tag.category.value,
                    source="normalized",
                    normalized_from=norm_tag.source_synonym if norm_tag.is_synonym else None,
                    is_synonym=norm_tag.is_synonym
                )
            else:
                # Default metadata for non-normalized tags
                source = self._infer_tag_source(tag, processing_history)
                tag_meta = TagMetadata(
                    tag=tag,
                    confidence=0.8,  # Default confidence
                    category="general",
                    source=source
                )

            tag_metadata.append(tag_meta)

        return tag_metadata

    def _infer_tag_source(self, tag: str, processing_history: Optional[List[ProcessingStep]]) -> str:
        """Infer the source of a tag based on processing history and tag content"""
        if processing_history:
            # Check processing steps for clues
            for step in processing_history:
                if 'openclip' in step.step_name.lower():
                    return 'openclip'
                elif 'yolo' in step.step_name.lower():
                    return 'yolo'
                elif 'blip' in step.step_name.lower():
                    return 'blip'

        # Infer from tag content
        tag_lower = tag.lower()
        if any(word in tag_lower for word in ['photorealistic', 'detailed', 'sharp', 'quality']):
            return 'quality'
        elif any(word in tag_lower for word in ['person', 'car', 'dog', 'cat']):
            return 'yolo'
        else:
            return 'openclip'  # Default assumption

    def _determine_category(self, tag_metadata: List[TagMetadata]) -> str:
        """Determine the primary category of the image"""
        category_counts = {}

        for tag_meta in tag_metadata:
            category = tag_meta.category
            category_counts[category] = category_counts.get(category, 0) + 1

        if not category_counts:
            return "unknown"

        # Return the most common category
        return max(category_counts, key=category_counts.get)

    def _calculate_quality_score(self, image_props: Dict[str, Any], tag_metadata: List[TagMetadata]) -> float:
        """Calculate an overall quality score for the image"""
        score = 0.5  # Base score

        # Size factor
        width, height = image_props['dimensions']
        if width >= 2048 and height >= 2048:
            score += 0.3
        elif width >= 1024 and height >= 1024:
            score += 0.2
        elif width >= 512 and height >= 512:
            score += 0.1

        # Quality tags factor
        quality_tags = [tag for tag in tag_metadata if tag.category == 'quality']
        if quality_tags:
            avg_confidence = sum(tag.confidence for tag in quality_tags) / len(quality_tags)
            score += avg_confidence * 0.2

        return min(score, 1.0)  # Cap at 1.0

    def _write_metadata(self, metadata: ImageMetadata, output_path: Path) -> None:
        """Write metadata to JSON file"""
        # Convert dataclasses to dictionaries
        metadata_dict = asdict(metadata)

        # Convert datetime objects and other non-serializable types
        metadata_dict = self._make_serializable(metadata_dict)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=2, ensure_ascii=False)

    def _make_serializable(self, obj: Any) -> Any:
        """Make object JSON serializable"""
        if isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, tuple):
            return list(obj)
        elif hasattr(obj, 'value'):  # Enum
            return obj.value
        else:
            return obj

    def generate_summary_metadata(self, processed_images: List[Dict[str, Any]]) -> Path:
        """Generate a summary metadata file for a batch of processed images"""
        summary = {
            "batch_summary": {
                "total_images": len(processed_images),
                "processing_timestamp": datetime.now().isoformat(),
                "profiles_used": list(set(img.get('profile', 'unknown') for img in processed_images)),
                "categories": {}
            },
            "images": processed_images
        }

        # Calculate category statistics
        for img in processed_images:
            category = img.get('category', 'unknown')
            if category not in summary["batch_summary"]["categories"]:
                summary["batch_summary"]["categories"][category] = 0
            summary["batch_summary"]["categories"][category] += 1

        # Write summary file
        summary_path = self.metadata_dir / "batch_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return summary_path