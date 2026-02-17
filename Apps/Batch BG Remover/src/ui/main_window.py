"""
Main Application Window
SOLID: Single Responsibility - UI layout and widget management
KISS: Clear widget hierarchy and simple event handling
"""

import io
import logging
from pathlib import Path
from typing import Optional

import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import filedialog

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore
except ImportError:  # pragma: no cover - optional runtime dependency
    DND_FILES = None
    TkinterDnD = None

from .controller import UIController, CyberpunkTheme
from ..config import config
from ..core import RemoverType


if TkinterDnD:
    class CTkDnD(TkinterDnD.DnDWrapper, ctk.CTk):
        """CustomTkinter root with TkDnD support."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)


class MainWindow:
    """
    Main application window.
    
    SOLID: Single Responsibility - manages UI widgets and layout
    KISS: Simple widget creation and event binding
    """

    SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
    
    def __init__(self):
        # Apply cyberpunk theme
        CyberpunkTheme.apply_to_app()

        self._dnd_available = TkinterDnD is not None and DND_FILES is not None

        # Create main window
        self.root = CTkDnD() if self._dnd_available else ctk.CTk()
        self.root.title("KS BG Eraser v2.0")
        self.root.geometry("1200x700")
        self.root.minsize(880, 540)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Initialize controller
        self.controller = UIController(self)
        self._logger = logging.getLogger(self.__class__.__name__)
        
        # UI variables
        self.output_folder = ctk.StringVar()
        self.show_preview = ctk.BooleanVar(value=config.ui_settings.show_preview)
        self.use_jit = ctk.BooleanVar(value=config.removal_settings.use_jit)
        self.threshold = ctk.DoubleVar(value=config.removal_settings.threshold)
        
    # UI elements (created in _create_main_content)
        self.folder_listbox: Optional[ctk.CTkTextbox] = None
        self.start_btn: Optional[ctk.CTkButton] = None
        self.cancel_btn: Optional[ctk.CTkButton] = None
        self.progress_bar: Optional[ctk.CTkProgressBar] = None
        self.status_label: Optional[ctk.CTkLabel] = None
        self.preview_label: Optional[ctk.CTkLabel] = None
        self.preview_frame: Optional[ctk.CTkFrame] = None
        self.output_entry: Optional[ctk.CTkEntry] = None
        self.input_drop_label: Optional[ctk.CTkLabel] = None
        self.threshold_label: Optional[ctk.CTkLabel] = None
        self._config_save_after_id: Optional[str] = None
        
        # Create main scrollable content and widgets
        self._create_main_content()
        self._setup_drag_and_drop()
        
        # Set up variable tracing to update config
        self._setup_variable_tracing()

        self._logger.info("MainWindow initialized")
    
    def _create_main_content(self):
        """Create all UI widgets with fixed header/buttons and scrollable middle content."""
        # Configure main grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)  # Middle scrollable area gets all extra space
        
        # Fixed header section
        header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        header_frame.columnconfigure(0, weight=1)
        self._create_header_content(header_frame)
        
        # Scrollable middle content
        self.scrollable = ctk.CTkScrollableFrame(self.root, corner_radius=10)
        self.scrollable.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        self.scrollable.grid_columnconfigure(0, weight=1)
        self._create_middle_content()
        
        # Fixed bottom controls
        controls_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        controls_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(4, 8))
        self._create_controls_content(controls_frame)
    
    def _create_header_content(self, parent):
        """Create the fixed header section."""
        # Main title
        title_label = ctk.CTkLabel(
            parent,
            text="KS BG Eraser",
            font=CyberpunkTheme.get_title_font(),
            text_color=CyberpunkTheme.ACCENT
        )
        title_label.grid(row=0, column=0, pady=(10, 5), sticky="ew")
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            parent,
            text="Batch background removal — simple and reliable",
            font=CyberpunkTheme.get_subtitle_font(),
            text_color=CyberpunkTheme.SECONDARY
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 10), sticky="ew")

    def _create_middle_content(self):
        """Create the scrollable middle sections."""
        self._create_input_section()
        self._create_output_section()
        self._create_settings_section()
        self._create_progress_section()
        self._create_preview_section()
        self._update_preview_visibility()

    def _create_controls_content(self, parent):
        """Create the fixed bottom controls section."""
        self.start_btn = ctk.CTkButton(
            parent,
            text="Start Processing",
            command=self._start_processing,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=CyberpunkTheme.ACCENT,
            text_color="black",
            hover_color=CyberpunkTheme.SUCCESS,
            height=40
        )
        self.start_btn.pack(side="left", padx=10, pady=10)
        
        self.cancel_btn = ctk.CTkButton(
            parent,
            text="Cancel",
            command=self._cancel_processing,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=CyberpunkTheme.ERROR,
            hover_color="#cc2020",
            height=40,
            state="disabled"
        )
        self.cancel_btn.pack(side="left", padx=10, pady=10)
    
    def _create_input_section(self):
        """Create the input folders section."""
        input_frame = ctk.CTkFrame(
            self.scrollable,
            fg_color=CyberpunkTheme.FRAME,
            border_width=2,
            border_color=CyberpunkTheme.ACCENT
        )
        input_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        # Section title
        ctk.CTkLabel(
            input_frame,
            text="Input Folders",
            font=CyberpunkTheme.get_section_font(),
            text_color=CyberpunkTheme.ACCENT
        ).pack(pady=(15, 10))
        
        # Folder list container
        list_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        list_frame.pack(pady=10, padx=15, fill="both", expand=True)
        
        # Folder list display
        # Add textbox with vertical scrollbar behavior handled by CTkTextbox
        self.folder_listbox = ctk.CTkTextbox(
            list_frame,
            height=100,
            font=CyberpunkTheme.get_body_font(),
            border_width=1,
            border_color=CyberpunkTheme.SECONDARY
        )
        self.folder_listbox.pack(pady=5, padx=5, fill="both", expand=True)
        
        # Folder control buttons
        button_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        button_frame.pack(pady=10, fill="x")
        
        ctk.CTkButton(
            button_frame,
            text="Add Folder",
            command=self._add_input_folder,
            font=CyberpunkTheme.get_bold_font(),
            fg_color=CyberpunkTheme.ACCENT,
            text_color="black",
            hover_color=CyberpunkTheme.SUCCESS
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Add File",
            command=self._add_input_file,
            font=CyberpunkTheme.get_bold_font(),
            fg_color=CyberpunkTheme.SECONDARY,
            hover_color="#0060cc"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Clear All",
            command=self._clear_folders,
            font=CyberpunkTheme.get_bold_font(),
            fg_color=CyberpunkTheme.ERROR,
            hover_color="#cc2020"
        ).pack(side="left", padx=5)

        self.input_drop_label = ctk.CTkLabel(
            input_frame,
            text="Drag and drop files/folders here",
            font=CyberpunkTheme.get_body_font(),
            text_color=CyberpunkTheme.SECONDARY
        )
        self.input_drop_label.pack(padx=15, pady=(0, 12), fill="x")
    
    def _create_output_section(self):
        """Create the output folder section."""
        output_frame = ctk.CTkFrame(
            self.scrollable,
            fg_color=CyberpunkTheme.FRAME,
            border_width=2,
            border_color=CyberpunkTheme.SECONDARY
        )
        output_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        # Configure grid
        output_frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            output_frame,
            text="💾 OUTPUT FOLDER:",
            font=CyberpunkTheme.get_bold_font(),
            text_color=CyberpunkTheme.SECONDARY
        ).grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        self.output_entry = ctk.CTkEntry(
            output_frame,
            textvariable=self.output_folder,
            font=CyberpunkTheme.get_body_font(),
            border_width=1,
            border_color=CyberpunkTheme.ACCENT
        )
        self.output_entry.grid(row=0, column=1, padx=10, sticky="ew")
        
        ctk.CTkButton(
            output_frame,
            text="🔍 BROWSE",
            command=self._select_output_folder,
            font=CyberpunkTheme.get_bold_font(),
            fg_color=CyberpunkTheme.SECONDARY,
            hover_color="#0060cc"
        ).grid(row=0, column=2, padx=15)
    
    def _create_settings_section(self):
        """Create the settings section."""
        settings_frame = ctk.CTkFrame(
            self.scrollable,
            fg_color=CyberpunkTheme.FRAME,
            border_width=2,
            border_color=CyberpunkTheme.ACCENT
        )
        settings_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        # Configure grid
        settings_frame.columnconfigure(1, weight=1)
        
        # Section title
        ctk.CTkLabel(
            settings_frame,
            text="⚙️ AI PROCESSING SETTINGS",
            font=CyberpunkTheme.get_section_font(),
            text_color=CyberpunkTheme.ACCENT
        ).grid(row=0, column=0, columnspan=3, pady=(15, 15))
        
        # Threshold setting
        ctk.CTkLabel(
            settings_frame,
            text="🎯 THRESHOLD:",
            font=CyberpunkTheme.get_bold_font(),
            text_color=CyberpunkTheme.SECONDARY
        ).grid(row=1, column=0, padx=15, pady=8, sticky="w")
        
        threshold_slider = ctk.CTkSlider(
            settings_frame,
            from_=0.0,
            to=1.0,
            variable=self.threshold,
            number_of_steps=100,
            button_color=CyberpunkTheme.ACCENT,
            progress_color=CyberpunkTheme.SECONDARY
        )
        threshold_slider.grid(row=1, column=1, padx=10, pady=8, sticky="ew")
        threshold_slider.configure(command=self._update_threshold_label)
        
        self.threshold_label = ctk.CTkLabel(
            settings_frame,
            text=f"{self.threshold.get():.2f}",
            font=CyberpunkTheme.get_bold_font(),
            text_color=CyberpunkTheme.ACCENT
        )
        self.threshold_label.grid(row=1, column=2, padx=15, pady=8)
        
        # JIT setting
        ctk.CTkCheckBox(
            settings_frame,
            text="🚀 TorchScript JIT (faster inference)",
            variable=self.use_jit,
            font=CyberpunkTheme.get_bold_font(),
            text_color=CyberpunkTheme.SECONDARY,
            checkmark_color=CyberpunkTheme.ACCENT
        ).grid(row=2, column=0, columnspan=3, padx=15, pady=8, sticky="w")
        
        # Preview setting
        ctk.CTkCheckBox(
            settings_frame,
            text="👁️ Show Live Preview",
            variable=self.show_preview,
            font=CyberpunkTheme.get_bold_font(),
            text_color=CyberpunkTheme.SECONDARY,
            checkmark_color=CyberpunkTheme.ACCENT
        ).grid(row=3, column=0, columnspan=3, padx=15, pady=(8, 15), sticky="w")
        
        # Remover type selection (future LayerDiffuse)
        remover_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        remover_frame.grid(row=4, column=0, columnspan=3, padx=15, pady=10, sticky="ew")
        
        ctk.CTkLabel(
            remover_frame,
            text="🤖 AI MODEL:",
            font=CyberpunkTheme.get_bold_font(),
            text_color=CyberpunkTheme.SECONDARY
        ).pack(side="left", padx=(0, 10))
        
        remover_options = [
            "InSPyReNet (Standard)",
            "LayerDiffuse Enhanced (Glass/Hair)"
        ]
        
        self.remover_combo = ctk.CTkComboBox(
            remover_frame,
            values=remover_options,
            font=CyberpunkTheme.get_body_font(),
            state="readonly",
            fg_color=CyberpunkTheme.SECONDARY,
            button_color=CyberpunkTheme.ACCENT
        )
        self.remover_combo.set(remover_options[0])
        self.remover_combo.pack(side="left", padx=5)
        
        # Material type selection for LayerDiffuse
        material_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        material_frame.grid(row=5, column=0, columnspan=3, padx=15, pady=10, sticky="ew")
        
        ctk.CTkLabel(
            material_frame,
            text="🎨 MATERIAL TYPE:",
            font=CyberpunkTheme.get_bold_font(),
            text_color=CyberpunkTheme.SECONDARY
        ).pack(side="left", padx=(0, 10))
        
        material_options = [
            "General (Standard)",
            "Glass (Transparent)",
            "Hair/Fur (Fine Details)",
            "Semi-Transparent (Glowing)"
        ]
        
        self.material_combo = ctk.CTkComboBox(
            material_frame,
            values=material_options,
            font=CyberpunkTheme.get_body_font(),
            state="readonly",
            fg_color=CyberpunkTheme.SECONDARY,
            button_color=CyberpunkTheme.ACCENT
        )
        self.material_combo.set(material_options[0])
        self.material_combo.pack(side="left", padx=5)
    
    def _create_progress_section(self):
        """Create the progress section."""
        progress_frame = ctk.CTkFrame(
            self.scrollable,
            fg_color=CyberpunkTheme.FRAME,
            border_width=2,
            border_color=CyberpunkTheme.SECONDARY
        )
        progress_frame.grid(row=3, column=0, padx=20, pady=15, sticky="ew")
        
        ctk.CTkLabel(
            progress_frame,
            text="📊 PROCESSING STATUS",
            font=CyberpunkTheme.get_section_font(),
            text_color=CyberpunkTheme.SECONDARY
        ).pack(pady=(15, 10))
        
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=25,
            progress_color=CyberpunkTheme.ACCENT,
            border_width=1,
            border_color=CyberpunkTheme.SECONDARY
        )
        self.progress_bar.pack(pady=10, padx=15, fill="x")
        self.progress_bar.set(0)
        
        # Status label shows detailed info including filename
        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="⚡ READY FOR AI PROCESSING ⚡",
            font=CyberpunkTheme.get_bold_font(),
            text_color=CyberpunkTheme.ACCENT
        )
        self.status_label.pack(pady=(10, 15))
    
    def _create_preview_section(self):
        """Create the preview section."""
        self.preview_frame = ctk.CTkFrame(
            self.scrollable,
            fg_color=CyberpunkTheme.FRAME,
            border_width=1,
            border_color=CyberpunkTheme.ACCENT
        )
        self.preview_frame.grid(row=4, column=0, padx=20, pady=10)
        
        ctk.CTkLabel(
            self.preview_frame,
            text="🖼️ LIVE PREVIEW",
            font=CyberpunkTheme.get_bold_font(),
            text_color=CyberpunkTheme.ACCENT
        ).pack(pady=(10, 5))
        
        self.preview_label = ctk.CTkLabel(self.preview_frame, text="")
        self.preview_label.pack(pady=(0, 10))

    def _save_config(self):
        """Persist current settings to disk."""
        self._config_save_after_id = None
        config.save_config()

    def _schedule_config_save(self):
        """Debounce config writes to avoid saving on every slider tick."""
        if self._config_save_after_id is not None:
            self.root.after_cancel(self._config_save_after_id)
        self._config_save_after_id = self.root.after(300, self._save_config)

    def _update_preview_visibility(self):
        """Show or hide preview area based on preference."""
        if not self.preview_frame:
            return

        if self.show_preview.get():
            self.preview_frame.grid()
        else:
            self.preview_frame.grid_remove()
            if self.preview_label:
                self.preview_label.configure(image=None)
                self.preview_label.image = None

    def _setup_drag_and_drop(self):
        """Configure drag-and-drop targets if tkinterdnd2 is available."""
        if not self._dnd_available:
            if self.input_drop_label:
                self.input_drop_label.configure(
                    text="Drag and drop unavailable (install tkinterdnd2)"
                )
            return

        def register_target(widget, handler):
            if not widget:
                return
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", handler)

        register_target(self.folder_listbox, self._on_input_drop)
        register_target(self.input_drop_label, self._on_input_drop)
        register_target(self.output_entry, self._on_output_drop)

        self._logger.info("Drag and drop initialized")

    def _parse_drop_paths(self, data: str) -> list[Path]:
        """Parse a TkDnD drop payload into filesystem paths."""
        try:
            raw_paths = self.root.tk.splitlist(data)
        except Exception:
            raw_paths = [data]

        parsed = []
        for raw_path in raw_paths:
            cleaned = str(raw_path).strip().strip("{}").strip("\"")
            if cleaned:
                parsed.append(Path(cleaned))
        return parsed

    def _on_input_drop(self, event):
        """Handle dropped input paths (folders and image files)."""
        paths = self._parse_drop_paths(event.data)
        if not paths:
            return

        file_paths = []
        ignored_files = 0
        for path in paths:
            if path.is_dir():
                self.controller.add_input_folder(str(path))
            elif path.is_file() and path.suffix.lower() in self.SUPPORTED_IMAGE_EXTENSIONS:
                file_paths.append(path)
            elif path.is_file():
                ignored_files += 1

        if ignored_files:
            self.set_status(f"Ignored {ignored_files} unsupported file(s)")

        if not file_paths:
            return

        # Keep drag-and-drop behavior predictable:
        # one file -> single-file mode, multiple files -> batch file mode.
        if len(file_paths) == 1:
            self._process_single_file(str(file_paths[0]))
            return

        self._process_file_batch([str(path) for path in file_paths])

    def _on_output_drop(self, event):
        """Handle dropped output target path."""
        paths = self._parse_drop_paths(event.data)
        if not paths:
            return

        first = paths[0]
        if first.is_dir():
            self.output_folder.set(str(first))
            self.set_status(f"Output folder set: {first}")
        elif first.is_file():
            self.output_folder.set(str(first.parent))
            self.set_status(f"Output folder set: {first.parent}")

    def _ensure_output_folder(self, title: str) -> Optional[str]:
        """Return output folder, prompting user if not already selected."""
        output_folder = self.output_folder.get().strip()
        if output_folder:
            return output_folder

        selected = filedialog.askdirectory(title=title)
        if not selected:
            return None

        self.output_folder.set(selected)
        return selected

    def _process_single_file(self, file_path: str):
        """Process one file using current settings."""
        output_folder = self._ensure_output_folder("Select Output Folder for Single File")
        if not output_folder:
            return

        remover_choice = self.remover_combo.get() if hasattr(self, 'remover_combo') else ""
        material_choice = self.material_combo.get() if hasattr(self, 'material_combo') else ""

        self.controller.start_single_file(
            file_path,
            output_folder,
            self.show_preview.get(),
            remover_choice,
            material_choice
        )

    def _process_file_batch(self, file_paths: list[str]):
        """Process multiple files as one run."""
        output_folder = self._ensure_output_folder("Select Output Folder for Dropped Files")
        if not output_folder:
            return

        remover_choice = self.remover_combo.get() if hasattr(self, 'remover_combo') else ""
        material_choice = self.material_combo.get() if hasattr(self, 'material_combo') else ""

        self.controller.start_file_batch(
            file_paths,
            output_folder,
            self.show_preview.get(),
            remover_choice,
            material_choice
        )
    
    def _setup_variable_tracing(self):
        """Set up variable tracing to update configuration."""
        def update_config(*args):
            config.removal_settings.threshold = self.threshold.get()
            config.removal_settings.use_jit = self.use_jit.get()
            config.ui_settings.show_preview = self.show_preview.get()
            self._schedule_config_save()

        def update_preview(*args):
            update_config()
            self._update_preview_visibility()
        
        self.threshold.trace_add('write', update_config)
        self.use_jit.trace_add('write', update_config)
        self.show_preview.trace_add('write', update_preview)
    
    # Event handlers
    def _add_input_folder(self):
        """Add input folder dialog."""
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.controller.add_input_folder(folder)

    def _add_input_file(self):
        """Pick a single input file and process it immediately in single-file mode."""
        file_path = filedialog.askopenfilename(title="Select Image File", filetypes=[
            ("Image Files", "*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.tiff"),
            ("All Files", "*")
        ])
        if not file_path:
            return
        self._process_single_file(file_path)
    
    def _clear_folders(self):
        """Clear all input folders."""
        self.controller.clear_folders()
    
    def _select_output_folder(self):
        """Select output folder dialog."""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)
    
    def _update_threshold_label(self, value):
        """Update the threshold label."""
        if self.threshold_label:
            self.threshold_label.configure(text=f"{float(value):.2f}")
    
    def _start_processing(self):
        """Start processing button handler."""
        remover_choice = self.remover_combo.get() if hasattr(self, 'remover_combo') else ""
        material_choice = self.material_combo.get() if hasattr(self, 'material_combo') else ""
        
        self.controller.start_processing(
            self.output_folder.get(),
            self.show_preview.get(),
            remover_choice,
            material_choice
        )
    
    def _cancel_processing(self):
        """Cancel processing button handler."""
        self.controller.cancel_processing()
    
    def _on_closing(self):
        """Handle window closing."""
        if self.controller.is_processing:
            self.controller.cancel_processing()
        if self._config_save_after_id is not None:
            self.root.after_cancel(self._config_save_after_id)
            self._save_config()
        self.controller.cleanup()
        self.root.destroy()
    
    # UI update methods (called by controller)
    def update_folder_display(self):
        """Update the folder list display."""
        if self.folder_listbox:
            self.folder_listbox.delete("1.0", "end")
            for i, folder in enumerate(self.controller.input_folders, 1):
                folder_name = Path(folder).name
                self.folder_listbox.insert("end", f"{i}. {folder_name}\n    📂 {folder}\n\n")
    
    def set_processing_state(self, is_processing: bool):
        """Update UI for processing state."""
        if is_processing:
            self.start_btn.configure(state="disabled")
            self.cancel_btn.configure(state="normal")
        else:
            self.start_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")
    
    def update_progress(self, current: int, total: int, info: str = ""):
        """Update progress bar and status."""
        if total > 0:
            fraction = current / total
            self.progress_bar.set(fraction)
            
            status_text = f"Processing: {current}/{total}"
            if info:
                status_text += f" - {info}"
            self.set_status(status_text)
    
    def set_status(self, text: str):
        """Set status label text."""
        if self.status_label:
            self.status_label.configure(text=text)
    
    def show_preview(self, image_data: bytes):
        """Show preview image."""
        if not self.preview_label:
            return
        
        try:
            img = Image.open(io.BytesIO(image_data))
            img.thumbnail(config.ui_settings.preview_size, Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            
            self.preview_label.configure(image=tk_img)
            self.preview_label.image = tk_img  # Keep reference
            
        except Exception as e:
            logging.warning(f"Failed to update preview: {e}")
    
    def run(self):
        """Start the application main loop."""
        self.root.mainloop()
