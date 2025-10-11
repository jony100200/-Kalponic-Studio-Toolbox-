import unittest
from unittest.mock import patch, MagicMock
from src.processor import ImageProcessor
from src.config import ProcessingConfig
from PIL import Image
import numpy as np

class TestImageProcessor(unittest.TestCase):

    @patch("src.processor.ImageProcessor._load_image")
    def test_process_image_iterations(self, mock_load_image):
        """Test that the processing pipeline runs the correct number of iterations."""
        # Mock input image
        mock_image = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        mock_load_image.return_value = mock_image

        # Mock configuration
        config = ProcessingConfig(process_iterations=3)

        # Spy on internal methods
        processor = ImageProcessor()
        processor._unmatte = MagicMock(return_value=np.array(mock_image))
        processor._refine_alpha = MagicMock(return_value=np.array(mock_image))
        processor._fix_fringe = MagicMock(return_value=np.array(mock_image))

        # Process image
        result = processor.process_image("dummy_path", config)

        # Verify the pipeline ran 3 times
        self.assertEqual(processor._unmatte.call_count, 3)
        self.assertEqual(processor._refine_alpha.call_count, 3)
        self.assertEqual(processor._fix_fringe.call_count, 3)
        self.assertIsNotNone(result)

if __name__ == "__main__":
    unittest.main()