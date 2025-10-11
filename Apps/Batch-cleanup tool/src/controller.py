"""
Controller to coordinate UI interactions with processing logic.
"""

import logging
from typing import Optional, Callable
from pathlib import Path

from .config import AppState, ProcessingConfig, MattePreset
from .batch_runner import BatchRunner

logger = logging.getLogger(__name__)

class Controller:
    """Controller class following MVC pattern to separate UI from business logic."""
    
    def __init__(self):
        self.app_state = AppState()
        self.batch_runner: Optional[BatchRunner] = None
        self._progress_callback: Optional[Callable] = None
        
    def set_progress_callback(self, callback: Callable):
        """Set the progress callback for UI updates."""
        self._progress_callback = callback
        
    def set_input_folder(self, folder_path: str) -> bool:
        """
        Set the input folder path.
        
        Args:
            folder_path: Path to the input folder
            
        Returns:
            True if valid folder, False otherwise
        """
        if folder_path and folder_path.strip():
            self.app_state.input_folder = folder_path.strip()
            logger.info(f"Input folder set to: {folder_path}")
            return True
        return False
    
    def set_output_folder(self, folder_path: str) -> bool:
        """
        Set the output folder path.
        
        Args:
            folder_path: Path to the output folder
            
        Returns:
            True if valid folder, False otherwise
        """
        if folder_path and folder_path.strip():
            self.app_state.output_folder = folder_path.strip()
            logger.info(f"Output folder set to: {folder_path}")
            return True
        return False
    
    def update_matte_preset(self, preset_name: str):
        """Update the matte removal preset."""
        try:
            preset = MattePreset(preset_name)
            self.app_state.processing_config.matte_preset = preset
            logger.debug(f"Matte preset updated to: {preset_name}")
        except ValueError:
            logger.error(f"Invalid matte preset: {preset_name}")
    
    def update_smooth(self, value: int):
        """Update smooth parameter (0-3)."""
        if 0 <= value <= 3:
            self.app_state.processing_config.smooth = value
            logger.debug(f"Smooth updated to: {value}")
    
    def update_feather(self, value: int):
        """Update feather parameter (0-3)."""
        if 0 <= value <= 3:
            self.app_state.processing_config.feather = value
            logger.debug(f"Feather updated to: {value}")
    
    def update_contrast(self, value: float):
        """Update contrast parameter (1.0-4.0)."""
        if 1.0 <= value <= 4.0:
            self.app_state.processing_config.contrast = value
            logger.debug(f"Contrast updated to: {value}")
    
    def update_shift_edge(self, value: int):
        """Update edge shift parameter (-2 to +2)."""
        if -2 <= value <= 2:
            self.app_state.processing_config.shift_edge = value
            logger.debug(f"Edge shift updated to: {value}")
    
    def update_fringe_fix(self, enabled: bool):
        """Update fringe fix enabled state."""
        self.app_state.processing_config.fringe_fix_enabled = enabled
        logger.debug(f"Fringe fix enabled: {enabled}")
    
    def update_fringe_band(self, value: int):
        """Update fringe band parameter (1-3)."""
        if 1 <= value <= 3:
            self.app_state.processing_config.fringe_band = value
            logger.debug(f"Fringe band updated to: {value}")
    
    def update_fringe_strength(self, value: int):
        """Update fringe strength parameter (1-3)."""
        if 1 <= value <= 3:
            self.app_state.processing_config.fringe_strength = value
            logger.debug(f"Fringe strength updated to: {value}")
    
    def update_skip_existing(self, enabled: bool):
        """Update skip existing files setting."""
        self.app_state.processing_config.skip_existing = enabled
        logger.debug(f"Skip existing files: {enabled}")
    
    def update_process_iterations(self, value: int):
        """Update the number of processing iterations."""
        if 1 <= value <= 10:
            self.app_state.processing_config.process_iterations = value
            logger.debug(f"Processing iterations updated to: {value}")
    
    def start_processing(self) -> bool:
        """
        Start batch processing.
        
        Returns:
            True if processing started successfully, False otherwise
        """
        if not self.app_state.input_folder:
            logger.error("Input folder not set")
            return False
        
        if not self.app_state.output_folder:
            logger.error("Output folder not set")
            return False
        
        if not self.app_state.processing_config.validate():
            logger.error("Invalid processing configuration")
            return False
        
        if self.app_state.is_processing:
            logger.warning("Processing already in progress")
            return False
        
        # Create new batch runner
        self.batch_runner = BatchRunner(self.app_state, self._progress_callback)
        
        # Start processing
        success = self.batch_runner.start_batch()
        if success:
            logger.info("Batch processing started")
        
        return success

    def start_single_file(self, input_file: str, output_folder: str, completion_callback: Optional[Callable] = None) -> bool:
        """Process a single file immediately. Calls completion_callback(success, input_path, output_path) when done."""
        if not input_file:
            logger.error("No input file specified for single-file processing")
            return False

        if not output_folder:
            logger.error("No output folder specified for single-file processing")
            return False

        try:
            # Run processing in a background thread to avoid blocking UI
            def worker():
                try:
                    from .io_handler import IOHandler
                    from .processor import ImageProcessor

                    ioh = IOHandler()
                    proc = ImageProcessor()

                    # Load and process image
                    processed_img = proc.process_image(input_file, self.app_state.processing_config)

                    # Generate output path
                    input_path = Path(input_file)
                    output_path = ioh.generate_output_path(input_path, output_folder, self.app_state.processing_config.add_suffix)

                    success = False
                    if processed_img is not None:
                        success = ioh.save_image(processed_img, output_path)

                    # Invoke completion callback if provided
                    if completion_callback:
                        try:
                            completion_callback(success, str(input_path), str(output_path))
                        except Exception as e:
                            logger.error(f"Completion callback failed: {e}")

                except Exception as e:
                    logger.error(f"Single-file processing error: {e}")
                    if completion_callback:
                        try:
                            completion_callback(False, input_file, "")
                        except:
                            pass

            import threading
            threading.Thread(target=worker, daemon=True).start()
            return True
        except Exception as e:
            logger.error(f"Failed to start single-file processing: {e}")
            return False
    
    def stop_processing(self):
        """Stop current batch processing."""
        if self.batch_runner and self.app_state.is_processing:
            self.batch_runner.stop_batch()
            logger.info("Batch processing stop requested")
    
    def generate_preview(self) -> Optional[tuple]:
        """
        Generate a before/after preview.
        
        Returns:
            Tuple of (original_image, processed_image) or None
        """
        if not self.batch_runner:
            self.batch_runner = BatchRunner(self.app_state, self._progress_callback)
        
        return self.batch_runner.get_random_preview()
    
    def get_input_folder(self) -> Optional[str]:
        """Get current input folder."""
        return self.app_state.input_folder
    
    def get_output_folder(self) -> Optional[str]:
        """Get current output folder."""
        return self.app_state.output_folder
    
    def is_processing(self) -> bool:
        """Check if currently processing."""
        return self.app_state.is_processing
    
    def get_processing_stats(self) -> tuple:
        """
        Get current processing statistics.
        
        Returns:
            Tuple of (processed_count, total_count, error_count)
        """
        return (
            self.app_state.processed_count,
            self.app_state.total_count, 
            self.app_state.error_count
        )
    
    def get_config_values(self) -> dict:
        """
        Get current configuration values for UI.
        
        Returns:
            Dictionary with current configuration values
        """
        config = self.app_state.processing_config
        return {
            'matte_preset': config.matte_preset.value,
            'smooth': config.smooth,
            'feather': config.feather,
            'contrast': config.contrast,
            'shift_edge': config.shift_edge,
            'fringe_fix_enabled': config.fringe_fix_enabled,
            'fringe_band': config.fringe_band,
            'fringe_strength': config.fringe_strength,
            'skip_existing': config.skip_existing
        }
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.app_state.processing_config = ProcessingConfig()
        logger.info("Configuration reset to defaults")
