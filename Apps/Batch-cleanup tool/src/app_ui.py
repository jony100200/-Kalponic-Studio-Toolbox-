"""
Professional CustomTkinter GUI for the Batch Image Cleanup Tool.
Cyberpunk-themed interface with muted colors for comfortable viewing.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import logging
from typing import Optional, Dict, Any

from .controller import Controller
from .config import MattePreset
try:
    from .config_professional import ProcessorType, MaterialType, PresetConfigs, ProfessionalConfig
except ImportError:
    # Fallback if professional config doesn't exist yet
    ProcessorType = None
    MaterialType = None
    PresetConfigs = None
    ProfessionalConfig = None

logger = logging.getLogger(__name__)

# Set appearance mode and cyberpunk color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Cyberpunk color palette - muted, eye-friendly
CYBERPUNK_COLORS = {
    'bg_primary': '#0a0b0d',      # Very dark background
    'bg_secondary': '#1a1d23',    # Secondary dark
    'bg_accent': '#252831',       # Accent frames
    'text_primary': '#e8e8e8',    # Primary text
    'text_secondary': '#a8b2c8',  # Secondary text
    'accent_cyan': '#4a9eff',     # Muted cyan
    'accent_purple': '#8b5fbf',   # Muted purple
    'accent_green': '#5fb85f',    # Muted green
    'accent_red': '#bf5f5f',      # Muted red
    'accent_orange': '#bf8f5f',   # Muted orange
    'border': '#3a4054',          # Border color
    'hover': '#2a3044'            # Hover state
}

class AppUI:
    """Professional application UI with cyberpunk theming and advanced features."""
    
    def __init__(self, controller: Controller):
        self.controller = controller
        self.controller.set_progress_callback(self.update_progress)
        
        # Initialize main window with cyberpunk styling
        self.root = ctk.CTk()
        self.root.title("Professional Image Cleanup Tool - Photoshop Quality")
        self.root.geometry("900x900")
        
        # Configure cyberpunk theme colors
        self.root.configure(fg_color=CYBERPUNK_COLORS['bg_primary'])
        
        # Set window icon and other properties
        self.root.resizable(True, True)
        self.root.minsize(800, 700)
        
        # Variables for UI controls
        self.input_folder_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        self.matte_preset_var = tk.StringVar(value=MattePreset.WHITE_MATTE.value)
        
        # Enhanced ranges for professional processing
        self.smooth_var = tk.IntVar(value=2)
        self.feather_var = tk.IntVar(value=1)
        self.contrast_var = tk.DoubleVar(value=3.0)
        self.shift_edge_var = tk.IntVar(value=-1)
        self.fringe_fix_var = tk.BooleanVar(value=True)
        self.fringe_band_var = tk.IntVar(value=2)
        self.fringe_strength_var = tk.IntVar(value=2)
        self.skip_existing_var = tk.BooleanVar(value=True)
        
        # Professional processing variables
        if ProcessorType:
            self.processor_type_var = tk.StringVar(value=ProcessorType.PROFESSIONAL.value)
            self.material_type_var = tk.StringVar(value=MaterialType.AUTO.value)
        else:
            self.processor_type_var = tk.StringVar(value="Professional")
            self.material_type_var = tk.StringVar(value="Auto Detect")
        
        self.surgical_processing_var = tk.BooleanVar(value=True)
        self.use_alpha_pyramid_var = tk.BooleanVar(value=True)
        self.legacy_contrast_var = tk.BooleanVar(value=True)
        self.preserve_details_var = tk.BooleanVar(value=True)
        
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0.0)
        
        # Preview image references
        self.preview_original: Optional[ImageTk.PhotoImage] = None
        self.preview_processed: Optional[ImageTk.PhotoImage] = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the complete professional UI layout with cyberpunk styling."""
        # Create main container with scrollable frame
        self.main_frame = ctk.CTkScrollableFrame(
            self.root,
            fg_color=CYBERPUNK_COLORS['bg_primary'],
            scrollbar_button_color=CYBERPUNK_COLORS['accent_cyan'],
            scrollbar_button_hover_color=CYBERPUNK_COLORS['hover']
        )
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Add cyberpunk header
        self.setup_header()
        self.setup_processor_selection()
        self.setup_folder_selection()
        self.setup_processing_presets()
        self.setup_processing_options()
        self.setup_professional_options()
        self.setup_fringe_fix()
        self.setup_control_buttons()
        self.setup_progress_section()
        self.setup_preview_section()
        
        # Bind UI events to controller
        self.bind_events()
        
    def setup_folder_selection(self):
        """Setup folder selection section."""
        # Folder Selection Frame
        folder_frame = ctk.CTkFrame(self.main_frame)
        folder_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(folder_frame, text="Folder Selection", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        # Input folder
        input_frame = ctk.CTkFrame(folder_frame)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(input_frame, text="Input Folder:").pack(anchor="w", padx=10, pady=(10, 0))
        
        input_row = ctk.CTkFrame(input_frame)
        input_row.pack(fill="x", padx=10, pady=(5, 10))
        
        self.input_entry = ctk.CTkEntry(input_row, textvariable=self.input_folder_var, 
                                       placeholder_text="Select input folder...")
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(input_row, text="Browse", width=80,
                     command=self.browse_input_folder).pack(side="right")
        
        # Output folder
        output_frame = ctk.CTkFrame(folder_frame)
        output_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(output_frame, text="Output Folder:").pack(anchor="w", padx=10, pady=(10, 0))
        
        output_row = ctk.CTkFrame(output_frame)
        output_row.pack(fill="x", padx=10, pady=(5, 10))
        
        self.output_entry = ctk.CTkEntry(output_row, textvariable=self.output_folder_var,
                                        placeholder_text="Select output folder...")
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(output_row, text="Browse", width=80,
                     command=self.browse_output_folder).pack(side="right")
    
    def setup_processing_options(self):
        """Setup processing options section."""
        # Processing Options Frame
        options_frame = ctk.CTkFrame(self.main_frame)
        options_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(options_frame, text="Processing Options", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        # Matte preset
        matte_frame = ctk.CTkFrame(options_frame)
        matte_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(matte_frame, text="Matte Preset:").pack(anchor="w", padx=10, pady=(10, 0))
        
        self.matte_dropdown = ctk.CTkOptionMenu(
            matte_frame, 
            variable=self.matte_preset_var,
            values=[preset.value for preset in MattePreset]
        )
        self.matte_dropdown.pack(anchor="w", padx=10, pady=(5, 10))
        
        # Alpha refinement controls
        alpha_frame = ctk.CTkFrame(options_frame)
        alpha_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(alpha_frame, text="Alpha Refinement", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
        
        # Smooth control
        smooth_frame = ctk.CTkFrame(alpha_frame)
        smooth_frame.pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(smooth_frame, text="Smooth (0-3):").pack(side="left", padx=(10, 5))
        self.smooth_slider = ctk.CTkSlider(smooth_frame, from_=0, to=3, number_of_steps=3,
                                          variable=self.smooth_var)
        self.smooth_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.smooth_label = ctk.CTkLabel(smooth_frame, text="2", width=30)
        self.smooth_label.pack(side="right", padx=(5, 10))
        
        # Feather control
        feather_frame = ctk.CTkFrame(alpha_frame)
        feather_frame.pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(feather_frame, text="Feather (0-3):").pack(side="left", padx=(10, 5))
        self.feather_slider = ctk.CTkSlider(feather_frame, from_=0, to=3, number_of_steps=3,
                                           variable=self.feather_var)
        self.feather_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.feather_label = ctk.CTkLabel(feather_frame, text="1", width=30)
        self.feather_label.pack(side="right", padx=(5, 10))
        
        # Contrast control
        contrast_frame = ctk.CTkFrame(alpha_frame)
        contrast_frame.pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(contrast_frame, text="Contrast (1.0-4.0):").pack(side="left", padx=(10, 5))
        self.contrast_slider = ctk.CTkSlider(contrast_frame, from_=1.0, to=4.0, 
                                            variable=self.contrast_var)
        self.contrast_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.contrast_label = ctk.CTkLabel(contrast_frame, text="3.0", width=30)
        self.contrast_label.pack(side="right", padx=(5, 10))
        
        # Shift Edge control
        shift_frame = ctk.CTkFrame(alpha_frame)
        shift_frame.pack(fill="x", padx=10, pady=(2, 10))
        
        ctk.CTkLabel(shift_frame, text="Shift Edge (-2 to +2):").pack(side="left", padx=(10, 5))
        self.shift_slider = ctk.CTkSlider(shift_frame, from_=-2, to=2, number_of_steps=4,
                                         variable=self.shift_edge_var)
        self.shift_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.shift_label = ctk.CTkLabel(shift_frame, text="-1", width=30)
        self.shift_label.pack(side="right", padx=(5, 10))
    
    def setup_fringe_fix(self):
        """Setup fringe fix section."""
        # Fringe Fix Frame
        fringe_frame = ctk.CTkFrame(self.main_frame)
        fringe_frame.pack(fill="x", pady=(0, 10))
        
        # Header with toggle
        fringe_header = ctk.CTkFrame(fringe_frame)
        fringe_header.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(fringe_header, text="Fringe Fix", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        
        self.fringe_toggle = ctk.CTkSwitch(fringe_header, text="Enable", 
                                          variable=self.fringe_fix_var)
        self.fringe_toggle.pack(side="right")
        
        # Fringe controls
        self.fringe_controls_frame = ctk.CTkFrame(fringe_frame)
        self.fringe_controls_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Band control
        band_frame = ctk.CTkFrame(self.fringe_controls_frame)
        band_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(band_frame, text="Band (1-3):").pack(side="left", padx=(10, 5))
        self.band_slider = ctk.CTkSlider(band_frame, from_=1, to=3, number_of_steps=2,
                                        variable=self.fringe_band_var)
        self.band_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.band_label = ctk.CTkLabel(band_frame, text="2", width=30)
        self.band_label.pack(side="right", padx=(5, 10))
        
        # Strength control
        strength_frame = ctk.CTkFrame(self.fringe_controls_frame)
        strength_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(strength_frame, text="Strength (1-3):").pack(side="left", padx=(10, 5))
        self.strength_slider = ctk.CTkSlider(strength_frame, from_=1, to=3, number_of_steps=2,
                                            variable=self.fringe_strength_var)
        self.strength_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.strength_label = ctk.CTkLabel(strength_frame, text="2", width=30)
        self.strength_label.pack(side="right", padx=(5, 10))
    
    def setup_control_buttons(self):
        """Setup control buttons section."""
        # Control Buttons Frame
        control_frame = ctk.CTkFrame(self.main_frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        # Options row
        options_row = ctk.CTkFrame(control_frame)
        options_row.pack(fill="x", padx=10, pady=(10, 5))
        
        self.skip_existing_cb = ctk.CTkCheckBox(options_row, text="Skip existing files", 
                                               variable=self.skip_existing_var)
        self.skip_existing_cb.pack(side="left", padx=10)
        
        ctk.CTkButton(options_row, text="Reset to Defaults", 
                     command=self.reset_defaults).pack(side="right", padx=10)
        
        # Main buttons row
        button_row = ctk.CTkFrame(control_frame)
        button_row.pack(fill="x", padx=10, pady=(5, 10))
        
        self.preview_btn = ctk.CTkButton(button_row, text="Generate Preview", 
                                        command=self.generate_preview)
        self.preview_btn.pack(side="left", padx=(0, 5))
        
        self.run_btn = ctk.CTkButton(button_row, text="Run Batch", 
                                    command=self.start_processing,
                                    fg_color="green", hover_color="darkgreen")
        self.run_btn.pack(side="right", padx=(5, 0))
        
        self.cancel_btn = ctk.CTkButton(button_row, text="Cancel", 
                                       command=self.stop_processing,
                                       fg_color="red", hover_color="darkred")
        self.cancel_btn.pack(side="right", padx=(5, 5))
        self.cancel_btn.configure(state="disabled")
    
    def setup_progress_section(self):
        """Setup progress tracking section."""
        # Progress Frame
        progress_frame = ctk.CTkFrame(self.main_frame)
        progress_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(progress_frame, text="Progress", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        # Status label
        self.status_label = ctk.CTkLabel(progress_frame, textvariable=self.status_var)
        self.status_label.pack(pady=(0, 10))
    
    def setup_preview_section(self):
        """Setup preview section."""
        # Preview Frame
        preview_frame = ctk.CTkFrame(self.main_frame)
        preview_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(preview_frame, text="Preview", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        # Preview container
        self.preview_container = ctk.CTkFrame(preview_frame)
        self.preview_container.pack(fill="x", padx=10, pady=(0, 10))
        
        # Preview labels
        preview_labels_frame = ctk.CTkFrame(self.preview_container)
        preview_labels_frame.pack(fill="x", pady=(10, 5))
        
        ctk.CTkLabel(preview_labels_frame, text="Original").pack(side="left", padx=(10, 0))
        ctk.CTkLabel(preview_labels_frame, text="Processed").pack(side="right", padx=(0, 10))
        
        # Preview images frame
        self.preview_images_frame = ctk.CTkFrame(self.preview_container)
        self.preview_images_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Placeholder labels for images
        self.original_preview_label = ctk.CTkLabel(self.preview_images_frame, 
                                                  text="No preview", width=300, height=200)
        self.original_preview_label.pack(side="left", padx=(10, 5), pady=10)
        
        self.processed_preview_label = ctk.CTkLabel(self.preview_images_frame, 
                                                   text="No preview", width=300, height=200)
        self.processed_preview_label.pack(side="right", padx=(5, 10), pady=10)
    
    def bind_events(self):
        """Bind UI events to controller methods."""
        # Folder selection
        self.input_folder_var.trace_add("write", lambda *args: 
                                       self.controller.set_input_folder(self.input_folder_var.get()))
        self.output_folder_var.trace_add("write", lambda *args: 
                                        self.controller.set_output_folder(self.output_folder_var.get()))
        
        # Processing options
        self.matte_preset_var.trace_add("write", lambda *args: 
                                       self.controller.update_matte_preset(self.matte_preset_var.get()))
        
        # Slider value updates
        self.smooth_var.trace_add("write", self.update_smooth)
        self.feather_var.trace_add("write", self.update_feather)
        self.contrast_var.trace_add("write", self.update_contrast)
        self.shift_edge_var.trace_add("write", self.update_shift_edge)
        
        # Fringe fix
        self.fringe_fix_var.trace_add("write", self.update_fringe_fix)
        self.fringe_band_var.trace_add("write", self.update_fringe_band)
        self.fringe_strength_var.trace_add("write", self.update_fringe_strength)
        
        # Options
        self.skip_existing_var.trace_add("write", lambda *args: 
                                        self.controller.update_skip_existing(self.skip_existing_var.get()))
    
    def update_smooth(self, *args):
        """Update smooth value and label."""
        value = self.smooth_var.get()
        self.smooth_label.configure(text=str(value))
        self.controller.update_smooth(value)
    
    def update_feather(self, *args):
        """Update feather value and label."""
        value = self.feather_var.get()
        self.feather_label.configure(text=str(value))
        self.controller.update_feather(value)
    
    def update_contrast(self, *args):
        """Update contrast value and label."""
        value = self.contrast_var.get()
        self.contrast_label.configure(text=f"{value:.1f}")
        self.controller.update_contrast(value)
    
    def update_shift_edge(self, *args):
        """Update shift edge value and label."""
        value = self.shift_edge_var.get()
        self.shift_label.configure(text=str(value))
        self.controller.update_shift_edge(value)
    
    def update_fringe_fix(self, *args):
        """Update fringe fix enabled state."""
        enabled = self.fringe_fix_var.get()
        self.controller.update_fringe_fix(enabled)
        
        # Enable/disable fringe controls
        state = "normal" if enabled else "disabled"
        for widget in self.fringe_controls_frame.winfo_children():
            # Only configure state for specific widget types that support it
            if isinstance(widget, (ctk.CTkSlider, ctk.CTkOptionMenu, ctk.CTkButton)):
                try:
                    widget.configure(state=state)
                except:
                    pass  # Skip if state is not supported
    
    def update_fringe_band(self, *args):
        """Update fringe band value and label."""
        value = self.fringe_band_var.get()
        self.band_label.configure(text=str(value))
        self.controller.update_fringe_band(value)
    
    def update_fringe_strength(self, *args):
        """Update fringe strength value and label."""
        value = self.fringe_strength_var.get()
        self.strength_label.configure(text=str(value))
        self.controller.update_fringe_strength(value)
    
    def browse_input_folder(self):
        """Open folder browser for input folder."""
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.input_folder_var.set(folder)
    
    def browse_output_folder(self):
        """Open folder browser for output folder."""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder_var.set(folder)
    
    def reset_defaults(self):
        """Reset all settings to default values."""
        self.controller.reset_to_defaults()
        self.load_config_values()
    
    def load_config_values(self):
        """Load configuration values from controller to UI."""
        config = self.controller.get_config_values()
        
        self.matte_preset_var.set(config['matte_preset'])
        self.smooth_var.set(config['smooth'])
        self.feather_var.set(config['feather'])
        self.contrast_var.set(config['contrast'])
        self.shift_edge_var.set(config['shift_edge'])
        self.fringe_fix_var.set(config['fringe_fix_enabled'])
        self.fringe_band_var.set(config['fringe_band'])
        self.fringe_strength_var.set(config['fringe_strength'])
        self.skip_existing_var.set(config['skip_existing'])
    
    def start_processing(self):
        """Start batch processing."""
        if not self.controller.get_input_folder():
            messagebox.showerror("Error", "Please select an input folder")
            return
        
        if not self.controller.get_output_folder():
            messagebox.showerror("Error", "Please select an output folder")
            return
        
        success = self.controller.start_processing()
        if success:
            self.run_btn.configure(state="disabled")
            self.cancel_btn.configure(state="normal")
        else:
            messagebox.showerror("Error", "Failed to start processing")
    
    def stop_processing(self):
        """Stop batch processing."""
        self.controller.stop_processing()
        self.run_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
    
    def generate_preview(self):
        """Generate a preview of processing."""
        if not self.controller.get_input_folder():
            messagebox.showwarning("Warning", "Please select an input folder first")
            return
        
        self.preview_btn.configure(state="disabled", text="Generating...")
        self.root.update()
        
        try:
            preview_data = self.controller.generate_preview()
            if preview_data:
                original, processed = preview_data
                self.display_preview(original, processed)
            else:
                messagebox.showinfo("Info", "No images found or unable to generate preview")
        except Exception as e:
            logger.error(f"Preview generation error: {e}")
            messagebox.showerror("Error", f"Failed to generate preview: {e}")
        finally:
            self.preview_btn.configure(state="normal", text="Generate Preview")
    
    def display_preview(self, original: Image.Image, processed: Image.Image):
        """Display preview images."""
        try:
            # Resize images for display
            max_size = (300, 200)
            
            original.thumbnail(max_size, Image.Resampling.LANCZOS)
            processed.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.preview_original = ImageTk.PhotoImage(original)
            self.preview_processed = ImageTk.PhotoImage(processed)
            
            # Update labels
            self.original_preview_label.configure(image=self.preview_original, text="")
            self.processed_preview_label.configure(image=self.preview_processed, text="")
            
        except Exception as e:
            logger.error(f"Preview display error: {e}")
    
    def update_progress(self, status: str, processed: int, total: int, errors: int):
        """Update progress bar and status."""
        try:
            # Update progress bar
            if total > 0:
                progress = processed / total
                self.progress_bar.set(progress)
            else:
                self.progress_bar.set(0)
            
            # Update status
            self.status_var.set(status)
            
            # Update UI
            self.root.update_idletasks()
            
        except Exception as e:
            logger.error(f"Progress update error: {e}")
    
    def run(self):
        """Start the application."""
        try:
            # Load initial config values
            self.load_config_values()
            
            # Start main loop
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"UI runtime error: {e}")
            messagebox.showerror("Fatal Error", f"Application error: {e}")
        finally:
            # Cleanup
            if self.controller.is_processing():
                self.controller.stop_processing()
