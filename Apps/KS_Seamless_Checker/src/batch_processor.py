import os
import cv2
import csv
from io import BytesIO
from PIL import Image
# Add parent directory to sys.path for relative imports when run directly
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from .image_checker import ImageChecker

class BatchProcessor:
    def __init__(self, checker, supported_formats, preview_folder):
        self.checker = checker
        self.supported_formats = supported_formats
        # preview_folder kept for backward compatibility (CSV default location),
        # but we no longer write tiled previews to disk by default.
        self.preview_folder = preview_folder
        # preview_mode: 'memory' or 'disk' - default to memory
        self.preview_mode = 'memory'
        # thumbnail settings
        self.thumbnail_only_in_memory = True
        self.thumbnail_max_size = 256

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
        # Full tiled preview bytes
        buf = BytesIO()
        preview_bytes = b''
        try:
            preview.save(buf, format='PNG')
            preview_bytes = buf.getvalue()
        except Exception:
            preview_bytes = b''

        # Create a scaled thumbnail (PIL.Image) and bytes
        thumb_bytes = b''
        try:
            thumb = preview.copy()
            max_size = int(self.thumbnail_max_size) if self.thumbnail_max_size else 256
            thumb.thumbnail((max_size, max_size), Image.LANCZOS)
            tbuf = BytesIO()
            thumb.save(tbuf, format='PNG')
            thumb_bytes = tbuf.getvalue()
        except Exception:
            thumb_bytes = b''

        filename = os.path.basename(file_path)
        result = {
            'file': filename,
            'seamless': seamless,
            # full tiled preview bytes (may be omitted if thumbnail_only_in_memory=True)
            'preview_bytes': preview_bytes,
            # thumbnail bytes (smaller, used for table and optionally preview)
            'thumb_bytes': thumb_bytes,
            'preview_path': ''
        }

        # If configured to save previews to disk, write the PNG and include path
        if self.preview_mode == 'disk' and preview_bytes:
            try:
                os.makedirs(self.preview_folder, exist_ok=True)
                preview_path = os.path.join(self.preview_folder, f"tiled_{filename}")
                with open(preview_path, 'wb') as out_f:
                    out_f.write(preview_bytes)
                result['preview_path'] = preview_path
            except Exception:
                # Fail silently but keep preview_bytes in-memory
                result['preview_path'] = ''

        # If configured to only keep thumbnails in memory, drop the full preview bytes to save RAM
        if self.thumbnail_only_in_memory:
            result['preview_bytes'] = b''

        return result

    def save_results_csv(self, results, csv_path=None):
        """Save results (list of dicts) to a CSV file. If csv_path is None, saves to preview_folder/results.csv."""
        if csv_path is None:
            csv_path = os.path.join(self.preview_folder, 'results.csv')
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['file', 'seamless', 'preview_path'])
            for r in results:
                # preview_path may be empty since previews are in-memory; if so but thumbnail exists, mark as <in-memory>
                p = r.get('preview_path', '')
                if not p and r.get('thumb_bytes'):
                    p = '<in-memory>'
                writer.writerow([r.get('file'), r.get('seamless'), p])
        return csv_path