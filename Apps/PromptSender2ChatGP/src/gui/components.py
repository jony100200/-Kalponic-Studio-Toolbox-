"""
GUI components for the Prompt Sequencer application.
Contains all the UI panels and tabs for the main window.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import time
from datetime import datetime
from typing import Callable, Optional, List

from ..core.sequencer import SequencerState

class StatusPanel(ctk.CTkFrame):
    """Status panel showing current state and progress"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.grid_columnconfigure(0, weight=1)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup status panel UI"""
        # Title
        title_label = ctk.CTkLabel(self, text="Status", font=ctk.CTkFont(size=16, weight="bold"))
        title_label.grid(row=0, column=0, pady=(5, 10), sticky="w")
        
        # Status indicators
        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        status_frame.grid_columnconfigure(1, weight=1)
        
        # State indicator
        state_frame = ctk.CTkFrame(status_frame)
        state_frame.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(state_frame, text="State:").pack(side="left", padx=5)
        self.state_light = ctk.CTkLabel(state_frame, text="●", text_color="gray", font=ctk.CTkFont(size=20))
        self.state_light.pack(side="left", padx=2)
        self.state_label = ctk.CTkLabel(state_frame, text="Idle")
        self.state_label.pack(side="left", padx=5)
        
        # Progress frame
        progress_frame = ctk.CTkFrame(status_frame)
        progress_frame.grid(row=0, column=1, padx=5, pady=5, sticky="e")
        
        self.progress_label = ctk.CTkLabel(progress_frame, text="Ready")
        self.progress_label.pack(padx=5, pady=2)
        
        self.current_file_label = ctk.CTkLabel(progress_frame, text="", font=ctk.CTkFont(size=11))
        self.current_file_label.pack(padx=5, pady=2)
    
    def update_state(self, state: SequencerState):
        """Update the state display"""
        state_colors = {
            SequencerState.IDLE: ("gray", "Idle"),
            SequencerState.RUNNING: ("green", "Running"),
            SequencerState.PAUSED: ("yellow", "Paused"),
            SequencerState.STOPPING: ("orange", "Stopping"),
            SequencerState.ERROR: ("red", "Error"),
            SequencerState.WAITING_FOR_USER: ("purple", "Waiting for User")
        }
        
        color, text = state_colors.get(state, ("gray", "Unknown"))
        self.state_light.configure(text_color=color)
        self.state_label.configure(text=text)
    
    def update_progress(self, current: int, total: int, current_file: str):
        """Update progress display"""
        if total > 0:
            self.progress_label.configure(text=f"Progress: {current}/{total}")
        else:
            self.progress_label.configure(text="Ready")
        
        if current_file:
            display_file = current_file if len(current_file) <= 30 else f"...{current_file[-27:]}"
            self.current_file_label.configure(text=f"File: {display_file}")
        else:
            self.current_file_label.configure(text="")

