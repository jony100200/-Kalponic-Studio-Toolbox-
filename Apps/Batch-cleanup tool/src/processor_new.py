"""
Core image processing operations for fringe removal and alpha refinement.
Uses only Pillow (PIL) - no OpenCV or NumPy dependencies.
"""

from PIL import Image, ImageFilter, ImageOps, ImageEnhance
import logging
from typing import Tuple, Optional

from .config import ProcessingConfig, MattePreset

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Handles core image processing operations using only Pillow."""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
    
    def process_image(self, image: Image.Image) -> Image.Image:
        """Process a single image through the complete pipeline."""
        try:
            # Ensure image has alpha channel
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Step 1: Unmatte (remove background contamination)
            if self.config.preset != MattePreset.NONE:
                image = self._unmatte(image)
            
            # Step 2: Refine alpha channel
            image = self._refine_alpha(image)
            
            # Step 3: Apply fringe fix
            if self.config.fringe_fix_enabled:
                image = self._fringe_fix(image)
            
            logger.info("Image processed successfully")
            return image
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise
    
    def _unmatte(self, image: Image.Image) -> Image.Image:
        """Remove white/black background contamination from edges."""
        try:
            r, g, b, a = image.split()
            
            if self.config.preset == MattePreset.WHITE:
                # Remove white contamination
                r = self._remove_contamination(r, a, 255)
                g = self._remove_contamination(g, a, 255)
                b = self._remove_contamination(b, a, 255)
            elif self.config.preset == MattePreset.BLACK:
                # Remove black contamination
                r = self._remove_contamination(r, a, 0)
                g = self._remove_contamination(g, a, 0)
                b = self._remove_contamination(b, a, 0)
            elif self.config.preset == MattePreset.AUTO:
                # Auto-detect and remove contamination (default to white)
                r = self._remove_contamination(r, a, 255)
                g = self._remove_contamination(g, a, 255)
                b = self._remove_contamination(b, a, 255)
            
            return Image.merge('RGBA', (r, g, b, a))
            
        except Exception as e:
            logger.error(f"Error in unmatte: {e}")
            return image
    
    def _remove_contamination(self, channel: Image.Image, alpha: Image.Image, bg_value: int) -> Image.Image:
        """Remove background contamination from a color channel."""
        pixels = list(channel.getdata())
        alpha_pixels = list(alpha.getdata())
        
        result_pixels = []
        for color, a in zip(pixels, alpha_pixels):
            if a > 0 and a < 255:  # Semi-transparent pixel
                alpha_ratio = a / 255.0
                if alpha_ratio > 0.1:
                    # Remove background contamination: (observed - bg*(1-alpha)) / alpha
                    clean_color = (color - bg_value * (1 - alpha_ratio)) / alpha_ratio
                    clean_color = max(0, min(255, int(clean_color)))
                    result_pixels.append(clean_color)
                else:
                    result_pixels.append(color)
            else:
                result_pixels.append(color)
        
        result = Image.new('L', channel.size)
        result.putdata(result_pixels)
        return result
    
    def _refine_alpha(self, image: Image.Image) -> Image.Image:
        """Refine the alpha channel with smoothing, feathering, contrast, and edge shifting."""
        try:
            r, g, b, a = image.split()
            
            # Step 1: Smooth alpha
            if self.config.smooth > 0:
                radius = self.config.smooth
                a = a.filter(ImageFilter.GaussianBlur(radius=radius))
            
            # Step 2: Feather alpha
            if self.config.feather > 0:
                radius = self.config.feather
                a = a.filter(ImageFilter.GaussianBlur(radius=radius))
            
            # Step 3: Adjust contrast
            if self.config.contrast != 1.0:
                enhancer = ImageEnhance.Contrast(a)
                a = enhancer.enhance(self.config.contrast)
            
            # Step 4: Shift edges
            if self.config.shift_edge != 0:
                a = self._shift_alpha_edges(a, self.config.shift_edge)
            
            return Image.merge('RGBA', (r, g, b, a))
            
        except Exception as e:
            logger.error(f"Error in refine_alpha: {e}")
            return image
    
    def _shift_alpha_edges(self, alpha: Image.Image, shift: int) -> Image.Image:
        """Shift alpha channel edges inward (negative) or outward (positive)."""
        try:
            if shift == 0:
                return alpha
            
            if shift > 0:
                # Dilate (expand alpha)
                for _ in range(abs(shift)):
                    alpha = alpha.filter(ImageFilter.MaxFilter(3))
            else:
                # Erode (contract alpha)
                for _ in range(abs(shift)):
                    alpha = alpha.filter(ImageFilter.MinFilter(3))
            
            return alpha
            
        except Exception as e:
            logger.error(f"Error in shift_alpha_edges: {e}")
            return alpha
    
    def _fringe_fix(self, image: Image.Image) -> Image.Image:
        """Apply fringe fixing to remove color artifacts at edges."""
        try:
            if not self.config.fringe_fix_enabled:
                return image
            
            r, g, b, a = image.split()
            
            # Create edge mask for fringe area
            edge_mask = self._create_fringe_mask(a, self.config.fringe_band)
            
            # Apply fringe correction
            strength = self.config.fringe_strength / 3.0  # Normalize to 0-1
            
            # Simple fringe fix: blend edge colors with nearby opaque colors
            r = self._fix_channel_fringe(r, a, edge_mask, strength)
            g = self._fix_channel_fringe(g, a, edge_mask, strength)
            b = self._fix_channel_fringe(b, a, edge_mask, strength)
            
            return Image.merge('RGBA', (r, g, b, a))
            
        except Exception as e:
            logger.error(f"Error in fringe_fix: {e}")
            return image
    
    def _create_fringe_mask(self, alpha: Image.Image, band_width: int) -> Image.Image:
        """Create a mask for the fringe area around edges."""
        # Create edge detection mask
        edge_mask = alpha.filter(ImageFilter.FIND_EDGES)
        
        # Dilate the edge mask to create a band
        for _ in range(band_width):
            edge_mask = edge_mask.filter(ImageFilter.MaxFilter(3))
        
        return edge_mask
    
    def _fix_channel_fringe(self, channel: Image.Image, alpha: Image.Image, 
                          edge_mask: Image.Image, strength: float) -> Image.Image:
        """Fix fringing in a single color channel."""
        # Apply median filter to reduce fringe artifacts
        filtered_channel = channel.filter(ImageFilter.MedianFilter(3))
        
        # Blend original and filtered based on strength and edge mask
        pixels = list(channel.getdata())
        filtered_pixels = list(filtered_channel.getdata())
        mask_pixels = list(edge_mask.getdata())
        
        result_pixels = []
        for orig, filt, mask in zip(pixels, filtered_pixels, mask_pixels):
            if mask > 0:  # In fringe area
                blend_factor = (mask / 255.0) * strength
                result = int(orig * (1 - blend_factor) + filt * blend_factor)
                result_pixels.append(result)
            else:
                result_pixels.append(orig)
        
        result = Image.new('L', channel.size)
        result.putdata(result_pixels)
        return result
    
    def create_preview(self, original: Image.Image, processed: Image.Image) -> Image.Image:
        """Create a side-by-side preview image."""
        try:
            # Resize images to reasonable preview size
            max_height = 300
            
            # Calculate aspect ratios
            orig_ratio = original.width / original.height
            proc_ratio = processed.width / processed.height
            
            # Resize original if needed
            if original.height > max_height:
                new_height = max_height
                new_width = int(new_height * orig_ratio)
                original = original.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Resize processed if needed
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
            if original.mode == 'RGBA':
                combined.paste(original, (0, 0), original)
            else:
                combined.paste(original, (0, 0))
                
            if processed.mode == 'RGBA':
                combined.paste(processed, (original.width + 10, 0), processed)
            else:
                combined.paste(processed, (original.width + 10, 0))
            
            return combined
            
        except Exception as e:
            logger.error(f"Error creating preview: {e}")
            return original
