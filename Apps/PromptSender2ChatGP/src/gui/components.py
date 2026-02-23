"""
GUI components for the Prompt Sequencer application.
Contains all the UI panels and tabs for the main window.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import uuid
import logging

logger = logging.getLogger(__name__)
import time
from datetime import datetime
from typing import Callable, Optional, List

from ..core.sequencer import SequencerState

def _clamp_int(value, default: int, minimum: int, maximum: int) -> int:
    """Parse integer and clamp to safe range."""
    try:
        parsed = int(value)
    except Exception:
        parsed = default
    return max(minimum, min(maximum, parsed))

def _clamp_float(value, default: float, minimum: float, maximum: float) -> float:
    """Parse float and clamp to safe range."""
    try:
        parsed = float(value)
    except Exception:
        parsed = default
    return max(minimum, min(maximum, parsed))

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
        self.preflight_callback: Optional[Callable] = None
        self.resume_snapshot_callback: Optional[Callable] = None
        self.show_last_summary_callback: Optional[Callable] = None
        self.save_profile_callback: Optional[Callable] = None
        self.apply_profile_callback: Optional[Callable] = None
        self.refresh_profiles_callback: Optional[Callable] = None
        
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

        # Safety and behavior toggles
        safety_frame = ctk.CTkFrame(self)
        safety_frame.pack(fill="x", padx=10, pady=5)
        safety_frame.grid_columnconfigure(0, weight=1)
        safety_frame.grid_columnconfigure(1, weight=1)
        safety_frame.grid_columnconfigure(2, weight=1)

        safety_label = ctk.CTkLabel(
            safety_frame,
            text="Execution Safety",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        safety_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=(5, 4))

        self.dry_run_var = tk.BooleanVar(value=False)
        self.skip_duplicates_var = tk.BooleanVar(value=False)
        self.prompt_vars_var = tk.BooleanVar(value=True)
        self.queue_snapshot_var = tk.BooleanVar(value=True)
        self.auto_resume_snapshot_var = tk.BooleanVar(value=False)
        self.error_screenshots_var = tk.BooleanVar(value=True)
        self.dry_run_var.trace_add("write", self._on_safety_toggle_changed)
        self.skip_duplicates_var.trace_add("write", self._on_safety_toggle_changed)
        self.queue_snapshot_var.trace_add("write", self._on_safety_toggle_changed)
        self.auto_resume_snapshot_var.trace_add("write", self._on_safety_toggle_changed)

        ctk.CTkCheckBox(
            safety_frame, text="Dry Run", variable=self.dry_run_var
        ).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ctk.CTkCheckBox(
            safety_frame, text="Skip Duplicates", variable=self.skip_duplicates_var
        ).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ctk.CTkCheckBox(
            safety_frame, text="Prompt Variables", variable=self.prompt_vars_var
        ).grid(row=1, column=2, sticky="w", padx=5, pady=2)

        ctk.CTkCheckBox(
            safety_frame, text="Queue Snapshots", variable=self.queue_snapshot_var
        ).grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ctk.CTkCheckBox(
            safety_frame, text="Auto Resume Queue", variable=self.auto_resume_snapshot_var
        ).grid(row=2, column=1, sticky="w", padx=5, pady=2)
        ctk.CTkCheckBox(
            safety_frame, text="Error Screenshots", variable=self.error_screenshots_var
        ).grid(row=2, column=2, sticky="w", padx=5, pady=2)

        # Retry tuning
        retry_frame = ctk.CTkFrame(self)
        retry_frame.pack(fill="x", padx=10, pady=5)
        retry_frame.grid_columnconfigure(1, weight=1)
        retry_frame.grid_columnconfigure(3, weight=1)
        retry_frame.grid_columnconfigure(5, weight=1)

        retry_label = ctk.CTkLabel(
            retry_frame,
            text="Reliability Tuning",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        retry_label.grid(row=0, column=0, columnspan=6, sticky="w", padx=5, pady=(5, 4))

        ctk.CTkLabel(retry_frame, text="Paste Retries:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.paste_retries_var = tk.StringVar(value="3")
        self.paste_retries_entry = ctk.CTkEntry(retry_frame, textvariable=self.paste_retries_var, width=70)
        self.paste_retries_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)

        ctk.CTkLabel(retry_frame, text="Retry Delay (s):").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        self.retry_delay_var = tk.StringVar(value="0.5")
        self.retry_delay_entry = ctk.CTkEntry(retry_frame, textvariable=self.retry_delay_var, width=70)
        self.retry_delay_entry.grid(row=1, column=3, sticky="w", padx=5, pady=2)

        ctk.CTkLabel(retry_frame, text="Focus Retries:").grid(row=1, column=4, sticky="w", padx=5, pady=2)
        self.focus_retries_var = tk.StringVar(value="3")
        self.focus_retries_entry = ctk.CTkEntry(retry_frame, textvariable=self.focus_retries_var, width=70)
        self.focus_retries_entry.grid(row=1, column=5, sticky="w", padx=5, pady=2)

        # Profiles
        profile_frame = ctk.CTkFrame(self)
        profile_frame.pack(fill="x", padx=10, pady=5)
        profile_frame.grid_columnconfigure(1, weight=1)

        profile_label = ctk.CTkLabel(
            profile_frame,
            text="Profiles",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        profile_label.grid(row=0, column=0, columnspan=6, sticky="w", padx=5, pady=(5, 4))

        ctk.CTkLabel(profile_frame, text="Saved:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.profile_var = tk.StringVar(value="<none>")
        self.profile_menu = ctk.CTkOptionMenu(profile_frame, variable=self.profile_var, values=["<none>"], width=240)
        self.profile_menu.grid(row=1, column=1, sticky="w", padx=5, pady=2)

        self.load_profile_button = ctk.CTkButton(
            profile_frame, text="Load", command=self._apply_profile, width=70
        )
        self.load_profile_button.grid(row=1, column=2, padx=2, pady=2)

        self.refresh_profiles_button = ctk.CTkButton(
            profile_frame, text="Refresh", command=self.refresh_profiles, width=70
        )
        self.refresh_profiles_button.grid(row=1, column=3, padx=2, pady=2)

        self.profile_name_var = tk.StringVar(value="")
        self.profile_name_entry = ctk.CTkEntry(
            profile_frame, textvariable=self.profile_name_var, placeholder_text="new profile name", width=180
        )
        self.profile_name_entry.grid(row=2, column=1, sticky="w", padx=5, pady=2)

        self.save_profile_button = ctk.CTkButton(
            profile_frame, text="Save Current", command=self._save_profile, width=110
        )
        self.save_profile_button.grid(row=2, column=2, padx=2, pady=2)
        
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

        util_frame = ctk.CTkFrame(self)
        util_frame.pack(fill="x", padx=10, pady=(0, 5))

        self.preflight_button = ctk.CTkButton(
            util_frame, text="Preflight Check", command=self._preflight, width=120
        )
        self.preflight_button.pack(side="left", padx=5, pady=4)

        self.resume_snapshot_button = ctk.CTkButton(
            util_frame, text="Resume Snapshot", command=self._resume_snapshot, width=130
        )
        self.resume_snapshot_button.pack(side="left", padx=2, pady=4)

        self.last_summary_button = ctk.CTkButton(
            util_frame, text="Open Last Summary", command=self._show_last_summary, width=140
        )
        self.last_summary_button.pack(side="left", padx=2, pady=4)

        self.risk_label = ctk.CTkLabel(
            util_frame,
            text="Risk: Normal",
            font=ctk.CTkFont(size=11),
            text_color="gray65"
        )
        self.risk_label.pack(side="right", padx=10, pady=4)
        self._update_risk_indicator()
    
    def set_callbacks(
        self,
        start_callback=None,
        pause_callback=None,
        resume_callback=None,
        stop_callback=None,
        manual_resume_callback=None,
        preflight_callback=None,
        resume_snapshot_callback=None,
        show_last_summary_callback=None,
        save_profile_callback=None,
        apply_profile_callback=None,
        refresh_profiles_callback=None
    ):
        """Set callback functions"""
        self.start_callback = start_callback
        self.pause_callback = pause_callback
        self.resume_callback = resume_callback
        self.stop_callback = stop_callback
        self.manual_resume_callback = manual_resume_callback
        self.preflight_callback = preflight_callback
        self.resume_snapshot_callback = resume_snapshot_callback
        self.show_last_summary_callback = show_last_summary_callback
        self.save_profile_callback = save_profile_callback
        self.apply_profile_callback = apply_profile_callback
        self.refresh_profiles_callback = refresh_profiles_callback
    
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

    def _preflight(self):
        """Preflight button callback."""
        if self.preflight_callback:
            self.preflight_callback()

    def _resume_snapshot(self):
        """Resume snapshot button callback."""
        if self.resume_snapshot_callback:
            self.resume_snapshot_callback()

    def _show_last_summary(self):
        """Open last summary button callback."""
        if self.show_last_summary_callback:
            self.show_last_summary_callback()

    def _on_safety_toggle_changed(self, *_):
        """Recompute risk indicator when safety toggles change."""
        self._update_risk_indicator()

    def _update_risk_indicator(self):
        """Update small risk-level indicator from current safety settings."""
        dry_run = bool(self.dry_run_var.get())
        skip_duplicates = bool(self.skip_duplicates_var.get())
        queue_snapshots = bool(self.queue_snapshot_var.get())
        auto_resume = bool(self.auto_resume_snapshot_var.get())

        if dry_run:
            text = "Risk: Safe (Dry Run)"
            color = "#4caf50"
        elif skip_duplicates and queue_snapshots:
            text = "Risk: Guarded"
            color = "#8bc34a"
        elif queue_snapshots or auto_resume:
            text = "Risk: Normal"
            color = "#fbc02d"
        else:
            text = "Risk: Elevated"
            color = "#ff7043"

        self.risk_label.configure(text=text, text_color=color)

    def _save_profile(self):
        """Save profile callback with entered name."""
        name = self.profile_name_var.get().strip()
        if not name:
            messagebox.showwarning("Profile", "Enter a profile name")
            return

        if self.save_profile_callback:
            success = bool(self.save_profile_callback(name))
        else:
            success = bool(getattr(self.config, "save_profile", lambda _n: False)(name))
            if success:
                self.config.save()

        if success:
            self.profile_name_var.set("")
            self.refresh_profiles(select_name=name)
            messagebox.showinfo("Profile", f"Profile saved: {name}")
        else:
            messagebox.showerror("Profile", f"Could not save profile: {name}")

    def _apply_profile(self):
        """Apply selected profile."""
        name = (self.profile_var.get() or "").strip()
        if not name or name == "<none>":
            messagebox.showwarning("Profile", "Select a profile first")
            return

        if self.apply_profile_callback:
            success = bool(self.apply_profile_callback(name))
        else:
            success = bool(getattr(self.config, "apply_profile", lambda _n: False)(name))
            if success:
                self.config.save()

        if success:
            messagebox.showinfo("Profile", f"Profile loaded: {name}")
        else:
            messagebox.showerror("Profile", f"Profile not found: {name}")

    def refresh_profiles(self, select_name: Optional[str] = None):
        """Refresh profile dropdown options."""
        profiles: List[str] = []
        if self.refresh_profiles_callback:
            try:
                profiles = list(self.refresh_profiles_callback() or [])
            except Exception:
                profiles = []
        elif hasattr(self.config, "list_profiles"):
            try:
                profiles = list(self.config.list_profiles())
            except Exception:
                profiles = []

        values = profiles if profiles else ["<none>"]
        current = select_name or (self.profile_var.get().strip() if self.profile_var.get() else "")
        if current not in values:
            current = values[0]

        self.profile_menu.configure(values=values)
        self.profile_var.set(current)
    
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
            self.preflight_button.configure(state="normal")
            self.resume_snapshot_button.configure(state="normal")
            self.save_profile_button.configure(state="normal")
            self.load_profile_button.configure(state="normal")
            self.refresh_profiles_button.configure(state="normal")
        elif state == SequencerState.RUNNING:
            self.start_button.configure(state="disabled")
            self.pause_button.configure(state="normal")
            self.resume_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.manual_resume_button.configure(state="disabled")
            self.preflight_button.configure(state="disabled")
            self.resume_snapshot_button.configure(state="disabled")
            self.save_profile_button.configure(state="disabled")
            self.load_profile_button.configure(state="disabled")
            self.refresh_profiles_button.configure(state="disabled")
        elif state == SequencerState.PAUSED:
            self.start_button.configure(state="disabled")
            self.pause_button.configure(state="disabled")
            self.resume_button.configure(state="normal")
            self.stop_button.configure(state="normal")
            self.manual_resume_button.configure(state="disabled")
            self.preflight_button.configure(state="disabled")
            self.resume_snapshot_button.configure(state="disabled")
            self.save_profile_button.configure(state="disabled")
            self.load_profile_button.configure(state="disabled")
            self.refresh_profiles_button.configure(state="disabled")
        elif state == SequencerState.WAITING_FOR_USER:
            self.start_button.configure(state="disabled")
            self.pause_button.configure(state="disabled")
            self.resume_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.manual_resume_button.configure(state="normal")
            self.preflight_button.configure(state="disabled")
            self.resume_snapshot_button.configure(state="disabled")
            self.save_profile_button.configure(state="disabled")
            self.load_profile_button.configure(state="disabled")
            self.refresh_profiles_button.configure(state="disabled")
        else:  # STOPPING, ERROR
            self.start_button.configure(state="disabled")
            self.pause_button.configure(state="disabled")
            self.resume_button.configure(state="disabled")
            self.stop_button.configure(state="disabled")
            self.manual_resume_button.configure(state="disabled")
            self.preflight_button.configure(state="disabled")
            self.resume_snapshot_button.configure(state="disabled")
            self.save_profile_button.configure(state="disabled")
            self.load_profile_button.configure(state="disabled")
            self.refresh_profiles_button.configure(state="disabled")

    def load_settings(self):
        """Load settings from config"""
        self.window_entry.delete(0, 'end')
        self.window_entry.insert(0, self.config.target_window)
        self.delay_var.set(str(self.config.initial_delay))
        self.dry_run_var.set(bool(getattr(self.config, "dry_run", False)))
        self.skip_duplicates_var.set(bool(getattr(self.config, "skip_duplicates", False)))
        self.prompt_vars_var.set(bool(getattr(self.config, "prompt_variables_enabled", True)))
        self.queue_snapshot_var.set(bool(getattr(self.config, "queue_snapshot_enabled", True)))
        self.auto_resume_snapshot_var.set(bool(getattr(self.config, "auto_resume_queue_from_snapshot", False)))
        self.error_screenshots_var.set(bool(getattr(self.config, "enable_error_screenshots", True)))
        self.paste_retries_var.set(str(getattr(self.config, "paste_max_retries", 3)))
        self.retry_delay_var.set(str(getattr(self.config, "paste_retry_delay", 0.5)))
        self.focus_retries_var.set(str(getattr(self.config, "focus_retries", 3)))
        self.refresh_profiles()
        self._update_risk_indicator()

    def save_settings(self):
        """Save settings to config"""
        self.config.target_window = self.window_entry.get().strip()
        self.config.initial_delay = _clamp_int(self.delay_var.get(), 3, 0, 600)
        self.config.dry_run = bool(self.dry_run_var.get())
        self.config.skip_duplicates = bool(self.skip_duplicates_var.get())
        self.config.prompt_variables_enabled = bool(self.prompt_vars_var.get())
        self.config.queue_snapshot_enabled = bool(self.queue_snapshot_var.get())
        self.config.auto_resume_queue_from_snapshot = bool(self.auto_resume_snapshot_var.get())
        self.config.enable_error_screenshots = bool(self.error_screenshots_var.get())
        self.config.paste_max_retries = _clamp_int(self.paste_retries_var.get(), 3, 1, 10)
        self.config.paste_retry_delay = _clamp_float(self.retry_delay_var.get(), 0.5, 0.05, 10.0)
        self.config.focus_retries = _clamp_int(self.focus_retries_var.get(), 3, 1, 10)

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
        self.config.text_paste_enter_grace = _clamp_int(self.grace_var.get(), 400, 0, 30000)
        self.config.text_generation_wait = _clamp_int(self.wait_var.get(), 45, 0, 7200)
        self.config.text_jitter_percent = _clamp_int(self.jitter_var.get(), 15, 0, 100)
        self.config.text_auto_enter = self.auto_enter_var.get()

class ImageModeTab(ctk.CTkScrollableFrame):
    """Image + text mode configuration tab with scrolling and queue support"""
    
    def __init__(self, parent, config):
        super().__init__(parent, orientation="vertical")
        self.config = config
        self.grid_columnconfigure(0, weight=1)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup image mode UI"""
        # Mode selection
        mode_frame = ctk.CTkFrame(self)
        mode_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        mode_frame.grid_columnconfigure(1, weight=1)
        
        mode_label = ctk.CTkLabel(mode_frame, text="Processing Mode:", font=ctk.CTkFont(size=14, weight="bold"))
        mode_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 10))
        
        self.mode_var = tk.StringVar(value="single")
        single_radio = ctk.CTkRadioButton(mode_frame, text="Single Folder", variable=self.mode_var, 
                                         value="single", command=self._on_mode_change)
        single_radio.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        queue_radio = ctk.CTkRadioButton(mode_frame, text="Queue Mode (Multiple Folders)", 
                                        variable=self.mode_var, value="queue", command=self._on_mode_change)
        queue_radio.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # Single folder mode UI
        self.single_frame = ctk.CTkFrame(self)
        self.single_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.single_frame.grid_columnconfigure(1, weight=1)
        
        # Image folder
        img_folder_label = ctk.CTkLabel(self.single_frame, text="Image Files Folder:")
        img_folder_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        
        self.img_folder_entry = ctk.CTkEntry(self.single_frame, placeholder_text="Select folder containing images")
        self.img_folder_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        
        img_folder_button = ctk.CTkButton(self.single_frame, text="Browse", command=self._select_image_folder, width=80)
        img_folder_button.grid(row=1, column=1, padx=2, pady=2)
        
        # Global prompt file
        prompt_label = ctk.CTkLabel(self.single_frame, text="Global Prompt File (optional):")
        prompt_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=(10, 2))
        
        self.prompt_entry = ctk.CTkEntry(self.single_frame, placeholder_text="Select .txt file with global prompt")
        self.prompt_entry.grid(row=3, column=0, sticky="ew", padx=5, pady=2)
        
        prompt_button = ctk.CTkButton(self.single_frame, text="Browse", command=self._select_prompt_file, width=80)
        prompt_button.grid(row=3, column=1, padx=2, pady=2)
        
        # Queue mode UI
        self.queue_frame = ctk.CTkFrame(self)
        self.queue_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        self.queue_frame.grid_columnconfigure(0, weight=1)
        
        queue_label = ctk.CTkLabel(self.queue_frame, text="Folder Queue:", font=ctk.CTkFont(size=14, weight="bold"))
        queue_label.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 10))
        
        # Queue controls
        queue_controls = ctk.CTkFrame(self.queue_frame)
        queue_controls.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        queue_controls.grid_columnconfigure(4, weight=1)
        
        add_button = ctk.CTkButton(queue_controls, text="Add Folder", command=self._add_to_queue, width=80)
        add_button.grid(row=0, column=0, padx=2, pady=2)
        
        remove_button = ctk.CTkButton(queue_controls, text="Remove", command=self._remove_from_queue, width=80)
        remove_button.grid(row=0, column=1, padx=2, pady=2)
        
        clear_button = ctk.CTkButton(queue_controls, text="Clear All", command=self._clear_queue, width=80)
        clear_button.grid(row=0, column=2, padx=2, pady=2)
        
        up_button = ctk.CTkButton(queue_controls, text="Move Up", command=self._move_up, width=80)
        up_button.grid(row=0, column=3, padx=2, pady=2)
        
        down_button = ctk.CTkButton(queue_controls, text="Move Down", command=self._move_down, width=80)
        down_button.grid(row=0, column=4, padx=2, pady=2)
        
        # Queue list
        self.queue_listbox = tk.Listbox(self.queue_frame, height=8)
        self.queue_listbox.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        # Settings frame (shared by both modes)
        settings_frame = ctk.CTkFrame(self)
        settings_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        settings_frame.grid_columnconfigure(1, weight=1)
        
        settings_label = ctk.CTkLabel(settings_frame, text="Image Mode Settings:", font=ctk.CTkFont(size=14, weight="bold"))
        settings_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 10))
        
        # Settings grid - more responsive layout
        row = 1
        
        # Intra delay - Enhanced UI with slider and seconds display
        intra_frame = ctk.CTkFrame(settings_frame)
        intra_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        intra_frame.grid_columnconfigure(1, weight=1)
        
        # Label with tooltip-like info
        intra_label = ctk.CTkLabel(intra_frame, text="⏱️ Image Upload Delay (sec):", font=ctk.CTkFont(size=11, weight="bold"))
        intra_label.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 2))
        
        # Info text
        info_label = ctk.CTkLabel(intra_frame, text="Time to wait after pasting image for upload to complete", 
                                 font=ctk.CTkFont(size=9), text_color="gray70")
        info_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=(0, 5))
        
        # Slider and entry controls
        controls_frame = ctk.CTkFrame(intra_frame)
        controls_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5))
        controls_frame.grid_columnconfigure(0, weight=1)
        
        # Slider (0-10 seconds)
        self.intra_slider = ctk.CTkSlider(controls_frame, from_=0, to=10, number_of_steps=20, 
                                         command=self._on_intra_slider_change)
        self.intra_slider.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        
        # Entry field for precise control
        self.intra_var = tk.StringVar(value="3.0")
        self.intra_entry = ctk.CTkEntry(controls_frame, textvariable=self.intra_var, width=80, 
                                       placeholder_text="sec")
        self.intra_entry.grid(row=0, column=1, padx=(0, 5), pady=2)
        self.intra_entry.bind("<FocusOut>", self._on_intra_entry_change)
        self.intra_entry.bind("<Return>", self._on_intra_entry_change)
        
        # Current value display
        self.intra_display = ctk.CTkLabel(controls_frame, text="3.0 sec (3000 ms)", 
                                         font=ctk.CTkFont(size=9), text_color="gray60")
        self.intra_display.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=(0, 5))
        
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
        
        # Initialize UI state
        self._on_mode_change()
    
    def _on_mode_change(self):
        """Handle mode change between single and queue"""
        is_single = self.mode_var.get() == "single"
        
        if is_single:
            self.single_frame.grid()
            self.queue_frame.grid_remove()
        else:
            self.single_frame.grid_remove()
            self.queue_frame.grid()
    
    def _add_to_queue(self):
        """Add folder and prompt pair to queue"""
        # Select image folder
        folder = filedialog.askdirectory(title="Select Image Folder for Queue")
        if not folder:
            return
        
        # Select prompt file (optional)
        prompt_file = filedialog.askopenfilename(
            title="Select Prompt File (Optional)",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        # Create queue item
        folder_name = os.path.basename(folder.rstrip('/\\'))
        prompt_name = os.path.basename(prompt_file) if prompt_file else "No prompt"
        
        queue_item = {
            "id": str(uuid.uuid4()),
            "image_folder": folder,
            "prompt_file": prompt_file or "",
            "name": folder_name,
            "notes": "",
            "tags": []
        }
        
        # Add to config queue
        if not hasattr(self.config, 'image_queue_items') or self.config.image_queue_items is None:
            self.config.image_queue_items = []
        
        self.config.image_queue_items.append(queue_item)
        # log enqueue event
        try:
            logger.info(f"Enqueued queue item: {folder_name} id={queue_item['id']}")
        except Exception:
            pass
        
        # Update listbox
        display_text = f"{folder_name} → {prompt_name}"
        self.queue_listbox.insert(tk.END, display_text)
        
        # If a live queue object exists (sequencer running), push the item there too
        try:
            qobj = getattr(self.config, 'image_queue_obj', None)
            if qobj is not None:
                # queue.Queue supports .put()
                qobj.put(queue_item)
        except Exception:
            pass
    
    def _remove_from_queue(self):
        """Remove selected item from queue"""
        selection = self.queue_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        self.queue_listbox.delete(index)
        
        if hasattr(self.config, 'image_queue_items') and self.config.image_queue_items:
            removed = self.config.image_queue_items.pop(index)
            try:
                logger.info(f"Removed queue item via GUI: {removed.get('name')} id={removed.get('id')}")
            except Exception:
                pass
            # Signal cancellation for currently-processing item (cooperative)
            try:
                cancel_set = getattr(self.config, 'image_queue_cancel_requests', None)
                if cancel_set is None:
                    # initialize if missing
                    self.config.image_queue_cancel_requests = set()
                    cancel_set = self.config.image_queue_cancel_requests
                cancel_set.add(removed.get('id'))
                skip_set = getattr(self.config, 'image_queue_skip_requests', None)
                if skip_set is None:
                    self.config.image_queue_skip_requests = set()
                    skip_set = self.config.image_queue_skip_requests
                skip_set.add(removed.get('id'))
                logger.info(f"Requested cancel for queue item id={removed.get('id')}")
            except Exception:
                pass
    
    def _clear_queue(self):
        """Clear all items from queue"""
        self.queue_listbox.delete(0, tk.END)
        if hasattr(self.config, 'image_queue_items'):
            # Request cancellation for all outstanding items
            try:
                cancel_set = getattr(self.config, 'image_queue_cancel_requests', None)
                if cancel_set is None:
                    self.config.image_queue_cancel_requests = set()
                    cancel_set = self.config.image_queue_cancel_requests
                skip_set = getattr(self.config, 'image_queue_skip_requests', None)
                if skip_set is None:
                    self.config.image_queue_skip_requests = set()
                    skip_set = self.config.image_queue_skip_requests
                for itm in self.config.image_queue_items:
                    cancel_set.add(itm.get('id'))
                    skip_set.add(itm.get('id'))
                logger.info(f"Requested cancel for all queue items: count={len(self.config.image_queue_items)}")
            except Exception:
                pass
            self.config.image_queue_items = []
        # Clear live queue if present
        try:
            if hasattr(self.config, 'image_queue_obj') and self.config.image_queue_obj is not None:
                import queue as _pyqueue
                self.config.image_queue_obj = _pyqueue.Queue()
                logger.info("Cleared live queue via GUI clear action")
        except Exception:
            pass
    
    def _move_up(self):
        """Move selected item up in queue"""
        selection = self.queue_listbox.curselection()
        if not selection or selection[0] == 0:
            return
        
        index = selection[0]
        
        # Move in listbox
        item = self.queue_listbox.get(index)
        self.queue_listbox.delete(index)
        self.queue_listbox.insert(index - 1, item)
        self.queue_listbox.selection_set(index - 1)
        
        # Move in config
        if hasattr(self.config, 'image_queue_items') and self.config.image_queue_items:
            self.config.image_queue_items[index], self.config.image_queue_items[index - 1] = \
                self.config.image_queue_items[index - 1], self.config.image_queue_items[index]
    
    def _move_down(self):
        """Move selected item down in queue"""
        selection = self.queue_listbox.curselection()
        if not selection or selection[0] >= self.queue_listbox.size() - 1:
            return
        
        index = selection[0]
        
        # Move in listbox
        item = self.queue_listbox.get(index)
        self.queue_listbox.delete(index)
        self.queue_listbox.insert(index + 1, item)
        self.queue_listbox.selection_set(index + 1)
        
        # Move in config
        if hasattr(self.config, 'image_queue_items') and self.config.image_queue_items:
            self.config.image_queue_items[index], self.config.image_queue_items[index + 1] = \
                self.config.image_queue_items[index + 1], self.config.image_queue_items[index]
    
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
        # Single folder mode settings
        self.img_folder_entry.delete(0, 'end')
        self.img_folder_entry.insert(0, self.config.image_input_folder)
        self.prompt_entry.delete(0, 'end')
        self.prompt_entry.insert(0, self.config.global_prompt_file)
        
        # Queue mode settings
        self.mode_var.set("queue" if getattr(self.config, 'image_queue_mode', False) else "single")
        self._on_mode_change()
        
        # Load queue items
        if hasattr(self.config, 'image_queue_items') and self.config.image_queue_items:
            self.queue_listbox.delete(0, tk.END)
            for item in self.config.image_queue_items:
                folder_name = item.get('name', 'Unknown')
                prompt_name = os.path.basename(item.get('prompt_file', '')) or "No prompt"
                display_text = f"{folder_name} → {prompt_name}"
                self.queue_listbox.insert(tk.END, display_text)
        
        # Other settings
        intra_seconds = self.config.image_intra_delay / 1000.0
        self.intra_var.set(f"{intra_seconds}")
        self.intra_slider.set(intra_seconds)
        self._update_intra_display(intra_seconds)
        self.grace_var.set(str(self.config.image_paste_enter_grace))
        self.wait_var.set(str(self.config.image_generation_wait))
        self.jitter_var.set(str(self.config.image_jitter_percent))
        self.auto_enter_var.set(self.config.image_auto_enter)
        self.repeat_prompt_var.set(self.config.image_repeat_prompt)
    
    def save_settings(self):
        """Save settings to config"""
        # Mode selection
        self.config.image_queue_mode = (self.mode_var.get() == "queue")
        
        # Single folder mode settings
        self.config.image_input_folder = self.img_folder_entry.get().strip()
        self.config.global_prompt_file = self.prompt_entry.get().strip()
        
        # Other settings
        intra_seconds = _clamp_float(self.intra_var.get(), 3.0, 0.0, 30.0)
        self.config.image_intra_delay = int(intra_seconds * 1000)
        self.config.image_paste_enter_grace = _clamp_int(self.grace_var.get(), 400, 0, 30000)
        self.config.image_generation_wait = _clamp_int(self.wait_var.get(), 60, 0, 7200)
        self.config.image_jitter_percent = _clamp_int(self.jitter_var.get(), 15, 0, 100)
        self.config.image_auto_enter = self.auto_enter_var.get()
        self.config.image_repeat_prompt = self.repeat_prompt_var.get()
    
    def _on_intra_slider_change(self, value):
        """Handle intra delay slider change"""
        # Convert slider value (0-10) to seconds and update display
        seconds = round(value, 1)
        self.intra_var.set(f"{seconds}")
        self._update_intra_display(seconds)
    
    def _on_intra_entry_change(self, event=None):
        """Handle intra delay entry field change"""
        try:
            seconds = float(self.intra_var.get())
            # Clamp to reasonable range
            seconds = max(0, min(10, seconds))
            self.intra_var.set(f"{seconds}")
            # Update slider position
            self.intra_slider.set(seconds)
            self._update_intra_display(seconds)
        except ValueError:
            # Reset to current slider value
            current_value = self.intra_slider.get()
            self.intra_var.set(f"{current_value}")
            self._update_intra_display(current_value)
    
    def _update_intra_display(self, seconds):
        """Update the intra delay display text"""
        ms = int(seconds * 1000)
        self.intra_display.configure(text=f"{seconds} sec ({ms} ms)")

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
