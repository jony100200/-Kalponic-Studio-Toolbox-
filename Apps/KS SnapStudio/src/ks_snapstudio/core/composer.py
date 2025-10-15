"""
Background composition functionality for KS SnapStudio.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any, List
from pathlib import Path
import random
import logging

logger = logging.getLogger(__name__)


class BackgroundComposer:
    """Handles background generation and composition for previews."""

    def __init__(self):
        self._background_types = {
            'solid': self._create_solid_background,
            'gradient': self._create_gradient_background,
            'noise': self._create_noise_background,
            'pattern': self._create_pattern_background,
        }

        # Predefined color palettes
        self._color_palettes = {
            'neutral': [
                (240, 240, 240),  # Light gray
                (220, 220, 220),  # Medium light gray
                (180, 180, 180),  # Medium gray
                (100, 100, 100),  # Dark gray
                (250, 250, 250),  # Off-white
            ],
            'warm': [
                (255, 235, 205),  # Light cream
                (255, 218, 185),  # Peach
                (255, 192, 159),  # Light coral
                (255, 160, 122),  # Light salmon
                (255, 228, 196),  # Bisque
            ],
            'cool': [
                (240, 248, 255),  # Alice blue
                (224, 255, 255),  # Light cyan
                (209, 238, 238),  # Pale turquoise
                (176, 224, 230),  # Powder blue
                (240, 255, 255),  # Azure
            ],
            'dark': [
                (32, 32, 32),     # Dark gray
                (48, 48, 48),     # Medium dark gray
                (24, 24, 24),     # Very dark gray
                (16, 16, 16),     # Almost black
                (40, 40, 40),     # Charcoal
            ]
        }

    def compose_background(self, foreground: np.ndarray,
                          bg_type: str = 'random',
                          palette: str = 'random',
                          **kwargs) -> np.ndarray:
        """
        Compose a background for the foreground image.

        Args:
            foreground: Foreground image with alpha channel
            bg_type: Background type ('solid', 'gradient', 'noise', 'pattern', 'random')
            palette: Color palette ('neutral', 'warm', 'cool', 'dark', 'random')
            **kwargs: Additional parameters for background generation

        Returns:
            Composited image with background
        """
        height, width = foreground.shape[:2]

        # Select random types if requested
        if bg_type == 'random':
            bg_type = random.choice(list(self._background_types.keys()))

        if palette == 'random':
            palette = random.choice(list(self._color_palettes.keys()))

        # Generate background
        background = self._generate_background(bg_type, palette, width, height, **kwargs)

        # Composite with foreground
        result = self._composite_with_alpha(foreground, background)

        logger.info(f"Composed {bg_type} background with {palette} palette")
        return result

    def _generate_background(self, bg_type: str, palette: str,
                           width: int, height: int, **kwargs) -> np.ndarray:
        """Generate background of specified type."""
        if bg_type not in self._background_types:
            logger.warning(f"Unknown background type {bg_type}, using solid")
            bg_type = 'solid'

        generator = self._background_types[bg_type]
        return generator(palette, width, height, **kwargs)

    def _create_solid_background(self, palette: str, width: int, height: int, **kwargs) -> np.ndarray:
        """Create a solid color background."""
        colors = self._color_palettes.get(palette, self._color_palettes['neutral'])
        color = random.choice(colors)
        return np.full((height, width, 3), color, dtype=np.uint8)

    def _create_gradient_background(self, palette: str, width: int, height: int,
                                  direction: str = 'random', **kwargs) -> np.ndarray:
        """Create a gradient background."""
        colors = self._color_palettes.get(palette, self._color_palettes['neutral'])

        # Select two colors
        color1, color2 = random.sample(colors, 2)

        # Random direction if not specified
        if direction == 'random':
            direction = random.choice(['horizontal', 'vertical', 'diagonal'])

        background = np.zeros((height, width, 3), dtype=np.uint8)

        if direction == 'horizontal':
            for x in range(width):
                ratio = x / width
                color = self._interpolate_color(color1, color2, ratio)
                background[:, x] = color
        elif direction == 'vertical':
            for y in range(height):
                ratio = y / height
                color = self._interpolate_color(color1, color2, ratio)
                background[y, :] = color
        else:  # diagonal
            for y in range(height):
                for x in range(width):
                    ratio = (x + y) / (width + height)
                    color = self._interpolate_color(color1, color2, ratio)
                    background[y, x] = color

        return background

    def _create_noise_background(self, palette: str, width: int, height: int,
                               intensity: float = 0.3, **kwargs) -> np.ndarray:
        """Create a noise-based background."""
        colors = self._color_palettes.get(palette, self._color_palettes['neutral'])
        base_color = random.choice(colors)

        # Create base background
        background = np.full((height, width, 3), base_color, dtype=np.uint8)

        # Add noise
        noise = np.random.randint(-50, 50, (height, width, 3), dtype=np.int16)
        background = np.clip(background.astype(np.int16) + (noise * intensity), 0, 255).astype(np.uint8)

        return background

    def _create_pattern_background(self, palette: str, width: int, height: int,
                                 pattern: str = 'random', **kwargs) -> np.ndarray:
        """Create a patterned background."""
        colors = self._color_palettes.get(palette, self._color_palettes['neutral'])
        color1, color2 = random.sample(colors, 2)

        if pattern == 'random':
            pattern = random.choice(['checkerboard', 'stripes', 'dots'])

        background = np.full((height, width, 3), color1, dtype=np.uint8)

        if pattern == 'checkerboard':
            square_size = random.randint(20, 50)
            for y in range(0, height, square_size):
                for x in range(0, width, square_size):
                    if (x // square_size + y // square_size) % 2 == 1:
                        background[y:y+square_size, x:x+square_size] = color2

        elif pattern == 'stripes':
            stripe_width = random.randint(10, 30)
            for y in range(0, height, stripe_width * 2):
                background[y:y+stripe_width, :] = color2

        elif pattern == 'dots':
            dot_size = random.randint(5, 15)
            spacing = dot_size * 3
            for y in range(0, height, spacing):
                for x in range(0, width, spacing):
                    cv2.circle(background, (x, y), dot_size, color2, -1)

        return background

    def _interpolate_color(self, color1: Tuple[int, int, int],
                          color2: Tuple[int, int, int],
                          ratio: float) -> Tuple[int, int, int]:
        """Interpolate between two colors."""
        return tuple(
            int(c1 + (c2 - c1) * ratio)
            for c1, c2 in zip(color1, color2)
        )

    def _composite_with_alpha(self, foreground: np.ndarray, background: np.ndarray) -> np.ndarray:
        """Composite foreground with alpha over background."""
        # Ensure foreground has alpha channel
        if foreground.shape[2] == 3:
            # Add alpha channel if missing
            alpha = np.full(foreground.shape[:2], 255, dtype=np.uint8)
            foreground = np.dstack([foreground, alpha])

        # Normalize alpha to 0-1
        alpha = foreground[:, :, 3].astype(np.float32) / 255.0
        alpha = np.expand_dims(alpha, axis=2)

        # Composite
        result = (foreground[:, :, :3] * alpha + background * (1 - alpha)).astype(np.uint8)

        return result

    def get_available_palettes(self) -> List[str]:
        """Get list of available color palettes."""
        return list(self._color_palettes.keys())

    def get_available_backgrounds(self) -> List[str]:
        """Get list of available background types."""
        return list(self._background_types.keys())

    def add_custom_palette(self, name: str, colors: List[Tuple[int, int, int]]):
        """Add a custom color palette."""
        self._color_palettes[name] = colors
        logger.info(f"Added custom palette '{name}' with {len(colors)} colors")</content>
<parameter name="filePath">E:\__Kalponic Studio Repositories\-Kalponic-Studio-Toolbox-\Apps\KS SnapStudio\src\ks_snapstudio\core\composer.py