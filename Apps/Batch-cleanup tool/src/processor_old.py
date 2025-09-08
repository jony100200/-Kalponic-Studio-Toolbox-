"""
Core image processing operations for fringe removal and alpha refinement.
"""

from PIL import Image, ImageFilter, ImageOps, ImageEnhance
import logging
from typing import Tuple, Optional
import math

from .config import ProcessingConfig, MattePreset

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Handles core image processing operations."""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
    
    def process_image(self, image: Image.Image) -> Image.Image:
        """
        Main processing pipeline for a single image.
        
        Args:
            image: PIL Image (preferably RGBA)
            
        Returns:
            Processed PIL Image
        """
        # Ensure RGBA format
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Convert to numpy array for processing
        img_array = np.array(image)
        
        # Step 1: Un-matte (remove background contamination)
        if self.config.matte_preset != MattePreset.AUTO:
            img_array = self._unmatte(img_array)
        
        # Step 2: Refine alpha channel
        img_array = self._refine_alpha(img_array)
        
        # Step 3: Fringe fix
        if self.config.fringe_fix_enabled:
            img_array = self._fringe_fix(img_array)
        
        # Convert back to PIL Image
        return Image.fromarray(img_array, 'RGBA')
    
    def _unmatte(self, img_array: np.ndarray) -> np.ndarray:
        """
        Remove matte contamination from semi-transparent edges.
        
        Args:
            img_array: RGBA numpy array
            
        Returns:
            Processed RGBA numpy array
        """
        result = img_array.copy()
        alpha = img_array[:, :, 3].astype(np.float32) / 255.0
        
        # Avoid division by zero
        alpha_safe = np.maximum(alpha, 0.001)
        
        if self.config.matte_preset == MattePreset.WHITE_MATTE:
            # Remove white contamination
            for c in range(3):  # RGB channels
                contaminated = img_array[:, :, c].astype(np.float32)
                # Un-premultiply assuming white background
                clean = (contaminated - 255 * (1 - alpha)) / alpha_safe
                result[:, :, c] = np.clip(clean, 0, 255).astype(np.uint8)
                
        elif self.config.matte_preset == MattePreset.BLACK_MATTE:
            # Remove black contamination
            for c in range(3):  # RGB channels
                contaminated = img_array[:, :, c].astype(np.float32)
                # Un-premultiply assuming black background
                clean = contaminated / alpha_safe
                result[:, :, c] = np.clip(clean, 0, 255).astype(np.uint8)
        
        return result
    
    def _refine_alpha(self, img_array: np.ndarray) -> np.ndarray:
        """
        Refine alpha channel: smooth → feather → contrast → shift.
        
        Args:
            img_array: RGBA numpy array
            
        Returns:
            Processed RGBA numpy array
        """
        result = img_array.copy()
        alpha = result[:, :, 3]
        
        # Step 1: Smooth
        if self.config.smooth > 0:
            kernel_size = self.config.smooth * 2 + 1
            alpha = cv2.GaussianBlur(alpha, (kernel_size, kernel_size), 0)
        
        # Step 2: Feather (additional blur for soft edges)
        if self.config.feather > 0:
            feather_kernel = self.config.feather * 2 + 1
            alpha = cv2.GaussianBlur(alpha, (feather_kernel, feather_kernel), 0)
        
        # Step 3: Contrast adjustment
        if self.config.contrast != 1.0:
            alpha = alpha.astype(np.float32) / 255.0
            # Apply gamma correction for contrast
            alpha = np.power(alpha, 1.0 / self.config.contrast)
            alpha = (alpha * 255).astype(np.uint8)
        
        # Step 4: Edge shift (erode/dilate)
        if self.config.shift_edge != 0:
            kernel = np.ones((3, 3), np.uint8)
            if self.config.shift_edge > 0:
                # Dilate (expand edges)
                for _ in range(abs(self.config.shift_edge)):
                    alpha = cv2.dilate(alpha, kernel, iterations=1)
            else:
                # Erode (shrink edges)
                for _ in range(abs(self.config.shift_edge)):
                    alpha = cv2.erode(alpha, kernel, iterations=1)
        
        result[:, :, 3] = alpha
        return result
    
    def _fringe_fix(self, img_array: np.ndarray) -> np.ndarray:
        """
        Fix color fringes around edges using inpainting.
        
        Args:
            img_array: RGBA numpy array
            
        Returns:
            Processed RGBA numpy array
        """
        result = img_array.copy()
        alpha = img_array[:, :, 3]
        
        # Create mask for fringe area (semi-transparent edges)
        alpha_norm = alpha.astype(np.float32) / 255.0
        
        # Find edge pixels (areas with partial transparency)
        edge_threshold_low = 0.1
        edge_threshold_high = 0.9
        edge_mask = (alpha_norm > edge_threshold_low) & (alpha_norm < edge_threshold_high)
        
        # Expand the mask based on band setting
        kernel = np.ones((self.config.fringe_band * 2 + 1, self.config.fringe_band * 2 + 1), np.uint8)
        edge_mask = cv2.dilate(edge_mask.astype(np.uint8), kernel, iterations=1)
        
        # For each RGB channel, inpaint the fringe areas
        for c in range(3):
            channel = result[:, :, c]
            
            # Create inpainting mask (areas to fix)
            inpaint_mask = edge_mask.copy()
            
            # Use cv2.inpaint to fix fringes
            if np.any(inpaint_mask):
                # Adjust inpainting strength
                inpaint_radius = max(1, self.config.fringe_strength)
                inpainted = cv2.inpaint(channel, inpaint_mask, inpaint_radius, cv2.INPAINT_TELEA)
                
                # Blend based on strength setting
                blend_factor = self.config.fringe_strength / 3.0
                result[:, :, c] = (channel * (1 - blend_factor) + inpainted * blend_factor).astype(np.uint8)
        
        return result
    
    def create_preview(self, original: Image.Image, processed: Image.Image) -> Image.Image:
        """
        Create a side-by-side preview image.
        
        Args:
            original: Original PIL Image
            processed: Processed PIL Image
            
        Returns:
            Combined preview image
        """
        # Resize images to reasonable preview size
        max_height = 300
        orig_ratio = original.width / original.height
        proc_ratio = processed.width / processed.height
        
        if original.height > max_height:
            new_height = max_height
            new_width = int(new_height * orig_ratio)
            original = original.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        if processed.height > max_height:
            new_height = max_height
            new_width = int(new_height * proc_ratio)
            processed = processed.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create combined image
        total_width = original.width + processed.width + 10  # 10px gap
        max_height = max(original.height, processed.height)
        
        # Create white background
        combined = Image.new('RGB', (total_width, max_height), 'white')
        
        # Paste images
        combined.paste(original, (0, 0))
        combined.paste(processed, (original.width + 10, 0))
        
        return combined