class ControlPanel(ctk.CTkFrame):
    """Global control panel with window selection and main controls"""
    
    def __init__(self, parent, config, window_detector):
        super().__init__(parent)
        self.config = config
        self.window_detector = window_detector
        
        # Callbacks
        self.start_callback: Optional[Callable] = None
        self.pause_callback: Optional[Callable] = None
        self.resume_callback: Optional[Callable] = None
        self.stop_callback: Optional[Callable] = None
        self.manual_resume_callback: Optional[Callable] = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup control panel UI"""
        # Title
        title_label = ctk.CTkLabel(self, text="Global Controls", font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=(5, 10))
        
        # Window target section
        window_frame = ctk.CTkFrame(self)
        window_frame.pack(fill="x", padx=10, pady=5)
        
        window_label = ctk.CTkLabel(window_frame, text="Target Window:")
        window_label.pack(side="left", padx=5)
        
        self.window_entry = ctk.CTkEntry(window_frame, placeholder_text="Window title substring")
        self.window_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        self.find_button = ctk.CTkButton(window_frame, text="Find Windows", command=self._find_windows, width=100)
        self.find_button.pack(side="left", padx=2)
        
        self.test_button = ctk.CTkButton(window_frame, text="Test Focus", command=self._test_focus, width=80)
        self.test_button.pack(side="left", padx=2)
        
        # Delay section
        delay_frame = ctk.CTkFrame(self)
        delay_frame.pack(fill="x", padx=10, pady=5)
        
        delay_label = ctk.CTkLabel(delay_frame, text="Initial Delay (sec):")
        delay_label.pack(side="left", padx=5)
        
        self.delay_var = tk.StringVar(value="3")
        self.delay_spinbox = ctk.CTkEntry(delay_frame, textvariable=self.delay_var, width=60)
        self.delay_spinbox.pack(side="left", padx=5)
        
        # Control buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.start_button = ctk.CTkButton(button_frame, text="Start", command=self._start, width=80)
        self.start_button.pack(side="left", padx=5)
        
        self.pause_button = ctk.CTkButton(button_frame, text="Pause", command=self._pause, width=80, state="disabled")
        self.pause_button.pack(side="left", padx=2)
        
        self.resume_button = ctk.CTkButton(button_frame, text="Resume", command=self._resume, width=80, state="disabled")
        self.resume_button.pack(side="left", padx=2)
        
        self.stop_button = ctk.CTkButton(button_frame, text="Stop", command=self._stop, width=80, state="disabled")
        self.stop_button.pack(side="left", padx=2)
        
        self.manual_resume_button = ctk.CTkButton(button_frame, text="Resume After Manual Fix", 
                                                 command=self._manual_resume, width=140, state="disabled")
        self.manual_resume_button.pack(side="left", padx=2)
    
    def set_callbacks(self, start_callback=None, pause_callback=None, resume_callback=None, 
                      stop_callback=None, manual_resume_callback=None):
        """Set callback functions"""
        self.start_callback = start_callback
        self.pause_callback = pause_callback
        self.resume_callback = resume_callback
        self.stop_callback = stop_callback
        self.manual_resume_callback = manual_resume_callback
    
    def _find_windows(self):
        """Find and display available windows"""
        windows = self.window_detector.find_windows()
        if windows:
            # Create selection dialog
            dialog = WindowSelectionDialog(self, windows)
            selected = dialog.show()
            if selected:
                self.window_entry.delete(0, 'end')
                self.window_entry.insert(0, selected)
        else:
            messagebox.showinfo("Windows", "No windows found")
    
    def _test_focus(self):
        """Test focusing the target window and input box"""
        target = self.window_entry.get().strip()
        if not target:
            messagebox.showwarning("Warning", "Please enter a window title substring")
            return
        
        # Test window focus
        success = self.window_detector.focus_window(target)
        if not success:
            messagebox.showerror("Error", "Could not focus the target window")
            return
        
        # Test input box focus with detailed feedback
        input_success = self.window_detector.focus_input_box(retries=2)
        
        if input_success:
            messagebox.showinfo("Success", 
                "✓ Window focused successfully!\n"
                "✓ Input box focused using keyboard navigation!\n\n"
                "The application is ready to automate prompts.")
        else:
            response = messagebox.askyesno("Partial Success", 
                "✓ Window focused successfully!\n"
                "⚠ Could not auto-focus input box.\n\n"
                "This may still work during automation as the app will retry.\n"
                "Would you like to manually click in the input box now to test?")
            
            if response:
                messagebox.showinfo("Manual Test", 
                    "Please click inside the input box of the target application, "
                    "then click OK to continue the test.")
                
                # Test if we can paste after manual focus
                test_success = self._test_manual_paste()
                if test_success:
                    messagebox.showinfo("Success", 
                        "✓ Manual focus test successful!\n"
                        "The app should work with occasional manual assistance.")
                else:
                    messagebox.showerror("Error", 
                        "Manual focus test failed. Check the target application.")
    
    def _test_manual_paste(self) -> bool:
        """Test paste functionality after manual focus"""
        try:
            import pyperclip
            import pyautogui
            
            # Save original clipboard
            original = pyperclip.paste()
            
            # Test paste
            test_text = "<<<FOCUS TEST>>>"
            pyperclip.copy(test_text)
            time.sleep(0.1)
            
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.1)
            
            # Clean up
            for _ in range(len(test_text)):
                pyautogui.press('backspace')
                time.sleep(0.01)
            
            # Restore clipboard
            pyperclip.copy(original)
            
            return True
            
        except Exception as e:
            return False
    
    def _start(self):
        """Start button callback"""
        if self.start_callback:
            self.start_callback()
    
    def _pause(self):
        """Pause button callback"""
        if self.pause_callback:
            self.pause_callback()
    
    def _resume(self):
        """Resume button callback"""
        if self.resume_callback:
            self.resume_callback()
    
    def _stop(self):
        """Stop button callback"""
        if self.stop_callback:
            self.stop_callback()
    
    def _manual_resume(self):
        """Manual resume button callback"""
        if self.manual_resume_callback:
            self.manual_resume_callback()
    
    def show_manual_intervention_needed(self):
        """Show that manual intervention is needed"""
        self.manual_resume_button.configure(state="normal")
        self.pause_button.configure(state="disabled")
        self.resume_button.configure(state="disabled")
    
    def update_state(self, state: SequencerState):
        """Update button states based on sequencer state"""
        if state == SequencerState.IDLE:
            self.start_button.configure(state="normal")
            self.pause_button.configure(state="disabled")
            self.resume_button.configure(state="disabled")
            self.stop_button.configure(state="disabled")
            self.manual_resume_button.configure(state="disabled")
        elif state == SequencerState.RUNNING:
            self.start_button.configure(state="disabled")
            self.pause_button.configure(state="normal")
            self.resume_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.manual_resume_button.configure(state="disabled")
        elif state == SequencerState.PAUSED:
            self.start_button.configure(state="disabled")
            self.pause_button.configure(state="disabled")
            self.resume_button.configure(state="normal")
            self.stop_button.configure(state="normal")
            self.manual_resume_button.configure(state="disabled")
        elif state == SequencerState.WAITING_FOR_USER:
            self.start_button.configure(state="disabled")
            self.pause_button.configure(state="disabled")
            self.resume_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.manual_resume_button.configure(state="normal")
        else:  # STOPPING, ERROR
            self.start_button.configure(state="disabled")
            self.pause_button.configure(state="disabled")
            self.resume_button.configure(state="disabled")
            self.stop_button.configure(state="disabled")
            self.manual_resume_button.configure(state="disabled")
    
    def load_settings(self):
        """Load settings from config"""
        self.window_entry.delete(0, 'end')
        self.window_entry.insert(0, self.config.target_window)
        self.delay_var.set(str(self.config.initial_delay))
    
    def save_settings(self):
        """Save settings to config"""
        self.config.target_window = self.window_entry.get().strip()
        try:
            self.config.initial_delay = int(self.delay_var.get())
        except ValueError:
            self.config.initial_delay = 3

class TextModeTab(ctk.CTkScrollableFrame):
    """Text mode configuration tab with scrolling"""
    
    def __init__(self, parent, config):
        super().__init__(parent, orientation="vertical")
        self.config = config
        self.grid_columnconfigure(0, weight=1)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup text mode UI"""
        # Input folder selection
        folder_frame = ctk.CTkFrame(self)
        folder_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        folder_frame.grid_columnconfigure(1, weight=1)
        
        folder_label = ctk.CTkLabel(folder_frame, text="Text Files Folder:")
        folder_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        
        self.folder_entry = ctk.CTkEntry(folder_frame, placeholder_text="Select folder containing .txt files")
        self.folder_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        
        folder_button = ctk.CTkButton(folder_frame, text="Browse", command=self._select_folder, width=80)
        folder_button.grid(row=1, column=1, padx=2, pady=2)
        
        # Settings frame
        settings_frame = ctk.CTkFrame(self)
        settings_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        settings_frame.grid_columnconfigure(1, weight=1)
        
        settings_label = ctk.CTkLabel(settings_frame, text="Text Mode Settings:", font=ctk.CTkFont(size=14, weight="bold"))
        settings_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 10))
        
        # Settings grid - more responsive layout
        row = 1
        
        # Paste->Enter Grace
        ctk.CTkLabel(settings_frame, text="Paste→Enter Grace (ms):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.grace_var = tk.StringVar(value="400")
        ctk.CTkEntry(settings_frame, textvariable=self.grace_var, width=100).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # Generation Wait
        ctk.CTkLabel(settings_frame, text="Generation Wait (sec):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.wait_var = tk.StringVar(value="45")
        ctk.CTkEntry(settings_frame, textvariable=self.wait_var, width=100).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # Jitter
        ctk.CTkLabel(settings_frame, text="Jitter (±%):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.jitter_var = tk.StringVar(value="15")
        ctk.CTkEntry(settings_frame, textvariable=self.jitter_var, width=100).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # Auto-Enter toggle
        self.auto_enter_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(settings_frame, text="Auto-Enter", variable=self.auto_enter_var).grid(row=row, column=0, sticky="w", padx=5, pady=5)
    
    def _select_folder(self):
        """Select input folder"""
        folder = filedialog.askdirectory(title="Select Text Files Folder")
        if folder:
            self.folder_entry.delete(0, 'end')
            self.folder_entry.insert(0, folder)
    
    def load_settings(self):
        """Load settings from config"""
        self.folder_entry.delete(0, 'end')
        self.folder_entry.insert(0, self.config.text_input_folder)
        self.grace_var.set(str(self.config.text_paste_enter_grace))
        self.wait_var.set(str(self.config.text_generation_wait))
        self.jitter_var.set(str(self.config.text_jitter_percent))
        self.auto_enter_var.set(self.config.text_auto_enter)
    
    def save_settings(self):
        """Save settings to config"""
        self.config.text_input_folder = self.folder_entry.get().strip()
        try:
            self.config.text_paste_enter_grace = int(self.grace_var.get())
            self.config.text_generation_wait = int(self.wait_var.get())
            self.config.text_jitter_percent = int(self.jitter_var.get())
        except ValueError:
            pass  # Keep existing values
        self.config.text_auto_enter = self.auto_enter_var.get()

class ImageModeTab(ctk.CTkScrollableFrame):
    """Image + text mode configuration tab with scrolling"""
    
    def __init__(self, parent, config):
        super().__init__(parent, orientation="vertical")
        self.config = config
        self.grid_columnconfigure(0, weight=1)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup image mode UI"""
        # Input folder selection
        folder_frame = ctk.CTkFrame(self)
        folder_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        folder_frame.grid_columnconfigure(1, weight=1)
        
        # Image folder
        img_folder_label = ctk.CTkLabel(folder_frame, text="Image Files Folder:")
        img_folder_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        
        self.img_folder_entry = ctk.CTkEntry(folder_frame, placeholder_text="Select folder containing images")
        self.img_folder_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        
        img_folder_button = ctk.CTkButton(folder_frame, text="Browse", command=self._select_image_folder, width=80)
        img_folder_button.grid(row=1, column=1, padx=2, pady=2)
        
        # Global prompt file
        prompt_label = ctk.CTkLabel(folder_frame, text="Global Prompt File (optional):")
        prompt_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=(10, 2))
        
        self.prompt_entry = ctk.CTkEntry(folder_frame, placeholder_text="Select .txt file with global prompt")
        self.prompt_entry.grid(row=3, column=0, sticky="ew", padx=5, pady=2)
        
        prompt_button = ctk.CTkButton(folder_frame, text="Browse", command=self._select_prompt_file, width=80)
        prompt_button.grid(row=3, column=1, padx=2, pady=2)
        
        # Settings frame
        settings_frame = ctk.CTkFrame(self)
        settings_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        settings_frame.grid_columnconfigure(1, weight=1)
        
        settings_label = ctk.CTkLabel(settings_frame, text="Image Mode Settings:", font=ctk.CTkFont(size=14, weight="bold"))
        settings_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 10))
        
        # Settings grid - more responsive layout
        row = 1
        
        # Intra delay
        ctk.CTkLabel(settings_frame, text="Intra Delay after Image (ms):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.intra_var = tk.StringVar(value="300")
        ctk.CTkEntry(settings_frame, textvariable=self.intra_var, width=100).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # Paste->Enter Grace
        ctk.CTkLabel(settings_frame, text="Paste→Enter Grace (ms):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.grace_var = tk.StringVar(value="400")
        ctk.CTkEntry(settings_frame, textvariable=self.grace_var, width=100).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # Generation Wait
        ctk.CTkLabel(settings_frame, text="Generation Wait (sec):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.wait_var = tk.StringVar(value="60")
        ctk.CTkEntry(settings_frame, textvariable=self.wait_var, width=100).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # Jitter
        ctk.CTkLabel(settings_frame, text="Jitter (±%):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.jitter_var = tk.StringVar(value="15")
        ctk.CTkEntry(settings_frame, textvariable=self.jitter_var, width=100).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # Toggles
        self.auto_enter_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(settings_frame, text="Auto-Enter", variable=self.auto_enter_var).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        
        self.repeat_prompt_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(settings_frame, text="Repeat prompt per image", variable=self.repeat_prompt_var).grid(row=row, column=1, sticky="w", padx=5, pady=5)
    
    def _select_image_folder(self):
        """Select image folder"""
        folder = filedialog.askdirectory(title="Select Image Files Folder")
        if folder:
            self.img_folder_entry.delete(0, 'end')
            self.img_folder_entry.insert(0, folder)
    
    def _select_prompt_file(self):
        """Select global prompt file"""
        file = filedialog.askopenfilename(
            title="Select Global Prompt File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file:
            self.prompt_entry.delete(0, 'end')
            self.prompt_entry.insert(0, file)
    
    def load_settings(self):
        """Load settings from config"""
        self.img_folder_entry.delete(0, 'end')
        self.img_folder_entry.insert(0, self.config.image_input_folder)
        self.prompt_entry.delete(0, 'end')
        self.prompt_entry.insert(0, self.config.global_prompt_file)
        self.intra_var.set(str(self.config.image_intra_delay))
        self.grace_var.set(str(self.config.image_paste_enter_grace))
        self.wait_var.set(str(self.config.image_generation_wait))
        self.jitter_var.set(str(self.config.image_jitter_percent))
        self.auto_enter_var.set(self.config.image_auto_enter)
        self.repeat_prompt_var.set(self.config.image_repeat_prompt)
    
    def save_settings(self):
        """Save settings to config"""
        self.config.image_input_folder = self.img_folder_entry.get().strip()
        self.config.global_prompt_file = self.prompt_entry.get().strip()
        try:
            self.config.image_intra_delay = int(self.intra_var.get())
            self.config.image_paste_enter_grace = int(self.grace_var.get())
            self.config.image_generation_wait = int(self.wait_var.get())
            self.config.image_jitter_percent = int(self.jitter_var.get())
        except ValueError:
            pass  # Keep existing values
        self.config.image_auto_enter = self.auto_enter_var.get()
        self.config.image_repeat_prompt = self.repeat_prompt_var.get()

class LogPanel(ctk.CTkFrame):
    """Log panel with scrollable text display"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.setup_ui()
        self.log_entries = []
    
    def setup_ui(self):
        """Setup log panel UI"""
        # Title and controls
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 2))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(header_frame, text="Activity Log", font=ctk.CTkFont(size=14, weight="bold"))
        title_label.grid(row=0, column=0, sticky="w", padx=5)
        
        button_frame = ctk.CTkFrame(header_frame)
        button_frame.grid(row=0, column=1, sticky="e", padx=5)
        
        clear_button = ctk.CTkButton(button_frame, text="Clear", command=self._clear_log, width=60)
        clear_button.pack(side="right", padx=2)
        
        export_button = ctk.CTkButton(button_frame, text="Export", command=self._export_log, width=60)
        export_button.pack(side="right", padx=2)
        
        # Log display with proper scrolling
        self.log_text = ctk.CTkTextbox(self, height=150, wrap="word")
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=2)
    
    def add_log_entry(self, message: str, level: str = "info"):
        """Add a log entry"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_upper = level.upper()
        log_line = f"[{timestamp}] {level_upper}: {message}\n"
        
        self.log_entries.append(log_line)
        self.log_text.insert("end", log_line)
        self.log_text.see("end")
        
        # Limit log entries to prevent memory issues
        if len(self.log_entries) > 1000:
            self.log_entries = self.log_entries[-500:]  # Keep last 500
            self._refresh_display()
    
    def _clear_log(self):
        """Clear the log display"""
        self.log_text.delete("1.0", "end")
        self.log_entries.clear()
    
    def _export_log(self):
        """Export log to file"""
        if not self.log_entries:
            messagebox.showinfo("Export", "No log entries to export")
            return
        
        file = filedialog.asksaveasfilename(
            title="Export Log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file:
            try:
                with open(file, 'w', encoding='utf-8') as f:
                    f.writelines(self.log_entries)
                messagebox.showinfo("Export", f"Log exported to {file}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export log: {e}")
    
    def _refresh_display(self):
        """Refresh the log display"""
        self.log_text.delete("1.0", "end")
        for entry in self.log_entries:
            self.log_text.insert("end", entry)
        self.log_text.see("end")

class WindowSelectionDialog:
    """Dialog for selecting a window from available windows"""
    
    def __init__(self, parent, windows: List[str]):
        self.parent = parent
        self.windows = windows
        self.result = None
        
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Select Window")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        # Title
        title_label = ctk.CTkLabel(self.dialog, text="Available Windows:", font=ctk.CTkFont(size=14, weight="bold"))
        title_label.pack(pady=10)
        
        # Window list
        self.listbox = tk.Listbox(self.dialog)
        self.listbox.pack(fill="both", expand=True, padx=20, pady=10)
        
        for window in self.windows:
            self.listbox.insert("end", window)
        
        # Buttons
        button_frame = ctk.CTkFrame(self.dialog)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        select_button = ctk.CTkButton(button_frame, text="Select", command=self._select)
        select_button.pack(side="right", padx=5)
        
        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=self._cancel)
        cancel_button.pack(side="right", padx=5)
        
        # Bind double-click
        self.listbox.bind("<Double-Button-1>", lambda e: self._select())
    
    def _select(self):
        """Select the highlighted window"""
        selection = self.listbox.curselection()
        if selection:
            self.result = self.windows[selection[0]]
        self.dialog.destroy()
    
    def _cancel(self):
        """Cancel selection"""
        self.result = None
        self.dialog.destroy()
    
    def show(self) -> Optional[str]:
        """Show dialog and return selected window"""
        self.dialog.wait_window()
        return self.result
