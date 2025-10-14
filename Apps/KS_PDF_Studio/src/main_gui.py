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
import fnmatch

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
    # COLORS are centralized in src/theme.py. Keep an empty placeholder here
    # so the class exists; the real values are loaded (and override this)
    # further down when importing the centralized theme.
    COLORS = {}

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

        # Frame and label defaults
        style.configure('TFrame', background=DarkTheme.COLORS['bg_primary'], relief='flat')
        style.configure('TLabel', background=DarkTheme.COLORS['bg_primary'], foreground=DarkTheme.COLORS['fg_primary'])

        # Buttons
        style.configure('TButton', background=DarkTheme.COLORS['button_bg'], foreground=DarkTheme.COLORS['button_fg'], borderwidth=0, focusthickness=3)
        style.map('TButton', background=[('active', DarkTheme.COLORS.get('button_active_bg', DarkTheme.COLORS['highlight']))], foreground=[('disabled', DarkTheme.COLORS['fg_secondary'])])

        # Entries / Combobox
        style.configure('TEntry', fieldbackground=DarkTheme.COLORS['entry_bg'], foreground=DarkTheme.COLORS['entry_fg'])
        style.configure('TCombobox', fieldbackground=DarkTheme.COLORS['entry_bg'], foreground=DarkTheme.COLORS['entry_fg'])
        # Entry selection colors
        root.option_add('*Entry.selectBackground', DarkTheme.COLORS.get('entry_select_bg', DarkTheme.COLORS.get('select_bg', DarkTheme.COLORS['fg_accent'])))
        root.option_add('*Entry.selectForeground', DarkTheme.COLORS.get('entry_select_fg', DarkTheme.COLORS.get('select_fg', DarkTheme.COLORS['bg_primary'])))

        # Notebook / Tabs
        style.configure('TNotebook', background=DarkTheme.COLORS['bg_primary'], tabmargins=[2, 5, 2, 0], borderwidth=0)
        style.configure('TNotebook.Tab', background=DarkTheme.COLORS['bg_secondary'], foreground=DarkTheme.COLORS['fg_primary'], padding=[8, 4])
        style.map('TNotebook.Tab', background=[('selected', DarkTheme.COLORS['bg_tertiary'])], foreground=[('selected', DarkTheme.COLORS['fg_primary'])])

        # LabelFrames, Checkbuttons, Progress
        style.configure('TLabelFrame', background=DarkTheme.COLORS['bg_primary'], foreground=DarkTheme.COLORS['fg_primary'], borderwidth=1)
        style.configure('TCheckbutton', background=DarkTheme.COLORS['bg_primary'], foreground=DarkTheme.COLORS['fg_primary'])
        style.configure('TProgressbar', troughcolor=DarkTheme.COLORS['bg_secondary'], background=DarkTheme.COLORS['bg_tertiary'])

        # PanedWindow and additional separators
        style.configure('TPanedwindow', background=DarkTheme.COLORS['bg_primary'])
        style.configure('TSeparator', background=DarkTheme.COLORS['border'])

        # Menus and classic widgets don't use ttk styles, set via option_add
        root.option_add('*Menu.background', DarkTheme.COLORS['bg_secondary'])
        root.option_add('*Menu.foreground', DarkTheme.COLORS['fg_primary'])
        root.option_add('*Menu.activeBackground', DarkTheme.COLORS.get('menu_active_bg', DarkTheme.COLORS['highlight']))
        root.option_add('*Menu.activeForeground', DarkTheme.COLORS.get('menu_active_fg', DarkTheme.COLORS['fg_primary']))

        # Text widgets and selection colors (muted, non-white selection)
        root.option_add('*Text.background', DarkTheme.COLORS['text_bg'])
        root.option_add('*Text.foreground', DarkTheme.COLORS['text_fg'])
        root.option_add('*Text.selectBackground', DarkTheme.COLORS.get('select_bg', DarkTheme.COLORS['fg_accent']))
        root.option_add('*Text.selectForeground', DarkTheme.COLORS.get('select_fg', DarkTheme.COLORS['bg_primary']))
        root.option_add('*Text.insertBackground', DarkTheme.COLORS['fg_primary'])

        # Listbox styling (classic widget) - use muted selection
        root.option_add('*Listbox.background', DarkTheme.COLORS['text_bg'])
        root.option_add('*Listbox.foreground', DarkTheme.COLORS['text_fg'])
        root.option_add('*Listbox.selectBackground', DarkTheme.COLORS.get('select_bg', DarkTheme.COLORS['fg_accent']))
        root.option_add('*Listbox.selectForeground', DarkTheme.COLORS.get('select_fg', DarkTheme.COLORS['bg_primary']))

        # Scrollbar (thumb and trough)
        root.option_add('*Scrollbar.background', DarkTheme.COLORS.get('scrollbar_bg', DarkTheme.COLORS['bg_secondary']))
        root.option_add('*Scrollbar.troughColor', DarkTheme.COLORS.get('scroll_track', DarkTheme.COLORS['bg_secondary']))
        root.option_add('*Scrollbar.activeBackground', DarkTheme.COLORS.get('scroll_thumb', DarkTheme.COLORS['scrollbar_fg']))
        # Ttk scrollbar style when available
        try:
            style.configure('Vertical.TScrollbar', background=DarkTheme.COLORS.get('scroll_thumb', DarkTheme.COLORS['scrollbar_fg']), troughcolor=DarkTheme.COLORS.get('scroll_track', DarkTheme.COLORS['bg_secondary']))
            style.configure('Horizontal.TScrollbar', background=DarkTheme.COLORS.get('scroll_thumb', DarkTheme.COLORS['scrollbar_fg']), troughcolor=DarkTheme.COLORS.get('scroll_track', DarkTheme.COLORS['bg_secondary']))
            # Dark variant we will explicitly use in our custom text areas
            style.configure('Dark.Vertical.TScrollbar', background=DarkTheme.COLORS.get('scroll_thumb', '#505050'), troughcolor=DarkTheme.COLORS.get('scroll_track', '#2d2d2d'), arrowcolor=DarkTheme.COLORS.get('fg_primary', '#e0e0e0'))
            style.map('Dark.Vertical.TScrollbar', background=[('active', DarkTheme.COLORS.get('highlight', '#505050'))])
        except Exception:
            pass

        # Canvas and labelframe borders
        style.configure('TLabelframe', background=DarkTheme.COLORS['bg_primary'], bordercolor=DarkTheme.COLORS['border'])
        style.configure('TLabelframe.Label', background=DarkTheme.COLORS['bg_primary'], foreground=DarkTheme.COLORS['fg_primary'])

        # Treeview selection (where used)
        try:
            style.configure('Treeview', background=DarkTheme.COLORS['bg_secondary'], foreground=DarkTheme.COLORS['fg_primary'], fieldbackground=DarkTheme.COLORS['bg_secondary'])
            style.map('Treeview', background=[('selected', DarkTheme.COLORS.get('tree_selected_bg', DarkTheme.COLORS.get('select_bg', DarkTheme.COLORS['fg_accent'])))], foreground=[('selected', DarkTheme.COLORS.get('tree_selected_fg', DarkTheme.COLORS.get('select_fg', DarkTheme.COLORS['bg_primary'])))])
        except Exception:
            pass

        # Ensure classic separator widgets and frames have dark borders
        root.option_add('*Separator.background', DarkTheme.COLORS['border'])
        root.option_add('*Frame.background', DarkTheme.COLORS['bg_primary'])

        # Remove focus highlight rings that can appear white on some Windows themes
        root.option_add('*HighlightColor', DarkTheme.COLORS.get('focus_ring', DarkTheme.COLORS['bg_primary']))
        root.option_add('*HighlightBackground', DarkTheme.COLORS.get('focus_ring', DarkTheme.COLORS['bg_primary']))


