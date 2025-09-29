"""
Processing Engine
SOLID: Single Responsibility, Open/Closed
KISS: Simple processing logic with clear interfaces
"""

import logging
import threading
from pathlib import Path
from typing import Callable, Optional, List, Tuple
from dataclasses import dataclass, field
from typing import List

from .factory import RemoverManager, RemoverType
from ..config.settings import config


@dataclass
class ProcessingStats:
    """Statistics for processing operations."""
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    failed_paths: List[str] = field(default_factory=list)
    skipped_paths: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100
    
    def __str__(self) -> str:
        return f"Processed: {self.processed_files}/{self.total_files} ({self.success_rate:.1f}%), Failed: {self.failed_files}, Skipped: {self.skipped_files}"


class ProcessingEngine:
    """
    Core processing engine for batch background removal.
    
    SOLID: Single Responsibility - only handles processing workflow
    KISS: Clean separation of concerns, simple API
    """
    
    def __init__(self, remover_type: RemoverType = RemoverType.INSPYRENET):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._remover_manager = RemoverManager(remover_type)
        self._cancelled = False
        self._stats = ProcessingStats()
        self.material_hint = "general"  # Default material hint
        
        # Supported image extensions
        self.SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
    
    def cancel(self):
        """Cancel the current processing operation."""
        self._cancelled = True
        self._logger.info("Processing cancellation requested")
    
    def reset_stats(self):
        """Reset processing statistics."""
        self._stats = ProcessingStats()
    
    def get_stats(self) -> ProcessingStats:
        """Get current processing statistics."""
        return self._stats
    
    def process_single_image(self, input_path: Path, output_path: Path) -> bool:
        """
        Process a single image file.
        
        Args:
            input_path: Path to input image
            output_path: Path for output image
            
        Returns:
            True if processing successful, False otherwise
        """
        try:
            # Read input image
            image_data = input_path.read_bytes()
            
            # Process with background remover - use advanced processing if available
            remover_info = self._remover_manager.get_active_remover_info()
            if remover_info.get('advanced_features', False):
                # Use material-specific processing for LayerDiffuse
                active_remover = self._remover_manager._primary_remover
                if hasattr(active_remover, 'remove_with_material_type'):
                    result_data = active_remover.remove_with_material_type(image_data, self.material_hint)
                else:
                    result_data = self._remover_manager.remove_background(image_data)
            else:
                # Standard processing
                result_data = self._remover_manager.remove_background(image_data)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write result
            output_path.write_bytes(result_data)
            
            self._logger.debug(f"Successfully processed: {input_path.name}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to process {input_path.name}: {e}")
            return False
    
    def process_folder(
        self,
        input_folder: Path,
        output_folder: Path,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        preview_callback: Optional[Callable[[bytes], None]] = None,
        show_preview: bool = False,
    ) -> ProcessingStats:
        """
        Process all supported images in a folder.
        
        Args:
            input_folder: Input folder path
            output_folder: Output folder path
            progress_callback: Optional progress callback (current, total)
            preview_callback: Optional preview callback for processed images
            show_preview: Whether to show previews
            
        Returns:
            Processing statistics
        """
        input_folder = Path(input_folder)
        output_folder = Path(output_folder)
        
        # Find all supported image files
        image_files = []
        for ext in self.SUPPORTED_EXTENSIONS:
            image_files.extend(input_folder.glob(f"*{ext}"))
            image_files.extend(input_folder.glob(f"*{ext.upper()}"))
        
        image_files = sorted(set(image_files))  # Remove duplicates and sort
        
        if not image_files:
            raise FileNotFoundError(f"No supported image files found in {input_folder}")
        
        # Reset stats for this operation
        folder_stats = ProcessingStats()
        folder_stats.total_files = len(image_files)
        
        self._logger.info(f"Processing {len(image_files)} files from {input_folder}")
        
        # Create output folder
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Process each file
        for idx, input_path in enumerate(image_files, 1):
            if self._cancelled:
                self._logger.info("Processing cancelled by user")
                break
            
            # Generate output path
            output_filename = input_path.stem + config.processing_settings.suffix + ".png"
            output_path = output_folder / output_filename
            
            # Skip if output already exists (optional)
            if output_path.exists():
                self._logger.debug(f"Skipping existing file: {output_filename}")
                folder_stats.skipped_files += 1
                folder_stats.skipped_paths.append(str(input_path))
                continue
            
            # Process the image
            success = self.process_single_image(input_path, output_path)
            
            if success:
                folder_stats.processed_files += 1
                
                # Show preview if requested
                if show_preview and preview_callback:
                    try:
                        preview_data = output_path.read_bytes()
                        preview_callback(preview_data)
                    except Exception as e:
                        self._logger.warning(f"Preview callback failed: {e}")
            else:
                folder_stats.failed_files += 1
                folder_stats.failed_paths.append(str(input_path))
            
            # Update progress (include filename as info)
            if progress_callback:
                try:
                    progress_callback(idx, len(image_files), input_path.name)
                except Exception as e:
                    self._logger.warning(f"Progress callback failed: {e}")
        
        self._logger.info(f"Folder processing complete: {folder_stats}")
        return folder_stats
    
    def process_folder_queue(
        self,
        folder_pairs: List[Tuple[Path, Path]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        preview_callback: Optional[Callable[[bytes], None]] = None,
        show_preview: bool = False,
    ) -> ProcessingStats:
        """
        Process multiple folder pairs (input, output).
        
        Args:
            folder_pairs: List of (input_folder, output_folder) tuples
            progress_callback: Optional progress callback (current, total, info)
            preview_callback: Optional preview callback
            show_preview: Whether to show previews
            
        Returns:
            Combined processing statistics
        """
        # Reset stats
        self.reset_stats()
        
        # Count total files across all folders
        for input_folder, _ in folder_pairs:
            try:
                image_files = []
                for ext in self.SUPPORTED_EXTENSIONS:
                    image_files.extend(Path(input_folder).glob(f"*{ext}"))
                    image_files.extend(Path(input_folder).glob(f"*{ext.upper()}"))
                self._stats.total_files += len(set(image_files))
            except Exception as e:
                self._logger.warning(f"Could not count files in {input_folder}: {e}")
        
        if self._stats.total_files == 0:
            raise FileNotFoundError("No supported image files found in any input folders")
        
        self._logger.info(f"Starting queue processing: {len(folder_pairs)} folders, {self._stats.total_files} total files")
        
        current_file = 0
        
        # Process each folder pair
        for folder_idx, (input_folder, output_folder) in enumerate(folder_pairs, 1):
            if self._cancelled:
                break
            
            folder_name = Path(input_folder).name
            self._logger.info(f"Processing folder {folder_idx}/{len(folder_pairs)}: {folder_name}")
            
            try:
                # Process this folder
                folder_stats = self.process_folder(
                    input_folder,
                    output_folder,
                    progress_callback=lambda curr, total: progress_callback(
                        current_file + curr, 
                        self._stats.total_files,
                        f"Folder: {folder_name}"
                    ) if progress_callback else None,
                    preview_callback=preview_callback,
                    show_preview=show_preview
                )
                
                # Update overall stats
                self._stats.processed_files += folder_stats.processed_files
                self._stats.failed_files += folder_stats.failed_files
                self._stats.skipped_files += folder_stats.skipped_files
                # Merge path lists
                self._stats.failed_paths.extend(folder_stats.failed_paths)
                self._stats.skipped_paths.extend(folder_stats.skipped_paths)
                
                # Update file counter
                current_file += folder_stats.total_files
                
            except Exception as e:
                self._logger.error(f"Failed to process folder {folder_name}: {e}")
                # Still update file counter for failed folders
                try:
                    image_files = []
                    for ext in self.SUPPORTED_EXTENSIONS:
                        image_files.extend(Path(input_folder).glob(f"*{ext}"))
                    current_file += len(set(image_files))
                    self._stats.failed_files += len(set(image_files))
                except:
                    pass
        
        self._logger.info(f"Queue processing finished: {self._stats}")
        return self._stats
    
    def switch_remover(self, new_type: RemoverType, **kwargs):
        """Switch to a different background remover."""
        try:
            self._remover_manager.switch_primary(new_type, **kwargs)
            self._logger.info(f"Switched to remover: {new_type.value}")
        except Exception as e:
            self._logger.error(f"Failed to switch remover: {e}")
            raise
    
    def configure_remover(self, **kwargs) -> bool:
        """Configure the current primary remover."""
        return self._remover_manager.configure_remover(self._remover_manager.primary_type, **kwargs)
    
    def get_remover_info(self) -> dict:
        """Get information about the active remover."""
        return self._remover_manager.get_active_remover_info()
    
    def cleanup(self):
        """Clean up processing engine resources."""
        self._remover_manager.cleanup()
        self._logger.info("ProcessingEngine cleanup complete")