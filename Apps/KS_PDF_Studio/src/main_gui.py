"""
KS PDF Studio - Main GUI Application
Complete graphical user interface for KS PDF Studio with AI integration and dark theme.

Author: Kalponic Studio
Version: 2.0.0
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import json
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Any
import os
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.pdf_engine import KSPDFEngine
from core.markdown_parser import KSMarkdownParser
from core.image_handler import KSImageHandler
from core.code_formatter import KSCodeFormatter
from core.pdf_extractor import KSPDFExtractor, PDFExtractorUtils
from templates.base_template import KSPDFTemplate, TemplateManager
from utils.file_utils import KSFileHandler
from ai.ai_manager import AIModelManager
from ai.ai_enhancement import AIEnhancer
from ai.ai_controls import AIControlPanel, AIStatusBar
from monetization.watermarking import PDFWatermarker, WatermarkConfig
from monetization.license_manager import LicenseManager, LicenseEnforcement, create_personal_license, create_commercial_license, create_enterprise_license
from monetization.analytics import AnalyticsTracker, AnalyticsDashboard


class DarkTheme:
    """Dark theme configuration for KS PDF Studio."""

    # Color palette - muted colors easy on eyes
    COLORS = {
        'bg_primary': '#1e1e1e',      # Main background
        'bg_secondary': '#2d2d2d',    # Secondary backgrounds
        'bg_tertiary': '#3a3a3a',     # Tertiary backgrounds
        'fg_primary': '#e0e0e0',      # Primary text
        'fg_secondary': '#b0b0b0',    # Secondary text
        'fg_accent': '#4a9eff',       # Accent color (muted blue)
        'border': '#404040',          # Borders
        'highlight': '#505050',       # Highlights
        'success': '#4a9e4a',         # Success color
        'warning': '#9e9e4a',         # Warning color
        'error': '#9e4a4a',           # Error color
        'button_bg': '#404040',       # Button background
        'button_fg': '#e0e0e0',       # Button text
        'entry_bg': '#2d2d2d',        # Entry background
        'entry_fg': '#e0e0e0',        # Entry text
        'text_bg': '#1a1a1a',         # Text widget background
        'text_fg': '#e0e0e0',         # Text widget text
        'scrollbar_bg': '#404040',    # Scrollbar background
        'scrollbar_fg': '#606060',    # Scrollbar foreground
    }

    @staticmethod
    def apply_theme(root):
        """Apply dark theme to tkinter application."""
        # Prefer a modern theme with better ttk support
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            # fallback - don't crash if theme not available
            pass

        # Configure overall window
        root.configure(bg=DarkTheme.COLORS['bg_primary'])

        # Global font and paddings
        default_font = ('Segoe UI', 10)
        root.option_add('*Font', default_font)

        # Ttk style base configuration
        style.configure('.', background=DarkTheme.COLORS['bg_primary'], foreground=DarkTheme.COLORS['fg_primary'])

        style.configure('TFrame', background=DarkTheme.COLORS['bg_primary'])
        style.configure('TLabel', background=DarkTheme.COLORS['bg_primary'], foreground=DarkTheme.COLORS['fg_primary'])

        style.configure('TButton', background=DarkTheme.COLORS['button_bg'], foreground=DarkTheme.COLORS['button_fg'], borderwidth=0, focusthickness=3)
        style.map('TButton', background=[('active', DarkTheme.COLORS['highlight'])], foreground=[('disabled', DarkTheme.COLORS['fg_secondary'])])

        style.configure('TEntry', fieldbackground=DarkTheme.COLORS['entry_bg'], foreground=DarkTheme.COLORS['entry_fg'])
        style.configure('TCombobox', fieldbackground=DarkTheme.COLORS['entry_bg'], foreground=DarkTheme.COLORS['entry_fg'])

        style.configure('TNotebook', background=DarkTheme.COLORS['bg_primary'], tabmargins=[2, 5, 2, 0])
        style.configure('TNotebook.Tab', background=DarkTheme.COLORS['bg_secondary'], foreground=DarkTheme.COLORS['fg_primary'], padding=[8, 4])
        style.map('TNotebook.Tab', background=[('selected', DarkTheme.COLORS['bg_tertiary'])], foreground=[('selected', DarkTheme.COLORS['fg_primary'])])

        style.configure('TLabelFrame', background=DarkTheme.COLORS['bg_primary'], foreground=DarkTheme.COLORS['fg_primary'], borderwidth=1)
        style.configure('TCheckbutton', background=DarkTheme.COLORS['bg_primary'], foreground=DarkTheme.COLORS['fg_primary'])
        style.configure('TProgressbar', troughcolor=DarkTheme.COLORS['bg_secondary'], background=DarkTheme.COLORS['bg_tertiary'])

        # Menus and classic widgets don't use ttk styles, set via option_add
        root.option_add('*Menu.background', DarkTheme.COLORS['bg_secondary'])
        root.option_add('*Menu.foreground', DarkTheme.COLORS['fg_primary'])
        root.option_add('*Menu.activeBackground', DarkTheme.COLORS['highlight'])
        root.option_add('*Menu.activeForeground', DarkTheme.COLORS['fg_primary'])

        # Text widgets
        root.option_add('*Text.background', DarkTheme.COLORS['text_bg'])
        root.option_add('*Text.foreground', DarkTheme.COLORS['text_fg'])
        root.option_add('*Text.selectBackground', DarkTheme.COLORS['fg_accent'])
        root.option_add('*Text.selectForeground', DarkTheme.COLORS['bg_primary'])
        root.option_add('*Text.insertBackground', DarkTheme.COLORS['fg_primary'])

        # Listbox styling (classic widget)
        root.option_add('*Listbox.background', DarkTheme.COLORS['text_bg'])
        root.option_add('*Listbox.foreground', DarkTheme.COLORS['text_fg'])
        root.option_add('*Listbox.selectBackground', DarkTheme.COLORS['fg_accent'])
        root.option_add('*Listbox.selectForeground', DarkTheme.COLORS['bg_primary'])

        # Scrollbar
        root.option_add('*Scrollbar.background', DarkTheme.COLORS['scrollbar_bg'])
        root.option_add('*Scrollbar.troughColor', DarkTheme.COLORS['bg_secondary'])
        root.option_add('*Scrollbar.activeBackground', DarkTheme.COLORS['scrollbar_fg'])


class KSPDFStudioApp:
    """
    Main application class for KS PDF Studio with dark theme.
    """

    def __init__(self, root):
        """
        Initialize the KS PDF Studio application.

        Args:
            root: Root tkinter window
        """
        self.root = root
        self.root.title("KS PDF Studio v2.0 - AI-Powered Tutorial Creation")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        # Apply dark theme
        DarkTheme.apply_theme(root)

        # Initialize core components
        self._init_components()

        # Setup UI
        self._setup_ui()

        # Load settings
        self._load_settings()

        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _init_components(self):
        """Initialize all application components."""
        try:
            # Core components
            self.pdf_engine = KSPDFEngine()
            self.markdown_parser = KSMarkdownParser()
            self.image_handler = KSImageHandler()
            self.code_formatter = KSCodeFormatter()
            self.pdf_extractor = KSPDFExtractor()
            self.file_handler = KSFileHandler()

            # Template system
            self.template_manager = TemplateManager()

            # AI components
            self.ai_manager = AIModelManager()
            self.ai_enhancer = AIEnhancer(self.ai_manager)

            # Monetization components
            self.watermarker = PDFWatermarker()
            self.license_manager = LicenseManager()
            self.license_enforcement = LicenseEnforcement(self.license_manager)
            self.analytics_tracker = AnalyticsTracker()
            self.analytics_dashboard = AnalyticsDashboard(self.analytics_tracker)

            # Current project state
            self.current_file = None
            self.current_content = ""
            self.is_modified = False

        except Exception as e:
            messagebox.showerror("Initialization Error",
                               f"Failed to initialize KS PDF Studio: {e}")
            self.root.destroy()
            return

    def _setup_ui(self):
        """Set up the main user interface."""
        # Create main menu
        self._create_menu()

        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Create toolbar
        self._create_toolbar(main_container)

        # Create main content area with paned window
        self._create_main_content(main_container)

        # Create status bar
        self._create_status_bar(main_container)

        # Create AI status bar
        self.ai_status_bar = AIStatusBar(main_container, self.ai_manager)
        self.ai_status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _create_menu(self):
        """Create the main menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)

        file_menu.add_command(label="New Project", command=self._new_project,
                            accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self._open_file,
                            accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self._save_file,
                            accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self._save_file_as,
                            accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Export PDF", command=self._export_pdf,
                            accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        edit_menu.add_command(label="Undo", command=self._undo,
                            accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self._redo,
                            accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Find", command=self._find,
                            accelerator="Ctrl+F")
        edit_menu.add_command(label="Replace", command=self._replace,
                            accelerator="Ctrl+H")

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)

        view_menu.add_command(label="Preview PDF", command=self._preview_pdf)
        view_menu.add_command(label="Show AI Panel", command=self._show_ai_panel)
        view_menu.add_command(label="Templates", command=self._show_templates)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        tools_menu.add_command(label="Batch Process", command=self._batch_process)
        tools_menu.add_command(label="Image Optimizer", command=self._image_optimizer)
        tools_menu.add_command(label="Code Formatter", command=self._code_formatter)
        tools_menu.add_command(label="Extract PDF Text", command=self._extract_pdf_text)

        # AI menu
        ai_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="AI", menu=ai_menu)

        ai_menu.add_command(label="Enhance Content", command=self._ai_enhance_content)
        ai_menu.add_command(label="Generate Tutorial", command=self._ai_generate_tutorial)
        ai_menu.add_command(label="Suggest Images", command=self._ai_suggest_images)
        ai_menu.add_separator()
        ai_menu.add_command(label="AI Settings", command=self._show_ai_panel)

        # Monetization menu
        monetization_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Monetization", menu=monetization_menu)

        monetization_menu.add_command(label="Add Watermark", command=self._add_watermark)
        monetization_menu.add_command(label="Create License", command=self._create_license)
        monetization_menu.add_command(label="Validate License", command=self._validate_license)
        monetization_menu.add_separator()
        monetization_menu.add_command(label="Analytics Dashboard", command=self._show_analytics)
        monetization_menu.add_command(label="Export Analytics", command=self._export_analytics)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)

        help_menu.add_command(label="Documentation", command=self._show_docs)
        help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)

        # Bind keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self._new_project())
        self.root.bind('<Control-o>', lambda e: self._open_file())
        self.root.bind('<Control-s>', lambda e: self._save_file())
        self.root.bind('<Control-Shift-s>', lambda e: self._save_file_as())
        self.root.bind('<Control-e>', lambda e: self._export_pdf())
        self.root.bind('<Control-z>', lambda e: self._undo())
        self.root.bind('<Control-y>', lambda e: self._redo())
        self.root.bind('<Control-f>', lambda e: self._find())
        self.root.bind('<Control-h>', lambda e: self._replace())

    def _create_toolbar(self, parent):
        """Create the main toolbar."""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        # File operations
        ttk.Button(toolbar, text="📄 New", command=self._new_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📂 Open", command=self._open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 Save", command=self._save_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📊 Export PDF", command=self._export_pdf).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Edit operations
        ttk.Button(toolbar, text="↶ Undo", command=self._undo).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="↷ Redo", command=self._redo).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # AI operations
        ttk.Button(toolbar, text="🤖 Enhance", command=self._ai_enhance_content).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📝 Generate", command=self._ai_generate_tutorial).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🖼️ Images", command=self._ai_suggest_images).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # View operations
        ttk.Button(toolbar, text="👁️ Preview", command=self._preview_pdf).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="⚙️ AI Panel", command=self._show_ai_panel).pack(side=tk.LEFT, padx=2)

    def _create_main_content(self, parent):
        """Create the main content area."""
        # Create paned window for resizable panels
        self.main_paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        # Left panel - Editor
        self._create_editor_panel()

        # Right panel - Preview/AI
        self._create_preview_panel()

    def _create_editor_panel(self):
        """Create the markdown editor panel."""
        editor_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(editor_frame, weight=1)

        # Editor toolbar
        editor_toolbar = ttk.Frame(editor_frame)
        editor_toolbar.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(editor_toolbar, text="Markdown Editor", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)

        # Editor controls
        ttk.Button(editor_toolbar, text="📋 Paste", command=self._paste_content).pack(side=tk.RIGHT, padx=2)
        ttk.Button(editor_toolbar, text="📄 Format", command=self._format_markdown).pack(side=tk.RIGHT, padx=2)

        # Main editor
        self.editor_text = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg=DarkTheme.COLORS['text_bg'],
            fg=DarkTheme.COLORS['text_fg'],
            insertbackground=DarkTheme.COLORS['fg_primary'],
        )
        self.editor_text.pack(fill=tk.BOTH, expand=True)

        # Bind events
        self.editor_text.bind('<KeyRelease>', self._on_editor_change)
        self.editor_text.bind('<Control-a>', lambda e: self._select_all())

    def _create_preview_panel(self):
        """Create the preview and AI panel."""
        preview_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(preview_frame, weight=1)

        # Preview notebook
        self.preview_notebook = ttk.Notebook(preview_frame)
        self.preview_notebook.pack(fill=tk.BOTH, expand=True)

        # PDF Preview tab
        self._create_pdf_preview_tab()

        # AI Enhancement tab
        self._create_ai_enhancement_tab()

        # Templates tab
        self._create_templates_tab()

    def _create_pdf_preview_tab(self):
        """Create PDF preview tab."""
        preview_tab = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(preview_tab, text="PDF Preview")

        # Preview controls
        controls_frame = ttk.Frame(preview_tab)
        controls_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(controls_frame, text="🔄 Refresh", command=self._refresh_preview).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="📖 Open PDF", command=self._open_pdf).pack(side=tk.LEFT, padx=2)

        # Preview area (placeholder for now)
        self.preview_text = scrolledtext.ScrolledText(
            preview_tab,
            wrap=tk.WORD,
            font=('Arial', 10),
            bg=DarkTheme.COLORS['text_bg'],
            fg=DarkTheme.COLORS['text_fg'],
            insertbackground=DarkTheme.COLORS['fg_primary'],
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        self.preview_text.insert('1.0', "PDF preview will appear here...\n\nClick 'Refresh' to generate preview.")

    def _create_ai_enhancement_tab(self):
        """Create AI enhancement tab."""
        ai_tab = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(ai_tab, text="AI Enhancement")

        # AI controls
        self.ai_panel = AIControlPanel(ai_tab, self.ai_manager)
        self.ai_panel.pack(fill=tk.BOTH, expand=True)

    def _create_templates_tab(self):
        """Create templates tab."""
        templates_tab = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(templates_tab, text="Templates")

        # Template list
        template_frame = ttk.LabelFrame(templates_tab, text="Available Templates", padding=10)
        template_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Template listbox
        self.template_listbox = tk.Listbox(
            template_frame,
            height=10,
            bg=DarkTheme.COLORS['text_bg'],
            fg=DarkTheme.COLORS['text_fg'],
            selectbackground=DarkTheme.COLORS['fg_accent'],
            selectforeground=DarkTheme.COLORS['bg_primary'],
            highlightbackground=DarkTheme.COLORS['border']
        )
        self.template_listbox.pack(fill=tk.BOTH, expand=True)

        # Load available templates
        self._load_template_list()

        # Template controls
        controls_frame = ttk.Frame(templates_tab)
        controls_frame.pack(fill=tk.X)

        ttk.Button(controls_frame, text="Apply Template", command=self._apply_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="Preview Template", command=self._preview_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="Create New", command=self._create_template).pack(side=tk.LEFT, padx=2)

    def _create_status_bar(self, parent):
        """Create the status bar."""
        self.status_bar = ttk.Frame(parent)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Status labels
        self.status_file = ttk.Label(self.status_bar, text="No file open")
        self.status_file.pack(side=tk.LEFT, padx=5)

        self.status_modified = ttk.Label(self.status_bar, text="")
        self.status_modified.pack(side=tk.LEFT, padx=5)

        self.status_position = ttk.Label(self.status_bar, text="Ln 1, Col 1")
        self.status_position.pack(side=tk.RIGHT, padx=5)

        # Bind cursor position updates
        self.editor_text.bind('<Button-1>', self._update_cursor_position)
        self.editor_text.bind('<KeyRelease>', self._update_cursor_position)

    def _load_template_list(self):
        """Load available templates into the listbox."""
        try:
            templates = self.template_manager.get_available_templates()
            self.template_listbox.delete(0, tk.END)

            for template in templates:
                self.template_listbox.insert(tk.END, template['name'])

        except Exception as e:
            messagebox.showerror("Template Error", f"Failed to load templates: {e}")

    def _load_settings(self):
        """Load application settings."""
        # This would load from a settings file
        # For now, just set defaults
        pass

    def _save_settings(self):
        """Save application settings."""
        # This would save to a settings file
        pass

    # File operations
    def _new_project(self):
        """Create a new project."""
        if self._check_unsaved_changes():
            self.current_file = None
            self.current_content = ""
            self.editor_text.delete('1.0', tk.END)
            self.is_modified = False
            self._update_status()

    def _open_file(self):
        """Open a markdown file."""
        if not self._check_unsaved_changes():
            return

        file_path = filedialog.askopenfilename(
            title="Open Markdown File",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                self.current_file = Path(file_path)
                self.current_content = content
                self.editor_text.delete('1.0', tk.END)
                self.editor_text.insert('1.0', content)
                self.is_modified = False
                self._update_status()

            except Exception as e:
                messagebox.showerror("Open Error", f"Failed to open file: {e}")

    def _save_file(self):
        """Save the current file."""
        if self.current_file:
            self._save_file_to(self.current_file)
        else:
            self._save_file_as()

    def _save_file_as(self):
        """Save the current file with a new name."""
        file_path = filedialog.asksaveasfilename(
            title="Save Markdown File",
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )

        if file_path:
            self.current_file = Path(file_path)
            self._save_file_to(self.current_file)

    def _save_file_to(self, file_path: Path):
        """Save content to a specific file."""
        try:
            content = self.editor_text.get('1.0', tk.END)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.current_content = content
            self.is_modified = False
            self._update_status()

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save file: {e}")

    def _export_pdf(self):
        """Export the current content to PDF."""
        if not self.current_file:
            messagebox.showwarning("No File", "Please save your markdown file first.")
            return

        pdf_path = filedialog.asksaveasfilename(
            title="Export PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if pdf_path:
            self._generate_pdf(pdf_path)

    def _generate_pdf(self, pdf_path: str):
        """Generate PDF from current content."""
        def pdf_worker():
            try:
                content = self.editor_text.get('1.0', tk.END)

                # Parse markdown
                parsed = self.markdown_parser.parse_markdown(content)

                # Generate PDF
                success = self.pdf_engine.convert_markdown_to_pdf(
                    content, pdf_path,
                    template_name="professional"
                )

                if success:
                    messagebox.showinfo("Export Complete",
                                      f"PDF exported successfully to:\n{pdf_path}")
                else:
                    messagebox.showerror("Export Failed", "Failed to generate PDF.")

            except Exception as e:
                messagebox.showerror("Export Error", f"PDF generation failed: {e}")

        thread = threading.Thread(target=pdf_worker, daemon=True)
        thread.start()

    # Edit operations
    def _undo(self):
        """Undo the last edit."""
        try:
            self.editor_text.edit_undo()
        except:
            pass

    def _redo(self):
        """Redo the last undone edit."""
        try:
            self.editor_text.edit_redo()
        except:
            pass

    def _find(self):
        """Show find dialog."""
        # Simple find implementation
        find_text = tk.simpledialog.askstring("Find", "Enter text to find:")
        if find_text:
            content = self.editor_text.get('1.0', tk.END)
            start_pos = content.find(find_text)
            if start_pos != -1:
                # Highlight found text
                end_pos = start_pos + len(find_text)
                self.editor_text.tag_add("found", f"1.{start_pos}", f"1.{end_pos}")
                self.editor_text.tag_config("found", background="yellow")
                self.editor_text.see(f"1.{start_pos}")

    def _replace(self):
        """Show replace dialog."""
        # Simple replace implementation
        find_text = tk.simpledialog.askstring("Replace", "Find:")
        if find_text:
            replace_text = tk.simpledialog.askstring("Replace", "Replace with:")
            if replace_text is not None:
                content = self.editor_text.get('1.0', tk.END)
                new_content = content.replace(find_text, replace_text)
                self.editor_text.delete('1.0', tk.END)
                self.editor_text.insert('1.0', new_content)

    # AI operations
    def _ai_enhance_content(self):
        """Enhance content using AI."""
        content = self.editor_text.get('1.0', tk.END).strip()
        if not content:
            messagebox.showwarning("No Content", "Please enter some content to enhance.")
            return

        # Switch to AI tab
        self.preview_notebook.select(1)  # AI Enhancement tab

        # Set content in AI panel
        self.ai_panel.enhancement_text.delete('1.0', tk.END)
        self.ai_panel.enhancement_text.insert('1.0', content)

        # Trigger enhancement
        self.ai_panel._enhance_content()

    def _ai_generate_tutorial(self):
        """Generate tutorial using AI."""
        # Switch to AI tab
        self.preview_notebook.select(1)

        # Show tutorial generation tab
        self.ai_panel.notebook.select(2)  # Tutorial Generation tab

    def _ai_suggest_images(self):
        """Suggest images for content."""
        content = self.editor_text.get('1.0', tk.END).strip()
        if not content:
            messagebox.showwarning("No Content", "Please enter some content first.")
            return

        # This would integrate with AI image suggestion
        messagebox.showinfo("Image Suggestions", "Image suggestion feature coming soon!")

    # View operations
    def _preview_pdf(self):
        """Preview the PDF."""
        content = self.editor_text.get('1.0', tk.END)
        if not content.strip():
            messagebox.showwarning("No Content", "Please enter some content to preview.")
            return

        self._refresh_preview()

    def _refresh_preview(self):
        """Refresh the PDF preview."""
        content = self.editor_text.get('1.0', tk.END)

        # Simple text preview for now
        try:
            parsed = self.markdown_parser.parse_markdown(content)
            preview_content = f"Title: {parsed.get('title', 'Untitled')}\n\n"
            preview_content += f"Sections: {len(parsed.get('sections', []))}\n"
            preview_content += f"Images: {len(parsed.get('images', []))}\n\n"
            preview_content += "Content Preview:\n" + "-" * 50 + "\n"
            preview_content += content[:500] + ("..." if len(content) > 500 else "")

            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', preview_content)

        except Exception as e:
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', f"Preview error: {e}")

    def _open_pdf(self):
        """Open the generated PDF."""
        # This would open the PDF in system viewer
        messagebox.showinfo("Open PDF", "PDF opening feature coming soon!")

    def _show_ai_panel(self):
        """Show the AI control panel."""
        self.preview_notebook.select(1)  # AI Enhancement tab

    def _show_templates(self):
        """Show the templates panel."""
        self.preview_notebook.select(2)  # Templates tab

    # Template operations
    def _apply_template(self):
        """Apply selected template."""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a template.")
            return

        template_name = self.template_listbox.get(selection[0])
        try:
            template = self.template_manager.get_template(template_name)
            if template:
                # Apply template to current content
                messagebox.showinfo("Template Applied", f"Template '{template_name}' applied!")
            else:
                messagebox.showerror("Template Error", "Template not found.")

        except Exception as e:
            messagebox.showerror("Template Error", f"Failed to apply template: {e}")

    def _preview_template(self):
        """Preview selected template."""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a template.")
            return

        template_name = self.template_listbox.get(selection[0])
        messagebox.showinfo("Template Preview", f"Preview for '{template_name}' coming soon!")

    def _create_template(self):
        """Create a new template."""
        messagebox.showinfo("Create Template", "Template creation feature coming soon!")

    # Utility operations
    def _extract_pdf_text(self):
        """Extract text from PDF and insert into editor."""
        pdf_path = filedialog.askopenfilename(
            title="Select PDF to Extract",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if not pdf_path:
            return

        # Ask for output format
        format_choice = tk.simpledialog.askstring(
            "Output Format",
            "Choose output format (txt/md):",
            initialvalue="md"
        )

        if not format_choice or format_choice.lower() not in ['txt', 'md']:
            return

        try:
            # Validate PDF
            if not PDFExtractorUtils.validate_pdf(pdf_path):
                messagebox.showerror("Invalid PDF", "The selected file is not a valid PDF.")
                return

            # Extract text
            if format_choice.lower() == 'md':
                extracted_text = self.pdf_extractor.extract_to_markdown(pdf_path)
            else:
                result = self.pdf_extractor.extract_text(pdf_path)
                extracted_text = result['text']

            # Insert into editor
            current_text = self.editor.get('1.0', tk.END).strip()
            if current_text:
                # Ask if user wants to replace or append
                choice = messagebox.askyesno(
                    "Insert Extracted Text",
                    "Replace current content or append to end?",
                    detail="Yes = Replace, No = Append"
                )
                if choice:
                    self.editor.delete('1.0', tk.END)
                else:
                    extracted_text = f"\n\n{extracted_text}"

            self.editor.insert(tk.END, extracted_text)
            self.is_modified = True
            self._update_title()

            # Show success message with stats
            result = self.pdf_extractor.extract_text(pdf_path)
            messagebox.showinfo(
                "Extraction Complete",
                f"Successfully extracted text from PDF!\n\n"
                f"Pages: {result['page_count']}\n"
                f"Characters: {result.get('total_chars', len(result['text']))}\n"
                f"Format: {format_choice.upper()}"
            )

        except Exception as e:
            messagebox.showerror("Extraction Error", f"Failed to extract PDF text: {e}")

    def _batch_process(self):
        """Show batch processing dialog."""
        messagebox.showinfo("Batch Process", "Batch processing feature coming soon!")

    def _image_optimizer(self):
        """Show image optimizer dialog."""
        messagebox.showinfo("Image Optimizer", "Image optimization feature coming soon!")

    def _code_formatter(self):
        """Show code formatter dialog."""
        messagebox.showinfo("Code Formatter", "Code formatting feature coming soon!")

    # Editor events
    def _on_editor_change(self, event=None):
        """Handle editor content changes."""
        current_content = self.editor_text.get('1.0', tk.END)
        self.is_modified = current_content != self.current_content
        self._update_status()

    def _update_cursor_position(self, event=None):
        """Update cursor position in status bar."""
        try:
            line, col = self.editor_text.index(tk.INSERT).split('.')
            self.status_position.config(text=f"Ln {line}, Col {int(col) + 1}")
        except:
            pass

    def _update_status(self):
        """Update status bar information."""
        if self.current_file:
            file_name = self.current_file.name
            self.status_file.config(text=file_name)
        else:
            self.status_file.config(text="Untitled")

        if self.is_modified:
            self.status_modified.config(text="Modified")
        else:
            self.status_modified.config(text="")

    def _check_unsaved_changes(self) -> bool:
        """Check for unsaved changes and prompt user."""
        if self.is_modified:
            response = messagebox.askyesnocancel("Unsaved Changes",
                                               "You have unsaved changes. Save them?")
            if response is None:  # Cancel
                return False
            elif response:  # Yes
                self._save_file()
        return True

    def _select_all(self):
        """Select all text in editor."""
        self.editor_text.tag_add(tk.SEL, '1.0', tk.END)
        self.editor_text.mark_set(tk.INSERT, tk.END)
        return 'break'

    def _paste_content(self):
        """Paste content into editor."""
        try:
            content = self.root.clipboard_get()
            self.editor_text.insert(tk.INSERT, content)
        except:
            pass

    def _format_markdown(self):
        """Format the markdown content."""
        content = self.editor_text.get('1.0', tk.END)
        # Basic formatting - could be enhanced
        formatted = content.strip()
        self.editor_text.delete('1.0', tk.END)
        self.editor_text.insert('1.0', formatted)

    # Help operations
    def _show_docs(self):
        """Show documentation."""
        docs_url = "https://github.com/kalponic-studio/ks-pdf-studio"
        webbrowser.open(docs_url)

    def _show_shortcuts(self):
        """Show keyboard shortcuts."""
        shortcuts = """
KS PDF Studio Keyboard Shortcuts:

File Operations:
  Ctrl+N        New Project
  Ctrl+O        Open File
  Ctrl+S        Save File
  Ctrl+Shift+S  Save As
  Ctrl+E        Export PDF

Edit Operations:
  Ctrl+Z        Undo
  Ctrl+Y        Redo
  Ctrl+F        Find
  Ctrl+H        Replace

AI Operations:
  (Available in AI Enhancement tab)

View Operations:
  (Available in menu)
"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)

    def _show_about(self):
        """Show about dialog."""
        about_text = """
KS PDF Studio v2.0

AI-Powered Tutorial Creation Tool

Created by Kalponic Studio

Features:
• Markdown to PDF conversion
• AI content enhancement
• Professional templates
• Image optimization
• Code syntax highlighting

For more information, visit:
https://github.com/kalponic-studio/ks-pdf-studio
"""
        messagebox.showinfo("About KS PDF Studio", about_text)

    def _on_closing(self):
        """Handle application closing."""
        if self._check_unsaved_changes():
            self._save_settings()
            self.root.destroy()

    # Monetization operations
    def _add_watermark(self):
        """Add watermark to PDF."""
        if not self.current_file:
            messagebox.showwarning("No File", "Please save your markdown file first.")
            return

        # Generate PDF first if needed
        pdf_path = filedialog.asksaveasfilename(
            title="Save PDF for Watermarking",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )

        if not pdf_path:
            return

        # Generate PDF
        self._generate_pdf(pdf_path)

        # Ask for watermark details
        watermark_text = tk.simpledialog.askstring("Watermark", "Enter watermark text:")
        if not watermark_text:
            return

        try:
            # Configure watermark
            config = WatermarkConfig(
                text=watermark_text,
                opacity=0.3,
                angle=45,
                font_size=50,
                color=(128, 128, 128)
            )

            # Apply watermark
            watermarked_path = pdf_path.replace('.pdf', '_watermarked.pdf')
            success = self.watermarker.apply_watermark(pdf_path, watermarked_path, config)

            if success:
                messagebox.showinfo("Success", f"Watermarked PDF saved as:\n{watermarked_path}")
            else:
                messagebox.showerror("Error", "Failed to apply watermark")

        except Exception as e:
            messagebox.showerror("Watermark Error", f"Failed to add watermark: {e}")

    def _create_license(self):
        """Create a new license."""
        # Simple license creation dialog
        user_name = tk.simpledialog.askstring("License Creation", "Enter user name:")
        if not user_name:
            return

        user_email = tk.simpledialog.askstring("License Creation", "Enter user email:")
        if not user_email:
            return

        license_type = tk.simpledialog.askstring("License Creation",
                                                "Enter license type (personal/commercial/enterprise):")
        if not license_type:
            return

        content_title = tk.simpledialog.askstring("License Creation", "Enter content title:")
        if not content_title:
            return

        try:
            # Create license
            user_info = {
                'id': f"user_{hash(user_email) % 10000}",
                'name': user_name,
                'email': user_email
            }

            content_info = {
                'id': f"content_{hash(content_title) % 10000}",
                'title': content_title
            }

            if license_type.lower() == 'personal':
                license_key, license_info = create_personal_license(
                    self.license_manager, user_info, content_info)
            elif license_type.lower() == 'commercial':
                license_key, license_info = create_commercial_license(
                    self.license_manager, user_info, content_info)
            elif license_type.lower() == 'enterprise':
                license_key, license_info = create_enterprise_license(
                    self.license_manager, user_info, content_info)
            else:
                messagebox.showerror("Error", "Invalid license type")
                return

            # Show license key
            messagebox.showinfo("License Created",
                              f"License created successfully!\n\n"
                              f"License Key: {license_key}\n"
                              f"User: {license_info.user_name}\n"
                              f"Content: {license_info.content_title}\n"
                              f"Type: {license_info.license_type}")

        except Exception as e:
            messagebox.showerror("License Error", f"Failed to create license: {e}")

    def _validate_license(self):
        """Validate a license key."""
        license_key = tk.simpledialog.askstring("License Validation", "Enter license key:")
        if not license_key:
            return

        try:
            license_info = self.license_manager.validate_license(license_key)

            if license_info:
                status = "Valid" if license_info.is_valid() else "Expired/Invalid"
                messagebox.showinfo("License Validation",
                                  f"License Status: {status}\n\n"
                                  f"User: {license_info.user_name}\n"
                                  f"Content: {license_info.content_title}\n"
                                  f"Type: {license_info.license_type}\n"
                                  f"Expires: {license_info.expiry_date or 'Never'}")
            else:
                messagebox.showerror("Invalid License", "The license key is invalid.")

        except Exception as e:
            messagebox.showerror("Validation Error", f"Failed to validate license: {e}")

    def _show_analytics(self):
        """Show analytics dashboard."""
        try:
            report = self.analytics_dashboard.generate_report(days=30)

            # Create analytics window
            analytics_window = tk.Toplevel(self.root)
            analytics_window.title("Analytics Dashboard")
            analytics_window.geometry("800x600")

            # Analytics text area
            text_area = scrolledtext.ScrolledText(analytics_window, wrap=tk.WORD,
                                                font=('Consolas', 10))
            text_area.pack(fill=tk.BOTH, expand=True)
            text_area.insert('1.0', report)
            text_area.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("Analytics Error", f"Failed to generate analytics: {e}")

    def _export_analytics(self):
        """Export analytics data."""
        file_path = filedialog.asksaveasfilename(
            title="Export Analytics",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                self.analytics_dashboard.export_data(file_path)
                messagebox.showinfo("Export Complete", f"Analytics exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export analytics: {e}")


def main():
    """Main application entry point."""
    root = tk.Tk()
    app = KSPDFStudioApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()