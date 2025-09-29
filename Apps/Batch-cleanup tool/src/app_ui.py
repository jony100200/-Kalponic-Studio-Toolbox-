"""
Professional CustomTkinter GUI for KS Image Cleanup — professional quality fringe removal and edge enhancement.
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
        self.root.title("KS Image Cleanup")
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
        
    def setup_header(self):
        """Setup cyberpunk-styled header section."""
        header_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=CYBERPUNK_COLORS['bg_secondary'],
            border_width=2,
            border_color=CYBERPUNK_COLORS['accent_cyan']
        )
        header_frame.pack(fill="x", pady=(0, 15))
        
        # Title with cyberpunk styling
        title_label = ctk.CTkLabel(
            header_frame,
            text="KS Image Cleanup",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=CYBERPUNK_COLORS['accent_cyan']
        )
        title_label.pack(pady=(15, 5))
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Professional Edge Cleanup & Fringe Removal",
            font=ctk.CTkFont(size=12),
            text_color=CYBERPUNK_COLORS['text_secondary']
        )
        subtitle_label.pack(pady=(0, 15))
    
    def setup_processor_selection(self):
        """Setup processor type selection with professional options."""
        processor_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=CYBERPUNK_COLORS['bg_secondary'],
            border_width=1,
            border_color=CYBERPUNK_COLORS['border']
        )
        processor_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            processor_frame,
            text="⚙ Processing Engine",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CYBERPUNK_COLORS['accent_purple']
        ).pack(pady=(15, 10))
        
        # Processor type selection
        processor_row = ctk.CTkFrame(processor_frame, fg_color="transparent")
        processor_row.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            processor_row,
            text="Engine:",
            text_color=CYBERPUNK_COLORS['text_primary']
        ).pack(side="left", padx=(0, 10))
        
        processor_options = ["Professional", "OpenCV Enhanced", "Basic"]
        if ProcessorType:
            processor_options = [p.value for p in ProcessorType]
        
        self.processor_dropdown = ctk.CTkOptionMenu(
            processor_row,
            variable=self.processor_type_var,
            values=processor_options,
            button_color=CYBERPUNK_COLORS['accent_purple'],
            button_hover_color=CYBERPUNK_COLORS['hover'],
            dropdown_hover_color=CYBERPUNK_COLORS['hover']
        )
        self.processor_dropdown.pack(side="left", padx=(0, 20))
        
        # Material type selection
        ctk.CTkLabel(
            processor_row,
            text="Material:",
            text_color=CYBERPUNK_COLORS['text_primary']
        ).pack(side="left", padx=(0, 10))
        
        material_options = ["Auto Detect", "Standard", "Hair/Fur", "Glass/Transparent", "Complex Edges"]
        if MaterialType:
            material_options = [m.value for m in MaterialType]
        
        self.material_dropdown = ctk.CTkOptionMenu(
            processor_row,
            variable=self.material_type_var,
            values=material_options,
            button_color=CYBERPUNK_COLORS['accent_cyan'],
            button_hover_color=CYBERPUNK_COLORS['hover'],
            dropdown_hover_color=CYBERPUNK_COLORS['hover']
        )
        self.material_dropdown.pack(side="left")
    
    def setup_processing_presets(self):
        """Setup Photoshop-like preset selection."""
        presets_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=CYBERPUNK_COLORS['bg_secondary'],
            border_width=1,
            border_color=CYBERPUNK_COLORS['border']
        )
        presets_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            presets_frame,
            text="⚡ Quick Presets",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CYBERPUNK_COLORS['accent_orange']
        ).pack(pady=(15, 10))
        
        # Preset buttons row
        presets_row = ctk.CTkFrame(presets_frame, fg_color="transparent")
        presets_row.pack(fill="x", padx=15, pady=(0, 15))
        
        preset_buttons = [
            ("Photoshop-like", CYBERPUNK_COLORS['accent_cyan'], self.load_photoshop_preset),
            ("Hair/Fur Specialist", CYBERPUNK_COLORS['accent_purple'], self.load_hair_preset),
            ("Glass/Transparent", CYBERPUNK_COLORS['accent_green'], self.load_glass_preset),
            ("Maximum Quality", CYBERPUNK_COLORS['accent_orange'], self.load_max_quality_preset)
        ]
        
        for i, (text, color, command) in enumerate(preset_buttons):
            btn = ctk.CTkButton(
                presets_row,
                text=text,
                fg_color=color,
                hover_color=CYBERPUNK_COLORS['hover'],
                command=command,
                width=120
            )
            btn.pack(side="left", padx=(0, 10) if i < 3 else (0, 0))
    
    def setup_folder_selection(self):
        """Setup folder selection section with cyberpunk styling."""
        # Folder Selection Frame
        folder_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=CYBERPUNK_COLORS['bg_secondary'],
            border_width=1,
            border_color=CYBERPUNK_COLORS['border']
        )
        folder_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            folder_frame,
            text="📁 Folder Selection",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CYBERPUNK_COLORS['accent_cyan']
        ).pack(pady=(15, 10))
        
        # Input folder
        input_frame = ctk.CTkFrame(
            folder_frame,
            fg_color=CYBERPUNK_COLORS['bg_accent'],
            border_width=1,
            border_color=CYBERPUNK_COLORS['border']
        )
        input_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            input_frame,
            text="Input Folder:",
            text_color=CYBERPUNK_COLORS['text_primary']
        ).pack(anchor="w", padx=15, pady=(15, 0))
        
        input_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        input_row.pack(fill="x", padx=15, pady=(8, 15))
        
        self.input_entry = ctk.CTkEntry(
            input_row,
            textvariable=self.input_folder_var,
            placeholder_text="Select input folder...",
            border_color=CYBERPUNK_COLORS['border'],
            fg_color=CYBERPUNK_COLORS['bg_primary']
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        ctk.CTkButton(
            input_row,
            text="Browse",
            width=80,
            fg_color=CYBERPUNK_COLORS['accent_cyan'],
            hover_color=CYBERPUNK_COLORS['hover'],
            command=self.browse_input_folder
        ).pack(side="right")
        
        # Output folder
        output_frame = ctk.CTkFrame(
            folder_frame,
            fg_color=CYBERPUNK_COLORS['bg_accent'],
            border_width=1,
            border_color=CYBERPUNK_COLORS['border']
        )
        output_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        ctk.CTkLabel(
            output_frame,
            text="Output Folder:",
            text_color=CYBERPUNK_COLORS['text_primary']
        ).pack(anchor="w", padx=15, pady=(15, 0))
        
        output_row = ctk.CTkFrame(output_frame, fg_color="transparent")
        output_row.pack(fill="x", padx=15, pady=(8, 15))
        
        self.output_entry = ctk.CTkEntry(
            output_row,
            textvariable=self.output_folder_var,
            placeholder_text="Select output folder...",
            border_color=CYBERPUNK_COLORS['border'],
            fg_color=CYBERPUNK_COLORS['bg_primary']
        )
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        ctk.CTkButton(
            output_row,
            text="Browse",
            width=80,
            fg_color=CYBERPUNK_COLORS['accent_cyan'],
            hover_color=CYBERPUNK_COLORS['hover'],
            command=self.browse_output_folder
        ).pack(side="right")
    
    def setup_processing_options(self):
        """Setup processing options section with enhanced ranges and cyberpunk styling."""
        # Processing Options Frame
        options_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=CYBERPUNK_COLORS['bg_secondary'],
            border_width=1,
            border_color=CYBERPUNK_COLORS['border']
        )
        options_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            options_frame,
            text="⚙ Processing Options",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CYBERPUNK_COLORS['accent_cyan']
        ).pack(pady=(15, 10))
        
        # Matte preset
        matte_frame = ctk.CTkFrame(
            options_frame,
            fg_color=CYBERPUNK_COLORS['bg_accent'],
            border_width=1,
            border_color=CYBERPUNK_COLORS['border']
        )
        matte_frame.pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(
            matte_frame,
            text="Matte Preset:",
            text_color=CYBERPUNK_COLORS['text_primary']
        ).pack(anchor="w", padx=15, pady=(15, 0))
        
        self.matte_dropdown = ctk.CTkOptionMenu(
            matte_frame,
            variable=self.matte_preset_var,
            values=[preset.value for preset in MattePreset],
            button_color=CYBERPUNK_COLORS['accent_cyan'],
            button_hover_color=CYBERPUNK_COLORS['hover'],
            dropdown_hover_color=CYBERPUNK_COLORS['hover']
        )
        self.matte_dropdown.pack(anchor="w", padx=15, pady=(8, 15))
        
        # Alpha refinement controls with enhanced ranges
        alpha_frame = ctk.CTkFrame(
            options_frame,
            fg_color=CYBERPUNK_COLORS['bg_accent'],
            border_width=1,
            border_color=CYBERPUNK_COLORS['border']
        )
        alpha_frame.pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(
            alpha_frame,
            text="Alpha Refinement",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CYBERPUNK_COLORS['text_primary']
        ).pack(pady=(15, 10))
        
        # Enhanced Smooth control (0-5 range)
        smooth_frame = ctk.CTkFrame(alpha_frame, fg_color="transparent")
        smooth_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            smooth_frame,
            text="Smooth (0-5):",
            text_color=CYBERPUNK_COLORS['text_secondary']
        ).pack(side="left", padx=(0, 10))
        
        self.smooth_slider = ctk.CTkSlider(
            smooth_frame,
            from_=0, to=5, number_of_steps=5,
            variable=self.smooth_var,
            button_color=CYBERPUNK_COLORS['accent_cyan'],
            button_hover_color=CYBERPUNK_COLORS['hover']
        )
        self.smooth_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.smooth_label = ctk.CTkLabel(smooth_frame, text="2", width=30)
        self.smooth_label.pack(side="right", padx=(5, 0))
        
        # Enhanced Feather control (0-5 range)
        feather_frame = ctk.CTkFrame(alpha_frame, fg_color="transparent")
        feather_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            feather_frame,
            text="Feather (0-5):",
            text_color=CYBERPUNK_COLORS['text_secondary']
        ).pack(side="left", padx=(0, 10))
        
        self.feather_slider = ctk.CTkSlider(
            feather_frame,
            from_=0, to=5, number_of_steps=5,
            variable=self.feather_var,
            button_color=CYBERPUNK_COLORS['accent_purple'],
            button_hover_color=CYBERPUNK_COLORS['hover']
        )
        self.feather_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.feather_label = ctk.CTkLabel(feather_frame, text="1", width=30)
        self.feather_label.pack(side="right", padx=(5, 0))
        
        # Enhanced Contrast control (0.5-5.0 range)
        contrast_frame = ctk.CTkFrame(alpha_frame, fg_color="transparent")
        contrast_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            contrast_frame,
            text="Contrast (0.5-5.0):",
            text_color=CYBERPUNK_COLORS['text_secondary']
        ).pack(side="left", padx=(0, 10))
        
        self.contrast_slider = ctk.CTkSlider(
            contrast_frame,
            from_=0.5, to=5.0,
            variable=self.contrast_var,
            button_color=CYBERPUNK_COLORS['accent_green'],
            button_hover_color=CYBERPUNK_COLORS['hover']
        )
        self.contrast_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.contrast_label = ctk.CTkLabel(contrast_frame, text="3.0", width=30)
        self.contrast_label.pack(side="right", padx=(5, 0))
        
        # Enhanced Shift Edge control (-5 to +5 range)
        shift_frame = ctk.CTkFrame(alpha_frame, fg_color="transparent")
        shift_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        ctk.CTkLabel(
            shift_frame,
            text="Shift Edge (-5 to +5):",
            text_color=CYBERPUNK_COLORS['text_secondary']
        ).pack(side="left", padx=(0, 10))
        
        self.shift_slider = ctk.CTkSlider(
            shift_frame,
            from_=-5, to=5, number_of_steps=10,
            variable=self.shift_edge_var,
            button_color=CYBERPUNK_COLORS['accent_orange'],
            button_hover_color=CYBERPUNK_COLORS['hover']
        )
        self.shift_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.shift_label = ctk.CTkLabel(shift_frame, text="-1", width=30)
        self.shift_label.pack(side="right", padx=(5, 0))
    
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
    
    def setup_professional_options(self):
        """Setup professional processing options with cyberpunk styling."""
        # Professional Options Frame
        pro_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=CYBERPUNK_COLORS['bg_secondary'],
            border_width=1,
            border_color=CYBERPUNK_COLORS['accent_purple']
        )
        pro_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            pro_frame,
            text="⚙ Professional Features (Photoshop-like)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CYBERPUNK_COLORS['accent_purple']
        ).pack(pady=(15, 10))
        
        # Professional toggles in a grid
        toggles_frame = ctk.CTkFrame(pro_frame, fg_color="transparent")
        toggles_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Row 1
        row1 = ctk.CTkFrame(toggles_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 8))
        
        self.surgical_toggle = ctk.CTkSwitch(
            row1,
            text="Surgical Processing (PS Local Fix)",
            variable=self.surgical_processing_var,
            button_color=CYBERPUNK_COLORS['accent_purple'],
            button_hover_color=CYBERPUNK_COLORS['hover'],
            text_color=CYBERPUNK_COLORS['text_primary']
        )
        self.surgical_toggle.pack(side="left", padx=(0, 30))
        
        self.pyramid_toggle = ctk.CTkSwitch(
            row1,
            text="Alpha Pyramid (Glass/Transparency)",
            variable=self.use_alpha_pyramid_var,
            button_color=CYBERPUNK_COLORS['accent_cyan'],
            button_hover_color=CYBERPUNK_COLORS['hover'],
            text_color=CYBERPUNK_COLORS['text_primary']
        )
        self.pyramid_toggle.pack(side="left")
        
        # Row 2
        row2 = ctk.CTkFrame(toggles_frame, fg_color="transparent")
        row2.pack(fill="x")
        
        self.legacy_toggle = ctk.CTkSwitch(
            row2,
            text="Legacy Contrast (PS Re-harden)",
            variable=self.legacy_contrast_var,
            button_color=CYBERPUNK_COLORS['accent_green'],
            button_hover_color=CYBERPUNK_COLORS['hover'],
            text_color=CYBERPUNK_COLORS['text_primary']
        )
        self.legacy_toggle.pack(side="left", padx=(0, 30))
        
        self.details_toggle = ctk.CTkSwitch(
            row2,
            text="Preserve Fine Details (Hair/Fur)",
            variable=self.preserve_details_var,
            button_color=CYBERPUNK_COLORS['accent_orange'],
            button_hover_color=CYBERPUNK_COLORS['hover'],
            text_color=CYBERPUNK_COLORS['text_primary']
        )
        self.details_toggle.pack(side="left")
    
    # Preset loading methods
    def load_photoshop_preset(self):
        """Load Photoshop-like preset configuration."""
        if PresetConfigs:
            config = PresetConfigs.photoshop_like()
            self.apply_preset_config(config)
        else:
            # Fallback manual configuration
            self.matte_preset_var.set("White Matte")
            self.smooth_var.set(1)
            self.feather_var.set(1)
            self.contrast_var.set(3.5)
            self.shift_edge_var.set(-1)
            self.fringe_fix_var.set(True)
            self.fringe_band_var.set(2)
            self.fringe_strength_var.set(3)
            self.surgical_processing_var.set(True)
            self.legacy_contrast_var.set(True)
        self.update_all_labels()

    def load_hair_preset(self):
        """Load hair/fur specialist preset."""
        if PresetConfigs:
            config = PresetConfigs.hair_fur_specialist()
            self.apply_preset_config(config)
        else:
            self.material_type_var.set("Hair/Fur")
            self.smooth_var.set(1)
            self.feather_var.set(0)
            self.contrast_var.set(2.5)
            self.shift_edge_var.set(0)
            self.preserve_details_var.set(True)
            self.surgical_processing_var.set(True)
        self.update_all_labels()

    def load_glass_preset(self):
        """Load glass/transparent preset."""
        if PresetConfigs:
            config = PresetConfigs.glass_transparent()
            self.apply_preset_config(config)
        else:
            self.material_type_var.set("Glass/Transparent")
            self.smooth_var.set(3)
            self.feather_var.set(2)
            self.contrast_var.set(2.0)
            self.shift_edge_var.set(0)
            self.use_alpha_pyramid_var.set(True)
        self.update_all_labels()

    def load_max_quality_preset(self):
        """Load maximum quality preset."""
        if PresetConfigs:
            config = PresetConfigs.maximum_quality()
            self.apply_preset_config(config)
        else:
            self.processor_type_var.set("Professional")
            self.material_type_var.set("Auto Detect")
            self.smooth_var.set(2)
            self.feather_var.set(2)
            self.contrast_var.set(3.0)
            self.shift_edge_var.set(-1)
            self.surgical_processing_var.set(True)
            self.use_alpha_pyramid_var.set(True)
            self.legacy_contrast_var.set(True)
            self.preserve_details_var.set(True)
        self.update_all_labels()

    def apply_preset_config(self, config):
        """Apply a preset configuration to the UI."""
        self.matte_preset_var.set(config.matte_preset.value)
        self.smooth_var.set(config.smooth)
        self.feather_var.set(config.feather)
        self.contrast_var.set(config.contrast)
        self.shift_edge_var.set(config.shift_edge)
        self.fringe_fix_var.set(config.fringe_fix_enabled)
        self.fringe_band_var.set(config.fringe_band)
        self.fringe_strength_var.set(config.fringe_strength)
        
        if hasattr(config, 'professional') and config.professional:
            prof = config.professional
            if hasattr(prof, 'processor_type'):
                self.processor_type_var.set(prof.processor_type.value)
            if hasattr(prof, 'material_type'):
                self.material_type_var.set(prof.material_type.value)
            self.surgical_processing_var.set(prof.surgical_processing)
            self.use_alpha_pyramid_var.set(prof.use_alpha_pyramid)
            self.legacy_contrast_var.set(prof.legacy_contrast_mode)
            self.preserve_details_var.set(prof.preserve_fine_details)
    
    def update_all_labels(self):
        """Update all slider labels with current values."""
        try:
            self.smooth_label.configure(text=str(self.smooth_var.get()))
            self.feather_label.configure(text=str(self.feather_var.get()))
            self.contrast_label.configure(text=f"{self.contrast_var.get():.1f}")
            self.shift_label.configure(text=str(self.shift_edge_var.get()))
            self.band_label.configure(text=str(self.fringe_band_var.get()))
            self.strength_label.configure(text=str(self.fringe_strength_var.get()))
        except AttributeError:
            # Labels might not be created yet
            pass
