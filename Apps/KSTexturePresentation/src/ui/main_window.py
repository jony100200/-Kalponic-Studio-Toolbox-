"""
Main Window UI - Sci-Fi Dark Theme with Folder Batch Processing
Modern dark interface for batch merging icons with backgrounds
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import math
import json

from ..services.image_processor import ImageProcessor
from ..services.file_service import FileService

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MainWindow:
    """Main application window with sci-fi dark theme and batch processing"""
    
    def __init__(self, settings):
        """
        Initialize main window with CustomTkinter
        
        Args:
            settings: Application settings object
        """
        self.settings = settings
        self.image_processor = ImageProcessor()
        self.file_service = FileService(settings.get_supported_formats())
        self.colors = settings.get_sci_fi_colors()
        
        # Initialize UI
        self.root = ctk.CTk()
        self.root.title("🚀 SPRITE NEXUS - Batch Icon Processor")
        self.root.geometry(settings.get_window_size())
        self.root.minsize(800, 600)
        
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        self._build_ui()
    
    def _build_ui(self):
        """Build sci-fi user interface components"""
        # Header with title and status
        self._build_header()
        
        # Main content area with tabview
        self._build_main_content()
        
        # Footer with status and info
        self._build_footer()
        
        # Initialize grid info display
        self._update_grid_info()
    
    def _build_header(self):
        """Build futuristic header section"""
        header_frame = ctk.CTkFrame(self.root, height=80, corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Logo/Icon area
        logo_frame = ctk.CTkFrame(header_frame, width=60, corner_radius=10)
        logo_frame.grid(row=0, column=0, padx=20, pady=15, sticky="ns")
        
        logo_label = ctk.CTkLabel(
            logo_frame, 
            text="🎯",
            font=ctk.CTkFont(size=24)
        )
        logo_label.pack(expand=True)
        
        # Title section
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=1, sticky="ew", padx=10, pady=15)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="SPRITE NEXUS",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.colors["primary"]
        )
        title_label.pack(anchor="w")
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Batch Icon Processing Matrix",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text"]
        )
        subtitle_label.pack(anchor="w")
        
        # System status
        status_frame = ctk.CTkFrame(header_frame, width=120)
        status_frame.grid(row=0, column=2, padx=20, pady=15, sticky="ns")
        
        status_label = ctk.CTkLabel(
            status_frame,
            text="● BATCH READY",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["primary"]
        )
        status_label.pack(expand=True)
    
    def _build_main_content(self):
        """Build main content area"""
        # Create main scrollable frame
        main_frame = ctk.CTkScrollableFrame(self.root, corner_radius=15)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Input folders section
        self._build_folder_selection(main_frame)
        
        # Processing settings section
        self._build_processing_settings(main_frame)
        
        # Spritesheet settings section
        self._build_spritesheet_settings(main_frame)
        
        # Action buttons section
        self._build_action_buttons(main_frame)
    
    def _build_folder_selection(self, parent):
        """Build folder selection section"""
        folder_frame = ctk.CTkFrame(parent, corner_radius=15)
        folder_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        folder_frame.grid_columnconfigure(1, weight=1)
        
        # Section title
        ctk.CTkLabel(
            folder_frame,
            text="📁 SOURCE DIRECTORIES",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["secondary"]
        ).grid(row=0, column=0, columnspan=3, padx=20, pady=(20, 15), sticky="w")
        
        # Icon folder
        ctk.CTkLabel(
            folder_frame,
            text="Icon Folder:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=1, column=0, padx=20, pady=5, sticky="w")
        
        self.icon_folder_var = ctk.StringVar()
        self.icon_folder_entry = ctk.CTkEntry(
            folder_frame,
            textvariable=self.icon_folder_var,
            placeholder_text="Select folder containing icon images...",
            height=35,
            corner_radius=8
        )
        self.icon_folder_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkButton(
            folder_frame,
            text="📂 SELECT",
            command=self._select_icon_folder,
            width=100,
            height=35,
            corner_radius=8,
            fg_color=self.colors["accent"],
            hover_color=self.colors["primary"]
        ).grid(row=1, column=2, padx=20, pady=5)
        
        # Background folder
        ctk.CTkLabel(
            folder_frame,
            text="Background Folder:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=2, column=0, padx=20, pady=5, sticky="w")
        
        self.bg_folder_var = ctk.StringVar()
        self.bg_folder_entry = ctk.CTkEntry(
            folder_frame,
            textvariable=self.bg_folder_var,
            placeholder_text="Select folder containing background images...",
            height=35,
            corner_radius=8
        )
        self.bg_folder_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkButton(
            folder_frame,
            text="🌌 SELECT",
            command=self._select_bg_folder,
            width=100,
            height=35,
            corner_radius=8,
            fg_color=self.colors["accent"],
            hover_color=self.colors["primary"]
        ).grid(row=2, column=2, padx=20, pady=5)
        
        # Output folder
        ctk.CTkLabel(
            folder_frame,
            text="Output Folder:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=3, column=0, padx=20, pady=5, sticky="w")
        
        self.output_folder_var = ctk.StringVar()
        self.output_folder_entry = ctk.CTkEntry(
            folder_frame,
            textvariable=self.output_folder_var,
            placeholder_text="Select output folder for processed images...",
            height=35,
            corner_radius=8
        )
        self.output_folder_entry.grid(row=3, column=1, padx=10, pady=(5, 20), sticky="ew")
        
        ctk.CTkButton(
            folder_frame,
            text="💾 SELECT",
            command=self._select_output_folder,
            width=100,
            height=35,
            corner_radius=8,
            fg_color=self.colors["accent"],
            hover_color=self.colors["primary"]
        ).grid(row=3, column=2, padx=20, pady=(5, 20))
    
    def _build_processing_settings(self, parent):
        """Build processing settings section"""
        settings_frame = ctk.CTkFrame(parent, corner_radius=15)
        settings_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        settings_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Section title
        ctk.CTkLabel(
            settings_frame,
            text="⚙️ PROCESSING CONFIGURATION",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["secondary"]
        ).grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 15), sticky="w")
        
        # Left column - Size settings
        size_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        size_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(
            size_frame,
            text="Output Size:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(0, 5))
        
        # Size preset dropdown
        size_options = [f"{name} ({w}x{h})" for name, (w, h) in self.settings.get_size_presets()]
        self.size_preset_var = ctk.StringVar(value=size_options[4])  # Default to Large
        self.size_dropdown = ctk.CTkComboBox(
            size_frame,
            variable=self.size_preset_var,
            values=size_options,
            state="readonly",
            command=self._on_size_preset_change
        )
        self.size_dropdown.pack(fill="x", padx=10, pady=5)
        
        # Custom size entry
        custom_frame = ctk.CTkFrame(size_frame, fg_color="transparent")
        custom_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            custom_frame,
            text="Custom:",
            font=ctk.CTkFont(size=10)
        ).pack(side="left")
        
        self.custom_width_var = ctk.StringVar(value="512")
        self.custom_height_var = ctk.StringVar(value="512")
        
        ctk.CTkEntry(
            custom_frame,
            textvariable=self.custom_width_var,
            width=60,
            placeholder_text="W"
        ).pack(side="left", padx=(10, 2))
        
        ctk.CTkLabel(custom_frame, text="×").pack(side="left", padx=2)
        
        ctk.CTkEntry(
            custom_frame,
            textvariable=self.custom_height_var,
            width=60,
            placeholder_text="H"
        ).pack(side="left", padx=(2, 0))
        
        # Right column - Options
        options_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        options_frame.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(
            options_frame,
            text="Options:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(0, 5))
        
        # Output Mode selection
        output_mode_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        output_mode_frame.pack(anchor="w", padx=10, pady=5, fill="x")
        
        ctk.CTkLabel(
            output_mode_frame,
            text="🎯 Output Mode:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["secondary"]
        ).pack(anchor="w", padx=5)
        
        self.output_mode_var = ctk.StringVar(value="sprite_sheets")
        
        modes_frame = ctk.CTkFrame(output_mode_frame, fg_color="transparent")
        modes_frame.pack(anchor="w", padx=15, pady=2, fill="x")
        
        self.sprite_sheets_radio = ctk.CTkRadioButton(
            modes_frame,
            text="Sprite Sheets",
            variable=self.output_mode_var,
            value="sprite_sheets",
            font=ctk.CTkFont(size=10)
        )
        self.sprite_sheets_radio.pack(side="left", padx=(0, 15))
        
        self.individual_pngs_radio = ctk.CTkRadioButton(
            modes_frame,
            text="Individual PNGs",
            variable=self.output_mode_var,
            value="individual_pngs",
            font=ctk.CTkFont(size=10)
        )
        self.individual_pngs_radio.pack(side="left", padx=(0, 15))
        
        self.both_radio = ctk.CTkRadioButton(
            modes_frame,
            text="Both",
            variable=self.output_mode_var,
            value="both",
            font=ctk.CTkFont(size=10)
        )
        self.both_radio.pack(side="left")
        
        # File count display
        self.file_count_label = ctk.CTkLabel(
            options_frame,
            text="📊 Ready to scan folders...",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["primary"]
        )
        self.file_count_label.pack(anchor="w", padx=10, pady=(10, 0))
    
    def _build_spritesheet_settings(self, parent):
        """Build spritesheet settings section"""
        sheet_frame = ctk.CTkFrame(parent, corner_radius=15)
        sheet_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        sheet_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Section title
        ctk.CTkLabel(
            sheet_frame,
            text="🔮 SPRITESHEET MATRIX",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["secondary"]
        ).grid(row=0, column=0, columnspan=3, padx=20, pady=(20, 15), sticky="w")
        
        # Grid settings
        grid_frame = ctk.CTkFrame(sheet_frame, fg_color="transparent")
        grid_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(
            grid_frame,
            text="Grid Rows:",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", padx=5)
        
        self.rows_var = ctk.StringVar(value=str(self.settings.get_default_rows()))
        self.rows_entry = ctk.CTkEntry(
            grid_frame,
            textvariable=self.rows_var,
            width=80,
            height=30,
            placeholder_text="8"
        )
        self.rows_entry.pack(padx=5, pady=2)
        self.rows_entry.bind('<KeyRelease>', self._on_grid_change)
        
        # Columns
        cols_frame = ctk.CTkFrame(sheet_frame, fg_color="transparent")
        cols_frame.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(
            cols_frame,
            text="Grid Columns:",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", padx=5)
        
        self.cols_var = ctk.StringVar(value=str(self.settings.get_default_columns()))
        self.cols_entry = ctk.CTkEntry(
            cols_frame,
            textvariable=self.cols_var,
            width=80,
            height=30,
            placeholder_text="8"
        )
        self.cols_entry.pack(padx=5, pady=2)
        self.cols_entry.bind('<KeyRelease>', self._on_grid_change)
        
        # Options
        options_frame = ctk.CTkFrame(sheet_frame, fg_color="transparent")
        options_frame.grid(row=1, column=2, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(
            options_frame,
            text="Sheet Options:",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", padx=5)
        
        # Power of two option
        self.power_of_two_var = ctk.BooleanVar(value=False)
        self.power_of_two_check = ctk.CTkCheckBox(
            options_frame,
            text="Power of 2 Canvas",
            variable=self.power_of_two_var,
            font=ctk.CTkFont(size=10)
        )
        self.power_of_two_check.pack(anchor="w", padx=5, pady=2)
        
        # Grid info
        self.grid_info_label = ctk.CTkLabel(
            options_frame,
            text="Grid: 8×8 = 64 cells",
            font=ctk.CTkFont(size=9),
            text_color=self.colors["primary"]
        )
        self.grid_info_label.pack(anchor="w", padx=5, pady=(10, 0))
    
    def _build_action_buttons(self, parent):
        """Build action buttons section"""
        action_frame = ctk.CTkFrame(parent, corner_radius=15)
        action_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=20)
        action_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Scan button
        ctk.CTkButton(
            action_frame,
            text="🔍 SCAN FOLDERS",
            command=self._scan_folders,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["accent"],
            hover_color=self.colors["primary"],
            corner_radius=15
        ).grid(row=0, column=0, padx=10, pady=15, sticky="ew")
        
        # Process button
        ctk.CTkButton(
            action_frame,
            text="⚡ PROCESS BATCH",
            command=self._process_batch,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["primary"],
            hover_color=self.colors["secondary"],
            corner_radius=15
        ).grid(row=0, column=1, padx=10, pady=15, sticky="ew")
    
    def _build_footer(self):
        """Build footer with status information"""
        footer_frame = ctk.CTkFrame(self.root, height=40, corner_radius=0)
        footer_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        footer_frame.grid_columnconfigure(1, weight=1)
        
        # Status indicator
        self.status_label = ctk.CTkLabel(
            footer_frame,
            text="🟢 System Ready",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["primary"]
        )
        self.status_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Version info
        version_label = ctk.CTkLabel(
            footer_frame,
            text="Sprite Nexus v3.0 | Batch Processing | KISS + SOLID",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["text"]
        )
        version_label.grid(row=0, column=2, padx=20, pady=10, sticky="e")
    
    def _select_icon_folder(self):
        """Select icon folder"""
        folder = filedialog.askdirectory(title="🎯 Select Icon Folder")
        if folder:
            self.icon_folder_var.set(folder)
            self._scan_folders()
    
    def _select_bg_folder(self):
        """Select background folder"""
        folder = filedialog.askdirectory(title="🌌 Select Background Folder")
        if folder:
            self.bg_folder_var.set(folder)
            self._scan_folders()
    
    def _select_output_folder(self):
        """Select output folder"""
        folder = filedialog.askdirectory(title="💾 Select Output Folder")
        if folder:
            self.output_folder_var.set(folder)
    
    def _on_size_preset_change(self, value):
        """Handle size preset change"""
        # Extract size from preset string
        try:
            size_part = value.split("(")[1].split(")")[0]
            width, height = map(int, size_part.split("x"))
            self.custom_width_var.set(str(width))
            self.custom_height_var.set(str(height))
        except:
            pass
    
    def _on_grid_change(self, event=None):
        """Handle grid entry changes with validation."""
        self._update_grid_info()
    
    def _update_grid_info(self, value=None):
        """Update grid information labels"""
        try:
            rows_text = self.rows_var.get()
            cols_text = self.cols_var.get()
            
            # Validate and convert to integers
            rows = int(rows_text) if rows_text.isdigit() and int(rows_text) > 0 else 8
            cols = int(cols_text) if cols_text.isdigit() and int(cols_text) > 0 else 8
            
            # Clamp to reasonable ranges
            rows = max(1, min(50, rows))
            cols = max(1, min(50, cols))
            
            total_cells = rows * cols
        except (ValueError, AttributeError):
            # Use defaults if there's any issue
            rows, cols = 8, 8
            total_cells = 64
        
        # Calculate number of sheets based on current file count
        file_count_text = self.file_count_label.cget("text")
        if "Found:" in file_count_text:
            try:
                # Extract icon count from the text
                parts = file_count_text.split("Found:")[1].split("icons")[0].strip()
                icon_count = int(parts)
                
                if icon_count > 0:
                    num_sheets = math.ceil(icon_count / total_cells)
                    if num_sheets > 1:
                        self.grid_info_label.configure(
                            text=f"Grid: {rows}×{cols} = {total_cells} cells/sheet\n{num_sheets} sheets needed"
                        )
                    else:
                        self.grid_info_label.configure(text=f"Grid: {rows}×{cols} = {total_cells} cells")
                else:
                    self.grid_info_label.configure(text=f"Grid: {rows}×{cols} = {total_cells} cells")
            except:
                self.grid_info_label.configure(text=f"Grid: {rows}×{cols} = {total_cells} cells")
        else:
            self.grid_info_label.configure(text=f"Grid: {rows}×{cols} = {total_cells} cells")
    
    def _scan_folders(self):
        """Scan selected folders and update file counts"""
        icon_folder = self.icon_folder_var.get()
        bg_folder = self.bg_folder_var.get()
        
        if not icon_folder or not bg_folder:
            self.file_count_label.configure(text="📊 Select folders to scan...")
            self._update_grid_info()  # Update grid info even with no files
            return
        
        try:
            icon_files = self.image_processor.get_image_files(icon_folder)
            bg_files = self.image_processor.get_image_files(bg_folder)
            
            self.file_count_label.configure(
                text=f"📊 Found: {len(icon_files)} icons, {len(bg_files)} backgrounds"
            )
            
            # Update grid info to show sheet count
            self._update_grid_info()
            
            if len(icon_files) == 0:
                self._show_error_dialog("Scan Error", "No valid icon files found in selected folder.")
            elif len(bg_files) == 0:
                self._show_error_dialog("Scan Error", "No valid background files found in selected folder.")
            else:
                self.status_label.configure(text="🟡 Ready to Process")
                
        except Exception as e:
            self.file_count_label.configure(text=f"❌ Scan error: {str(e)}")
            self._update_grid_info()
    
    def _get_target_size(self):
        """Get target size from UI settings"""
        try:
            width = int(self.custom_width_var.get())
            height = int(self.custom_height_var.get())
            return (width, height)
        except ValueError:
            return self.settings.get_default_sprite_size()
    
    def _process_batch(self):
        """Process batch of icons with backgrounds based on selected output mode"""
        icon_folder = self.icon_folder_var.get()
        bg_folder = self.bg_folder_var.get()
        output_folder = self.output_folder_var.get()
        
        # Validate inputs
        if not all([icon_folder, bg_folder, output_folder]):
            self._show_error_dialog("Input Error", "Please select all required folders.")
            return
        
        try:
            self.status_label.configure(text="🔄 Processing Batch...")
            self.root.update()
            
            # Get settings
            target_size = self._get_target_size()
            output_mode = self.output_mode_var.get()
            
            # Get and validate grid values
            try:
                rows = int(self.rows_var.get()) if self.rows_var.get().isdigit() else 8
                cols = int(self.cols_var.get()) if self.cols_var.get().isdigit() else 8
                rows = max(1, min(50, rows))
                cols = max(1, min(50, cols))
            except (ValueError, AttributeError):
                rows, cols = 8, 8
                
            power_of_two = self.power_of_two_var.get()
            
            # Get folder name for output naming
            folder_base_name = os.path.basename(icon_folder.rstrip(os.sep))
            
            # Track results
            results = {"sprite_sheets": [], "individual_files": [], "index_files": []}
            
            # Process based on output mode
            if output_mode in ["sprite_sheets", "both"]:
                # Create sprite sheets
                merged_images, _ = self.image_processor.batch_merge_icons_with_backgrounds(
                    icon_folder=icon_folder,
                    bg_folder=bg_folder,
                    output_folder=None,  # Don't save individual files here
                    target_size=target_size,
                    save_individual=False
                )
                
                if merged_images:
                    # Create spritesheets with versioning
                    base_name = self._get_unique_filename(output_folder, f"{folder_base_name}_sheet", "png")
                    spritesheet_path = os.path.join(output_folder, f"{base_name}.png")
                    
                    success, created_files = self.image_processor.create_spritesheet_from_images(
                        images=merged_images,
                        output_path=spritesheet_path,
                        rows=rows,
                        cols=cols,
                        cell_size=target_size,
                        power_of_two=power_of_two,
                        max_pot_size=self.settings.get_max_power_of_two()
                    )
                    
                    if success:
                        results["sprite_sheets"] = created_files
                    
                    # Clean up merged images
                    for img in merged_images:
                        img.close()
            
            if output_mode in ["individual_pngs", "both"]:
                # Create individual PNGs
                individual_output_folder = os.path.join(output_folder, folder_base_name)
                os.makedirs(individual_output_folder, exist_ok=True)
                
                merged_images, _ = self.image_processor.batch_merge_icons_with_backgrounds(
                    icon_folder=icon_folder,
                    bg_folder=bg_folder,
                    output_folder=individual_output_folder,
                    target_size=target_size,
                    save_individual=True,
                    use_versioning=True
                )
                
                if merged_images:
                    # Create index.json
                    index_data = {
                        "folder_name": folder_base_name,
                        "total_files": len(merged_images),
                        "cell_size": target_size,
                        "files": [os.path.basename(img.filename) for img in merged_images if hasattr(img, 'filename')]
                    }
                    
                    index_path = os.path.join(individual_output_folder, "index.json")
                    with open(index_path, 'w') as f:
                        json.dump(index_data, f, indent=2)
                    
                    results["individual_files"] = [img.filename for img in merged_images if hasattr(img, 'filename')]
                    results["index_files"] = [index_path]
                    
                    # Clean up merged images
                    for img in merged_images:
                        img.close()
            
            # Show results
            self._show_batch_results(results, output_mode, rows, cols, target_size, folder_base_name)
            self.status_label.configure(text="✅ Batch Completed")
            
        except Exception as e:
            self._show_error_dialog("Processing Error", f"An error occurred: {str(e)}")
            self.status_label.configure(text="❌ Processing Failed")
    
    def _get_unique_filename(self, folder, base_name, extension):
        """Get unique filename with versioning (_v2, _v3, etc.)"""
        counter = 1
        while True:
            if counter == 1:
                filename = base_name
            else:
                filename = f"{base_name}_v{counter}"
            
            full_path = os.path.join(folder, f"{filename}.{extension}")
            if not os.path.exists(full_path):
                return filename
            counter += 1
    
    def _show_batch_results(self, results, output_mode, rows, cols, target_size, folder_base_name):
        """Show batch processing results"""
        summary_parts = []
        
        if results["sprite_sheets"]:
            sheet_count = len(results["sprite_sheets"])
            total_cells = rows * cols
            summary_parts.append(f"• Created {sheet_count} spritesheet(s)")
            summary_parts.append(f"• Grid: {rows}×{cols} per sheet ({total_cells} cells)")
            summary_parts.append("• Sprite sheet files:")
            for sheet in results["sprite_sheets"]:
                summary_parts.append(f"  - {os.path.basename(sheet)}")
        
        if results["individual_files"]:
            file_count = len(results["individual_files"])
            summary_parts.append(f"• Created {file_count} individual PNG(s)")
            summary_parts.append(f"• Saved to: {folder_base_name}/")
            if results["index_files"]:
                summary_parts.append("• Created index.json with file list")
        
        summary_parts.append(f"• Cell size: {target_size[0]}×{target_size[1]}")
        summary_parts.append(f"• Base name: {folder_base_name}")
        
        self._show_success_dialog(
            "Batch Complete",
            f"Successfully processed icons in {output_mode.replace('_', ' ').title()} mode!\n\n"
            f"📊 Summary:\n" + "\n".join(summary_parts)
        )
    
    def _show_success_dialog(self, title, message):
        """Show success dialog with sci-fi styling"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"✅ {title}")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"500x300+{x}+{y}")
        
        ctk.CTkLabel(
            dialog,
            text="🚀 MISSION ACCOMPLISHED",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["primary"]
        ).pack(pady=20)
        
        ctk.CTkLabel(
            dialog,
            text=message,
            font=ctk.CTkFont(size=12),
            wraplength=450,
            justify="left"
        ).pack(pady=10, padx=20)
        
        ctk.CTkButton(
            dialog,
            text="CONTINUE",
            command=dialog.destroy,
            fg_color=self.colors["primary"],
            hover_color=self.colors["secondary"]
        ).pack(pady=20)
    
    def _show_error_dialog(self, title, message):
        """Show error dialog with sci-fi styling"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"⚠️ {title}")
        dialog.geometry("450x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (250 // 2)
        dialog.geometry(f"450x250+{x}+{y}")
        
        ctk.CTkLabel(
            dialog,
            text="🔴 SYSTEM ALERT",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["secondary"]
        ).pack(pady=20)
        
        ctk.CTkLabel(
            dialog,
            text=message,
            font=ctk.CTkFont(size=12),
            wraplength=400
        ).pack(pady=10)
        
        ctk.CTkButton(
            dialog,
            text="ACKNOWLEDGE",
            command=dialog.destroy,
            fg_color=self.colors["secondary"],
            hover_color=self.colors["accent"]
        ).pack(pady=20)
    
    def run(self):
        """Start the application"""
        self.root.mainloop()
