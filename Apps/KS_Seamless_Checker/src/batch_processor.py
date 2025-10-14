import os
import cv2
from .image_checker import ImageChecker

class BatchProcessor:
    def __init__(self, checker, supported_formats, preview_folder):
        self.checker = checker
        self.supported_formats = supported_formats
        self.preview_folder = preview_folder
        os.makedirs(self.preview_folder, exist_ok=True)

    def process_folder(self, folder_path):
        """Process all images in folder, return results and save previews."""
        results = []
        for file in os.listdir(folder_path):
            if any(file.lower().endswith(ext) for ext in self.supported_formats):
                img_path = os.path.join(folder_path, file)
                img = cv2.imread(img_path)
                if img is not None:
                    seamless = self.checker.is_seamless(img)
                    preview = self.checker.create_tiled_preview(img)
                    preview_path = os.path.join(self.preview_folder, f"tiled_{file}")
                    preview.save(preview_path)
                    results.append({
                        'file': file,
                        'seamless': seamless,
                        'preview_path': preview_path
                    })
        return results