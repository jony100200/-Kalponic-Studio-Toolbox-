"""
Professional-grade image processor that mimics and exceeds Photoshop's fringe removal capabilities.
Implements advanced algorithms for superior edge processing, color unmixing, and selective enhancement.
"""

import cv2
import numpy as np
from PIL import Image, ImageFilter
import logging
from typing import Optional, Tuple, Dict, List
from .config import ProcessingConfig

logger = logging.getLogger(__name__)

class ProfessionalImageProcessor:
    """
    Professional image processor with Photoshop-quality fringe removal and edge enhancement.
    Implements advanced techniques including:
    - Gradient-based edge detection
    - Color unmixing algorithms
    - Alpha pyramid processing
    - Material-specific optimization
    - Selective surgical processing
    """
    
    def __init__(self):
        """Initialize the professional processor."""
        self.edge_cache = {}  # Cache edge masks for performance
        
    def process_image(self, image_path: str, config: ProcessingConfig) -> Optional[Image.Image]:
        """
        Process a single image with professional-grade techniques.
        
        Args:
            image_path: Path to the input image
            config: Processing configuration
            
        Returns:
            Professionally processed PIL Image or None if error
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
                alpha = np.full((img_array.shape[0], img_array.shape[1], 1), 255, dtype=np.uint8)
                img_array = np.concatenate([img_array, alpha], axis=2)
            
            # Professional processing pipeline
            logger.info("Starting professional image processing")
            
            # Step 1: Analyze image characteristics
            edge_map, material_type = self._analyze_image_characteristics(img_array)
            
            # Step 2: Advanced unmatte with color analysis
            if config.matte_preset.value != "Auto":
                img_array = self._professional_unmatte(img_array, config, edge_map)
            
            # Step 3: Alpha pyramid processing for complex transparency
            img_array = self._alpha_pyramid_processing(img_array, config)
            
            # Step 4: Material-specific enhancement
            img_array = self._material_specific_enhancement(img_array, material_type, config)
            
            # Step 5: Surgical fringe removal (only where needed)
            if config.fringe_fix_enabled:
                img_array = self._surgical_fringe_removal(img_array, config, edge_map)
            
            # Step 6: Professional edge refinement
            img_array = self._professional_edge_refinement(img_array, config)
            
            # Convert back to PIL Image
            result = Image.fromarray(img_array, 'RGBA')
            logger.info("Professional processing completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in professional processing {image_path}: {e}")
            return None
    
    def _load_image(self, image_path: str) -> Optional[Image.Image]:
        """Load image from file path."""
        try:
            image = Image.open(image_path)
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            return image
        except Exception as e:
            logger.error(f"Error loading {image_path}: {e}")
            return None
    
    def _analyze_image_characteristics(self, img_array: np.ndarray) -> Tuple[np.ndarray, str]:
        """
        Analyze image to detect edge characteristics and material type.
        Similar to Photoshop's intelligent analysis.
        """
        alpha = img_array[:, :, 3]
        
        # Create sophisticated edge map using multiple techniques
        # Method 1: Gradient-based edge detection
        grad_x = cv2.Sobel(alpha, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(alpha, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Method 2: Laplacian edge detection for fine details
        laplacian = cv2.Laplacian(alpha, cv2.CV_64F)
        
        # Method 3: Multi-scale edge detection
        blur1 = cv2.GaussianBlur(alpha, (3, 3), 1.0)
        blur2 = cv2.GaussianBlur(alpha, (5, 5), 2.0)
        multi_scale_edges = np.abs(blur1.astype(np.float32) - blur2.astype(np.float32))
        
        # Combine all edge detection methods
        edge_map = np.maximum.reduce([
            gradient_magnitude / np.max(gradient_magnitude + 1e-8),
            np.abs(laplacian) / (np.max(np.abs(laplacian)) + 1e-8),
            multi_scale_edges / (np.max(multi_scale_edges) + 1e-8)
        ])
        
        # Normalize edge map
        edge_map = (edge_map * 255).astype(np.uint8)
        
        # Detect material type based on edge characteristics
        material_type = self._detect_material_type(img_array, edge_map)
        
        return edge_map, material_type
    
    def _detect_material_type(self, img_array: np.ndarray, edge_map: np.ndarray) -> str:
        """
        Detect material type for specialized processing.
        """
        alpha = img_array[:, :, 3]
        
        # Calculate edge complexity metrics
        edge_density = np.mean(edge_map > 50)
        fine_detail_density = np.mean(edge_map > 150)
        transparency_variance = np.var(alpha[alpha > 0])
        
        # Material classification
        if fine_detail_density > 0.3:
            return "hair_fur"  # High fine detail density
        elif transparency_variance > 2000 and edge_density < 0.1:
            return "glass"  # High transparency variance, low edge density
        elif edge_density > 0.2:
            return "complex"  # High edge density
        else:
            return "standard"  # Standard material
    
    def _professional_unmatte(self, img_array: np.ndarray, config: ProcessingConfig, edge_map: np.ndarray) -> np.ndarray:
        """
        Advanced unmatte processing using color analysis and gradient information.
        Mimics Photoshop's sophisticated color unmixing.
        """
        result = img_array.copy()
        alpha = img_array[:, :, 3].astype(np.float32) / 255.0
        
        # Create precise edge mask using gradient information
        edge_mask = edge_map > 30  # Focus on significant edges only
        
        # Process each color channel with advanced color unmixing
        for c in range(3):  # RGB channels
            channel = result[:, :, c].astype(np.float32)
            
            if config.matte_preset.value == "White Matte":
                # Advanced white matte removal with color analysis
                contaminated_mask = edge_mask & (channel > 180) & (alpha < 0.95)
                if np.any(contaminated_mask):
                    # Use color unmixing formula: C = (Observed - BG*(1-α)) / α
                    clean_color = (channel[contaminated_mask] - 255 * (1 - alpha[contaminated_mask])) / (alpha[contaminated_mask] + 1e-8)
                    clean_color = np.clip(clean_color, 0, 255)
                    
                    # Smooth transition to avoid artifacts
                    blend_factor = np.minimum(1.0, (255 - channel[contaminated_mask]) / 75.0)
                    channel[contaminated_mask] = channel[contaminated_mask] * (1 - blend_factor) + clean_color * blend_factor
            
            elif config.matte_preset.value == "Black Matte":
                # Advanced black matte removal
                contaminated_mask = edge_mask & (channel < 75) & (alpha < 0.95)
                if np.any(contaminated_mask):
                    clean_color = (channel[contaminated_mask] - 0 * (1 - alpha[contaminated_mask])) / (alpha[contaminated_mask] + 1e-8)
                    clean_color = np.clip(clean_color, 0, 255)
                    
                    blend_factor = np.minimum(1.0, channel[contaminated_mask] / 75.0)
                    channel[contaminated_mask] = channel[contaminated_mask] * (1 - blend_factor) + clean_color * blend_factor
            
            result[:, :, c] = np.clip(channel, 0, 255).astype(np.uint8)
        
        return result
    
    def _alpha_pyramid_processing(self, img_array: np.ndarray, config: ProcessingConfig) -> np.ndarray:
        """
        Advanced alpha channel processing using pyramid techniques.
        Handles complex transparency scenarios like glass and translucent materials.
        """
        result = img_array.copy()
        alpha = result[:, :, 3].astype(np.float32)
        
        # Create Gaussian pyramid for multi-scale processing
        pyramid_levels = 4
        pyramid = [alpha]
        
        for i in range(pyramid_levels - 1):
            alpha_down = cv2.pyrDown(pyramid[-1])
            pyramid.append(alpha_down)
        
        # Process each pyramid level
        for i, level in enumerate(pyramid):
            scale_factor = 2 ** i
            
            # Apply smoothing based on scale
            if config.smooth > 0:
                smooth_strength = max(1, config.smooth - i)
                for _ in range(smooth_strength):
                    level = cv2.GaussianBlur(level, (3, 3), 0.7)
            
            # Apply feathering
            if config.feather > 0:
                feather_kernel = max(3, config.feather - i * 2)
                if feather_kernel > 0:
                    level = cv2.GaussianBlur(level, (feather_kernel, feather_kernel), feather_kernel * 0.5)
            
            pyramid[i] = level
        
        # Reconstruct alpha from pyramid
        processed_alpha = pyramid[-1]
        for i in range(len(pyramid) - 2, -1, -1):
            processed_alpha = cv2.pyrUp(processed_alpha)
            # Ensure size matches
            if processed_alpha.shape != pyramid[i].shape:
                processed_alpha = cv2.resize(processed_alpha, (pyramid[i].shape[1], pyramid[i].shape[0]))
            # Blend with original level
            processed_alpha = processed_alpha * 0.7 + pyramid[i] * 0.3
        
        # Apply contrast and edge shifting
        if config.contrast != 1.0:
            processed_alpha = np.clip(((processed_alpha / 255.0 - 0.5) * config.contrast + 0.5) * 255.0, 0, 255)
        
        if config.shift_edge != 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            if config.shift_edge > 0:
                for _ in range(config.shift_edge):
                    processed_alpha = cv2.dilate(processed_alpha, kernel, iterations=1)
            else:
                for _ in range(abs(config.shift_edge)):
                    processed_alpha = cv2.erode(processed_alpha, kernel, iterations=1)
        
        result[:, :, 3] = processed_alpha.astype(np.uint8)
        return result
    
    def _material_specific_enhancement(self, img_array: np.ndarray, material_type: str, config: ProcessingConfig) -> np.ndarray:
        """
        Apply material-specific enhancements based on detected characteristics.
        """
        if material_type == "hair_fur":
            return self._enhance_hair_fur(img_array, config)
        elif material_type == "glass":
            return self._enhance_glass(img_array, config)
        elif material_type == "complex":
            return self._enhance_complex_edges(img_array, config)
        else:
            return img_array
    
    def _enhance_hair_fur(self, img_array: np.ndarray, config: ProcessingConfig) -> np.ndarray:
        """Specialized processing for hair and fur materials."""
        result = img_array.copy()
        alpha = result[:, :, 3].astype(np.float32)
        
        # Use anisotropic diffusion to preserve fine details while smoothing
        # This maintains hair strands while reducing noise
        alpha_smooth = cv2.bilateralFilter(alpha.astype(np.uint8), 9, 75, 75).astype(np.float32)
        
        # Blend based on local variance (high variance = keep original, low variance = use smooth)
        local_variance = cv2.Laplacian(alpha.astype(np.uint8), cv2.CV_64F)
        variance_factor = np.abs(local_variance) / (np.max(np.abs(local_variance)) + 1e-8)
        
        result[:, :, 3] = (alpha * variance_factor + alpha_smooth * (1 - variance_factor)).astype(np.uint8)
        return result
    
    def _enhance_glass(self, img_array: np.ndarray, config: ProcessingConfig) -> np.ndarray:
        """Specialized processing for glass and transparent materials."""
        result = img_array.copy()
        alpha = result[:, :, 3].astype(np.float32)
        
        # Preserve transparency gradients while cleaning edges
        grad_x = cv2.Sobel(alpha, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(alpha, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Smooth low-gradient areas more aggressively
        smooth_mask = gradient_magnitude < np.percentile(gradient_magnitude, 70)
        alpha_smooth = cv2.GaussianBlur(alpha, (5, 5), 1.5)
        
        alpha[smooth_mask] = alpha_smooth[smooth_mask]
        result[:, :, 3] = alpha.astype(np.uint8)
        
        return result
    
    def _enhance_complex_edges(self, img_array: np.ndarray, config: ProcessingConfig) -> np.ndarray:
        """Processing for complex edge scenarios."""
        result = img_array.copy()
        alpha = result[:, :, 3]
        
        # Use morphological opening to clean up complex edges
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        alpha_opened = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, kernel)
        alpha_closed = cv2.morphologyEx(alpha_opened, cv2.MORPH_CLOSE, kernel)
        
        result[:, :, 3] = alpha_closed
        return result
    
    def _surgical_fringe_removal(self, img_array: np.ndarray, config: ProcessingConfig, edge_map: np.ndarray) -> np.ndarray:
        """
        Surgical fringe removal - only processes areas that actually have fringe problems.
        Mimics Photoshop's selective processing approach.
        """
        result = img_array.copy()
        alpha = img_array[:, :, 3]
        height, width = img_array.shape[:2]
        
        # Identify problematic fringe areas using color analysis
        fringe_mask = self._detect_fringe_areas(img_array, edge_map)
        
        if not np.any(fringe_mask):
            return result  # No fringe detected, return original
        
        # Process each color channel only in problematic areas
        for c in range(3):
            channel = result[:, :, c].astype(np.float32)
            
            # Get fringe pixels
            fringe_pixels = np.where(fringe_mask)
            
            for i in range(len(fringe_pixels[0])):
                y, x = fringe_pixels[0][i], fringe_pixels[1][i]
                
                # Smart neighborhood analysis
                corrected_color = self._analyze_neighborhood_color(
                    img_array, x, y, config.fringe_band, alpha[y, x]
                )
                
                if corrected_color is not None:
                    # Apply correction with strength control
                    strength = config.fringe_strength / 3.0
                    current_color = channel[y, x]
                    new_color = current_color * (1 - strength) + corrected_color[c] * strength
                    channel[y, x] = new_color
            
            result[:, :, c] = np.clip(channel, 0, 255).astype(np.uint8)
        
        return result
    
    def _detect_fringe_areas(self, img_array: np.ndarray, edge_map: np.ndarray) -> np.ndarray:
        """
        Intelligently detect areas that actually have fringe problems.
        """
        alpha = img_array[:, :, 3]
        
        # Semi-transparent edge areas
        semi_transparent = (alpha > 10) & (alpha < 240)
        
        # Areas with significant color variation in semi-transparent regions
        color_variance = np.var(img_array[:, :, :3].astype(np.float32), axis=2)
        high_variance = color_variance > np.percentile(color_variance[semi_transparent], 80)
        
        # Areas with unusual color characteristics (potential contamination)
        unusual_color = self._detect_unusual_colors(img_array)
        
        # Combine criteria
        fringe_mask = semi_transparent & (high_variance | unusual_color) & (edge_map > 40)
        
        # Clean up mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fringe_mask = cv2.morphologyEx(fringe_mask.astype(np.uint8), cv2.MORPH_OPEN, kernel)
        
        return fringe_mask.astype(bool)
    
    def _detect_unusual_colors(self, img_array: np.ndarray) -> np.ndarray:
        """Detect pixels with unusual color characteristics that might indicate contamination."""
        rgb = img_array[:, :, :3].astype(np.float32)
        alpha = img_array[:, :, 3].astype(np.float32) / 255.0
        
        # Detect overly bright or dark pixels in semi-transparent areas
        brightness = np.mean(rgb, axis=2)
        semi_transparent = (alpha > 0.1) & (alpha < 0.9)
        
        unusual_bright = semi_transparent & (brightness > 220)
        unusual_dark = semi_transparent & (brightness < 35)
        
        return unusual_bright | unusual_dark
    
    def _analyze_neighborhood_color(self, img_array: np.ndarray, x: int, y: int, 
                                   radius: int, pixel_alpha: int) -> Optional[np.ndarray]:
        """
        Analyze neighborhood to determine the correct color for a pixel.
        Uses sophisticated weighted averaging based on alpha values and distance.
        """
        height, width = img_array.shape[:2]
        
        # Define neighborhood bounds
        y_min, y_max = max(0, y - radius), min(height, y + radius + 1)
        x_min, x_max = max(0, x - radius), min(width, x + radius + 1)
        
        # Extract neighborhood
        neighborhood = img_array[y_min:y_max, x_min:x_max]
        neighbor_alpha = neighborhood[:, :, 3]
        neighbor_rgb = neighborhood[:, :, :3]
        
        # Find solid pixels (high alpha) in neighborhood
        solid_mask = neighbor_alpha > 200
        
        if not np.any(solid_mask):
            return None
        
        # Calculate weights based on alpha and distance
        center_y, center_x = y - y_min, x - x_min
        y_coords, x_coords = np.meshgrid(range(neighborhood.shape[0]), range(neighborhood.shape[1]), indexing='ij')
        distances = np.sqrt((y_coords - center_y)**2 + (x_coords - center_x)**2)
        
        # Combine alpha and distance weights
        alpha_weights = neighbor_alpha.astype(np.float32) / 255.0
        distance_weights = np.exp(-distances / radius)  # Gaussian falloff
        combined_weights = alpha_weights * distance_weights * solid_mask
        
        if np.sum(combined_weights) == 0:
            return None
        
        # Weighted average of RGB values
        weighted_rgb = np.zeros(3)
        for c in range(3):
            weighted_rgb[c] = np.average(neighbor_rgb[:, :, c], weights=combined_weights)
        
        return weighted_rgb
    
    def _professional_edge_refinement(self, img_array: np.ndarray, config: ProcessingConfig) -> np.ndarray:
        """
        Final professional edge refinement using advanced techniques.
        Mimics Photoshop's "Use Legacy Contrast" re-hardening.
        """
        result = img_array.copy()
        alpha = result[:, :, 3].astype(np.float32) / 255.0
        
        # Re-harden edges using contrast enhancement
        # This mimics PS's "Use Legacy Contrast" option
        enhanced_alpha = ((alpha - 0.5) * 1.5 + 0.5)  # Increase contrast
        enhanced_alpha = np.clip(enhanced_alpha, 0, 1)
        
        # Apply edge-preserving smoothing
        alpha_8bit = (enhanced_alpha * 255).astype(np.uint8)
        refined_alpha = cv2.bilateralFilter(alpha_8bit, 5, 50, 50)
        
        # Final cleanup with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        refined_alpha = cv2.morphologyEx(refined_alpha, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        result[:, :, 3] = refined_alpha
        return result