# Use centralized theme tokens when available
try:
    # Try importing as a top-level module (when src is on sys.path)
    import theme as _theme
    DarkTheme.COLORS = getattr(_theme, 'COLORS', {}) or DarkTheme.COLORS
except Exception:
    try:
        # Try package-relative import (when running as package)
        from .theme import COLORS as THEME_COLORS
        DarkTheme.COLORS = THEME_COLORS
    except Exception:
        # Fallback defaults to guarantee keys exist (used when running tests or imports from different CWDs)
        DarkTheme.COLORS = {
            'bg_primary': '#1e1e1e',
            'bg_secondary': '#2d2d2d',
            'bg_tertiary': '#3a3a3a',
            'fg_primary': '#e0e0e0',
            'fg_secondary': '#b0b0b0',
            'fg_accent': '#4a9eff',
            'border': '#404040',
            'highlight': '#505050',
            'success': '#4a9e4a',
            'warning': '#9e9e4a',
            'error': '#9e4a4a',
            'button_bg': '#404040',
            'button_fg': '#e0e0e0',
            'entry_bg': '#2d2d2d',
            'entry_fg': '#e0e0e0',
            'text_bg': '#1a1a1a',
            'text_fg': '#e0e0e0',
            'scrollbar_bg': '#404040',
            'scrollbar_fg': '#606060',
        }


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
        # Create custom dark menubar (instead of native OS menu)
        self._create_dark_menubar()

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
        """Deprecated: native menu replaced by _create_dark_menubar."""
        menubar = tk.Menu(self.root)  # keep for fallback if needed
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
        # Tools -> open the Extractor tab rather than running extraction directly
        tools_menu.add_command(label="Extract PDF Text", command=lambda: self.preview_notebook.select(self._find_tab_index_by_name('PDF Extractor')))

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

    def _create_dark_menubar(self):
        """Create a VS Code-like dark menubar made of buttons/labels so it takes theme colors and avoids white OS chrome."""
        bar_bg = DarkTheme.COLORS.get('bg_secondary', '#2d2d2d')
        bar_fg = DarkTheme.COLORS.get('fg_primary', '#e0e0e0')
        hover_bg = DarkTheme.COLORS.get('bg_tertiary', '#3a3a3a')

        container = tk.Frame(self.root, bg=bar_bg)
        container.pack(fill=tk.X)

        def make_menu(label, items):
            btn = tk.Label(container, text=label, bg=bar_bg, fg=bar_fg, padx=10, pady=4, cursor='hand2')
            btn.pack(side=tk.LEFT)

            menu = tk.Toplevel(self.root, bg=bar_bg)
            menu.withdraw()
            menu.overrideredirect(True)
            # menu items
            def add_item(text, cmd=None):
                it = tk.Label(menu, text=text, bg=bar_bg, fg=bar_fg, anchor='w', padx=12, pady=4)
                it.pack(fill=tk.X)
                it.bind('<Enter>', lambda e, w=it: w.configure(bg=hover_bg))
                it.bind('<Leave>', lambda e, w=it: w.configure(bg=bar_bg))
                if cmd:
                    it.bind('<Button-1>', lambda e: (cmd(), hide_all()))
            for text, cmd in items:
                add_item(text, cmd)

            def show_menu(event=None):
                x = btn.winfo_rootx()
                y = btn.winfo_rooty() + btn.winfo_height()
                menu.geometry(f"200x{menu.winfo_reqheight()}+{x}+{y}")
                menu.deiconify()
                menu.lift(aboveThis=self.root)

            def hide_menu(event=None):
                menu.withdraw()

            def hide_all():
                for child in container.winfo_children():
                    pass  # menus are Toplevels; we close in on_focus_out
                hide_menu()

            btn.bind('<Button-1>', show_menu)
            menu.bind('<FocusOut>', hide_menu)
            return btn, menu

        # File
        make_menu('File', [
            ('New Project	Ctrl+N', self._new_project),
            ('Open...	Ctrl+O', self._open_file),
            ('Save	Ctrl+S', self._save_file),
            ('Save As...	Ctrl+Shift+S', self._save_file_as),
            ('Export PDF	Ctrl+E', self._export_pdf),
            ('Exit', self._on_closing),
        ])
        # Edit
        make_menu('Edit', [
            ('Undo	Ctrl+Z', self._undo),
            ('Redo	Ctrl+Y', self._redo),
            ('Find	Ctrl+F', self._find),
            ('Replace	Ctrl+H', self._replace),
        ])
        # View
        make_menu('View', [
            ('Preview PDF', self._preview_pdf),
            ('Show AI Panel', self._show_ai_panel),
            ('Templates', self._show_templates),
        ])
        # Tools
        make_menu('Tools', [
            ('Batch Process', self._batch_process),
            ('Image Optimizer', self._image_optimizer),
            ('Code Formatter', self._code_formatter),
            ('Extract PDF Text', lambda: self.preview_notebook.select(self._find_tab_index_by_name('PDF Extractor'))),
        ])
        # AI
        make_menu('AI', [
            ('Enhance Content', self._ai_enhance_content),
            ('Generate Tutorial', self._ai_generate_tutorial),
            ('Suggest Images', self._ai_suggest_images),
            ('AI Settings', self._show_ai_panel),
        ])
        # Monetization
        make_menu('Monetization', [
            ('Add Watermark', self._add_watermark),
            ('Create License', self._create_license),
            ('Validate License', self._validate_license),
            ('Analytics Dashboard', self._show_analytics),
            ('Export Analytics', self._export_analytics),
        ])
        # Help
        make_menu('Help', [
            ('Documentation', self._show_docs),
            ('Keyboard Shortcuts', self._show_shortcuts),
            ('About', self._show_about),
        ])

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

        # Add a compact VS Code-like header bar beneath the toolbar
        try:
            self._create_top_header(parent)
        except Exception:
            pass

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

        # Main editor (Text + dark ttk scrollbar for full control)
        editor_container = ttk.Frame(editor_frame)
        editor_container.pack(fill=tk.BOTH, expand=True)
        self.editor_text = tk.Text(
            editor_container,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg=DarkTheme.COLORS['text_bg'],
            fg=DarkTheme.COLORS['text_fg'],
            insertbackground=DarkTheme.COLORS['fg_primary'],
            relief='flat',
            padx=6, pady=6,
        )
        self.editor_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        editor_scroll = ttk.Scrollbar(editor_container, orient=tk.VERTICAL, style='Dark.Vertical.TScrollbar', command=self.editor_text.yview)
        editor_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.editor_text.configure(yscrollcommand=editor_scroll.set)

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
        # PDF Extractor tab
        self._create_pdf_extractor_tab()

    def _find_tab_index_by_name(self, name: str) -> int:
        """Return the index of a notebook tab by its displayed name. Returns 0 if not found."""
        try:
            for idx in range(self.preview_notebook.index('end')):
                if self.preview_notebook.tab(idx, option='text') == name:
                    return idx
        except Exception:
            pass
        return 0

    def _create_top_header(self, parent):
        """Create a compact, themed header bar beneath the toolbar similar to VS Code's title area."""
        # Use tk widgets for the header so background colors reliably apply
        header_bg = DarkTheme.COLORS.get('bg_secondary', DarkTheme.COLORS['bg_primary'])
        fg = DarkTheme.COLORS.get('fg_primary', '#e0e0e0')
        fg_muted = DarkTheme.COLORS.get('fg_secondary', fg)

        header = tk.Frame(parent, bg=header_bg)
        header.pack(fill=tk.X, pady=(0, 0))

        # Left: small icon + title
        left = tk.Frame(header, bg=header_bg)
        left.pack(side=tk.LEFT, padx=(8, 8))
        icon = tk.Canvas(left, width=18, height=18, highlightthickness=0, bg=header_bg)
        icon.create_rectangle(2, 2, 16, 16, fill=DarkTheme.COLORS.get('fg_accent', '#4a9eff'), outline='')
        icon.pack(side=tk.LEFT)
        title = tk.Label(left, text='KS PDF Studio', font=('Segoe UI', 9, 'bold'), bg=header_bg, fg=fg)
        title.pack(side=tk.LEFT, padx=(6, 0))

        # Middle: filename / breadcrumb
        self.header_file_var = tk.StringVar(value='No file open')
        file_lbl = tk.Label(header, textvariable=self.header_file_var, bg=header_bg, fg=fg_muted, anchor='w')
        file_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.header_file_label = file_lbl

        # Right: compact action buttons (flat, small)
        right = tk.Frame(header, bg=header_bg)
        right.pack(side=tk.RIGHT, padx=8)
        def make_small_btn(text, cmd):
            b = tk.Button(right, text=text, command=cmd, bg=DarkTheme.COLORS.get('button_bg', '#404040'), fg=DarkTheme.COLORS.get('button_fg', '#e0e0e0'), relief='flat', bd=0, padx=6, pady=2)
            return b

        btn_preview = make_small_btn('Preview', self._preview_pdf)
        btn_preview.pack(side=tk.LEFT, padx=4)
        btn_ai = make_small_btn('AI Panel', self._show_ai_panel)
        btn_ai.pack(side=tk.LEFT, padx=4)

        # Thin separator line under the header (use border color)
        sep_line = tk.Frame(parent, height=1, bg=DarkTheme.COLORS.get('border', '#404040'))
        sep_line.pack(fill=tk.X)

    def _create_pdf_preview_tab(self):
        """Create PDF preview tab."""
        preview_tab = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(preview_tab, text="PDF Preview")

        # Preview controls
        controls_frame = ttk.Frame(preview_tab)
        controls_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(controls_frame, text="🔄 Refresh", command=self._refresh_preview).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="📖 Open PDF", command=self._open_pdf).pack(side=tk.LEFT, padx=2)

        # Preview area (Text + dark scrollbar)
        pv_container = ttk.Frame(preview_tab)
        pv_container.pack(fill=tk.BOTH, expand=True)
        self.preview_text = tk.Text(
            pv_container,
            wrap=tk.WORD,
            font=('Arial', 10),
            bg=DarkTheme.COLORS['text_bg'],
            fg=DarkTheme.COLORS['text_fg'],
            insertbackground=DarkTheme.COLORS['fg_primary'],
            relief='flat', padx=6, pady=6,
        )
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pv_scroll = ttk.Scrollbar(pv_container, orient=tk.VERTICAL, style='Dark.Vertical.TScrollbar', command=self.preview_text.yview)
        pv_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_text.configure(yscrollcommand=pv_scroll.set)
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

        # Template controls (use template_frame as parent to avoid potential NULL main window on some environments)
        controls_frame = ttk.Frame(template_frame)
        controls_frame.pack(fill=tk.X, pady=(5, 0))

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
            # TemplateManager exposes list_templates()
            templates = self.template_manager.list_templates()
            self.template_listbox.delete(0, tk.END)

            for template in templates:
                if isinstance(template, (dict,)) and 'name' in template:
                    display_name = template['name']
                else:
                    display_name = str(template)

                self.template_listbox.insert(tk.END, display_name)

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

    def _create_pdf_extractor_tab(self):
        """Create PDF Extractor tab."""
        extractor_tab = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(extractor_tab, text="PDF Extractor")

        # Controls frame
        ctrl = ttk.Frame(extractor_tab)
        ctrl.pack(fill=tk.X, pady=(5, 5))
        # Open / Export buttons (store as attributes so worker can disable/enable)
        self.extract_open_btn = ttk.Button(ctrl, text="Open PDF", command=self._open_pdf_for_extraction)
        self.extract_open_btn.pack(side=tk.LEFT, padx=4)

        self.extract_export_btn = ttk.Button(ctrl, text="Export", command=self._export_extracted)
        self.extract_export_btn.pack(side=tk.LEFT, padx=4)

        ttk.Label(ctrl, text="Format:").pack(side=tk.LEFT, padx=(10, 2))
        self.extract_format_var = tk.StringVar(value='md')
        ttk.Combobox(ctrl, textvariable=self.extract_format_var, values=['md', 'txt', 'docx'], width=6, state='readonly').pack(side=tk.LEFT)

        # Preview area (Text + dark scrollbar)
        ext_container = ttk.Frame(extractor_tab)
        ext_container.pack(fill=tk.BOTH, expand=True, pady=(5,0))
        self.extract_preview = tk.Text(
            ext_container,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg=DarkTheme.COLORS['text_bg'],
            fg=DarkTheme.COLORS['text_fg'],
            insertbackground=DarkTheme.COLORS['fg_primary'],
            relief='flat', padx=6, pady=6,
        )
        self.extract_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ext_scroll = ttk.Scrollbar(ext_container, orient=tk.VERTICAL, style='Dark.Vertical.TScrollbar', command=self.extract_preview.yview)
        ext_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.extract_preview.configure(yscrollcommand=ext_scroll.set)

        # Internal state
        self._last_extracted = None
        # Status label to show progress and messages
        self.extract_status = ttk.Label(extractor_tab, text="", background=DarkTheme.COLORS['bg_primary'], foreground=DarkTheme.COLORS['fg_secondary'])
        self.extract_status.pack(fill=tk.X, pady=(4, 0))

    def _themed_open_file(self, title="Open", filetypes=None, initialdir=None) -> Optional[str]:
        """A minimal, themed file-open dialog implemented as a Toplevel to avoid native OS chrome.
        Returns the selected full path or None if cancelled.
        filetypes: list of (desc, pattern) e.g. [("PDF files","*.pdf")]
        """
        if filetypes is None:
            filetypes = [("All files", "*")]

        dlg = tk.Toplevel(self.root)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.title(title)
        dlg.configure(bg=DarkTheme.COLORS['bg_primary'])
        dlg.geometry('720x420')

        sel = {'path': None}

        path_var = tk.StringVar(value=initialdir or os.getcwd())

        top_bar = ttk.Frame(dlg)
        top_bar.pack(fill=tk.X, padx=8, pady=8)
        ttk.Label(top_bar, text='Path:', background=DarkTheme.COLORS['bg_primary'], foreground=DarkTheme.COLORS['fg_primary']).pack(side=tk.LEFT)
        path_entry = ttk.Entry(top_bar, textvariable=path_var)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 6))

        def list_dir(path):
            try:
                entries = sorted(os.listdir(path), key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
            except Exception:
                entries = []
            lb.delete(0, tk.END)
            # parent dir
            parent = os.path.dirname(path)
            if parent and parent != path:
                lb.insert(tk.END, '..')
            for name in entries:
                full = os.path.join(path, name)
                if os.path.isdir(full):
                    lb.insert(tk.END, f'[D] {name}')
                else:
                    # filter by filetypes
                    keep = False
                    for _, pat in filetypes:
                        if pat == '*' or fnmatch.fnmatch(name, pat.replace('*', '*')):
                            keep = True
                            break
                    if keep:
                        lb.insert(tk.END, name)

        body = ttk.Frame(dlg)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        lb = tk.Listbox(body, bg=DarkTheme.COLORS['text_bg'], fg=DarkTheme.COLORS['text_fg'], selectbackground=DarkTheme.COLORS.get('select_bg', DarkTheme.COLORS['fg_accent']), selectforeground=DarkTheme.COLORS.get('select_fg', DarkTheme.COLORS['bg_primary']))
        vscroll = ttk.Scrollbar(body, orient=tk.VERTICAL, command=lb.yview)
        lb.config(yscrollcommand=vscroll.set)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vscroll.pack(side=tk.LEFT, fill=tk.Y)

        def on_refresh(_=None):
            p = path_var.get()
            if not p:
                p = os.getcwd()
                path_var.set(p)
            list_dir(p)

        def on_activate(evt=None):
            sel_idx = lb.curselection()
            if not sel_idx:
                return
            name = lb.get(sel_idx[0])
            cur = path_var.get()
            if name == '..':
                newp = os.path.dirname(cur) or cur
                path_var.set(newp)
                on_refresh()
                return
            if name.startswith('[D] '):
                dirname = name[4:]
                newp = os.path.join(cur, dirname)
                path_var.set(newp)
                on_refresh()
                return
            # file selected
            selected = os.path.join(cur, name)
            sel['path'] = selected
            dlg.destroy()

        lb.bind('<Double-Button-1>', on_activate)

        btn_bar = ttk.Frame(dlg)
        btn_bar.pack(fill=tk.X, padx=8, pady=(0, 8))
        ttk.Button(btn_bar, text='Refresh', command=on_refresh).pack(side=tk.LEFT)
        ttk.Button(btn_bar, text='Open', command=on_activate).pack(side=tk.RIGHT)
        ttk.Button(btn_bar, text='Cancel', command=dlg.destroy).pack(side=tk.RIGHT, padx=(0, 6))

        # initial populate
        on_refresh()

        # allow Enter to open
        dlg.bind('<Return>', on_activate)

        self.root.wait_window(dlg)
        return sel['path']

    def _themed_save_as(self, title='Save As', defaultextension='.md', initialdir=None) -> Optional[str]:
        """Minimal themed Save As dialog. Returns full path or None."""
        dlg = tk.Toplevel(self.root)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.title(title)
        dlg.configure(bg=DarkTheme.COLORS['bg_primary'])
        dlg.geometry('640x220')

        result = {'path': None}

        dir_var = tk.StringVar(value=initialdir or os.getcwd())
        name_var = tk.StringVar(value='untitled' + (defaultextension or ''))

        frm = ttk.Frame(dlg)
        frm.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        ttk.Label(frm, text='Folder:', background=DarkTheme.COLORS['bg_primary'], foreground=DarkTheme.COLORS['fg_primary']).grid(row=0, column=0, sticky=tk.W)
        dir_entry = ttk.Entry(frm, textvariable=dir_var)
        dir_entry.grid(row=0, column=1, sticky='we', padx=6)
        ttk.Label(frm, text='Filename:', background=DarkTheme.COLORS['bg_primary'], foreground=DarkTheme.COLORS['fg_primary']).grid(row=1, column=0, sticky=tk.W, pady=(8,0))
        name_entry = ttk.Entry(frm, textvariable=name_var)
        name_entry.grid(row=1, column=1, sticky='we', padx=6, pady=(8,0))

        frm.columnconfigure(1, weight=1)

        def on_ok():
            folder = dir_var.get() or os.getcwd()
            name = name_var.get() or ('untitled' + (defaultextension or ''))
            if not os.path.isdir(folder):
                try:
                    os.makedirs(folder, exist_ok=True)
                except Exception:
                    messagebox.showerror('Save Error', 'Cannot create folder')
                    return
            full = os.path.join(folder, name)
            # append extension if missing
            if defaultextension and not full.lower().endswith(defaultextension.lower()):
                full = full + defaultextension
            result['path'] = full
            dlg.destroy()

        btns = ttk.Frame(dlg)
        btns.pack(fill=tk.X, padx=12, pady=(0,12))
        ttk.Button(btns, text='Save', command=on_ok).pack(side=tk.RIGHT)
        ttk.Button(btns, text='Cancel', command=dlg.destroy).pack(side=tk.RIGHT, padx=(0,8))

        self.root.wait_window(dlg)
        return result['path']

    def _open_pdf_for_extraction(self):
        """Open a PDF and extract text into the extractor preview."""
        pdf_path = self._themed_open_file(title="Open PDF for Extraction", filetypes=[("PDF files", "*.pdf")])
        if not pdf_path:
            return

        # Run extraction in background to avoid UI hang
        def worker(path):
            try:
                # update UI: disable buttons and show status
                self.root.after(0, lambda: [
                    self.extract_open_btn.config(state=tk.DISABLED),
                    self.extract_export_btn.config(state=tk.DISABLED),
                    self.extract_status.config(text='Extracting...')
                ])

                if not PDFExtractorUtils.validate_pdf(path):
                    self.root.after(0, lambda: messagebox.showerror("Invalid PDF", "The selected file is not a valid PDF."))
                    return

                result = self.pdf_extractor.extract_text(path)
                if not result.get('success', True):
                    self.root.after(0, lambda: messagebox.showerror("Extraction Error", f"Extraction failed: {result.get('error')}"))
                    return

                md = self.pdf_extractor.extract_to_markdown(path)
                self._last_extracted = {'path': path, 'markdown': md, 'raw': result}

                # Update UI on main thread
                def update_ui():
                    try:
                        self.extract_preview.delete('1.0', tk.END)
                        self.extract_preview.insert('1.0', md)
                        # Switch to extractor tab
                        self.preview_notebook.select(self._find_tab_index_by_name('PDF Extractor'))
                    except Exception as e:
                        messagebox.showerror("UI Update Error", f"Failed to update extractor UI: {e}")

                self.root.after(0, update_ui)

                # re-enable buttons and clear status
                def finalize_ui():
                    self.extract_open_btn.config(state=tk.NORMAL)
                    self.extract_export_btn.config(state=tk.NORMAL)
                    self.extract_status.config(text='')

                self.root.after(0, finalize_ui)

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Extraction Error", f"Failed to extract PDF: {e}"))
                self.root.after(0, lambda: [
                    self.extract_open_btn.config(state=tk.NORMAL),
                    self.extract_export_btn.config(state=tk.NORMAL),
                    self.extract_status.config(text='')
                ])

        thread = threading.Thread(target=worker, args=(pdf_path,), daemon=True)
        thread.start()

    def _export_extracted(self):
        """Export the last extracted content to the chosen format."""
        if not self._last_extracted:
            messagebox.showwarning("No Extraction", "No extracted PDF content to export. Open a PDF first.")
            return

        fmt = self.extract_format_var.get()
        default_ext = '.md' if fmt == 'md' else ('.txt' if fmt == 'txt' else '.docx')

        # Use themed save-as to avoid native save dialog chrome
        file_path = self._themed_save_as(defaultextension=default_ext, initialdir=os.path.dirname(self._last_extracted.get('path', os.getcwd())))
        if not file_path:
            return

        try:
            content = self._last_extracted['markdown'] if fmt in ('md', 'txt') else self._last_extracted['markdown']

            # If docx requested, try to convert using python-docx if available
            if fmt == 'docx':
                try:
                    from docx import Document
                    doc = Document()
                    for line in content.split('\n'):
                        doc.add_paragraph(line)
                    doc.save(file_path)
                except Exception:
                    # fallback to plain text save
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            messagebox.showinfo("Export Complete", f"Extracted content exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export extracted content: {e}")

    # Utility operations
    def _extract_pdf_text(self):
        """Extract text from PDF and insert into editor."""
        # Open the PDF Extractor tab so the user can choose a file and export there.
        try:
            idx = self._find_tab_index_by_name('PDF Extractor')
            self.preview_notebook.select(idx)
        except Exception:
            messagebox.showinfo("PDF Extractor", "Open the 'PDF Extractor' tab to import and export PDF content.")

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

        # Mirror the filename into the top header for quick visibility
        try:
            if getattr(self, 'header_file_var', None) is not None:
                if self.current_file:
                    self.header_file_var.set(str(self.current_file))
                else:
                    self.header_file_var.set('No file open')
        except Exception:
            pass

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

            # Analytics text area (styled to dark theme)
            text_area = scrolledtext.ScrolledText(
                analytics_window,
                wrap=tk.WORD,
                font=('Consolas', 10),
                bg=DarkTheme.COLORS['text_bg'],
                fg=DarkTheme.COLORS['text_fg'],
                insertbackground=DarkTheme.COLORS['fg_primary']
            )
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