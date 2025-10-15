"""
🎯 Model Recommender for KS MetaMaker
=====================================
Recommends optimal AI models based on detected hardware capabilities
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelRecommendation:
    """Recommended model configuration"""
    profile: str
    tagging_model: str
    detection_model: str
    captioning_model: str
    reasoning: str
    download_urls: Dict[str, str]


class ModelRecommender:
    """Recommends AI models based on hardware profile"""

    def __init__(self):
        self._model_profiles = self._define_model_profiles()

    def _define_model_profiles(self) -> Dict[str, ModelRecommendation]:
        """Define model recommendations for each hardware profile"""
        return {
            "cpu_only": ModelRecommendation(
                profile="cpu_only",
                tagging_model="openai/clip-vit-base-patch32",
                detection_model="ultralytics/yolov8n",  # nano version for CPU
                captioning_model="Salesforce/blip-image-captioning-base",
                reasoning="CPU-only system detected. Using lightweight models optimized for CPU inference.",
                download_urls={
                    "tagging": "https://huggingface.co/openai/clip-vit-base-patch32/resolve/main/pytorch_model.bin",
                    "detection": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt",
                    "captioning": "https://huggingface.co/Salesforce/blip-image-captioning-base/resolve/main/pytorch_model.bin"
                }
            ),

            "edge_4g": ModelRecommendation(
                profile="edge_4g",
                tagging_model="google/siglip-base-patch16-224",
                detection_model="ultralytics/yolov8s",
                captioning_model="microsoft/DialoGPT-small",
                reasoning="Low VRAM system (≤4GB). Using efficient SigLIP for tagging and small YOLO model.",
                download_urls={
                    "tagging": "https://huggingface.co/google/siglip-base-patch16-224/resolve/main/pytorch_model.bin",
                    "detection": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt",
                    "captioning": "https://huggingface.co/microsoft/DialoGPT-small/resolve/main/pytorch_model.bin"
                }
            ),

            "mid_8g": ModelRecommendation(
                profile="mid_8g",
                tagging_model="google/siglip-base-patch16-256",
                detection_model="ultralytics/yolov8m",
                captioning_model="Salesforce/blip2-opt-2.7b",
                reasoning="Mid-range GPU (6-8GB VRAM). Using SigLIP-base and medium YOLO with BLIP2 for captions.",
                download_urls={
                    "tagging": "https://huggingface.co/google/siglip-base-patch16-256/resolve/main/pytorch_model.bin",
                    "detection": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8m.pt",
                    "captioning": "https://huggingface.co/Salesforce/blip2-opt-2.7b/resolve/main/pytorch_model.bin"
                }
            ),

            "pro_12g": ModelRecommendation(
                profile="pro_12g",
                tagging_model="BAAI/EVA-CLIP-8B",
                detection_model="ultralytics/yolov8l",
                captioning_model="Salesforce/blip2-flan-t5-xl",
                reasoning="Professional GPU (10-12GB VRAM). Using EVA-CLIP-8B and large YOLO with advanced BLIP2.",
                download_urls={
                    "tagging": "https://huggingface.co/BAAI/EVA-CLIP-8B/resolve/main/pytorch_model.bin",
                    "detection": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8l.pt",
                    "captioning": "https://huggingface.co/Salesforce/blip2-flan-t5-xl/resolve/main/pytorch_model.bin"
                }
            ),

            "max": ModelRecommendation(
                profile="max",
                tagging_model="laion/CLIP-ViT-H-14-laion2B-s32B-b79K",
                detection_model="ultralytics/yolov8x",
                captioning_model="Salesforce/blip2-flan-t5-xxl",
                reasoning="High-end GPU (>12GB VRAM). Using largest available models for maximum quality.",
                download_urls={
                    "tagging": "https://huggingface.co/laion/CLIP-ViT-H-14-laion2B-s32B-b79K/resolve/main/pytorch_model.bin",
                    "detection": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8x.pt",
                    "captioning": "https://huggingface.co/Salesforce/blip2-flan-t5-xxl/resolve/main/pytorch_model.bin"
                }
            )
        }

    def get_recommendation(self, hardware_profile: str) -> ModelRecommendation:
        """
        Get model recommendation for the given hardware profile

        Args:
            hardware_profile: One of ['cpu_only', 'edge_4g', 'mid_8g', 'pro_12g', 'max']

        Returns:
            ModelRecommendation with optimal models for the hardware
        """
        if hardware_profile not in self._model_profiles:
            logger.warning(f"Unknown hardware profile: {hardware_profile}, using cpu_only")
            hardware_profile = "cpu_only"

        return self._model_profiles[hardware_profile]

    def get_all_profiles(self) -> Dict[str, ModelRecommendation]:
        """Get all available model profiles"""
        return self._model_profiles.copy()

    def get_profile_requirements(self) -> Dict[str, Dict]:
        """Get hardware requirements for each profile"""
        return {
            "cpu_only": {"vram_gb": 0, "ram_gb": 4, "description": "CPU-only systems"},
            "edge_4g": {"vram_gb": 4, "ram_gb": 8, "description": "Low-end GPUs (≤4GB VRAM)"},
            "mid_8g": {"vram_gb": 8, "ram_gb": 16, "description": "Mid-range GPUs (6-8GB VRAM)"},
            "pro_12g": {"vram_gb": 12, "ram_gb": 24, "description": "Professional GPUs (10-12GB VRAM)"},
            "max": {"vram_gb": 16, "ram_gb": 32, "description": "High-end GPUs (>12GB VRAM)"}
        }