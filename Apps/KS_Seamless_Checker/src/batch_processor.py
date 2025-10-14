import os
import cv2
from .image_checker import ImageChecker
import csv

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
                r = self.process_file(img_path)
                if r:
                    results.append(r)
        return results

    def process_file(self, file_path):
        """Process a single image file and save a tiled preview. Returns a result dict or None."""
        if not os.path.isfile(file_path):
            return None
        if not any(file_path.lower().endswith(ext) for ext in self.supported_formats):
            return None
        img = cv2.imread(file_path)
        if img is None:
            return None
        seamless = self.checker.is_seamless(img)
        preview = self.checker.create_tiled_preview(img)
        filename = os.path.basename(file_path)
        os.makedirs(self.preview_folder, exist_ok=True)
        preview_path = os.path.join(self.preview_folder, f"tiled_{filename}")
        try:
            preview.save(preview_path)
        except Exception:
            preview_path = ''
        return {
            'file': filename,
            'seamless': seamless,
            'preview_path': preview_path
        }

    def save_results_csv(self, results, csv_path=None):
        """Save results (list of dicts) to a CSV file. If csv_path is None, saves to preview_folder/results.csv."""
        if csv_path is None:
            csv_path = os.path.join(self.preview_folder, 'results.csv')
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['file', 'seamless', 'preview_path'])
            for r in results:
                writer.writerow([r.get('file'), r.get('seamless'), r.get('preview_path')])
        return csv_path