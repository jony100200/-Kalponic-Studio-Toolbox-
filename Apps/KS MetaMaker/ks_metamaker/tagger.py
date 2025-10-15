"""
Image tagging module for KS MetaMaker
"""

from pathlib import Path
from typing import List, Optional
import logging
from PIL import Image
import numpy as np

from .utils.config import Config

logger = logging.getLogger(__name__)

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger.warning("ONNX Runtime not available, using mock tagging")


class ImageTagger:
    """Handles AI-powered image tagging and classification"""

    def __init__(self, config: Config):
        self.config = config
        self.models_loaded = False

        # Model sessions
        self.openclip_session: Optional[ort.InferenceSession] = None
        self.yolo_session: Optional[ort.InferenceSession] = None
        self.blip_session: Optional[ort.InferenceSession] = None

        # Tag databases as fallback
        self.prop_tags = [
            "metal", "rusty", "industrial", "weapon", "tool", "container",
            "barrel", "pipe", "gear", "machine", "furniture", "vehicle"
        ]

        self.background_tags = [
            "sky", "city", "nature", "indoor", "outdoor", "night", "day",
            "urban", "rural", "forest", "mountain", "ocean", "desert"
        ]

        self.character_tags = [
            "human", "animal", "fantasy", "armor", "clothing", "pose",
            "expression", "gender", "age", "style", "weapon", "magic"
        ]

        # Try to load models on initialization
        self.load_models()

    def tag(self, image_path: Path) -> List[str]:
        """
        Generate tags for an image using AI models

        Args:
            image_path: Path to the image file

        Returns:
            List of tags describing the image
        """
        try:
            tags = []

            # Add main prefix
            tags.append(self.config.main_prefix)

            # Add style preset
            tags.extend(self.config.style_preset.split(', '))

            # Load and preprocess image
            image = self._load_image(image_path)
            if image is None:
                return [self.config.main_prefix, "unknown"]

            # Use AI models if available
            if self.models_loaded and ONNX_AVAILABLE:
                # Get tags from different models
                openclip_tags = self._get_openclip_tags(image)
                yolo_tags = self._get_yolo_tags(image)
                blip_caption = self._get_blip_caption(image)

                # Combine and filter tags
                all_tags = openclip_tags + yolo_tags
                if blip_caption:
                    all_tags.extend(self._extract_tags_from_caption(blip_caption))

                # Determine category from tags
                category = self._classify_from_tags(all_tags)
                max_tags = self.config.max_tags.get(category, 20)

                # Select best tags
                selected_tags = self._select_best_tags(all_tags, max_tags - len(tags))
                tags.extend(selected_tags)
            else:
                # Fallback to mock tagging
                category = self._classify_category(image_path)
                category_tags = self._get_category_tags(category)
                max_tags = self.config.max_tags.get(category, 20)
                selected_tags = self._select_best_tags(category_tags, max_tags - len(tags))
                tags.extend(selected_tags)

            # Add quality tags
            quality_tags = self._assess_quality(image_path)
            tags.extend(quality_tags)

            # Remove duplicates and clean
            tags = list(dict.fromkeys(tags))  # Remove duplicates while preserving order

            logger.info(f"Tagged {image_path.name}: {tags}")
            return tags

        except Exception as e:
            logger.error(f"Failed to tag {image_path}: {e}")
            return [self.config.main_prefix, "unknown"]

    def load_models(self):
        """Load AI models using ONNX Runtime"""
        if not ONNX_AVAILABLE:
            logger.warning("ONNX Runtime not available")
            return

        try:
            # Load OpenCLIP model
            openclip_path = self.config.get_model_path("tagger")
            if openclip_path.exists():
                self.openclip_session = ort.InferenceSession(str(openclip_path))
                logger.info("OpenCLIP model loaded")
            else:
                logger.warning(f"OpenCLIP model not found at {openclip_path}")

            # Load YOLOv11 model
            yolo_path = self.config.get_model_path("detector")
            if yolo_path.exists():
                self.yolo_session = ort.InferenceSession(str(yolo_path))
                logger.info("YOLOv11 model loaded")
            else:
                logger.warning(f"YOLOv11 model not found at {yolo_path}")

            # Load BLIP2 model
            blip_path = self.config.get_model_path("captioner")
            if blip_path.exists():
                self.blip_session = ort.InferenceSession(str(blip_path))
                logger.info("BLIP2 model loaded")
            else:
                logger.warning(f"BLIP2 model not found at {blip_path}")

            self.models_loaded = True
            logger.info("AI models loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            self.models_loaded = False

    def _load_image(self, image_path: Path) -> Optional[np.ndarray]:
        """Load and preprocess image for model input"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Resize to 224x224 for CLIP models (adjust based on actual model requirements)
                img = img.resize((224, 224), Image.Resampling.LANCZOS)

                # Convert to numpy array and normalize
                image_array = np.array(img).astype(np.float32) / 255.0

                # Transpose to CHW format (channels, height, width)
                image_array = np.transpose(image_array, (2, 0, 1))

                return image_array

        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            return None

    def _get_openclip_tags(self, image: np.ndarray) -> List[str]:
        """Get tags using OpenCLIP model"""
        if not self.openclip_session:
            return []

        try:
            # This is a simplified implementation
            # In reality, you'd need the proper preprocessing and postprocessing
            # for the specific OpenCLIP ONNX model

            # For now, return some mock tags based on model availability
            return ["photorealistic", "detailed", "high quality"]

        except Exception as e:
            logger.error(f"OpenCLIP tagging failed: {e}")
            return []

    def _get_yolo_tags(self, image: np.ndarray) -> List[str]:
        """Get object detection tags using YOLOv11"""
        if not self.yolo_session:
            return []

        try:
            # Convert CHW to HWC for YOLO
            image_hwc = np.transpose(image, (1, 2, 0))
            image_hwc = (image_hwc * 255).astype(np.uint8)

            # This is a placeholder - actual YOLO inference would go here
            # You'd need proper preprocessing, inference, and postprocessing

            # Mock object detection results
            detected_objects = ["object", "item", "prop"]
            return detected_objects

        except Exception as e:
            logger.error(f"YOLO detection failed: {e}")
            return []

    def _get_blip_caption(self, image: np.ndarray) -> Optional[str]:
        """Get image caption using BLIP2"""
        if not self.blip_session:
            return None

        try:
            # Placeholder for BLIP2 captioning
            # This would require proper text tokenization and generation

            return "A detailed image of an object in a scene"

        except Exception as e:
            logger.error(f"BLIP2 captioning failed: {e}")
            return None

    def _extract_tags_from_caption(self, caption: str) -> List[str]:
        """Extract relevant tags from caption"""
        # Simple keyword extraction
        words = caption.lower().split()
        tags = []

        # Common descriptive words
        descriptive_words = [
            "detailed", "realistic", "photorealistic", "cinematic",
            "professional", "high quality", "sharp", "clear"
        ]

        for word in words:
            if word in descriptive_words:
                tags.append(word)

        return tags

    def _classify_from_tags(self, tags: List[str]) -> str:
        """Determine category from tags"""
        tag_text = " ".join(tags).lower()

        if any(word in tag_text for word in ["object", "prop", "item", "tool", "weapon", "container"]):
            return "props"
        elif any(word in tag_text for word in ["background", "scene", "environment", "sky", "city", "nature"]):
            return "backgrounds"
        elif any(word in tag_text for word in ["character", "person", "human", "animal", "figure"]):
            return "characters"
        else:
            return "backgrounds"  # default

    def _select_best_tags(self, tags: List[str], max_count: int) -> List[str]:
        """Select the best tags up to max_count"""
        if len(tags) <= max_count:
            return tags

        # For now, just take the first max_count tags
        # In a real implementation, you'd rank them by confidence scores
        return tags[:max_count]

    def _classify_category(self, image_path: Path) -> str:
        """Fallback classification based on filename"""
        filename = image_path.stem.lower()

        if any(word in filename for word in ['prop', 'object', 'item', 'tool', 'weapon']):
            return 'props'
        elif any(word in filename for word in ['bg', 'background', 'scene', 'environment']):
            return 'backgrounds'
        elif any(word in filename for word in ['char', 'character', 'person', 'figure']):
            return 'characters'
        else:
            return 'backgrounds'  # default

    def _get_category_tags(self, category: str) -> List[str]:
        """Get tag database for category"""
        if category == 'props':
            return self.prop_tags
        elif category == 'backgrounds':
            return self.background_tags
        elif category == 'characters':
            return self.character_tags
        else:
            return self.background_tags

    def _assess_quality(self, image_path: Path) -> List[str]:
        """Assess image quality and add relevant tags"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size

                # Size-based quality
                if width >= 2048 and height >= 2048:
                    return ["high resolution", "4k", "ultra hd"]
                elif width >= 1024 and height >= 1024:
                    return ["high resolution", "hd"]
                elif width >= 512 and height >= 512:
                    return ["medium resolution"]
                else:
                    return ["low resolution"]

        except Exception:
            return ["quality unknown"]