"""
Main GUI window for the Prompt Sequencer application.
Built with CustomTkinter for a modern interface.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import time
import logging
from typing import Optional

from ..core.sequencer import PromptSequencer, SequencerState
from ..automation.automation import WindowDetector
from .components import StatusPanel, ControlPanel, TextModeTab, ImageModeTab, LogPanel

class PromptSequencerGUI:
    """Main application window"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.sequencer = PromptSequencer(config)
        self.window_detector = WindowDetector()
        
        # Setup callbacks
        self.sequencer.set_callbacks(
            state_callback=self._on_state_change,
            progress_callback=self._on_progress_update,
            log_callback=self._on_log_message,
            manual_intervention_callback=self._on_manual_intervention_needed
        )
        
        # GUI setup
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("Prompt Sequencer")
        self.root.geometry("1000x800")
        self.root.minsize(800, 600)
        
        # Make window resizable and responsive
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Handle window resizing
        self.root.bind("<Configure>", self._on_window_resize)
        
        self._setup_ui()
        self._load_settings()
        self._adjust_for_screen_size()
        
        # Threading
        self.sequencer_thread: Optional[threading.Thread] = None
    
    def _setup_ui(self):
        """Setup the user interface"""
        # Create main scrollable frame
        self.main_scrollable = ctk.CTkScrollableFrame(
            self.root,
            orientation="vertical",
            height=600,
            corner_radius=0,
            scrollbar_button_color=("gray75", "gray25"),
            scrollbar_button_hover_color=("gray64", "gray40")
        )
        self.main_scrollable.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.main_scrollable.grid_columnconfigure(0, weight=1)
        
        # Top section - Global controls and status
        top_frame = ctk.CTkFrame(self.main_scrollable)
        top_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 10))
        top_frame.grid_columnconfigure(0, weight=1)
        
        # Global controls
        self.control_panel = ControlPanel(top_frame, self.config, self.window_detector)
        self.control_panel.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Status panel
        self.status_panel = StatusPanel(top_frame)
        self.status_panel.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Middle section - Tabs
        tabs_frame = ctk.CTkFrame(self.main_scrollable)
        tabs_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        tabs_frame.grid_columnconfigure(0, weight=1)
        tabs_frame.grid_rowconfigure(0, weight=1)
        
        self.notebook = ctk.CTkTabview(tabs_frame, height=350)
        self.notebook.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Text mode tab
        self.notebook.add("Text Mode")
        self.text_tab = TextModeTab(self.notebook.tab("Text Mode"), self.config)
        self.text_tab.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Image mode tab
        self.notebook.add("Image + Text Mode")
        self.image_tab = ImageModeTab(self.notebook.tab("Image + Text Mode"), self.config)
        self.image_tab.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Bottom section - Log panel
        log_frame = ctk.CTkFrame(self.main_scrollable)
        log_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        
        self.log_panel = LogPanel(log_frame)
        self.log_panel.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Connect control panel callbacks
        self.control_panel.set_callbacks(
            start_callback=self._start_sequencer,
            pause_callback=self._pause_sequencer,
            resume_callback=self._resume_sequencer,
            stop_callback=self._stop_sequencer,
            manual_resume_callback=self._manual_resume_sequencer
        )
        
        # Add status bar at the bottom
        self.status_bar = ctk.CTkFrame(self.root, height=25)
        self.status_bar.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        
        self.status_bar_label = ctk.CTkLabel(
            self.status_bar, 
            text="Ready • Use scroll wheel or scrollbar to navigate", 
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        self.status_bar_label.pack(side="left", padx=10, pady=2)
    
    def _adjust_for_screen_size(self):
        """Adjust window size based on screen resolution"""
        try:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Calculate optimal window size (80% of screen, but respecting min/max)
            optimal_width = min(1200, int(screen_width * 0.8))
            optimal_height = min(900, int(screen_height * 0.8))
            
            # Ensure minimum size
            window_width = max(800, optimal_width)
            window_height = max(600, optimal_height)
            
            # Center window on screen
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            
            self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # Adjust scrollable frame height based on window size
            if hasattr(self, 'main_scrollable'):
                self.main_scrollable.configure(height=window_height - 100)
                
        except Exception as e:
            self.logger.warning(f"Could not adjust window size: {e}")
    
    def _on_window_resize(self, event):
        """Handle window resize events"""
        # Only react to root window resize events
        if event.widget == self.root:
            try:
                # Update scrollable frame height based on new window size
                if hasattr(self, 'main_scrollable'):
                    new_height = max(400, self.root.winfo_height() - 100)
                    self.main_scrollable.configure(height=new_height)
                
                # Update status bar with current size
                if hasattr(self, 'status_bar_label'):
                    width = self.root.winfo_width()
                    height = self.root.winfo_height()
                    self.status_bar_label.configure(text=f"Window: {width}x{height} • Scroll to navigate all content")
                    
            except Exception as e:
                # Ignore resize errors to prevent crashes
                pass
    
    def _load_settings(self):
        """Load settings into UI components"""
        self.control_panel.load_settings()
        self.text_tab.load_settings()
        self.image_tab.load_settings()
    
    def _save_settings(self):
        """Save settings from UI components"""
        self.control_panel.save_settings()
        self.text_tab.save_settings()
        self.image_tab.save_settings()
        self.config.save()
    
    def _start_sequencer(self):
        """Start the sequencer in a separate thread"""
        if self.sequencer_thread and self.sequencer_thread.is_alive():
            return
        
        # Save current settings
        self._save_settings()
        
        # Determine mode
        current_tab = self.notebook.get()

        if current_tab == "Text Mode":
            if not self.config.text_input_folder:
                messagebox.showerror("Error", "Please select a text input folder")
                return

            self.sequencer_thread = threading.Thread(
                target=self._run_with_initial_delay,
                args=(self.sequencer.start_text_mode, self.config.text_input_folder),
                daemon=True
            )
        else:  # Image mode
            if self.config.image_queue_mode:
                # Queue mode (support dynamic enqueueing)
                import queue as _pyqueue

                # Ensure config has a persistent queue object for runtime
                if not hasattr(self.config, 'image_queue_obj') or self.config.image_queue_obj is None:
                    qobj = _pyqueue.Queue()
                    # Seed from existing items if present
                    if hasattr(self.config, 'image_queue_items') and self.config.image_queue_items:
                        for itm in self.config.image_queue_items:
                            qobj.put(itm)
                else:
                    qobj = self.config.image_queue_obj

                # Save queue object back to config
                self.config.image_queue_obj = qobj

                # Register callback to remove finished items from GUI
                def _on_queue_item_done(item_id: str):
                    # Remove matching entry from listbox and config (main thread)
                    self.root.after(0, lambda: self._on_queue_item_done_by_id(item_id))

                # Attach callback to sequencer
                self.sequencer.queue_item_done_callback = _on_queue_item_done

                self.sequencer_thread = threading.Thread(
                    target=self._run_with_initial_delay,
                    args=(self.sequencer.start_image_queue_mode, self.config.image_queue_obj),
                    daemon=True
                )
            else:
                # Single folder mode
                if not self.config.image_input_folder:
                    messagebox.showerror("Error", "Please select an image input folder")
                    return

                self.sequencer_thread = threading.Thread(
                    target=self._run_with_initial_delay,
                    args=(self.sequencer.start_image_mode,
                          self.config.image_input_folder,
                          self.config.global_prompt_file),
                    daemon=True
                )

        self.sequencer_thread.start()
    
    def _run_with_initial_delay(self, func, *args):
        """Run sequencer function with initial delay countdown"""
        try:
            if self.config.initial_delay > 0:
                for i in range(self.config.initial_delay, 0, -1):
                    if self.sequencer.state == SequencerState.STOPPING:
                        return
                    
                    self._on_log_message(f"Starting in {i} seconds...", "info")
                    time.sleep(1)
            
            func(*args)
            
        except Exception as e:
            self.logger.error(f"Error in sequencer thread: {e}")
            self._on_log_message(f"Sequencer error: {e}", "error")
    
    def _pause_sequencer(self):
        """Pause the sequencer"""
        self.sequencer.pause()
    
    def _resume_sequencer(self):
        """Resume the sequencer"""
        self.sequencer.resume()
    
    def _stop_sequencer(self):
        """Stop the sequencer"""
        self.sequencer.stop()
    
    def _manual_resume_sequencer(self):
        """Resume after manual intervention"""
        self.sequencer.resolve_manual_intervention()
    
    def _on_manual_intervention_needed(self, message: str):
        """Handle manual intervention requests"""
        # Show message in log
        self._on_log_message(f"MANUAL INTERVENTION: {message}", "warning")
        
        # Update UI to show manual intervention state
        self.root.after(0, lambda: self.control_panel.show_manual_intervention_needed())

    def _on_queue_item_done(self, folder_name: str):
        # Legacy name-based removal helper removed. Use _on_queue_item_done_by_id(item_id)
        # which the sequencer now calls with the unique item id for deterministic removal.
        return

    def _on_queue_item_done_by_id(self, item_id: str):
        """Remove completed queue item by its unique id."""
        try:
            listbox = self.image_tab.queue_listbox
            items = listbox.get(0, tk.END)
            match_index = None
            for idx, text in enumerate(items):
                # The display text contains folder name; we match by config ids instead
                pass

            # Remove from config by id and then from listbox by rebuilding display entries
            removed_name = None
            if hasattr(self.config, 'image_queue_items') and self.config.image_queue_items:
                for i, itm in enumerate(self.config.image_queue_items):
                    if itm.get('id') == item_id:
                        removed = self.config.image_queue_items.pop(i)
                        removed_name = removed.get('name')
                        break

            # Rebuild listbox contents to reflect removal
            if removed_name is not None:
                listbox.delete(0, tk.END)
                for itm in self.config.image_queue_items:
                    folder_name = itm.get('name', 'Unknown')
                    prompt_name = os.path.basename(itm.get('prompt_file', '')) or 'No prompt'
                    display_text = f"{folder_name} → {prompt_name}"
                    listbox.insert(tk.END, display_text)
        except Exception:
            pass
    
    def _on_state_change(self, state: SequencerState):
        """Handle sequencer state changes"""
        # Update UI on main thread
        self.root.after(0, lambda: self.status_panel.update_state(state))
        self.root.after(0, lambda: self.control_panel.update_state(state))
    
    def _on_progress_update(self, current: int, total: int, current_file: str):
        """Handle progress updates"""
        # Update UI on main thread
        self.root.after(0, lambda: self.status_panel.update_progress(current, total, current_file))
    
    def _on_log_message(self, message: str, level: str):
        """Handle log messages"""
        # Update UI on main thread
        self.root.after(0, lambda: self.log_panel.add_log_entry(message, level))
    
    def _on_closing(self):
        """Handle application closing"""
        try:
            # Stop sequencer if running
            if self.sequencer.state != SequencerState.IDLE:
                self.sequencer.stop()
                
                # Wait a bit for graceful shutdown
                if self.sequencer_thread and self.sequencer_thread.is_alive():
                    self.sequencer_thread.join(timeout=2.0)
            
            # Save settings
            self._save_settings()
            
            # Cleanup clipboard
            if hasattr(self.sequencer, 'paste_controller'):
                self.sequencer.paste_controller.cleanup()
            
            self.root.destroy()
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            self.root.destroy()
    
    def run(self):
        """Start the GUI application"""
        self.logger.info("Starting Prompt Sequencer GUI")
        self.root.mainloop()
