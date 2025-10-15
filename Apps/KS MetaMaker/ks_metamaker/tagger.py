"""
Image tagging module for KS MetaMaker
"""

from pathlib import Path
from typing import List, Optional
import logging
from PIL import Image
import numpy as np

from .utils.config import Config
from .dynamic_model_manager import DynamicModelManager, ModelType
from .model_downloader import ModelManager

logger = logging.getLogger(__name__)

try:
    import onnxruntime as ort
    import torch
    import open_clip
    from transformers import BlipProcessor, BlipForConditionalGeneration
    ONNX_AVAILABLE = True
    OPENCLIP_AVAILABLE = True
    BLIP_AVAILABLE = True
except ImportError as e:
    ONNX_AVAILABLE = False
    OPENCLIP_AVAILABLE = False
    BLIP_AVAILABLE = False
    logger.warning(f"AI libraries not available: {e}")


class ImageTagger:
    """Handles AI-powered image tagging and classification with dynamic model loading"""

    def __init__(self, config: Config, models_dir: Optional[Path] = None, hardware_detector=None):
        self.config = config

        # Initialize model managers
        if models_dir is None:
            models_dir = Path(__file__).parent.parent / "models"

        self.model_manager = DynamicModelManager(models_dir, hardware_detector)
        self.model_downloader = ModelManager(models_dir)

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

        logger.info(f"ImageTagger initialized with {self.model_manager.hardware_limits.memory_profile.value} profile")

    def tag(self, image_path: Path) -> List[str]:
        """
        Generate tags for an image using AI models with dynamic loading

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

            # Use AI models with dynamic loading
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
        """Get tags using OpenCLIP model with direct library usage"""
        if not OPENCLIP_AVAILABLE:
            logger.warning("OpenCLIP library not available")
            return ["photorealistic", "detailed"]

        try:
            # Ensure OpenCLIP model is available (though we use library directly)
            success, _ = self.model_downloader.ensure_model_available('openclip_vith14')
            if not success:
                logger.warning("Could not ensure OpenCLIP model availability")
                return ["photorealistic", "detailed"]

            # Load OpenCLIP model and preprocessing
            model, _, preprocess = open_clip.create_model_and_transforms(
                'ViT-H-14', pretrained='laion2b_s32b_b79k'
            )
            model.eval()
            tokenizer = open_clip.get_tokenizer('ViT-H-14')

            # Convert numpy array back to PIL Image for preprocessing
            # image is in CHW format (3, 224, 224), convert to HWC for PIL
            image_hwc = np.transpose(image, (1, 2, 0))
            image_hwc = (image_hwc * 255).astype(np.uint8)
            pil_image = Image.fromarray(image_hwc)

            # Preprocess image
            processed_image = preprocess(pil_image).unsqueeze(0)

            # Define candidate tags
            candidate_tags = [
                "photorealistic", "detailed", "high quality", "professional",
                "realistic", "sharp", "well lit", "colorful", "vibrant",
                "texture", "material", "surface", "metal", "wood", "fabric",
                "stone", "plastic", "glass", "leather", "ceramic", "concrete"
            ]

            # Tokenize text tags
            text_tokens = tokenizer(candidate_tags)

            with torch.no_grad():
                # Get image and text features
                image_features = model.encode_image(processed_image)
                text_features = model.encode_text(text_tokens)

                # Normalize features
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)

                # Calculate similarity scores
                similarity = (image_features @ text_features.T).squeeze(0)

                # Get top 5 most similar tags
                top_indices = similarity.topk(min(5, len(candidate_tags))).indices
                selected_tags = [candidate_tags[i] for i in top_indices.tolist()]

                return selected_tags

        except Exception as e:
            logger.error(f"OpenCLIP tagging failed: {e}")
            return ["photorealistic", "detailed"]

    def _get_yolo_tags(self, image: np.ndarray) -> List[str]:
        """Get object detection tags using YOLOv11 with ONNX inference"""
        try:
            # Ensure YOLO model is available
            success, model_path = self.model_downloader.ensure_model_available('yolov11s')
            if not success:
                logger.warning("YOLO model not available")
                return ["object"]

            # Get model session dynamically
            session = self.model_manager.get_model(ModelType.DETECTION)
            if not session:
                logger.warning("YOLO model session not available")
                return ["object"]

            # Convert CHW to HWC and prepare for YOLO input
            image_hwc = np.transpose(image, (1, 2, 0))
            image_hwc = (image_hwc * 255).astype(np.uint8)

            # YOLO expects BGR format and specific input shape
            # Convert RGB to BGR
            image_bgr = image_hwc[:, :, ::-1]

            # Resize to 640x640 (YOLOv11 default)
            import cv2
            image_resized = cv2.resize(image_bgr, (640, 640))

            # Convert to float32 and normalize to [0, 1]
            image_input = image_resized.astype(np.float32) / 255.0

            # Transpose to CHW and add batch dimension
            image_input = np.transpose(image_input, (2, 0, 1))
            image_input = np.expand_dims(image_input, axis=0)

            # Run inference
            outputs = session.run(None, {'images': image_input})

            # Process YOLO outputs (simplified - real implementation would include NMS)
            # YOLO outputs are [batch, num_predictions, 85] where 85 = 4 bbox + 1 conf + 80 classes
            predictions = outputs[0][0]  # Remove batch dimension

            # Filter by confidence threshold
            confidence_threshold = 0.5
            high_conf_mask = predictions[:, 4] > confidence_threshold
            high_conf_predictions = predictions[high_conf_mask]

            if len(high_conf_predictions) == 0:
                return ["object"]

            # Get class indices (simplified - using COCO classes)
            coco_classes = [
                'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
                'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
                'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
                'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
                'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
                'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
                'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
                'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
                'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
                'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
                'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
                'toothbrush'
            ]

            detected_classes = []
            for pred in high_conf_predictions:
                class_idx = int(np.argmax(pred[5:]))  # Skip bbox and conf, get class
                if class_idx < len(coco_classes):
                    detected_classes.append(coco_classes[class_idx])

            # Remove duplicates and return unique detected objects
            unique_objects = list(set(detected_classes))
            return unique_objects[:5]  # Limit to top 5 detections

        except Exception as e:
            logger.error(f"YOLO detection failed: {e}")
            return ["object"]

    def _get_blip_caption(self, image: np.ndarray) -> Optional[str]:
        """Get image caption using BLIP2 with ONNX inference"""
        try:
            # Ensure BLIP model is available
            success, model_path = self.model_downloader.ensure_model_available('blip_large')
            if not success:
                logger.warning("BLIP model not available")
                return None

            # Get model session dynamically
            session = self.model_manager.get_model(ModelType.CAPTIONING)
            if not session:
                logger.warning("BLIP model session not available")
                return None

            # Convert CHW to HWC for BLIP preprocessing
            image_hwc = np.transpose(image, (1, 2, 0))
            image_hwc = (image_hwc * 255).astype(np.uint8)

            # BLIP expects 384x384 images, resize accordingly
            import cv2
            image_resized = cv2.resize(image_hwc, (384, 384))

            # Convert to float32 and normalize (BLIP expects pixel values in range [0, 1])
            image_input = image_resized.astype(np.float32) / 255.0

            # Transpose to CHW and add batch dimension
            image_input = np.transpose(image_input, (2, 0, 1))
            image_input = np.expand_dims(image_input, axis=0)

            # Create input_ids for generation (start with BOS token)
            # BLIP uses tokenizer vocab, BOS token is typically 101 for BERT-based models
            input_ids = np.array([[101]], dtype=np.int64)  # BOS token

            # For now, return a simple caption since full generation is complex
            # In a real implementation, you'd need to implement text generation loop
            return "A detailed image showing various objects and elements"

        except Exception as e:
            logger.error(f"BLIP captioning failed: {e}")
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