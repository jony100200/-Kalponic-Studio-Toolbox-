"""
Enhanced UI System
SOLID: Single Responsibility, Interface Segregation
KISS: Clean separation of UI components and business logic
"""

import threading
import time
from tkinter import messagebox, filedialog
from pathlib import Path
from typing import Optional, List
import logging

import customtkinter as ctk

from ..core import ProcessingEngine, RemoverType, ProcessingStats
from ..config import config


class UIController:
    """
    UI Controller following SOLID principles.
    
    SOLID: Single Responsibility - manages UI state and business logic coordination
    KISS: Simple controller pattern
    """
    
    def __init__(self, app_window):
        self.app = app_window
        self.engine: Optional[ProcessingEngine] = None
        self.worker_thread: Optional[threading.Thread] = None
        self._logger = logging.getLogger(self.__class__.__name__)
        
        # UI state
        self.input_folders: List[str] = []
        self.is_processing = False
        self.material_hint = "general"  # Default material hint
        self._run_started_at: Optional[float] = None
        self._last_preview_at = 0.0
        self._preview_min_interval_sec = 0.25
        
        # Initialize processing engine
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the processing engine."""
        try:
            self.engine = ProcessingEngine(RemoverType.INSPYRENET)
            self._logger.info("Processing engine initialized")
        except Exception as e:
            self._logger.error(f"Failed to initialize processing engine: {e}")
            messagebox.showerror("Initialization Error", f"Failed to initialize processing engine:\n{e}")
    
    def add_input_folder(self, folder_path: str):
        """Add an input folder to the processing queue."""
        if folder_path and folder_path not in self.input_folders:
            self.input_folders.append(folder_path)
            self.app.update_folder_display()
            self._logger.info(f"Added input folder: {Path(folder_path).name}")
    
    def clear_folders(self):
        """Clear all input folders."""
        self.input_folders.clear()
        self.app.update_folder_display()
        self._logger.info("Cleared all input folders")
    
    def start_processing(self, output_folder: str, show_preview: bool = False, remover_choice: str = "", material_choice: str = ""):
        """Start the background removal processing."""
        if self.is_processing:
            self._logger.warning("Processing already in progress")
            return
        
        if not self.input_folders:
            messagebox.showerror("Error", "Please add at least one input folder")
            return
        
        if not output_folder.strip():
            messagebox.showerror("Error", "Please select an output folder")
            return
        
        if not self.engine:
            messagebox.showerror("Error", "Processing engine not initialized")
            return
        
        # Switch remover based on selection.
        target_remover = RemoverType.LAYERDIFFUSE if "LayerDiffuse" in remover_choice else RemoverType.INSPYRENET
        try:
            self.engine.switch_remover(target_remover)
            self._logger.info(f"Switched to {target_remover.value}")
        except Exception as e:
            self._logger.warning(f"Failed to switch remover to {target_remover.value}: {e}")
        
        # Store material choice for processing
        material_map = {
            "General (Standard)": "general",
            "Glass (Transparent)": "glass", 
            "Hair/Fur (Fine Details)": "hair",
            "Semi-Transparent (Glowing)": "transparent"
        }
        self.material_hint = material_map.get(material_choice, "general")
        
        # Update UI state
        self.is_processing = True
        self._run_started_at = time.monotonic()
        self._last_preview_at = 0.0
        self.app.set_processing_state(True)
        
        # Configure engine with current settings
        self._configure_engine()
        
        # Set material hint for processing
        if hasattr(self.engine, 'material_hint'):
            self.engine.material_hint = self.material_hint
        
        # Create folder pairs
        folder_pairs = []
        base_output = Path(output_folder)
        
        for input_folder in self.input_folders:
            folder_name = Path(input_folder).name
            if config.processing_settings.create_subfolders:
                output_path = base_output / f"{folder_name}_cleaned"
            else:
                output_path = base_output
            folder_pairs.append((Path(input_folder), output_path))
        
        # Start worker thread
        def worker():
            try:
                self._logger.info("Starting background removal processing")
                
                stats = self.engine.process_folder_queue(
                    folder_pairs,
                    progress_callback=self._on_progress,
                    preview_callback=self._on_preview if show_preview else None,
                    show_preview=show_preview
                )
                
                # Processing completed successfully
                self.app.root.after(0, lambda: self._on_processing_complete(stats, None))
                
            except Exception as e:
                self._logger.error(f"Processing failed: {e}")
                self.app.root.after(0, lambda: self._on_processing_complete(None, e))
        
        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()

    def start_single_file(self, input_file: str, output_folder: str, show_preview: bool = False, remover_choice: str = "", material_choice: str = ""):
        """Process a single file immediately (non-queued mode)."""
        if self.is_processing:
            self._logger.warning("Processing already in progress")
            messagebox.showwarning("Busy", "Processing already in progress")
            return

        if not input_file:
            messagebox.showerror("Error", "No input file selected")
            return

        if not output_folder:
            messagebox.showerror("Error", "Please select an output folder")
            return

        if not self.engine:
            messagebox.showerror("Error", "Processing engine not initialized")
            return

        # Switch remover based on selection.
        target_remover = RemoverType.LAYERDIFFUSE if "LayerDiffuse" in remover_choice else RemoverType.INSPYRENET
        try:
            self.engine.switch_remover(target_remover)
            self._logger.info(f"Switched to {target_remover.value}")
        except Exception as e:
            self._logger.warning(f"Failed to switch remover to {target_remover.value}: {e}")

        # Material choice map
        material_map = {
            "General (Standard)": "general",
            "Glass (Transparent)": "glass",
            "Hair/Fur (Fine Details)": "hair",
            "Semi-Transparent (Glowing)": "transparent"
        }
        self.material_hint = material_map.get(material_choice, "general")

        # Configure engine
        self._configure_engine()
        if hasattr(self.engine, 'material_hint'):
            self.engine.material_hint = self.material_hint

        # UI state
        self.is_processing = True
        self._run_started_at = time.monotonic()
        self._last_preview_at = 0.0
        self.app.set_processing_state(True)

        input_path = Path(input_file)
        # build output path using suffix and png extension
        output_filename = input_path.stem + config.processing_settings.suffix + ".png"
        output_path = Path(output_folder) / output_filename

        def worker():
            try:
                self._logger.info(f"Starting single-file processing: {input_path}")
                success = self.engine.process_single_image(input_path, output_path)

                # Update UI after processing
                def finish():
                    self.is_processing = False
                    self.app.set_processing_state(False)
                    if success:
                        self.app.set_status(f"Single file processed: {output_path.name}")
                        # show preview if requested
                        if show_preview:
                            try:
                                data = output_path.read_bytes()
                                self._on_preview(data)
                            except Exception as e:
                                self._logger.warning(f"Could not load preview: {e}")
                        messagebox.showinfo("Done", f"Processed: {output_path}")
                    else:
                        self.app.set_status("Single file processing failed")
                        messagebox.showerror("Failed", "Processing failed for the selected file")

                self.app.root.after(0, finish)

            except Exception as e:
                self._logger.error(f"Single-file processing failed: {e}")
                def fail():
                    self.is_processing = False
                    self.app.set_processing_state(False)
                    messagebox.showerror("Error", f"Processing failed: {e}")

                self.app.root.after(0, fail)

        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()

    def start_file_batch(
        self,
        input_files: List[str],
        output_folder: str,
        show_preview: bool = False,
        remover_choice: str = "",
        material_choice: str = "",
    ):
        """Process multiple files in a single queued run."""
        if self.is_processing:
            self._logger.warning("Processing already in progress")
            messagebox.showwarning("Busy", "Processing already in progress")
            return

        file_paths = [Path(p) for p in input_files if Path(p).is_file()]
        if not file_paths:
            messagebox.showerror("Error", "No valid input files were provided")
            return

        if not output_folder:
            messagebox.showerror("Error", "Please select an output folder")
            return

        if not self.engine:
            messagebox.showerror("Error", "Processing engine not initialized")
            return

        # Switch remover based on selection.
        target_remover = RemoverType.LAYERDIFFUSE if "LayerDiffuse" in remover_choice else RemoverType.INSPYRENET
        try:
            self.engine.switch_remover(target_remover)
            self._logger.info(f"Switched to {target_remover.value}")
        except Exception as e:
            self._logger.warning(f"Failed to switch remover to {target_remover.value}: {e}")

        # Material choice map
        material_map = {
            "General (Standard)": "general",
            "Glass (Transparent)": "glass",
            "Hair/Fur (Fine Details)": "hair",
            "Semi-Transparent (Glowing)": "transparent"
        }
        self.material_hint = material_map.get(material_choice, "general")

        # Configure engine
        self._configure_engine()
        if hasattr(self.engine, 'material_hint'):
            self.engine.material_hint = self.material_hint
        self.engine.reset_cancel()

        # UI state
        self.is_processing = True
        self._run_started_at = time.monotonic()
        self._last_preview_at = 0.0
        self.app.set_processing_state(True)
        self.app.set_status(f"Queued {len(file_paths)} files")

        output_base = Path(output_folder)

        def worker():
            stats = ProcessingStats(total_files=len(file_paths))
            try:
                self._logger.info(f"Starting multi-file processing: {len(file_paths)} files")

                for idx, input_path in enumerate(file_paths, 1):
                    if self.engine and self.engine.is_cancelled():
                        self._logger.info("Multi-file processing cancelled by user")
                        break

                    output_filename = input_path.stem + config.processing_settings.suffix + ".png"
                    output_path = output_base / output_filename

                    if output_path.exists():
                        stats.skipped_files += 1
                        stats.skipped_paths.append(str(input_path))
                        self._on_progress(idx, stats.total_files, f"{input_path.name} (skipped)")
                        continue

                    success = self.engine.process_single_image(input_path, output_path)
                    if success:
                        stats.processed_files += 1
                        if show_preview:
                            try:
                                data = output_path.read_bytes()
                                self._on_preview(data)
                            except Exception as preview_error:
                                self._logger.warning(f"Could not load preview: {preview_error}")
                    else:
                        stats.failed_files += 1
                        stats.failed_paths.append(str(input_path))

                    self._on_progress(idx, stats.total_files, input_path.name)

                self.app.root.after(0, lambda: self._on_processing_complete(stats, None))
            except Exception as e:
                self._logger.error(f"Multi-file processing failed: {e}")
                self.app.root.after(0, lambda: self._on_processing_complete(None, e))

        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()
    
    def cancel_processing(self):
        """Cancel the current processing operation."""
        if self.engine and self.is_processing:
            self.engine.cancel()
            self.app.set_status("Cancelling processing...")
            self._logger.info("Processing cancellation requested")
    
    def _configure_engine(self):
        """Configure the processing engine with current settings."""
        if not self.engine:
            return
        
        try:
            self.engine.configure_remover(
                threshold=config.removal_settings.threshold,
                use_jit=config.removal_settings.use_jit
            )
            self._logger.debug("Engine configured with current settings")
        except Exception as e:
            self._logger.warning(f"Failed to configure engine: {e}")
    
    def _on_progress(self, current: int, total: int, info: str = ""):
        """Handle progress updates from the processing engine."""
        if self._run_started_at and current > 0 and total > current:
            elapsed = max(time.monotonic() - self._run_started_at, 0.001)
            rate = current / elapsed
            if rate > 0:
                eta_seconds = int((total - current) / rate)
                eta_text = self._format_duration(eta_seconds)
                info = f"{info} | ETA {eta_text}" if info else f"ETA {eta_text}"

        def update_ui():
            self.app.update_progress(current, total, info)
        
        self.app.root.after(0, update_ui)
    
    def _on_preview(self, image_data: bytes):
        """Handle preview updates from the processing engine."""
        now = time.monotonic()
        if now - self._last_preview_at < self._preview_min_interval_sec:
            return
        self._last_preview_at = now

        def update_preview():
            self.app.show_preview(image_data)
        
        self.app.root.after(0, update_preview)

    def _format_duration(self, total_seconds: int) -> str:
        """Format seconds into mm:ss or hh:mm:ss."""
        hours, rem = divmod(max(total_seconds, 0), 3600)
        minutes, seconds = divmod(rem, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    def _on_processing_complete(self, stats, error):
        """Handle processing completion."""
        self.is_processing = False
        self._run_started_at = None
        self.app.set_processing_state(False)
        was_cancelled = self.engine.is_cancelled() if self.engine else False
        if self.engine:
            self.engine.reset_cancel()

        if was_cancelled and not error and stats is not None:
            messagebox.showinfo(
                "Processing Cancelled",
                f"Processing was cancelled.\n\n{stats}"
            )
            self.app.set_status(f"Cancelled: {stats.processed_files}/{stats.total_files} processed")
            self._logger.info(f"Processing cancelled. Stats: {stats}")
            return

        if error:
            if "No supported image files" in str(error):
                messagebox.showwarning("No Images", str(error))
                self.app.set_status("No images found to process")
            else:
                messagebox.showerror("Processing Error", f"Processing failed:\n{error}")
                self.app.set_status("Processing failed")
        else:
            # If there are failed files, offer to save the list and/or retry
            if getattr(stats, 'failed_files', 0) > 0 and getattr(stats, 'failed_paths', None):
                failed_count = stats.failed_files
                total = stats.total_files
                msg = f"Processing completed with {failed_count} failed out of {total} files.\n\nWould you like to save the failed file list for retry or re-run failed files now?"
                res = messagebox.askyesnocancel("Processing Complete - Failures", msg, default=messagebox.YES)

                # Yes -> Save failed list and offer retry
                if res is True:
                    # Save failed list to file
                    save_path = filedialog.asksaveasfilename(title="Save failed list as...", defaultextension=".txt", filetypes=[("Text Files","*.txt")])
                    if save_path:
                        try:
                            with open(save_path, 'w', encoding='utf-8') as f:
                                for p in stats.failed_paths:
                                    f.write(p + "\n")
                            messagebox.showinfo("Saved", f"Saved failed list to {save_path}")
                        except Exception as e:
                            messagebox.showerror("Save Error", f"Could not save failed list: {e}")

                    # Ask to retry now
                    retry_now = messagebox.askyesno("Retry Failed", "Retry failed files now? (Recommended if transient errors)")
                    if retry_now:
                        try:
                            # Build folder_pairs from failed paths mapping to same output folder structure
                            folder_pairs = []
                            base_output = Path(self.app.output_folder.get()) if self.app.output_folder.get() else None
                            if not base_output:
                                messagebox.showerror("Output Missing", "Please select an output folder before retrying failed files.")
                            else:
                                # Group failed files by their parent folder
                                from collections import defaultdict
                                groups = defaultdict(list)
                                for p in stats.failed_paths:
                                    groups[Path(p).parent].append(Path(p))

                                # Create temporary input folders by reusing original folders and set output paths
                                for parent_folder, files in groups.items():
                                    folder_name = parent_folder.name
                                    if config.processing_settings.create_subfolders:
                                        outp = base_output / f"{folder_name}_cleaned"
                                    else:
                                        outp = base_output
                                    folder_pairs.append((parent_folder, outp))

                                # Start processing only those folders (engine will skip already processed files)
                                def retry_worker():
                                    try:
                                        self.is_processing = True
                                        self.app.set_processing_state(True)
                                        stats2 = self.engine.process_folder_queue(
                                            folder_pairs,
                                            progress_callback=self._on_progress,
                                            preview_callback=self._on_preview,
                                            show_preview=self.app.show_preview.get()
                                        )
                                        self.app.root.after(0, lambda: self._on_processing_complete(stats2, None))
                                    except Exception as e:
                                        self.app.root.after(0, lambda: self._on_processing_complete(None, e))

                                self.worker_thread = threading.Thread(target=retry_worker, daemon=True)
                                self.worker_thread.start()

                        except Exception as e:
                            messagebox.showerror("Retry Error", f"Could not retry failed files: {e}")

                elif res is False:
                    # Save failed list without retry
                    save_path = filedialog.asksaveasfilename(title="Save failed list as...", defaultextension=".txt", filetypes=[("Text Files","*.txt")])
                    if save_path:
                        try:
                            with open(save_path, 'w', encoding='utf-8') as f:
                                for p in stats.failed_paths:
                                    f.write(p + "\n")
                            messagebox.showinfo("Saved", f"Saved failed list to {save_path}")
                        except Exception as e:
                            messagebox.showerror("Save Error", f"Could not save failed list: {e}")
                else:
                    # Cancel - do nothing
                    pass
            else:
                messagebox.showinfo("Processing Complete", 
                    f"Processing completed successfully!\n\n{stats}")
                self.app.set_status(f"Complete: {stats.processed_files}/{stats.total_files} processed")

        self._logger.info(f"Processing completed. Stats: {stats}")
    
    def get_remover_info(self) -> dict:
        """Get information about the current remover."""
        if self.engine:
            return self.engine.get_remover_info()
        return {"name": "Not initialized", "status": "error"}
    
    def switch_remover(self, remover_type: RemoverType):
        """Switch to a different remover type."""
        if not self.engine:
            return False
        
        try:
            self.engine.switch_remover(remover_type)
            self.app.set_status(f"Switched to {remover_type.value}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to switch remover: {e}")
            messagebox.showerror("Switch Error", f"Failed to switch remover:\n{e}")
            return False
    
    def cleanup(self):
        """Clean up controller resources."""
        if self.engine:
            self.engine.cleanup()
        if self.worker_thread and self.worker_thread.is_alive():
            # Cancel processing if still running
            if self.engine:
                self.engine.cancel()
        self._logger.info("UIController cleanup complete")


class CyberpunkTheme:
    """
    Cyberpunk theme configuration.
    
    SOLID: Single Responsibility - only handles theming
    KISS: Simple color and style definitions
    """
    
    # Muted cyberpunk colors - eye-friendly
    ACCENT = "#1fbf9c"          # Muted teal
    SECONDARY = "#4aa3ff"       # Soft electric blue
    BACKGROUND = "#0f1113"      # Near-black
    FRAME = "#141826"           # Dark slate
    SUCCESS = "#00cc35"         # Green
    ERROR = "#ff3030"           # Red
    WARNING = "#ffaa00"         # Orange
    
    @classmethod
    def apply_to_app(cls):
        """Apply theme to CustomTkinter."""
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")
    
    @classmethod
    def get_title_font(cls) -> ctk.CTkFont:
        """Get title font configuration."""
        return ctk.CTkFont(size=24, weight="bold")
    
    @classmethod
    def get_subtitle_font(cls) -> ctk.CTkFont:
        """Get subtitle font configuration."""
        return ctk.CTkFont(size=12, weight="bold")
    
    @classmethod
    def get_section_font(cls) -> ctk.CTkFont:
        """Get section header font configuration."""
        return ctk.CTkFont(size=14, weight="bold")
    
    @classmethod
    def get_body_font(cls) -> ctk.CTkFont:
        """Get body text font configuration."""
        return ctk.CTkFont(size=11)
    
    @classmethod
    def get_bold_font(cls) -> ctk.CTkFont:
        """Get bold body font configuration."""
        return ctk.CTkFont(size=11, weight="bold")
