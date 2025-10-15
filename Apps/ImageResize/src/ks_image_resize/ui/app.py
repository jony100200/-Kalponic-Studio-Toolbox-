"""
GUI application for KS Image Resize
"""

import os
import logging
from pathlib import Path
from typing import Optional
import threading

import customtkinter as ctk
from tkinter import filedialog

from ks_image_resize.config import ConfigManager, ResizePreset
from ks_image_resize.core.resizer import ImageResizer

logger = logging.getLogger(__name__)


class ImageResizeApp(ctk.CTk):
    """
    Main GUI application for batch image resizing.
    Follows Single Responsibility Principle - only handles UI interactions.
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        super().__init__()

        self.config_manager = config_manager or ConfigManager()
        self.resizer = ImageResizer(quality=self.config_manager.config.quality)

        # Configure window
        self.title("KS Image Resize - Batch Image Resizer")
        self.geometry("700x500")
        self.minsize(600, 400)

        # Apply theme
        ctk.set_appearance_mode(self.config_manager.config.theme)
        ctk.set_default_color_theme("blue")

        # Variables
        self.input_dir = ctk.StringVar()
        self.output_dir = ctk.StringVar()
        self.width_var = ctk.StringVar()
        self.height_var = ctk.StringVar()
        self.preset_var = ctk.StringVar(value="Custom")

        # Track processing state
        self.is_processing = False

        self._setup_ui()
        self._load_presets()

        logger.info("GUI application initialized")

    def _setup_ui(self):
        """Setup the user interface."""
        # Create main container with scrollable frame
        container = ctk.CTkFrame(self)
        container.pack(fill='both', expand=True, padx=10, pady=10)

        scrollable = ctk.CTkScrollableFrame(container)
        scrollable.pack(fill='both', expand=True)

        # Input directory section
        input_frame = ctk.CTkFrame(scrollable)
        input_frame.pack(fill='x', padx=10, pady=(10, 5))

        ctk.CTkLabel(input_frame, text="Input Directory:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor='w', padx=10, pady=(10, 5))

        input_entry_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        input_entry_frame.pack(fill='x', padx=10, pady=(0, 10))

        self.input_entry = ctk.CTkEntry(input_entry_frame, textvariable=self.input_dir, width=400)
        self.input_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))

        self.browse_input_btn = ctk.CTkButton(input_entry_frame, text="Browse", command=self._browse_input, width=80)
        self.browse_input_btn.pack(side='right')

        # Output directory section
        output_frame = ctk.CTkFrame(scrollable)
        output_frame.pack(fill='x', padx=10, pady=(5, 5))

        ctk.CTkLabel(output_frame, text="Output Directory (optional):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor='w', padx=10, pady=(10, 5))

        output_entry_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        output_entry_frame.pack(fill='x', padx=10, pady=(0, 10))

        self.output_entry = ctk.CTkEntry(output_entry_frame, textvariable=self.output_dir, width=400)
        self.output_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))

        self.browse_output_btn = ctk.CTkButton(output_entry_frame, text="Browse", command=self._browse_output, width=80)
        self.browse_output_btn.pack(side='right')

        # Dimensions section
        dims_frame = ctk.CTkFrame(scrollable)
        dims_frame.pack(fill='x', padx=10, pady=(5, 5))

        ctk.CTkLabel(dims_frame, text="Dimensions:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor='w', padx=10, pady=(10, 5))

        # Width and Height inputs
        dims_input_frame = ctk.CTkFrame(dims_frame, fg_color="transparent")
        dims_input_frame.pack(fill='x', padx=10, pady=(0, 10))

        # Width
        width_frame = ctk.CTkFrame(dims_input_frame, fg_color="transparent")
        width_frame.pack(side='left', padx=(0, 20))
        ctk.CTkLabel(width_frame, text="Width:").pack(anchor='w')
        self.width_entry = ctk.CTkEntry(width_frame, textvariable=self.width_var, width=120)
        self.width_entry.pack(pady=(2, 0))

        # Height
        height_frame = ctk.CTkFrame(dims_input_frame, fg_color="transparent")
        height_frame.pack(side='left')
        ctk.CTkLabel(height_frame, text="Height:").pack(anchor='w')
        self.height_entry = ctk.CTkEntry(height_frame, textvariable=self.height_var, width=120)
        self.height_entry.pack(pady=(2, 0))

        # Presets section
        presets_frame = ctk.CTkFrame(scrollable)
        presets_frame.pack(fill='x', padx=10, pady=(5, 5))

        ctk.CTkLabel(presets_frame, text="Presets:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor='w', padx=10, pady=(10, 5))

        preset_controls_frame = ctk.CTkFrame(presets_frame, fg_color="transparent")
        preset_controls_frame.pack(fill='x', padx=10, pady=(0, 10))

        self.preset_menu = ctk.CTkOptionMenu(
            preset_controls_frame,
            variable=self.preset_var,
            command=self._on_preset_select,
            width=200
        )
        self.preset_menu.pack(side='left', padx=(0, 10))

        self.add_preset_btn = ctk.CTkButton(preset_controls_frame, text="+", command=self._add_preset, width=30)
        self.add_preset_btn.pack(side='left', padx=(0, 5))

        self.remove_preset_btn = ctk.CTkButton(preset_controls_frame, text="-", command=self._remove_preset, width=30)
        self.remove_preset_btn.pack(side='left')

        # Progress section
        progress_frame = ctk.CTkFrame(scrollable)
        progress_frame.pack(fill='x', padx=10, pady=(5, 10))

        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=400)
        self.progress_bar.pack(pady=(10, 5))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(progress_frame, text="Ready")
        self.status_label.pack(pady=(0, 10))

        # Control buttons
        buttons_frame = ctk.CTkFrame(scrollable, fg_color="transparent")
        buttons_frame.pack(fill='x', padx=10, pady=(0, 10))

        self.resize_btn = ctk.CTkButton(
            buttons_frame,
            text="Start Resizing",
            command=self._start_resize,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.resize_btn.pack(pady=5)

        # Configure grid weights for proper resizing
        scrollable.grid_columnconfigure(0, weight=1)

    def _load_presets(self):
        """Load presets into the dropdown menu."""
        preset_names = self.config_manager.get_preset_names()
        self.preset_menu.configure(values=preset_names)
        if "Custom" in preset_names:
            self.preset_var.set("Custom")

    def _browse_input(self):
        """Browse for input directory."""
        directory = filedialog.askdirectory(title="Select Input Directory")
        if directory:
            self.input_dir.set(directory)

    def _browse_output(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir.set(directory)

    def _on_preset_select(self, preset_name: str):
        """Handle preset selection."""
        preset = self.config_manager.get_preset(preset_name)
        if preset:
            if preset.width is not None:
                self.width_var.set(str(preset.width))
            else:
                self.width_var.set("")

            if preset.height is not None:
                self.height_var.set(str(preset.height))
            else:
                self.height_var.set("")

    def _add_preset(self):
        """Add a new preset (placeholder for future enhancement)."""
        # For now, just show a message
        self.status_label.configure(text="Preset management coming soon!")

    def _remove_preset(self):
        """Remove the currently selected preset."""
        current_preset = self.preset_var.get()
        if current_preset and current_preset != "Custom":
            self.config_manager.remove_preset(current_preset)
            self._load_presets()
            self.preset_var.set("Custom")
            self.status_label.configure(text=f"Removed preset: {current_preset}")
        else:
            self.status_label.configure(text="Cannot remove Custom preset")

    def _start_resize(self):
        """Start the resize operation."""
        if self.is_processing:
            return

        input_path = self.input_dir.get().strip()
        if not input_path:
            self.status_label.configure(text="Please select an input directory")
            return

        input_dir = Path(input_path)
        if not input_dir.exists() or not input_dir.is_dir():
            self.status_label.configure(text="Input directory does not exist")
            return

        width_spec = self.width_var.get().strip()
        height_spec = self.height_var.get().strip()

        if not self.resizer.validate_dimensions(width_spec, height_spec):
            self.status_label.configure(text="Please specify at least one valid dimension")
            return

        # Determine output directory
        output_path = self.output_dir.get().strip()
        if not output_path:
            output_path = str(input_dir / self.config_manager.config.default_output_subfolder)

        output_dir = Path(output_path)

        # Start processing in background thread
        self._set_processing_state(True)
        self.status_label.configure(text="Starting batch resize...")

        thread = threading.Thread(
            target=self._run_resize,
            args=(input_dir, output_dir, width_spec, height_spec),
            daemon=True
        )
        thread.start()

    def _run_resize(self, input_dir: Path, output_dir: Path, width_spec: str, height_spec: str):
        """Run the resize operation in background thread."""
        try:
            success_count, failure_count = self.resizer.resize_batch(
                input_dir=input_dir,
                output_dir=output_dir,
                width_spec=width_spec,
                height_spec=height_spec,
                progress_callback=self._update_progress
            )

            self.after(0, lambda: self._on_resize_complete(success_count, failure_count, output_dir))

        except Exception as e:
            logger.error(f"Resize operation failed: {e}")
            self.after(0, lambda: self._on_resize_error(str(e)))

    def _update_progress(self, current: int, total: int, success: int, failure: int):
        """Update progress display."""
        progress = current / total if total > 0 else 0
        self.after(0, lambda: self._update_progress_ui(progress, current, total, success, failure))

    def _update_progress_ui(self, progress: float, current: int, total: int, success: int, failure: int):
        """Update progress UI elements."""
        self.progress_bar.set(progress)
        self.status_label.configure(text=f"Processing {current}/{total}... (✓{success} ✗{failure})")

    def _on_resize_complete(self, success_count: int, failure_count: int, output_dir: Path):
        """Handle successful resize completion."""
        self._set_processing_state(False)
        self.progress_bar.set(1.0)
        self.status_label.configure(
            text=f"Completed! ✓{success_count} successful, ✗{failure_count} failed. Saved to: {output_dir}"
        )

    def _on_resize_error(self, error_msg: str):
        """Handle resize error."""
        self._set_processing_state(False)
        self.progress_bar.set(0)
        self.status_label.configure(text=f"Error: {error_msg}")

    def _set_processing_state(self, processing: bool):
        """Set the processing state of UI controls."""
        self.is_processing = processing

        state = "disabled" if processing else "normal"
        self.input_entry.configure(state=state)
        self.output_entry.configure(state=state)
        self.width_entry.configure(state=state)
        self.height_entry.configure(state=state)
        self.preset_menu.configure(state=state)
        self.browse_input_btn.configure(state=state)
        self.browse_output_btn.configure(state=state)
        self.add_preset_btn.configure(state=state)
        self.remove_preset_btn.configure(state=state)

        button_text = "Cancel" if processing else "Start Resizing"
        self.resize_btn.configure(text=button_text, state=state)


def main():
    """Main entry point for GUI application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    app = ImageResizeApp()
    app.mainloop()


if __name__ == "__main__":
    main()