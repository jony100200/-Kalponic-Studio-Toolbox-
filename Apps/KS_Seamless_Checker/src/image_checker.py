import cv2
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim
import os
from skimage import color
from scipy import signal

try:
    from .ai_seam_checker import AISeamChecker
except ImportError:
    # Handle case when imported directly (not as part of package)
    from ai_seam_checker import AISeamChecker

class ImageChecker:
    """
    Advanced seamless texture detection using research-based methodology.

    Implements the TexTile approach with multi-scale analysis, multiple metrics,
    and optional AI classification for highly accurate seamless texture detection.
    Supports direction-specific classification: fully seamless, horizontal-only,
    vertical-only, or not seamless.
    """

    def __init__(self, threshold=10, use_ai=False, model_path=None):
        """
        Initialize the ImageChecker with configuration parameters.

        Args:
            threshold (float): Seamlessness threshold (lower = more seamless)
            use_ai (bool): Whether to use AI classification for hybrid approach
            model_path (str): Path to AI model file (if use_ai=True)
        """
        self.threshold = threshold
        self.use_ai = use_ai
        self.ai_checker = AISeamChecker(model_path) if use_ai else None

    def is_seamless(self, img, img_path=None):
        """
        Advanced seamless detection using research-based multi-scale analysis:
        - Lab color space conversion for perceptual uniformity
        - 2x2 tiled composite analysis (TexTile approach)
        - Multi-scale analysis (original, 1/2, 1/4 resolution)
        - MAD/RMSE, SSIM, and cross-correlation metrics
        - Canny edge detection for structural analysis
        - Optional EfficientNet-B0 AI classification
        """
        if img is None or img.size == 0:
            return False

        # Get traditional method result
        traditional_result = self._get_traditional_result(img)

        # Get AI result if available
        ai_result = None
        if self.use_ai and self.ai_checker and img_path:
            ai_result = self.ai_checker.is_seamless_ai(img_path)

        # Combine results for ultra-precise detection
        if ai_result is not None:
            # Both methods agree - high confidence
            if traditional_result == ai_result:
                return ai_result
            else:
                # Methods disagree - use traditional method as it's more robust
                # (AI might be overfitted or not trained well)
                return traditional_result
        else:
            # Only traditional method available
            return traditional_result

    def _get_traditional_result(self, img):
        """Get detailed results from traditional research-based method."""
        # Convert to Lab color space for perceptually uniform analysis
        lab_img = self._convert_to_lab(img)

        # Multi-scale analysis with image pyramid
        scales = [1.0, 0.5, 0.25]  # Original, half, quarter resolution

        horizontal_scores = []
        vertical_scores = []

        for scale in scales:
            scaled_img = self._scale_image(lab_img, scale)
            h_score, v_score = self._analyze_tileability_detailed(scaled_img)
            horizontal_scores.append(h_score)
            vertical_scores.append(v_score)

        # Combine multi-scale scores (weighted towards full resolution)
        weights = [0.5, 0.3, 0.2]

        combined_horizontal = sum(s * w for s, w in zip(horizontal_scores, weights))
        combined_vertical = sum(s * w for s, w in zip(vertical_scores, weights))

        # Determine seamless status for each direction
        horizontal_seamless = combined_horizontal < self.threshold
        vertical_seamless = combined_vertical < self.threshold

        # Smart classification: if one direction tiles perfectly but the other doesn't,
        # it might be a uniform pattern (stripes) that shouldn't be "fully seamless"
        perfect_tile_threshold = 5.0  # Very low score indicates near-perfect tiling

        if horizontal_seamless and vertical_seamless:
            # Both directions are seamless - check if it's truly varied or just uniform stripes
            if combined_vertical < perfect_tile_threshold and combined_horizontal > perfect_tile_threshold:
                # Vertical tiles perfectly, horizontal has variation - likely horizontal stripes
                seamless_type = 'horizontal_only'
                is_seamless = False
            elif combined_horizontal < perfect_tile_threshold and combined_vertical > perfect_tile_threshold:
                # Horizontal tiles perfectly, vertical has variation - likely vertical stripes
                seamless_type = 'vertical_only'
                is_seamless = False
            else:
                # Both have reasonable variation - truly fully seamless
                seamless_type = 'fully_seamless'
                is_seamless = True
        elif horizontal_seamless and not vertical_seamless:
            seamless_type = 'horizontal_only'
            is_seamless = False
        elif not horizontal_seamless and vertical_seamless:
            seamless_type = 'vertical_only'
            is_seamless = False
        else:
            seamless_type = 'not_seamless'
            is_seamless = False

    def get_seamless_score(self, img, img_path=None):
        """Get the actual seamless score from traditional method (for debugging)."""
        if img is None or img.size == 0:
            return float('inf')

        # Get AI result if available
        ai_result = None
        if self.use_ai and self.ai_checker and img_path:
            ai_result = self.ai_checker.is_seamless_ai(img_path)

        # Always return traditional score for debugging, but note AI result
        lab_img = self._convert_to_lab(img)

        # Multi-scale analysis with image pyramid
        scales = [1.0, 0.5, 0.25]  # Original, half, quarter resolution
        seamless_scores = []

        for scale in scales:
            scaled_img = self._scale_image(lab_img, scale)
            score = self._analyze_tileability(scaled_img)
            seamless_scores.append(score)

        # Combine multi-scale scores (weighted towards full resolution)
        weights = [0.5, 0.3, 0.2]
        combined_score = sum(s * w for s, w in zip(seamless_scores, weights))

        return combined_score

    def _convert_to_lab(self, img):
        """Convert image to Lab color space for perceptually uniform analysis."""
        # Convert BGR to RGB first (PIL uses RGB, OpenCV uses BGR)
        if isinstance(img, Image.Image):
            img_array = np.array(img)
            if img_array.shape[2] == 4:  # RGBA
                img_array = img_array[:, :, :3]  # Remove alpha
        else:
            img_array = img

        # Convert to RGB if needed
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            rgb_img = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
        else:
            rgb_img = img_array

        # Convert to Lab
        lab_img = color.rgb2lab(rgb_img)
        return lab_img

    def _scale_image(self, img, scale):
        """Scale image by given factor."""
        if scale == 1.0:
            return img
        h, w = img.shape[:2]
        new_h, new_w = int(h * scale), int(w * scale)
        scaled = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        return scaled

    def _analyze_tileability(self, lab_img):
        """Analyze tileability using 2x2 composite and multiple metrics."""
        # Create 2x2 tiled composite (TexTile approach)
        tiled_composite = self._create_tiled_composite(lab_img)

        # Analyze seams in the composite
        vertical_seam_score = self._analyze_composite_seam(tiled_composite, vertical=True)
        horizontal_seam_score = self._analyze_composite_seam(tiled_composite, vertical=False)

        # Also analyze direct edge comparison for additional insight
        direct_vertical = self._analyze_direct_edges(lab_img, vertical=True)
        direct_horizontal = self._analyze_direct_edges(lab_img, vertical=False)

        # Combine scores with weights
        composite_weight = 0.6  # More weight on composite analysis
        direct_weight = 0.4

        combined_vertical = (vertical_seam_score * composite_weight +
                           direct_vertical * direct_weight)
        combined_horizontal = (horizontal_seam_score * composite_weight +
                             direct_horizontal * direct_weight)

        # Overall tileability score
        overall_score = (combined_vertical + combined_horizontal) / 2
        return overall_score

    def _analyze_tileability_detailed(self, lab_img):
        """Analyze tileability and return separate horizontal and vertical scores."""
        # Create 2x2 tiled composite (TexTile approach)
        tiled_composite = self._create_tiled_composite(lab_img)

        # Analyze seams in the composite
        vertical_seam_score = self._analyze_composite_seam(tiled_composite, vertical=True)
        horizontal_seam_score = self._analyze_composite_seam(tiled_composite, vertical=False)

        # Also analyze direct edge comparison for additional insight
        direct_vertical = self._analyze_direct_edges(lab_img, vertical=True)
        direct_horizontal = self._analyze_direct_edges(lab_img, vertical=False)

        # Combine scores with weights
        composite_weight = 0.6  # More weight on composite analysis
        direct_weight = 0.4

        combined_vertical = (vertical_seam_score * composite_weight +
                           direct_vertical * direct_weight)
        combined_horizontal = (horizontal_seam_score * composite_weight +
                             direct_horizontal * direct_weight)

        # Additional check: ensure the image has meaningful variation in both directions
        # If an image is uniform in one direction (like stripes), it shouldn't be considered seamless
        variation_threshold = 5.0  # Minimum variation score to be considered "meaningful"

        h_variation = self._calculate_direction_variation(lab_img, vertical=False)  # Horizontal variation (variation across rows)
        v_variation = self._calculate_direction_variation(lab_img, vertical=True)   # Vertical variation (variation across columns)

        # Penalize scores if variation is too low in either direction (uniform patterns like stripes)
        if h_variation < variation_threshold:
            combined_horizontal += 50.0  # Heavy penalty for uniform horizontal patterns
        if v_variation < variation_threshold:
            combined_vertical += 50.0   # Heavy penalty for uniform vertical patterns

        return combined_horizontal, combined_vertical

    def get_detailed_seamless_info(self, img, img_path=None):
        """Get detailed seamless information including direction-specific results."""
        if img is None or img.size == 0:
            return {
                'is_seamless': False,
                'seamless_type': 'invalid',
                'horizontal_seamless': False,
                'vertical_seamless': False,
                'horizontal_score': float('inf'),
                'vertical_score': float('inf'),
                'ai_used': False
            }

        # Get traditional detailed results
        lab_img = self._convert_to_lab(img)

        # Multi-scale analysis with image pyramid
        scales = [1.0, 0.5, 0.25]  # Original, half, quarter resolution

        horizontal_scores = []
        vertical_scores = []

        for scale in scales:
            scaled_img = self._scale_image(lab_img, scale)
            h_score, v_score = self._analyze_tileability_detailed(scaled_img)
            horizontal_scores.append(h_score)
            vertical_scores.append(v_score)

        # Combine multi-scale scores (weighted towards full resolution)
        weights = [0.5, 0.3, 0.2]

        combined_horizontal = sum(s * w for s, w in zip(horizontal_scores, weights))
        combined_vertical = sum(s * w for s, w in zip(vertical_scores, weights))

        # Determine seamless status for each direction
        horizontal_seamless = combined_horizontal < self.threshold
        vertical_seamless = combined_vertical < self.threshold

        # Determine seamless type
        if horizontal_seamless and vertical_seamless:
            seamless_type = 'fully_seamless'
            is_seamless = True
        elif horizontal_seamless and not vertical_seamless:
            seamless_type = 'horizontal_only'
            is_seamless = False
        elif not horizontal_seamless and vertical_seamless:
            seamless_type = 'vertical_only'
            is_seamless = False
        else:
            seamless_type = 'not_seamless'
            is_seamless = False

        # Check AI if available
        ai_used = False
        if self.use_ai and self.ai_checker and img_path:
            ai_result = self.ai_checker.is_seamless_ai(img_path)
            if ai_result is not None:
                ai_used = True
                # If AI disagrees with traditional method, prefer traditional for detailed analysis
                # But for binary seamless check, use hybrid logic

        return {
            'is_seamless': is_seamless,
            'seamless_type': seamless_type,
            'horizontal_seamless': horizontal_seamless,
            'vertical_seamless': vertical_seamless,
            'horizontal_score': combined_horizontal,
            'vertical_score': combined_vertical,
            'ai_used': ai_used
        }

    def _create_tiled_composite(self, img):
        """Create 2x2 tiled composite to expose internal seams."""
        h, w = img.shape[:2]
        composite = np.zeros((2 * h, 2 * w, img.shape[2]), dtype=img.dtype)

        # Create 2x2 grid: A B
        #                   C D
        composite[0:h, 0:w] = img      # A
        composite[0:h, w:2*w] = img    # B
        composite[h:2*h, 0:w] = img    # C
        composite[h:2*h, w:2*w] = img  # D

        return composite

    def _analyze_composite_seam(self, composite, vertical=True):
        """Analyze seams in the 2x2 tiled composite."""
        h, w = composite.shape[:2]
        half_h, half_w = h // 2, w // 2

        if vertical:
            # Compare left and right halves along the vertical seam
            left_half = composite[:, :half_w]
            right_half = composite[:, half_w:]
            # Extract the seam region (middle column of overlap)
            seam_left = left_half[:, -10:]  # Last 10 columns of left
            seam_right = right_half[:, :10]  # First 10 columns of right
        else:
            # Compare top and bottom halves along the horizontal seam
            top_half = composite[:half_h, :]
            bottom_half = composite[half_h:, :]
            # Extract the seam region (middle row of overlap)
            seam_top = top_half[-10:, :]  # Last 10 rows of top
            seam_bottom = bottom_half[:10, :]  # First 10 rows of bottom

        edge1, edge2 = (seam_left, seam_right) if vertical else (seam_top, seam_bottom)

        # Multiple metrics for comprehensive analysis
        metrics = self._compute_seam_metrics(edge1, edge2)
        return metrics['combined_score']

    def _analyze_direct_edges(self, img, vertical=True):
        """Analyze direct edges (traditional approach) for comparison."""
        h, w = img.shape[:2]

        if vertical:
            # Compare left and right edges
            edge_width = min(32, w // 8)
            left_edge = img[:, :edge_width]
            right_edge = img[:, -edge_width:]
        else:
            # Compare top and bottom edges
            edge_height = min(32, h // 8)
            top_edge = img[:edge_height, :]
            bottom_edge = img[-edge_height:, :]

        edge1, edge2 = (left_edge, right_edge) if vertical else (top_edge, bottom_edge)

        # Use same metrics as composite analysis
        metrics = self._compute_seam_metrics(edge1, edge2)
        return metrics['combined_score']

    def _compute_seam_metrics(self, edge1, edge2):
        """Compute comprehensive seam metrics including MAD, SSIM, and cross-correlation."""
        # Normalize edges to 0-1 range for consistent analysis
        edge1_norm = edge1.astype(float) / 255.0 if edge1.dtype != float else edge1
        edge2_norm = edge2.astype(float) / 255.0 if edge2.dtype != float else edge2

        # Metric 1: Mean Absolute Difference (MAD)
        mad_score = np.mean(np.abs(edge1_norm - edge2_norm))

        # Metric 2: Root Mean Squared Error (RMSE)
        rmse_score = np.sqrt(np.mean((edge1_norm - edge2_norm) ** 2))

        # Metric 3: SSIM (Structural Similarity Index)
        try:
            if len(edge1.shape) == 3:  # Color image
                ssim_score = 1.0 - ssim(edge1_norm, edge2_norm,
                                       data_range=1.0, multichannel=True)
            else:  # Grayscale
                ssim_score = 1.0 - ssim(edge1_norm, edge2_norm,
                                       data_range=1.0, multichannel=False)
        except:
            ssim_score = 1.0  # If SSIM fails, assume not similar

        # Metric 4: Cross-correlation
        if len(edge1.shape) == 3:
            # For color images, compute correlation per channel and average
            corr_scores = []
            for c in range(edge1.shape[2]):
                corr = self._compute_cross_correlation(edge1_norm[:, :, c], edge2_norm[:, :, c])
                corr_scores.append(corr)
            cross_corr_score = 1.0 - np.mean(corr_scores)  # Convert to dissimilarity
        else:
            cross_corr_score = 1.0 - self._compute_cross_correlation(edge1_norm, edge2_norm)

        # Metric 5: Canny edge analysis
        canny_score = self._analyze_canny_edges(edge1, edge2)

        # Weighted combination of all metrics
        weights = {
            'mad': 0.2,
            'rmse': 0.2,
            'ssim': 0.3,
            'cross_corr': 0.15,
            'canny': 0.15
        }

        combined_score = (
            mad_score * weights['mad'] +
            rmse_score * weights['rmse'] +
            ssim_score * weights['ssim'] +
            cross_corr_score * weights['cross_corr'] +
            canny_score * weights['canny']
        )

        return {
            'mad': mad_score,
            'rmse': rmse_score,
            'ssim': ssim_score,
            'cross_corr': cross_corr_score,
            'canny': canny_score,
            'combined_score': combined_score
        }

    def _compute_cross_correlation(self, img1, img2):
        """Compute normalized cross-correlation between two images."""
        # Use scipy's correlate2d for 2D cross-correlation
        corr = signal.correlate2d(img1, img2, mode='valid')
        # Normalize by the geometric mean of the autocorrelations
        auto_corr1 = signal.correlate2d(img1, img1, mode='valid')
        auto_corr2 = signal.correlate2d(img2, img2, mode='valid')

        # Take the maximum correlation value
        max_corr = np.max(corr)
        norm_factor = np.sqrt(np.max(auto_corr1) * np.max(auto_corr2))

        if norm_factor > 0:
            normalized_corr = max_corr / norm_factor
        else:
            normalized_corr = 0.0

        # Clamp to [0, 1] range
        return np.clip(normalized_corr, 0.0, 1.0)

    def _analyze_canny_edges(self, edge1, edge2):
        """Analyze edge continuity using Canny edge detection."""
        # Convert to grayscale if needed
        if len(edge1.shape) == 3:
            gray1 = cv2.cvtColor((edge1 * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
            gray2 = cv2.cvtColor((edge2 * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        else:
            gray1 = (edge1 * 255).astype(np.uint8)
            gray2 = (edge2 * 255).astype(np.uint8)

        # Apply Canny edge detection
        edges1 = cv2.Canny(gray1, 50, 150)
        edges2 = cv2.Canny(gray2, 50, 150)

        # Count edge pixels
        edge_count1 = np.sum(edges1 > 0)
        edge_count2 = np.sum(edges2 > 0)

        # Compare edge patterns using XOR to find differences
        edge_diff = cv2.bitwise_xor(edges1, edges2)
        diff_count = np.sum(edge_diff > 0)

        # Calculate discontinuity score
        total_edge_pixels = edge_count1 + edge_count2
        if total_edge_pixels > 0:
            discontinuity_ratio = diff_count / total_edge_pixels
        else:
            discontinuity_ratio = 0.0

        return discontinuity_ratio

    def _calculate_direction_variation(self, lab_img, vertical=True):
        """Calculate variation/entropy in a specific direction to detect uniform patterns."""
        if lab_img.shape[2] == 3:  # Lab image
            gray = cv2.cvtColor((lab_img * (255.0/100.0)).astype(np.uint8), cv2.COLOR_LAB2RGB)
            gray = cv2.cvtColor(gray, cv2.COLOR_RGB2GRAY).astype(float) / 255.0
        else:
            gray = lab_img[:, :, 0] if lab_img.shape[2] > 0 else lab_img

        if vertical:
            # For vertical direction, check if columns are similar (low variation between columns)
            # Sample every 4th column to avoid noise
            cols_to_check = gray[:, ::4]  # Every 4th column
            if cols_to_check.shape[1] < 2:
                return 0.0

            # Calculate standard deviation across columns for each row
            col_std = np.std(cols_to_check, axis=1)  # Variation across columns
            avg_variation = np.mean(col_std)

            return avg_variation * 100.0  # Scale up
        else:
            # For horizontal direction, check if rows are similar (low variation between rows)
            # Sample every 4th row to avoid noise
            rows_to_check = gray[::4, :]  # Every 4th row
            if rows_to_check.shape[0] < 2:
                return 0.0

            # Calculate standard deviation across rows for each column
            row_std = np.std(rows_to_check, axis=0)  # Variation across rows
            avg_variation = np.mean(row_std)

            return avg_variation * 100.0  # Scale up

    def create_tiled_preview(self, img):
        """Create a 2x2 tiled preview with seam overlay visualization."""
        # Convert to BGR for OpenCV processing
        if isinstance(img, Image.Image):
            img_array = np.array(img)
            if img_array.shape[2] == 4:  # RGBA
                img_array = img_array[:, :, :3]  # Remove alpha
        else:
            img_array = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if len(img.shape) == 3 else img

        # Create 2x2 tiled composite
        h, w = img_array.shape[:2]
        tiled = np.zeros((2 * h, 2 * w, 3), dtype=np.uint8)

        tiled[0:h, 0:w] = img_array
        tiled[0:h, w:2*w] = img_array
        tiled[h:2*h, 0:w] = img_array
        tiled[h:2*h, w:2*w] = img_array

        # Analyze seams and add visual overlay
        lab_tiled = self._convert_to_lab(tiled)
        vertical_score = self._analyze_composite_seam(lab_tiled, vertical=True)
        horizontal_score = self._analyze_composite_seam(lab_tiled, vertical=False)

        # Add seam overlays if seams are detected (scores above threshold)
        seam_threshold = self.threshold * 0.8  # Slightly more sensitive for visualization

        if vertical_score > seam_threshold:
            # Draw vertical seam in red
            cv2.line(tiled, (w, 0), (w, 2*h), (0, 0, 255), 2)

        if horizontal_score > seam_threshold:
            # Draw horizontal seam in red
            cv2.line(tiled, (0, h), (2*w, h), (0, 0, 255), 2)

        return Image.fromarray(cv2.cvtColor(tiled, cv2.COLOR_BGR2RGB))