"""
Enhanced UI System
SOLID: Single Responsibility, Interface Segregation
KISS: Clean separation of UI components and business logic
"""

import threading
from tkinter import messagebox, filedialog
from pathlib import Path
from typing import Optional, List, Callable
import logging

import customtkinter as ctk
from PIL import Image, ImageTk

from ..core import ProcessingEngine, RemoverType
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
        
        # Switch remover based on selection
        if "LayerDiffuse" in remover_choice:
            try:
                self.engine.switch_remover(RemoverType.LAYERDIFFUSE)
                self._logger.info("Switched to LayerDiffuse Enhanced")
            except Exception as e:
                self._logger.warning(f"Failed to switch to LayerDiffuse, using default: {e}")
        
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
        def update_ui():
            self.app.update_progress(current, total, info)
        
        self.app.root.after(0, update_ui)
    
    def _on_preview(self, image_data: bytes):
        """Handle preview updates from the processing engine."""
        def update_preview():
            self.app.show_preview(image_data)
        
        self.app.root.after(0, update_preview)
    
    def _on_processing_complete(self, stats, error):
        """Handle processing completion."""
        self.is_processing = False
        self.app.set_processing_state(False)
        
        if error:
            if "No supported image files" in str(error):
                messagebox.showwarning("No Images", str(error))
                self.app.set_status("No images found to process")
            else:
                messagebox.showerror("Processing Error", f"Processing failed:\n{error}")
                self.app.set_status("Processing failed")
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