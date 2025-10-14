"""
Main processing pipeline for KS Sprite Splitter.

Orchestrates the end-to-end sprite separation process:
1. Ingest - Load and prepare images
2. Segment - Detect object instances
3. Parts - Split into semantic parts
4. Matte - Create soft alpha mattes
5. Pack - Channel-pack parts
6. Export - Write outputs and metadata
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import cv2
from PIL import Image

from .segment import get_segmenter_backend
from .matte import get_matte_backend
from .parts import get_part_backend, load_template
from .mock_backends import *  # Register mock backends
from .real_backends import *  # Register real backends


class SpriteProcessor:
    """
    Main processor for sprite separation pipeline.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.segmenter = get_segmenter_backend(config.get('objects_backend', 'mock'))
        self.matter = get_matte_backend(config.get('matte_backend', 'mock'))
        self.part_splitter = get_part_backend(config.get('parts_backend', 'mock'))

    def process_image(self, image_path: str, category: str = 'auto') -> Dict[str, Any]:
        """
        Process a single image through the full pipeline.

        Args:
            image_path: Path to input image
            category: Template category to use

        Returns:
            Processing results dictionary
        """
        # Load and prepare image
        image = self._load_image(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Generate hash for deterministic processing
        image_hash = self._hash_image(image)

        # Load template
        if category == 'auto':
            category = 'tree'  # Default fallback
        template = load_template(category, self.config.get('templates_dir', 'templates'))

        # Process through pipeline
        instances = self.segmenter.infer(image)

        results = {
            'image_path': image_path,
            'image_hash': image_hash,
            'category': category,
            'template': template,
            'instances': []
        }

        for instance in instances:
            # Split into parts
            parts = self.part_splitter.split(image, instance, template)

            # Create mattes for each part
            mattes = {}
            for part_name, part_mask in parts.items():
                matte = self.matter.refine(image, part_mask, template.get('matting', {}).get('band_px', 5))
                mattes[part_name] = matte

            instance_result = {
                'id': instance['id'],
                'class': instance.get('class', 'unknown'),
                'bbox': instance['bbox'],
                'score': instance.get('score', 0.0),
                'parts': parts,
                'mattes': mattes
            }

            results['instances'].append(instance_result)

        return results

    def _load_image(self, path: str) -> Optional[np.ndarray]:
        """Load image and convert to RGB numpy array."""
        try:
            img = Image.open(path)
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            return np.array(img)
        except Exception as e:
            print(f"Error loading image {path}: {e}")
            return None

    def _hash_image(self, image: np.ndarray) -> str:
        """Generate hash of image for deterministic processing."""
        # Simple hash based on image shape and a few pixels
        data = image.shape + tuple(image.flatten()[:100])  # Sample first 100 pixels
        return hashlib.md5(str(data).encode()).hexdigest()[:8]


class PipelineRunner:
    """
    High-level pipeline runner with export functionality.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.processor = SpriteProcessor(config)

    def run(self, input_path: str, output_dir: str, category: str = 'auto') -> str:
        """
        Run the full pipeline on input(s) and export results.

        Args:
            input_path: Path to input image or directory
            output_dir: Base output directory
            category: Template category

        Returns:
            Path to the run directory created
        """
        # Create timestamped run directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        run_dir = Path(output_dir) / f'Run_{timestamp}'
        run_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        separated_dir = run_dir / 'Separated'
        preview_dir = run_dir / 'Preview'
        logs_dir = run_dir / 'Logs'
        backup_dir = run_dir / 'Backup'

        separated_dir.mkdir(exist_ok=True)
        preview_dir.mkdir(exist_ok=True)
        logs_dir.mkdir(exist_ok=True)
        backup_dir.mkdir(exist_ok=True)

        # Find input files
        input_files = self._find_input_files(input_path)

        all_results = []
        for img_path in input_files:
            print(f"Processing: {img_path}")

            try:
                result = self.processor.process_image(str(img_path), category)
                self._export_result(result, separated_dir, preview_dir, backup_dir)
                all_results.append(result)
            except Exception as e:
                print(f"Error processing {img_path}: {e}")
                continue

        # Write context.json
        context = {
            'run_timestamp': timestamp,
            'config': self.config,
            'input_path': input_path,
            'category': category,
            'results': all_results
        }

        with open(logs_dir / 'context.json', 'w') as f:
            json.dump(context, f, indent=2, default=str)

        # Write simple log
        with open(logs_dir / 'run.log', 'w') as f:
            f.write(f"KS Sprite Splitter Run {timestamp}\n")
            f.write(f"Input: {input_path}\n")
            f.write(f"Category: {category}\n")
            f.write(f"Processed {len(all_results)} images\n")

        print(f"Pipeline complete. Results in: {run_dir}")
        return str(run_dir)

    def _find_input_files(self, input_path: str) -> List[Path]:
        """Find all valid input image files."""
        path = Path(input_path)
        supported_exts = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']

        if path.is_file():
            if path.suffix.lower() in supported_exts:
                return [path]
            else:
                return []
        elif path.is_dir():
            files = []
            for ext in supported_exts:
                files.extend(path.rglob(f'*{ext}'))
            return sorted(files)
        else:
            return []

    def _export_result(self, result: Dict[str, Any], separated_dir: Path,
                      preview_dir: Path, backup_dir: Path):
        """Export processing results to files."""
        img_name = Path(result['image_path']).stem
        img_dir = separated_dir / img_name
        img_dir.mkdir(exist_ok=True)

        # Load original image for export
        image = self.processor._load_image(result['image_path'])
        if image is None:
            return

        # Save original image
        cv2.imwrite(str(img_dir / 'color.png'), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))

        # Process each instance
        for instance in result['instances']:
            parts = instance['parts']
            mattes = instance['mattes']

            # Create packed texture (simple RGBA for now)
            height, width = image.shape[:2]
            packed = np.zeros((height, width, 4), dtype=np.uint8)

            # Pack parts into RGBA channels (simplified)
            part_names = list(parts.keys())
            for i, part_name in enumerate(part_names[:4]):  # Max 4 parts
                mask = parts[part_name].astype(np.uint8) * 255
                packed[:, :, i] = mask

            # Save packed texture
            cv2.imwrite(str(img_dir / 'parts.png'), packed)

            # Save individual mattes
            for part_name, matte in mattes.items():
                matte_8bit = (matte * 255).astype(np.uint8)
                cv2.imwrite(str(img_dir / f'matte_{part_name}.png'), matte_8bit)

        # Create simple preview (copy of original for now)
        cv2.imwrite(str(preview_dir / f'{img_name}_small.png'),
                   cv2.cvtColor(image, cv2.COLOR_RGB2BGR))