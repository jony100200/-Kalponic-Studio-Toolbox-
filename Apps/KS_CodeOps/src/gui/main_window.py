import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox
import os
from datetime import datetime

import customtkinter as ctk


class VSCodePromptSenderGUI:
    COLORS = {
        "bg": "#171A1F",
        "surface_1": "#1F242C",
        "surface_2": "#272E38",
        "border": "#343D4A",
        "text_primary": "#E6EBF2",
        "text_secondary": "#A8B2C3",
        "primary": "#6FA8FF",
        "primary_hover": "#86B6FF",
        "success": "#67B587",
        "warning": "#C6A15A",
        "error": "#C06B6B",
        "neutral_status": "#6E7B8F",
    }

    SPACING_8 = 8
    SPACING_12 = 12
    SPACING_16 = 16
    SPACING_24 = 24

    def __init__(self, config, sequencer):
        self.config = config
        self.sequencer = sequencer
        self.sequencer.set_log_callback(self._log)
        self._log_index = 0
        self._job_state = "Idle"
        os.makedirs("logs", exist_ok=True)
        self._activity_log_path = os.path.join("logs", f"ks_codeops_ui_activity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("KS CodeOps")
        self.root.geometry("1080x780")
        self.root.minsize(980, 680)
        self.root.configure(fg_color=self.COLORS["bg"])
        self.font_family = self._resolve_font_family()
        self.font_body = (self.font_family, 12)
        self.font_small = (self.font_family, 11)
        self.font_small_bold = (self.font_family, 11, "bold")

        self._build_ui()
        self._load_config_to_ui()
        self._refresh_status_strip()

    def _resolve_font_family(self) -> str:
        preferred = ["Inter", "Segoe UI", "Roboto", "Arial", "Helvetica"]
        try:
            available = {name.lower() for name in tkfont.families(self.root)}
        except Exception:
            available = set()
        for name in preferred:
            if name.lower() in available:
                return name
        return "Segoe UI"

    def _btn_style(self, kind: str):
        if kind == "primary":
            return {
                "fg_color": self.COLORS["primary"],
                "hover_color": self.COLORS["primary_hover"],
                "text_color": "#102036",
                "border_width": 0,
            }
        return {
            "fg_color": self.COLORS["surface_2"],
            "hover_color": self.COLORS["border"],
            "text_color": self.COLORS["text_primary"],
            "border_color": self.COLORS["border"],
            "border_width": 1,
        }

    def _make_button(self, parent, text: str, command, kind: str = "neutral", width: int = 132):
        style = self._btn_style(kind)
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=34,
            corner_radius=10,
            font=self.font_body,
            **style,
        )

    def _make_chip(self, parent, label: str):
        chip = ctk.CTkLabel(
            parent,
            text=label,
            fg_color=self.COLORS["surface_2"],
            text_color=self.COLORS["text_primary"],
            corner_radius=10,
            padx=10,
            pady=4,
            font=self.font_small_bold,
        )
        return chip

    def _build_ui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(
            self.root,
            fg_color=self.COLORS["surface_1"],
            corner_radius=12,
            border_width=1,
            border_color=self.COLORS["border"],
        )
        top.grid(row=0, column=0, sticky="ew", padx=self.SPACING_16, pady=self.SPACING_16)
        top.grid_columnconfigure(1, weight=1)
        top.grid_columnconfigure(3, weight=1)

        label_opts = {"text_color": self.COLORS["text_secondary"], "font": self.font_small}
        entry_opts = {
            "fg_color": self.COLORS["surface_2"],
            "border_color": self.COLORS["border"],
            "text_color": self.COLORS["text_primary"],
            "corner_radius": 10,
            "height": 34,
        }

        ctk.CTkLabel(top, text="Window Title", **label_opts).grid(row=0, column=0, padx=self.SPACING_12, pady=self.SPACING_8, sticky="w")
        self.window_title_var = tk.StringVar()
        ctk.CTkEntry(top, textvariable=self.window_title_var, **entry_opts).grid(
            row=0, column=1, padx=self.SPACING_8, pady=self.SPACING_8, sticky="ew"
        )

        ctk.CTkLabel(top, text="Focus Profile", **label_opts).grid(row=0, column=2, padx=self.SPACING_12, pady=self.SPACING_8, sticky="w")
        self.profile_var = tk.StringVar(value="chat_panel")
        ctk.CTkOptionMenu(
            top,
            variable=self.profile_var,
            values=["chat_panel", "editor"],
            fg_color=self.COLORS["surface_2"],
            button_color=self.COLORS["surface_2"],
            button_hover_color=self.COLORS["border"],
            dropdown_fg_color=self.COLORS["surface_2"],
            dropdown_hover_color=self.COLORS["border"],
            text_color=self.COLORS["text_primary"],
            corner_radius=10,
            height=34,
        ).grid(
            row=0, column=3, padx=self.SPACING_8, pady=self.SPACING_8, sticky="ew"
        )

        ctk.CTkLabel(top, text="Active Target", **label_opts).grid(row=1, column=0, padx=self.SPACING_12, pady=self.SPACING_8, sticky="w")
        self.target_var = tk.StringVar(value="copilot")
        self.target_menu = ctk.CTkOptionMenu(
            top,
            variable=self.target_var,
            values=["copilot"],
            fg_color=self.COLORS["surface_2"],
            button_color=self.COLORS["surface_2"],
            button_hover_color=self.COLORS["border"],
            dropdown_fg_color=self.COLORS["surface_2"],
            dropdown_hover_color=self.COLORS["border"],
            text_color=self.COLORS["text_primary"],
            corner_radius=10,
            height=34,
        )
        self.target_menu.grid(row=1, column=1, padx=self.SPACING_8, pady=self.SPACING_8, sticky="ew")

        self.auto_enter_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            top,
            text="Auto Enter",
            variable=self.auto_enter_var,
            checkbox_height=18,
            checkbox_width=18,
            corner_radius=5,
            border_width=1,
            border_color=self.COLORS["border"],
            fg_color=self.COLORS["primary"],
            hover_color=self.COLORS["primary_hover"],
            text_color=self.COLORS["text_secondary"],
        ).grid(row=1, column=3, padx=self.SPACING_8, pady=self.SPACING_8, sticky="w")

        status_strip = ctk.CTkFrame(
            top,
            fg_color=self.COLORS["surface_2"],
            corner_radius=10,
            border_width=1,
            border_color=self.COLORS["border"],
        )
        status_strip.grid(row=2, column=0, columnspan=4, sticky="ew", padx=self.SPACING_12, pady=(self.SPACING_8, self.SPACING_12))
        status_strip.grid_columnconfigure((0, 1, 2), weight=1)

        target_wrap = ctk.CTkFrame(status_strip, fg_color="transparent")
        target_wrap.grid(row=0, column=0, padx=self.SPACING_12, pady=self.SPACING_8, sticky="w")
        ctk.CTkLabel(target_wrap, text="Target", **label_opts).pack(side="left", padx=(0, 6))
        self.target_chip = self._make_chip(target_wrap, "--")
        self.target_chip.pack(side="left")

        backend_wrap = ctk.CTkFrame(status_strip, fg_color="transparent")
        backend_wrap.grid(row=0, column=1, padx=self.SPACING_12, pady=self.SPACING_8, sticky="w")
        ctk.CTkLabel(backend_wrap, text="Backend", **label_opts).pack(side="left", padx=(0, 6))
        self.backend_chip = self._make_chip(backend_wrap, "--")
        self.backend_chip.pack(side="left")

        state_wrap = ctk.CTkFrame(status_strip, fg_color="transparent")
        state_wrap.grid(row=0, column=2, padx=self.SPACING_12, pady=self.SPACING_8, sticky="w")
        ctk.CTkLabel(state_wrap, text="Job State", **label_opts).pack(side="left", padx=(0, 6))
        self.state_chip = self._make_chip(state_wrap, "Idle")
        self.state_chip.pack(side="left")

        actions = ctk.CTkFrame(
            self.root,
            fg_color=self.COLORS["surface_1"],
            corner_radius=12,
            border_width=1,
            border_color=self.COLORS["border"],
        )
        actions.grid(row=1, column=0, sticky="nsew", padx=self.SPACING_16, pady=(0, self.SPACING_16))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_rowconfigure(2, weight=1)

        button_row = ctk.CTkFrame(actions, fg_color="transparent")
        button_row.grid(row=0, column=0, sticky="ew", padx=self.SPACING_12, pady=(self.SPACING_12, self.SPACING_8))
        button_row.grid_columnconfigure(0, weight=1)

        primary_group = ctk.CTkFrame(button_row, fg_color="transparent")
        primary_group.grid(row=0, column=0, sticky="w")
        self.save_btn = self._make_button(primary_group, "Save Settings", self._save_settings, kind="neutral", width=130)
        self.save_btn.pack(side="left", padx=(0, self.SPACING_8))
        self.run_btn = self._make_button(primary_group, "Run Sequence", self._run_in_thread(self._run_sequence), kind="primary", width=138)
        self.run_btn.pack(side="left")

        secondary_group = ctk.CTkFrame(button_row, fg_color="transparent")
        secondary_group.grid(row=0, column=1, sticky="e")
        self.test_focus_btn = self._make_button(secondary_group, "Test Focus", self._run_in_thread(self._test_focus), kind="neutral", width=120)
        self.test_focus_btn.pack(side="left", padx=(0, self.SPACING_8))
        self.test_target_btn = self._make_button(secondary_group, "Test Target", self._run_in_thread(self._test_target), kind="neutral", width=120)
        self.test_target_btn.pack(side="left")

        calibration_section = ctk.CTkFrame(
            actions,
            fg_color=self.COLORS["surface_2"],
            corner_radius=12,
            border_width=1,
            border_color=self.COLORS["border"],
        )
        calibration_section.grid(row=1, column=0, sticky="ew", padx=self.SPACING_12, pady=(0, self.SPACING_8))
        ctk.CTkLabel(
            calibration_section,
            text="Calibration",
            text_color=self.COLORS["text_secondary"],
            font=self.font_small_bold,
        ).pack(side="left", padx=self.SPACING_12, pady=self.SPACING_8)

        self.record_click_btn = self._make_button(calibration_section, "Record Click", self._run_in_thread(self._record_click), kind="neutral", width=130)
        self.record_click_btn.pack(side="left", padx=(0, self.SPACING_8), pady=self.SPACING_8)
        self.record_target_click_btn = self._make_button(
            calibration_section,
            "Record Target Click",
            self._run_in_thread(self._record_target_click),
            kind="neutral",
            width=160,
        )
        self.record_target_click_btn.pack(side="left", pady=self.SPACING_8)

        tabs = ctk.CTkTabview(
            actions,
            fg_color=self.COLORS["surface_1"],
            segmented_button_fg_color=self.COLORS["surface_2"],
            segmented_button_selected_color=self.COLORS["primary"],
            segmented_button_selected_hover_color=self.COLORS["primary_hover"],
            segmented_button_unselected_color=self.COLORS["surface_2"],
            segmented_button_unselected_hover_color=self.COLORS["border"],
            text_color=self.COLORS["text_primary"],
            corner_radius=12,
            border_width=0,
        )
        tabs.grid(row=2, column=0, sticky="nsew", padx=self.SPACING_12, pady=(0, self.SPACING_12))
        tabs.add("Text")
        tabs.add("Image")
        tabs.add("Sequence")
        tabs.add("Logs")
        if hasattr(tabs, "_segmented_button"):
            try:
                tabs._segmented_button.configure(height=30, corner_radius=10)
                tabs._segmented_button.grid(sticky="w")
            except Exception:
                pass

        text_tab = tabs.tab("Text")
        text_tab.grid_columnconfigure(0, weight=1)
        text_tab.grid_rowconfigure(0, weight=1)
        self.text_box = ctk.CTkTextbox(
            text_tab,
            height=220,
            fg_color=self.COLORS["surface_2"],
            border_color=self.COLORS["border"],
            border_width=1,
            text_color=self.COLORS["text_primary"],
            corner_radius=12,
        )
        self.text_box.grid(row=0, column=0, sticky="nsew", padx=self.SPACING_8, pady=(self.SPACING_8, self.SPACING_8))
        text_action_bar = ctk.CTkFrame(
            text_tab,
            fg_color=self.COLORS["surface_1"],
            corner_radius=10,
            border_width=1,
            border_color=self.COLORS["border"],
        )
        text_action_bar.grid(row=1, column=0, sticky="ew", padx=self.SPACING_8, pady=(0, self.SPACING_8))
        text_action_bar.grid_columnconfigure(0, weight=1)
        self.send_text_btn = self._make_button(
            text_action_bar,
            "Send Text",
            self._run_in_thread(self._send_text),
            kind="primary",
            width=140,
        )
        self.send_text_btn.grid(row=0, column=1, padx=self.SPACING_8, pady=self.SPACING_8, sticky="e")

        image_tab = tabs.tab("Image")
        image_tab.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(image_tab, text="Image Path", **label_opts).grid(row=0, column=0, padx=self.SPACING_8, pady=self.SPACING_8, sticky="w")
        self.image_path_var = tk.StringVar()
        ctk.CTkEntry(image_tab, textvariable=self.image_path_var, **entry_opts).grid(row=0, column=1, padx=self.SPACING_8, pady=self.SPACING_8, sticky="ew")
        self.browse_image_btn = self._make_button(image_tab, "Browse", self._pick_image, kind="neutral", width=100)
        self.browse_image_btn.grid(row=0, column=2, padx=self.SPACING_8, pady=self.SPACING_8)
        self.send_image_btn = self._make_button(image_tab, "Send Image", self._run_in_thread(self._send_image), kind="primary", width=120)
        self.send_image_btn.grid(row=1, column=2, padx=self.SPACING_8, pady=self.SPACING_8)

        seq_tab = tabs.tab("Sequence")
        seq_tab.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(seq_tab, text="Sequence File", **label_opts).grid(row=0, column=0, padx=self.SPACING_8, pady=self.SPACING_8, sticky="w")
        self.sequence_path_var = tk.StringVar()
        ctk.CTkEntry(seq_tab, textvariable=self.sequence_path_var, **entry_opts).grid(row=0, column=1, padx=self.SPACING_8, pady=self.SPACING_8, sticky="ew")
        self.browse_seq_btn = self._make_button(seq_tab, "Browse", self._pick_sequence, kind="neutral", width=100)
        self.browse_seq_btn.grid(row=0, column=2, padx=self.SPACING_8, pady=self.SPACING_8)
        self.run_seq_btn = self._make_button(seq_tab, "Run Sequence", self._run_in_thread(self._run_sequence), kind="primary", width=130)
        self.run_seq_btn.grid(row=1, column=2, padx=self.SPACING_8, pady=self.SPACING_8)

        logs_tab = tabs.tab("Logs")
        logs_tab.grid_columnconfigure(0, weight=1)
        logs_tab.grid_rowconfigure(0, weight=1)
        self.log_box = ctk.CTkTextbox(
            logs_tab,
            fg_color=self.COLORS["surface_2"],
            border_color=self.COLORS["border"],
            border_width=1,
            text_color=self.COLORS["text_primary"],
            corner_radius=12,
        )
        self.log_box.grid(row=0, column=0, sticky="nsew", padx=self.SPACING_8, pady=self.SPACING_8)

        self._action_buttons = [
            self.save_btn,
            self.run_btn,
            self.test_focus_btn,
            self.test_target_btn,
            self.record_click_btn,
            self.record_target_click_btn,
            self.send_text_btn,
            self.browse_image_btn,
            self.send_image_btn,
            self.browse_seq_btn,
            self.run_seq_btn,
        ]

    def _refresh_status_strip(self):
        target = self.target_var.get().strip() if hasattr(self, "target_var") else self.config.active_target
        backend = str(getattr(self.config, "automation_backend", "pyautogui")).upper()
        self.target_chip.configure(text=target or "--")
        self.backend_chip.configure(text=backend)

        state_text = self._job_state
        state_color = self.COLORS["neutral_status"]
        low = state_text.lower()
        if low in {"running", "sending", "active"}:
            state_color = self.COLORS["warning"]
        elif low in {"ready", "completed", "ok", "success"}:
            state_color = self.COLORS["success"]
        elif low in {"failed", "error"}:
            state_color = self.COLORS["error"]
        self.state_chip.configure(text=state_text, fg_color=state_color, text_color="#0F1218")

    def _set_job_state(self, state: str):
        self._job_state = state
        self._refresh_status_strip()

    def _set_controls_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for btn in getattr(self, "_action_buttons", []):
            try:
                btn.configure(state=state)
            except Exception:
                pass

    def _run_in_thread(self, fn):
        def runner():
            self.root.after(0, lambda: self._set_controls_enabled(False))
            self.root.after(0, lambda: self._set_job_state("Running"))
            try:
                fn()
                self.root.after(0, lambda: self._set_job_state("Ready"))
            except Exception as exc:
                self.root.after(0, lambda: self._set_job_state("Error"))
                self.root.after(0, lambda: self._log(f"Error: {exc}"))
            finally:
                self.root.after(0, lambda: self._set_controls_enabled(True))
        return lambda: threading.Thread(target=runner, daemon=True).start()

    def _pick_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.webp")])
        if path:
            self.image_path_var.set(path)

    def _pick_sequence(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            self.sequence_path_var.set(path)

    def _load_config_to_ui(self):
        self.window_title_var.set(self.config.window_title)
        self.profile_var.set(self.config.focus_profile)
        self.auto_enter_var.set(self.config.auto_enter)
        names = list(self.config.targets.keys()) if isinstance(self.config.targets, dict) and self.config.targets else ["copilot"]
        self.target_menu.configure(values=names)
        active = self.config.active_target if self.config.active_target in names else names[0]
        self.target_var.set(active)
        self._refresh_status_strip()

    def _save_settings(self):
        self.config.window_title = self.window_title_var.get().strip() or "Visual Studio Code"
        self.config.focus_profile = self.profile_var.get()
        self.config.auto_enter = self.auto_enter_var.get()
        self.config.active_target = self.target_var.get().strip() or self.config.active_target
        self.config.save()
        self._log(f"Settings saved (active target: {self.config.active_target})")
        self._refresh_status_strip()

    def _test_focus(self):
        self._save_settings()
        self.sequencer.test_focus()

    def _record_click(self):
        self._save_settings()
        messagebox.showinfo("Record Click", "After this dialog, place your mouse on VS Code input area. Recording in 4 seconds.")
        self.sequencer.record_click(seconds=4)

    def _test_target(self):
        self._save_settings()
        target = self.target_var.get().strip()
        self.sequencer.activate_target(target)

    def _record_target_click(self):
        self._save_settings()
        target = self.target_var.get().strip()
        messagebox.showinfo("Record Target Click", f"After this dialog, place your mouse on {target} input area. Recording in 4 seconds.")
        self.sequencer.record_target_click(target_name=target, seconds=4)

    def _send_text(self):
        self._save_settings()
        text = self.text_box.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("No Text", "Enter text to send.")
            return
        self.sequencer.send_text(text, press_enter=self.config.auto_enter)

    def _send_image(self):
        self._save_settings()
        image_path = self.image_path_var.get().strip()
        if not image_path:
            messagebox.showwarning("No Image", "Pick an image path first.")
            return
        self.sequencer.send_image(image_path, press_enter=self.config.auto_enter)

    def _run_sequence(self):
        self._save_settings()
        sequence_file = self.sequence_path_var.get().strip()
        if not sequence_file:
            messagebox.showwarning("No Sequence", "Pick a sequence JSON file first.")
            return
        self.sequencer.run_sequence(sequence_file)

    def _log(self, message: str):
        self._log_index += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{self._log_index:04d}] {timestamp} | {message}"
        self.log_box.insert("end", f"{line}\n")
        self.log_box.see("end")
        try:
            with open(self._activity_log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    def run(self):
        self.root.mainloop()
