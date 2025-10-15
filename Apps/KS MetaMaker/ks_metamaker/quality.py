"""
Quality assessment module for KS MetaMaker
Handles blur detection, duplicate removal, and image quality evaluation
"""

from pathlib import Path
from typing import List, Dict, Set
import logging
from PIL import Image
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

logger = logging.getLogger(__name__)

try:
    import imagehash
    HASH_AVAILABLE = True
except ImportError:
    HASH_AVAILABLE = False
    logger.warning("imagehash not available, using basic duplicate detection")


class QualityAssessor:
    """Handles image quality assessment and filtering"""

    def __init__(self, blur_threshold: float = 100.0, duplicate_threshold: float = 0.9):
        """
        Initialize quality assessor

        Args:
            blur_threshold: Minimum variance of Laplacian for acceptable blur (lower = blurrier)
            duplicate_threshold: SSIM threshold for duplicate detection (higher = stricter)
        """
        self.blur_threshold = blur_threshold
        self.duplicate_threshold = duplicate_threshold
        self.processed_hashes: Set[str] = set()

    def assess_quality(self, image_path: Path) -> Dict[str, any]:
        """
        Assess overall quality of an image

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary with quality metrics
        """
        try:
            # Load image
            image = self._load_image_cv2(image_path)
            if image is None:
                return {"valid": False, "error": "Could not load image"}

            # Assess blur
            blur_score = self.detect_blur(image)

            # Assess brightness and contrast
            brightness, contrast = self.assess_brightness_contrast(image)

            # Overall quality score
            quality_score = self._calculate_quality_score(blur_score, brightness, contrast)

            return {
                "valid": True,
                "blur_score": blur_score,
                "brightness": brightness,
                "contrast": contrast,
                "quality_score": quality_score,
                "is_blurry": blur_score < self.blur_threshold,
                "recommendation": self._get_recommendation(blur_score, brightness, contrast)
            }

        except Exception as e:
            logger.error(f"Quality assessment failed for {image_path}: {e}")
            return {"valid": False, "error": str(e)}

    def detect_blur(self, image: np.ndarray) -> float:
        """
        Detect blur using variance of Laplacian

        Args:
            image: OpenCV image array

        Returns:
            Blur score (higher = sharper)
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Compute variance of Laplacian
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

            return laplacian_var

        except Exception as e:
            logger.error(f"Blur detection failed: {e}")
            return 0.0

    def assess_brightness_contrast(self, image: np.ndarray) -> tuple:
        """
        Assess brightness and contrast of image

        Args:
            image: OpenCV image array

        Returns:
            Tuple of (brightness, contrast)
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Calculate brightness (mean pixel value)
            brightness = np.mean(gray)

            # Calculate contrast (standard deviation)
            contrast = np.std(gray)

            return brightness, contrast

        except Exception as e:
            logger.error(f"Brightness/contrast assessment failed: {e}")
            return 0.0, 0.0

    def find_duplicates(self, image_paths: List[Path]) -> Dict[str, List[Path]]:
        """
        Find duplicate images using perceptual hashing

        Args:
            image_paths: List of image paths to check

        Returns:
            Dictionary mapping hash to list of duplicate paths
        """
        hash_groups = {}
        processed_images = {}

        for image_path in image_paths:
            try:
                if HASH_AVAILABLE:
                    # Use perceptual hashing
                    img_hash = self._calculate_perceptual_hash(image_path)
                else:
                    # Fallback to basic method
                    img_hash = self._calculate_basic_hash(image_path)

                if img_hash:
                    if img_hash not in hash_groups:
                        hash_groups[img_hash] = []
                    hash_groups[img_hash].append(image_path)

            except Exception as e:
                logger.error(f"Hash calculation failed for {image_path}: {e}")

        # Filter to only groups with duplicates
        duplicates = {hash_val: paths for hash_val, paths in hash_groups.items() if len(paths) > 1}

        return duplicates

    def filter_quality_images(self, image_paths: List[Path],
                            min_quality_score: float = 0.5) -> List[Path]:
        """
        Filter images based on quality assessment

        Args:
            image_paths: List of image paths
            min_quality_score: Minimum quality score (0-1)

        Returns:
            List of high-quality image paths
        """
        quality_images = []

        for image_path in image_paths:
            quality_info = self.assess_quality(image_path)

            if quality_info.get("valid", False):
                score = quality_info.get("quality_score", 0)
                if score >= min_quality_score:
                    quality_images.append(image_path)
                else:
                    logger.info(f"Filtered out low-quality image: {image_path.name} (score: {score:.2f})")
            else:
                logger.warning(f"Could not assess quality for: {image_path.name}")

        return quality_images

    def _load_image_cv2(self, image_path: Path) -> np.ndarray:
        """Load image using OpenCV"""
        try:
            image = cv2.imread(str(image_path))
            return image
        except Exception:
            return None

    def _calculate_perceptual_hash(self, image_path: Path) -> str:
        """Calculate perceptual hash using imagehash library"""
        try:
            with Image.open(image_path) as img:
                # Calculate average hash
                hash_obj = imagehash.average_hash(img)
                return str(hash_obj)
        except Exception:
            return None

    def _calculate_basic_hash(self, image_path: Path) -> str:
        """Calculate basic hash for duplicate detection"""
        try:
            with Image.open(image_path) as img:
                # Resize for consistent comparison
                img_resized = img.resize((64, 64), Image.Resampling.LANCZOS)
                img_gray = img_resized.convert('L')

                # Convert to numpy array
                img_array = np.array(img_gray)

                # Calculate simple hash
                hash_val = hash(img_array.tobytes())
                return str(hash_val)
        except Exception:
            return None

    def _calculate_quality_score(self, blur_score: float, brightness: float, contrast: float) -> float:
        """Calculate overall quality score (0-1)"""
        # Normalize blur score (assuming 0-1000 range, adjust as needed)
        blur_norm = min(1.0, blur_score / 500.0)

        # Normalize brightness (assuming 0-255 range)
        brightness_norm = 1.0 - abs(brightness - 128) / 128  # Peak at 128

        # Normalize contrast (assuming 0-128 range)
        contrast_norm = min(1.0, contrast / 64.0)

        # Weighted average
        score = (blur_norm * 0.5) + (brightness_norm * 0.25) + (contrast_norm * 0.25)

        return max(0.0, min(1.0, score))

    def _get_recommendation(self, blur_score: float, brightness: float, contrast: float) -> str:
        """Get quality recommendation"""
        issues = []

        if blur_score < self.blur_threshold:
            issues.append("blurry")

        if abs(brightness - 128) > 64:
            issues.append("brightness issues")

        if contrast < 32:
            issues.append("low contrast")

        if not issues:
            return "good quality"

        return f"issues: {', '.join(issues)}"