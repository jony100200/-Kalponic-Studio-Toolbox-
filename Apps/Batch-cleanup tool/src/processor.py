"""
Advanced image processor using OpenCV, NumPy, and Pillow.
Handles sophisticated unmatte, alpha refinement, and fringe fixing.
"""

import cv2
import numpy as np
from PIL import Image
import os
from typing import Optional, Tuple
from .config import ProcessingConfig


class ImageProcessor:
    """Handles core image processing operations using OpenCV and NumPy for best results."""
    
    def __init__(self):
        """Initialize the processor."""
        pass
    
    def process_image(self, image_path: str, config: ProcessingConfig) -> Optional[Image.Image]:
        """
        Process a single image according to the configuration.
        
        Args:
            image_path: Path to the input image
            config: Processing configuration
            
        Returns:
            Processed PIL Image or None if error
        """
        try:
            # Load image
            image = self._load_image(image_path)
            if image is None:
                return None

            # Convert to numpy array for processing
            img_array = np.array(image)

            # Ensure RGBA
            if img_array.shape[2] == 3:
                # Add alpha channel
                alpha = np.full((img_array.shape[0], img_array.shape[1], 1), 255, dtype=np.uint8)
                img_array = np.concatenate([img_array, alpha], axis=2)

            # Apply processing pipeline for the specified number of iterations
            for _ in range(config.process_iterations):
                if config.matte_preset.value != "Auto":
                    img_array = self._unmatte(img_array, config)

                img_array = self._refine_alpha(img_array, config)

                if config.fringe_fix_enabled:
                    img_array = self._fix_fringe(img_array, config)

            # Convert back to PIL Image. Passing a positional 'mode' to Image.fromarray
            # is deprecated in newer Pillow versions. Create the image and then
            # explicitly convert to 'RGBA' to ensure correct mode and avoid warnings.
            return Image.fromarray(img_array).convert('RGBA')

        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            return None
    
    def _load_image(self, image_path: str) -> Optional[Image.Image]:
        """Load image from file path."""
        try:
            image = Image.open(image_path)
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            return image
        except Exception as e:
            print(f"Error loading {image_path}: {e}")
            return None
    
    def _unmatte(self, img_array: np.ndarray, config: ProcessingConfig) -> np.ndarray:
        """
        Remove matte contamination from edges using advanced techniques.
        """
        height, width = img_array.shape[:2]
        result = img_array.copy()
        
        # Extract alpha channel
        alpha = img_array[:, :, 3]
        
        # Find edge regions (pixels that are semi-transparent)
        edge_mask = (alpha > 10) & (alpha < 245)
        
        # Create dilated and eroded versions to find edge bands
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        alpha_dilated = cv2.dilate(alpha, kernel, iterations=2)
        alpha_eroded = cv2.erode(alpha, kernel, iterations=1)
        
        # Edge band is the difference
        edge_band = (alpha_dilated > alpha_eroded) & (alpha > 0)
        
        if config.matte_preset.value == "White Matte":
            # Remove white contamination
            for c in range(3):  # RGB channels
                channel = result[:, :, c].astype(np.float32)
                
                # For edge pixels, remove white bias
                white_mask = edge_band & (channel > 200)
                if np.any(white_mask):
                    # Reduce white contamination
                    alpha_ratio = alpha[white_mask].astype(np.float32) / 255.0
                    contamination = (255 - channel[white_mask]) * (1 - alpha_ratio) * 0.5
                    channel[white_mask] = np.clip(channel[white_mask] - contamination, 0, 255)
                
                result[:, :, c] = channel.astype(np.uint8)
        
        elif config.matte_preset.value == "Black Matte":
            # Remove black contamination
            for c in range(3):  # RGB channels
                channel = result[:, :, c].astype(np.float32)
                
                # For edge pixels, remove black bias
                black_mask = edge_band & (channel < 50)
                if np.any(black_mask):
                    # Reduce black contamination
                    alpha_ratio = alpha[black_mask].astype(np.float32) / 255.0
                    contamination = channel[black_mask] * (1 - alpha_ratio) * 0.5
                    channel[black_mask] = np.clip(channel[black_mask] + contamination, 0, 255)
                
                result[:, :, c] = channel.astype(np.uint8)
        
        return result
    
    def _refine_alpha(self, img_array: np.ndarray, config: ProcessingConfig) -> np.ndarray:
        """Refine alpha channel with smoothing, feathering, contrast, and edge shift."""
        result = img_array.copy()
        alpha = result[:, :, 3].astype(np.float32)
        
        # Smoothing
        if config.smooth > 0:
            for _ in range(config.smooth):
                alpha = cv2.GaussianBlur(alpha, (3, 3), 0.5)
        
        # Feathering (more blur)
        if config.feather > 0:
            kernel_size = config.feather * 2 + 1
            alpha = cv2.GaussianBlur(alpha, (kernel_size, kernel_size), config.feather * 0.5)
        
        # Contrast adjustment
        if config.contrast != 1.0:
            # Apply contrast: new_alpha = ((alpha / 255.0 - 0.5) * contrast + 0.5) * 255.0
            alpha = np.clip(((alpha / 255.0 - 0.5) * config.contrast + 0.5) * 255.0, 0, 255)
        
        # Edge shift (erosion/dilation)
        if config.shift_edge != 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            if config.shift_edge > 0:
                # Dilate (expand edges outward)
                for _ in range(config.shift_edge):
                    alpha = cv2.dilate(alpha, kernel, iterations=1)
            else:
                # Erode (contract edges inward)
                for _ in range(abs(config.shift_edge)):
                    alpha = cv2.erode(alpha, kernel, iterations=1)
        
        result[:, :, 3] = alpha.astype(np.uint8)
        return result
    
    def _fix_fringe(self, img_array: np.ndarray, config: ProcessingConfig) -> np.ndarray:
        """
        Advanced fringe fixing using color analysis and inpainting.
        """
        result = img_array.copy()
        height, width = img_array.shape[:2]
        
        # Extract alpha channel
        alpha = img_array[:, :, 3]
        
        # Create edge mask based on band setting
        band_size = config.fringe_band
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (band_size * 2 + 1, band_size * 2 + 1))
        
        # Find semi-transparent edge regions
        edge_mask = (alpha > 10) & (alpha < 240)
        
        # Dilate the edge mask to get the band
        dilated_edges = cv2.dilate(edge_mask.astype(np.uint8), kernel, iterations=1)
        edge_band = dilated_edges & (alpha > 0)
        
        # For each color channel, fix fringe colors
        for c in range(3):  # RGB channels
            channel = result[:, :, c].astype(np.float32)
            
            # Find pixels in the edge band
            edge_pixels = np.where(edge_band)
            
            if len(edge_pixels[0]) == 0:
                continue
            
            # For each edge pixel, find nearby solid pixels and blend
            for i in range(len(edge_pixels[0])):
                y, x = edge_pixels[0][i], edge_pixels[1][i]
                
                # Define neighborhood
                y_min, y_max = max(0, y - band_size), min(height, y + band_size + 1)
                x_min, x_max = max(0, x - band_size), min(width, x + band_size + 1)
                
                # Get neighborhood alpha and color values
                neighbor_alpha = alpha[y_min:y_max, x_min:x_max]
                neighbor_color = channel[y_min:y_max, x_min:x_max]
                
                # Find solid pixels (high alpha) in neighborhood
                solid_mask = neighbor_alpha > 200
                
                if np.any(solid_mask):
                    # Calculate weighted average of solid pixels
                    solid_colors = neighbor_color[solid_mask]
                    weights = neighbor_alpha[solid_mask].astype(np.float32) / 255.0
                    
                    if len(solid_colors) > 0:
                        weighted_avg = np.average(solid_colors, weights=weights)
                        
                        # Blend based on strength
                        strength = config.fringe_strength / 3.0
                        current_color = channel[y, x]
                        new_color = current_color * (1 - strength) + weighted_avg * strength
                        channel[y, x] = new_color
            
            result[:, :, c] = np.clip(channel, 0, 255).astype(np.uint8)
        
        return result
