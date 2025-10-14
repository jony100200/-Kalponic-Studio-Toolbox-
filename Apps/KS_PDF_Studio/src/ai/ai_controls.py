"""
KS PDF Studio - AI Controls UI
User interface components for AI features and controls.

Author: Kalponic Studio
Version: 2.0.0
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path

from .ai_manager import AIModelManager
from .ai_enhancement import AIEnhancer


class AIControlPanel(ttk.Frame):
    """
    Control panel for AI features in KS PDF Studio.
    """

    def __init__(self, parent, ai_manager: AIModelManager, **kwargs):
        """
        Initialize AI control panel.

        Args:
            parent: Parent tkinter widget
            ai_manager: AIModelManager instance
        """
        super().__init__(parent, **kwargs)

        self.ai_manager = ai_manager
        self.enhancer = AIEnhancer(ai_manager)

        # UI state
        self.download_progress = {}
        self.current_operation = None

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Set up the user interface."""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        title_label = ttk.Label(main_frame, text="AI Enhancement Studio",
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))

        # Create notebook for different AI functions
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Model Management Tab
        self._create_model_management_tab()

        # Content Enhancement Tab
        self._create_enhancement_tab()

        # Tutorial Generation Tab
        self._create_tutorial_tab()

        # Settings Tab
        self._create_settings_tab()

    def _create_model_management_tab(self):
        """Create model management interface."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Model Management")

        # Model status frame
        status_frame = ttk.LabelFrame(tab, text="AI Models Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        # Model status displays
        self.model_status_vars = {}

        for model_key in ['distilbart', 'clip']:
            frame = ttk.Frame(status_frame)
            frame.pack(fill=tk.X, pady=2)

            # Model name
            name_label = ttk.Label(frame, text=f"{model_key.upper()}:",
                                  width=12, anchor='w')
            name_label.pack(side=tk.LEFT)

            # Status indicator
            status_var = tk.StringVar(value="Checking...")
            self.model_status_vars[model_key] = status_var

            status_label = ttk.Label(frame, textvariable=status_var,
                                   width=15, anchor='w')
            status_label.pack(side=tk.LEFT, padx=(10, 0))

            # Download button
            download_btn = ttk.Button(frame, text="Download",
                                    command=lambda m=model_key: self._download_model(m),
                                    width=10)
            download_btn.pack(side=tk.RIGHT, padx=(5, 0))

            # Load button
            load_btn = ttk.Button(frame, text="Load",
                                command=lambda m=model_key: self._load_model(m),
                                width=8)
            load_btn.pack(side=tk.RIGHT)

        # Refresh status button
        refresh_btn = ttk.Button(status_frame, text="Refresh Status",
                               command=self._refresh_model_status)
        refresh_btn.pack(pady=(10, 0))

        # Progress frame
        progress_frame = ttk.LabelFrame(tab, text="Download Progress", padding=10)
        progress_frame.pack(fill=tk.X, pady=(10, 0))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                          maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.pack()

        # Initial status refresh
        self._refresh_model_status()

    def _create_enhancement_tab(self):
        """Create content enhancement interface."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Content Enhancement")

        # Input frame
        input_frame = ttk.LabelFrame(tab, text="Input Content", padding=10)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Text input
        self.enhancement_text = scrolledtext.ScrolledText(input_frame, height=10,
                                                         bg='#1a1a1a', fg='#e0e0e0',
                                                         insertbackground='#e0e0e0')
        self.enhancement_text.pack(fill=tk.BOTH, expand=True)

        # Enhancement options frame
        options_frame = ttk.LabelFrame(tab, text="Enhancement Options", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))

        # Checkboxes for enhancement options
        self.enhancement_vars = {}

        options = [
            ('auto_expand_sections', 'Auto-expand thin sections'),
            ('suggest_images', 'Suggest relevant images'),
            ('add_examples', 'Add practical examples'),
            ('generate_exercises', 'Generate exercises'),
            ('improve_writing', 'Improve writing quality')
        ]

        for i, (var_name, label) in enumerate(options):
            var = tk.BooleanVar(value=True)
            self.enhancement_vars[var_name] = var

            chk = ttk.Checkbutton(options_frame, text=label, variable=var)
            chk.grid(row=i//2, column=i%2, sticky='w', padx=(0, 10), pady=2)

        # Enhance button
        enhance_btn = ttk.Button(tab, text="Enhance Content",
                               command=self._enhance_content)
        enhance_btn.pack(pady=(0, 10))

        # Results frame
        results_frame = ttk.LabelFrame(tab, text="Enhanced Content & Suggestions", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)

        # Results notebook
        results_notebook = ttk.Notebook(results_frame)
        results_notebook.pack(fill=tk.BOTH, expand=True)

        # Enhanced content tab
        enhanced_frame = ttk.Frame(results_notebook)
        results_notebook.add(enhanced_frame, text="Enhanced Content")

        self.enhanced_text = scrolledtext.ScrolledText(enhanced_frame, height=15,
                                                      bg='#1a1a1a', fg='#e0e0e0',
                                                      insertbackground='#e0e0e0')
        self.enhanced_text.pack(fill=tk.BOTH, expand=True)

        # Suggestions tab
        suggestions_frame = ttk.Frame(results_notebook)
        results_notebook.add(suggestions_frame, text="Suggestions")

        self.suggestions_text = scrolledtext.ScrolledText(suggestions_frame, height=15,
                                                        bg='#1a1a1a', fg='#e0e0e0',
                                                        insertbackground='#e0e0e0')
        self.suggestions_text.pack(fill=tk.BOTH, expand=True)

    def _create_tutorial_tab(self):
        """Create tutorial generation interface."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Tutorial Generation")

        # Topic input frame
        topic_frame = ttk.LabelFrame(tab, text="Tutorial Topic", padding=10)
        topic_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(topic_frame, text="Topic:").grid(row=0, column=0, sticky='w', pady=2)
        self.topic_var = tk.StringVar()
        topic_entry = ttk.Entry(topic_frame, textvariable=self.topic_var, width=50)
        topic_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)

        ttk.Label(topic_frame, text="Difficulty:").grid(row=1, column=0, sticky='w', pady=2)
        self.difficulty_var = tk.StringVar(value='beginner')
        difficulty_combo = ttk.Combobox(topic_frame, textvariable=self.difficulty_var,
                                       values=['beginner', 'intermediate', 'advanced'],
                                       state='readonly', width=15)
        difficulty_combo.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)

        self.include_images_var = tk.BooleanVar(value=False)
        images_chk = ttk.Checkbutton(topic_frame, text="Include image suggestions",
                                   variable=self.include_images_var)
        images_chk.grid(row=2, column=0, columnspan=2, sticky='w', pady=(5, 0))

        # Generate button
        generate_btn = ttk.Button(tab, text="Generate Tutorial",
                                command=self._generate_tutorial)
        generate_btn.pack(pady=(0, 10))

        # Results frame
        tutorial_frame = ttk.LabelFrame(tab, text="Generated Tutorial", padding=10)
        tutorial_frame.pack(fill=tk.BOTH, expand=True)

        self.tutorial_text = scrolledtext.ScrolledText(
            tutorial_frame,
            height=20,
            bg='#1a1a1a',
            fg='#e0e0e0',
            insertbackground='#e0e0e0'
        )
        self.tutorial_text.pack(fill=tk.BOTH, expand=True)

    def _create_settings_tab(self):
        """Create settings interface."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Settings")

        # AI Settings frame
        settings_frame = ttk.LabelFrame(tab, text="AI Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # Enhancement settings
        ttk.Label(settings_frame, text="Enhancement Settings:",
                  font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2,
                                                  sticky='w', pady=(0, 5))

        self.settings_vars = {}

        settings_options = [
            ('auto_expand_sections', 'Auto-expand sections'),
            ('suggest_images', 'Suggest images'),
            ('add_examples', 'Add examples'),
            ('generate_exercises', 'Generate exercises'),
            ('improve_writing', 'Improve writing')
        ]

        for i, (var_name, label) in enumerate(settings_options):
            var = tk.BooleanVar(value=True)
            self.settings_vars[var_name] = var

            chk = ttk.Checkbutton(settings_frame, text=label, variable=var)
            chk.grid(row=i+1, column=0, columnspan=2, sticky='w', pady=1)

        # Confidence threshold
        ttk.Label(settings_frame, text="Confidence Threshold:").grid(
            row=len(settings_options)+2, column=0, sticky='w', pady=(10, 0))

        self.confidence_var = tk.DoubleVar(value=0.3)
        confidence_scale = ttk.Scale(settings_frame, from_=0.1, to=1.0,
                                   variable=self.confidence_var, orient=tk.HORIZONTAL)
        confidence_scale.grid(row=len(settings_options)+2, column=1, sticky='ew',
                            padx=(10, 0), pady=(10, 0))

        confidence_label = ttk.Label(settings_frame, textvariable=self.confidence_var)
        confidence_label.grid(row=len(settings_options)+3, column=1, sticky='w')

        # Cache settings
        cache_frame = ttk.LabelFrame(tab, text="Cache Management", padding=10)
        cache_frame.pack(fill=tk.X, pady=(10, 0))

        # Cache info
        self.cache_info_var = tk.StringVar(value="Cache info will appear here")
        cache_info_label = ttk.Label(cache_frame, textvariable=self.cache_info_var,
                                   wraplength=400)
        cache_info_label.pack(anchor='w', pady=(0, 10))

        # Cache buttons
        button_frame = ttk.Frame(cache_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Refresh Cache Info",
                  command=self._refresh_cache_info).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(button_frame, text="Clear Cache",
                  command=self._clear_cache).pack(side=tk.LEFT)

        # Save settings button
        ttk.Button(tab, text="Save Settings",
                  command=self._save_settings).pack(pady=(10, 0))

    def _refresh_model_status(self):
        """Refresh the status of all AI models."""
        for model_key in self.model_status_vars:
            try:
                available = self.ai_manager.is_model_available(model_key)
                loaded = model_key in self.ai_manager._models

                if available and loaded:
                    status = "Loaded"
                elif available:
                    status = "Downloaded"
                else:
                    status = "Not Downloaded"

                self.model_status_vars[model_key].set(status)

            except Exception as e:
                self.model_status_vars[model_key].set(f"Error: {e}")

    def _download_model(self, model_key: str):
        """Download an AI model."""
        if messagebox.askyesno("Download Model",
                             f"Download {model_key.upper()} model (~{self.ai_manager.MODELS[model_key]['size_mb']}MB)?\n\n"
                             "This may take several minutes depending on your internet connection."):
            self._start_download(model_key)

    def _start_download(self, model_key: str):
        """Start model download in background thread."""
        def download_worker():
            try:
                self.current_operation = f"Downloading {model_key}"
                self.progress_label.config(text=f"Downloading {model_key.upper()}...")

                success = self.ai_manager.download_model(model_key)

                if success:
                    self.progress_label.config(text=f"{model_key.upper()} downloaded successfully!")
                    messagebox.showinfo("Download Complete",
                                      f"{model_key.upper()} model downloaded successfully!")
                else:
                    self.progress_label.config(text=f"Failed to download {model_key.upper()}")
                    messagebox.showerror("Download Failed",
                                       f"Failed to download {model_key.upper()} model.")

            except Exception as e:
                messagebox.showerror("Download Error", f"Download failed: {e}")
            finally:
                self.current_operation = None
                self.progress_var.set(0)
                self._refresh_model_status()

        thread = threading.Thread(target=download_worker, daemon=True)
        thread.start()

    def _load_model(self, model_key: str):
        """Load an AI model into memory."""
        try:
            success = self.ai_manager.load_model(model_key)
            if success:
                messagebox.showinfo("Model Loaded", f"{model_key.upper()} model loaded successfully!")
            else:
                messagebox.showerror("Load Failed", f"Failed to load {model_key.upper()} model.")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load model: {e}")

        self._refresh_model_status()

    def _enhance_content(self):
        """Enhance the content in the enhancement tab."""
        content = self.enhancement_text.get('1.0', tk.END).strip()

        if not content:
            messagebox.showwarning("No Content", "Please enter some content to enhance.")
            return

        # Get enhancement options
        options = {var: self.enhancement_vars[var].get()
                  for var in self.enhancement_vars}

        def enhance_worker():
            try:
                result = self.enhancer.enhance_markdown(content, options)

                # Update UI
                self.enhanced_text.delete('1.0', tk.END)
                self.enhanced_text.insert('1.0', result['enhanced_content'])

                # Show suggestions
                suggestions_text = ""
                for i, suggestion in enumerate(result['suggestions'], 1):
                    suggestions_text += f"{i}. {suggestion['type'].upper()}: {suggestion.get('reason', '')}\n"
                    if 'suggested_content' in suggestion:
                        suggestions_text += f"   Suggestion: {suggestion['suggested_content'][:100]}...\n"
                    suggestions_text += "\n"

                self.suggestions_text.delete('1.0', tk.END)
                self.suggestions_text.insert('1.0', suggestions_text)

            except Exception as e:
                messagebox.showerror("Enhancement Error", f"Failed to enhance content: {e}")

        thread = threading.Thread(target=enhance_worker, daemon=True)
        thread.start()

    def _generate_tutorial(self):
        """Generate a tutorial from the specified topic."""
        topic = self.topic_var.get().strip()

        if not topic:
            messagebox.showwarning("No Topic", "Please enter a tutorial topic.")
            return

        difficulty = self.difficulty_var.get()
        include_images = self.include_images_var.get()

        def generate_worker():
            try:
                result = self.enhancer.create_tutorial_from_topic(
                    topic, difficulty, include_images
                )

                if 'error' in result:
                    messagebox.showerror("Generation Error", result['error'])
                    return

                # Update UI
                self.tutorial_text.delete('1.0', tk.END)
                self.tutorial_text.insert('1.0', result['markdown'])

                messagebox.showinfo("Tutorial Generated",
                                  f"Tutorial for '{topic}' generated successfully!\n\n"
                                  f"Sections: {len(result['tutorial'].get('sections', []))}\n"
                                  f"Suggestions: {len(result.get('suggestions', []))}")

            except Exception as e:
                messagebox.showerror("Generation Error", f"Failed to generate tutorial: {e}")

        thread = threading.Thread(target=generate_worker, daemon=True)
        thread.start()

    def _load_settings(self):
        """Load user settings."""
        # Load enhancement settings
        for var_name, var in self.settings_vars.items():
            var.set(self.enhancer.settings.get(var_name, True))

        self.confidence_var.set(self.enhancer.settings.get('confidence_threshold', 0.3))

        # Load enhancement options
        for var_name, var in self.enhancement_vars.items():
            var.set(self.enhancer.settings.get(var_name, True))

        self._refresh_cache_info()

    def _save_settings(self):
        """Save user settings."""
        # Update enhancer settings
        for var_name, var in self.settings_vars.items():
            self.enhancer.settings[var_name] = var.get()

        self.enhancer.settings['confidence_threshold'] = self.confidence_var.get()

        messagebox.showinfo("Settings Saved", "AI settings saved successfully!")

    def _refresh_cache_info(self):
        """Refresh cache information display."""
        try:
            info = self.ai_manager.get_model_info()
            cache_info = f"Cache Directory: {info['cache_dir']}\n"
            cache_info += f"Device: {info['device']}\n\n"
            cache_info += "Models:\n"

            for model_key, model_info in info['models'].items():
                status = "✅ Available" if model_info['available'] else "❌ Not available"
                cache_info += f"  {model_key}: {status} ({model_info['size_mb']}MB)\n"

            self.cache_info_var.set(cache_info)

        except Exception as e:
            self.cache_info_var.set(f"Error loading cache info: {e}")

    def _clear_cache(self):
        """Clear the AI model cache."""
        if messagebox.askyesno("Clear Cache",
                             "Are you sure you want to clear the AI model cache?\n\n"
                             "This will remove downloaded models and you'll need to download them again."):
            try:
                # This would need to be implemented in AIModelManager
                # For now, just show a message
                messagebox.showinfo("Cache Cleared", "Cache clearing not yet implemented.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear cache: {e}")


class AIStatusBar(ttk.Frame):
    """
    Status bar showing AI model status and quick actions.
    """

    def __init__(self, parent, ai_manager: AIModelManager, **kwargs):
        """
        Initialize AI status bar.

        Args:
            parent: Parent tkinter widget
            ai_manager: AIModelManager instance
        """
        super().__init__(parent, **kwargs)

        self.ai_manager = ai_manager

        self._setup_ui()

    def _setup_ui(self):
        """Set up the status bar UI."""
        # Model status indicators
        ttk.Label(self, text="AI Models:").pack(side=tk.LEFT, padx=(5, 0))

        self.status_indicators = {}
        for model_key in ['distilbart', 'clip']:
            frame = ttk.Frame(self)
            frame.pack(side=tk.LEFT, padx=(10, 0))

            # Model icon/label
            label = ttk.Label(frame, text=f"{model_key[:3].upper()}:")
            label.pack(side=tk.LEFT)

            # Status indicator
            canvas = tk.Canvas(frame, width=12, height=12)
            self.status_indicators[model_key] = canvas
            canvas.pack(side=tk.LEFT, padx=(2, 0))

        # Quick actions
        ttk.Button(self, text="⚙️ Settings",
                  command=self._show_settings).pack(side=tk.RIGHT, padx=(0, 5))

        # Initial status update
        self.update_status()

    def update_status(self):
        """Update the status indicators."""
        for model_key, canvas in self.status_indicators.items():
            try:
                available = self.ai_manager.is_model_available(model_key)
                loaded = model_key in self.ai_manager._models

                # Clear canvas
                canvas.delete("all")

                # Draw status circle
                if loaded:
                    color = "green"  # Loaded
                elif available:
                    color = "yellow"  # Downloaded but not loaded
                else:
                    color = "red"    # Not available

                canvas.create_oval(2, 2, 10, 10, fill=color, outline="black")

            except:
                canvas.create_oval(2, 2, 10, 10, fill="gray", outline="black")

    def _show_settings(self):
        """Show AI settings dialog."""
        # This would open the AI control panel
        # For now, just show a message
        messagebox.showinfo("AI Settings", "AI settings panel would open here.")


# Convenience functions for integration
def create_ai_control_panel(parent, ai_manager=None):
    """Create an AI control panel widget."""
    if ai_manager is None:
        ai_manager = AIModelManager()

    return AIControlPanel(parent, ai_manager)


def create_ai_status_bar(parent, ai_manager=None):
    """Create an AI status bar widget."""
    if ai_manager is None:
        ai_manager = AIModelManager()

    return AIStatusBar(parent, ai_manager)


if __name__ == "__main__":
    # Test the AI controls UI
    root = tk.Tk()
    root.title("KS PDF Studio - AI Controls Test")
    root.geometry("800x600")

    # Create AI manager
    ai_manager = AIModelManager()

    # Create control panel
    control_panel = AIControlPanel(root, ai_manager)
    control_panel.pack(fill=tk.BOTH, expand=True)

    # Create status bar
    status_bar = AIStatusBar(root, ai_manager)
    status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    root.mainloop()