"""
⬇️ Model Downloader for KS MetaMaker
===================================
Downloads AI models from Hugging Face and Ultralytics
"""

import requests
import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional, Callable
from urllib.parse import urlparse
import time

logger = logging.getLogger(__name__)


class ModelDownloader:
    """Downloads AI models with progress tracking and verification"""

    def __init__(self, models_dir: Path, timeout: int = 300):
        self.models_dir = models_dir
        self.timeout = timeout
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def download_model(self, model_name: str, url: str,
                      progress_callback: Optional[Callable] = None) -> bool:
        """
        Download a model from the given URL

        Args:
            model_name: Name/key for the model (e.g., 'tagging', 'detection')
            url: Download URL
            progress_callback: Optional callback for progress updates

        Returns:
            True if download successful, False otherwise
        """
        try:
            # Determine filename from URL
            parsed_url = urlparse(url)
            filename = Path(parsed_url.path).name
            if not filename:
                filename = f"{model_name}.bin"

            filepath = self.models_dir / filename

            # Check if file already exists
            if filepath.exists():
                logger.info(f"Model {model_name} already exists at {filepath}")
                if progress_callback:
                    progress_callback(f"Model {model_name} already downloaded", 100)
                return True

            logger.info(f"Downloading {model_name} from {url}")

            # Start download
            response = requests.get(url, stream=True, timeout=self.timeout)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        if progress_callback and total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            progress_callback(f"Downloading {model_name}...", progress)

            logger.info(f"Successfully downloaded {model_name} to {filepath}")

            # Verify download
            if self._verify_download(filepath, total_size):
                if progress_callback:
                    progress_callback(f"Downloaded {model_name} successfully", 100)
                return True
            else:
                logger.error(f"Download verification failed for {model_name}")
                filepath.unlink()  # Delete corrupted file
                return False

        except Exception as e:
            logger.error(f"Failed to download {model_name}: {e}")
            if progress_callback:
                progress_callback(f"Failed to download {model_name}: {e}", 0)
            return False

    def download_all_models(self, recommendations: Dict[str, str],
                           progress_callback: Optional[Callable] = None) -> Dict[str, bool]:
        """
        Download all recommended models

        Args:
            recommendations: Dict mapping model types to download URLs
            progress_callback: Optional callback for overall progress

        Returns:
            Dict mapping model types to success status
        """
        results = {}
        total_models = len(recommendations)

        for i, (model_type, url) in enumerate(recommendations.items()):
            if progress_callback:
                progress_callback(f"Downloading {model_type} ({i+1}/{total_models})...", 0)

            success = self.download_model(model_type, url, progress_callback)
            results[model_type] = success

            if not success:
                logger.warning(f"Failed to download {model_type}")

        return results

    def _verify_download(self, filepath: Path, expected_size: int) -> bool:
        """Verify downloaded file integrity"""
        try:
            actual_size = filepath.stat().st_size
            if expected_size > 0 and actual_size != expected_size:
                logger.warning(f"Size mismatch: expected {expected_size}, got {actual_size}")
                return False
            return True
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False

    def get_downloaded_models(self) -> Dict[str, Path]:
        """Get list of downloaded model files"""
        models = {}
        if self.models_dir.exists():
            for file_path in self.models_dir.iterdir():
                if file_path.is_file():
                    # Try to determine model type from filename
                    filename = file_path.name.lower()
                    if 'clip' in filename or 'siglip' in filename or 'eva' in filename:
                        models['tagging'] = file_path
                    elif 'yolo' in filename:
                        models['detection'] = file_path
                    elif 'blip' in filename:
                        models['captioning'] = file_path
        return models

    def cleanup_failed_downloads(self) -> None:
        """Remove incomplete/failed downloads"""
        if self.models_dir.exists():
            for file_path in self.models_dir.iterdir():
                if file_path.is_file() and file_path.stat().st_size == 0:
                    file_path.unlink()
                    logger.info(f"Removed empty file: {file_path}")


class HuggingFaceDownloader(ModelDownloader):
    """Specialized downloader for Hugging Face models"""

    def __init__(self, models_dir: Path, timeout: int = 300, use_fast: bool = True):
        super().__init__(models_dir, timeout)
        self.use_fast = use_fast

    def download_hf_model(self, repo_id: str, filename: str = "pytorch_model.bin",
                         progress_callback: Optional[Callable] = None) -> bool:
        """
        Download a model from Hugging Face Hub

        Args:
            repo_id: Hugging Face repository ID (e.g., 'openai/clip-vit-base-patch32')
            filename: Filename to download
            progress_callback: Progress callback

        Returns:
            True if successful
        """
        if self.use_fast:
            url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"
        else:
            url = f"https://huggingface.co/{repo_id}/raw/main/{filename}"

        return self.download_model(f"{repo_id}/{filename}", url, progress_callback)


class UltralyticsDownloader(ModelDownloader):
    """Specialized downloader for Ultralytics YOLO models"""

    def download_yolo_model(self, model_name: str,
                           progress_callback: Optional[Callable] = None) -> bool:
        """
        Download a YOLO model from Ultralytics

        Args:
            model_name: Model name (e.g., 'yolov8n', 'yolov8s')
            progress_callback: Progress callback

        Returns:
            True if successful
        """
        url = f"https://github.com/ultralytics/assets/releases/download/v0.0.0/{model_name}.pt"
        return self.download_model(model_name, url, progress_callback)