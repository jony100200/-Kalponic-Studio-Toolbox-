"""
Batch processing runner with threading and progress tracking.
"""

import threading
import queue
import logging
from pathlib import Path
from typing import Callable, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import ProcessingConfig, AppState
from .processor import ImageProcessor
from .io_handler import IOHandler

logger = logging.getLogger(__name__)

class BatchRunner:
    """Manages batch processing with threading and progress updates."""
    
    def __init__(self, app_state: AppState, progress_callback: Optional[Callable] = None):
        self.app_state = app_state
        self.progress_callback = progress_callback
        self.io_handler = IOHandler()
        self._stop_event = threading.Event()
        self._executor: Optional[ThreadPoolExecutor] = None
        
    def start_batch(self) -> bool:
        """
        Start batch processing in a separate thread.
        
        Returns:
            True if batch started successfully, False otherwise
        """
        if self.app_state.is_processing:
            logger.warning("Batch processing already in progress")
            return False
        
        if not self.app_state.input_folder or not self.app_state.output_folder:
            logger.error("Input or output folder not specified")
            return False
        
        # Reset state
        self.app_state.reset_stats()
        self.app_state.is_processing = True
        self._stop_event.clear()
        
        # Start processing in background thread
        threading.Thread(target=self._run_batch, daemon=True).start()
        return True
    
    def stop_batch(self):
        """Stop the current batch processing."""
        logger.info("Stopping batch processing...")
        self._stop_event.set()
        
        if self._executor:
            self._executor.shutdown(wait=False)
        
        self.app_state.is_processing = False
        
        if self.progress_callback:
            self.progress_callback("Cancelled", self.app_state.processed_count, 
                                 self.app_state.total_count, self.app_state.error_count)
    
    def _run_batch(self):
        """Main batch processing loop."""
        try:
            # Get list of images to process
            image_files = self.io_handler.get_image_files(self.app_state.input_folder)
            
            if not image_files:
                self._finish_batch("No images found")
                return
            
            # Filter out already processed files if skip_existing is enabled
            if self.app_state.processing_config.skip_existing:
                image_files = self._filter_existing_files(image_files)
            
            self.app_state.total_count = len(image_files)
            
            if self.app_state.total_count == 0:
                self._finish_batch("All images already processed")
                return
            
            logger.info(f"Starting batch processing of {self.app_state.total_count} images")
            
            # Create processor
            processor = ImageProcessor()
            
            # Process images using ThreadPoolExecutor
            max_workers = min(4, len(image_files))  # Limit concurrent threads
            self._executor = ThreadPoolExecutor(max_workers=max_workers)
            
            # Submit all tasks
            future_to_file = {
                self._executor.submit(self._process_single_image, processor, file_path): file_path 
                for file_path in image_files
            }
            
            # Process completed tasks
            for future in as_completed(future_to_file):
                if self._stop_event.is_set():
                    break
                
                file_path = future_to_file[future]
                
                try:
                    success = future.result()
                    if success:
                        self.app_state.processed_count += 1
                    else:
                        self.app_state.error_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    self.app_state.error_count += 1
                
                # Update progress
                if self.progress_callback:
                    status = f"Processing {file_path.name}..."
                    self.progress_callback(status, self.app_state.processed_count, 
                                         self.app_state.total_count, self.app_state.error_count)
            
            # Finish batch
            if self._stop_event.is_set():
                self._finish_batch("Cancelled")
            else:
                self._finish_batch("Completed")
                
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            self._finish_batch(f"Error: {e}")
        finally:
            if self._executor:
                self._executor.shutdown(wait=True)
                self._executor = None
    
    def _process_single_image(self, processor: ImageProcessor, file_path: Path) -> bool:
        """
        Process a single image file.
        
        Args:
            processor: ImageProcessor instance
            file_path: Path to the image file
            
        Returns:
            True if processing succeeded, False otherwise
        """
        try:
            # Load image
            image = self.io_handler.load_image(file_path)
            if image is None:
                return False
            
            # Process image
            processed_image = processor.process_image(file_path, self.app_state.processing_config)
            
            # Generate output path
            output_path = self.io_handler.generate_output_path(
                file_path, 
                self.app_state.output_folder, 
                self.app_state.processing_config.add_suffix
            )
            
            # Save processed image
            success = self.io_handler.save_image(processed_image, output_path)
            
            if success:
                logger.debug(f"Successfully processed: {file_path.name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return False
    
    def _filter_existing_files(self, image_files: List[Path]) -> List[Path]:
        """
        Filter out files that have already been processed.
        
        Args:
            image_files: List of input image files
            
        Returns:
            List of files that haven't been processed yet
        """
        filtered_files = []
        
        for file_path in image_files:
            output_path = self.io_handler.generate_output_path(
                file_path, 
                self.app_state.output_folder, 
                self.app_state.processing_config.add_suffix
            )
            
            if not self.io_handler.file_exists(output_path):
                filtered_files.append(file_path)
            else:
                logger.debug(f"Skipping existing: {output_path.name}")
        
        return filtered_files
    
    def _finish_batch(self, status: str):
        """
        Finish batch processing and update state.
        
        Args:
            status: Final status message
        """
        self.app_state.is_processing = False
        
        if self.progress_callback:
            final_status = f"{status} • Processed {self.app_state.processed_count}/{self.app_state.total_count}"
            if self.app_state.error_count > 0:
                final_status += f" • Errors {self.app_state.error_count}"
            
            self.progress_callback(final_status, self.app_state.processed_count, 
                                 self.app_state.total_count, self.app_state.error_count)
        
        logger.info(f"Batch processing {status.lower()}: {self.app_state.processed_count}/{self.app_state.total_count} processed, {self.app_state.error_count} errors")
    
    def get_random_preview(self) -> Optional[tuple]:
        """
        Generate a preview for a random image from the input folder.
        
        Returns:
            Tuple of (original_image, processed_image) or None
        """
        if not self.app_state.input_folder:
            return None
        
        try:
            image_files = self.io_handler.get_image_files(self.app_state.input_folder)
            if not image_files:
                return None
            
            # Pick a random file
            import random
            random_file = random.choice(image_files)
            
            # Load and process
            original = self.io_handler.load_image(random_file)
            if original is None:
                return None
            
            processor = ImageProcessor()
            processed = processor.process_image(random_file, self.app_state.processing_config)
            
            return original, processed
            
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            return None
