import json
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox
import os
from datetime import datetime

import customtkinter as ctk
from src.core.job_runner import JobRunner


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
        self._advanced_visible = False
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
            height=32,
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

    def _badge(self, parent, text: str, fg: str, text_color: str = "#0F1218"):
        return ctk.CTkLabel(
            parent,
            text=text,
            fg_color=fg,
            text_color=text_color,
            corner_radius=9,
            padx=8,
            pady=2,
            font=self.font_small,
        )

    def _build_timeline_bar(self):
        self.timeline_frame = ctk.CTkFrame(
            self.root,
            fg_color=self.COLORS["surface_1"],
            corner_radius=10,
            border_width=1,
            border_color=self.COLORS["border"],
        )
        self.timeline_frame.grid(row=0, column=0, sticky="ew", padx=self.SPACING_16, pady=(self.SPACING_8, 0))

        self._timeline_stages = ["Plan", "Dispatch", "Execute", "Capture", "Validate", "Done"]
        self._timeline_stage_widgets = {}
        self._timeline_active = None

        stage_row = ctk.CTkFrame(self.timeline_frame, fg_color="transparent")
        stage_row.pack(fill="x", padx=self.SPACING_12, pady=self.SPACING_8)

        for index, stage in enumerate(self._timeline_stages):
            chip = ctk.CTkLabel(
                stage_row,
                text=stage,
                fg_color=self.COLORS["surface_2"],
                text_color=self.COLORS["text_secondary"],
                corner_radius=10,
                padx=10,
                pady=4,
                font=self.font_small_bold,
            )
            chip.pack(side="left")
            self._timeline_stage_widgets[stage] = chip
            if index < len(self._timeline_stages) - 1:
                sep = ctk.CTkLabel(
                    stage_row,
                    text=">",
                    text_color=self.COLORS["text_secondary"],
                    font=self.font_small_bold,
                )
                sep.pack(side="left", padx=(6, 6))

        self._set_timeline_stage(None)

    def _set_timeline_stage(self, stage: str, failed: bool = False):
        def apply():
            active = stage if stage in self._timeline_stages else None
            active_index = self._timeline_stages.index(active) if active else -1
            self._timeline_active = active
            for idx, name in enumerate(self._timeline_stages):
                widget = self._timeline_stage_widgets.get(name)
                if not widget:
                    continue
                if failed and name == active:
                    fg = self.COLORS["error"]
                    tc = "#111111"
                elif active and idx < active_index:
                    fg = self.COLORS["success"]
                    tc = "#111111"
                elif active and idx == active_index:
                    fg = self.COLORS["warning"]
                    tc = "#111111"
                else:
                    fg = self.COLORS["surface_2"]
                    tc = self.COLORS["text_secondary"]
                widget.configure(fg_color=fg, text_color=tc)

        if threading.current_thread() is threading.main_thread():
            apply()
        else:
            self.root.after(0, apply)

    def _build_ui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self._build_timeline_bar()

        self.page = ctk.CTkScrollableFrame(
            self.root,
            fg_color=self.COLORS["bg"],
            corner_radius=0,
        )
        self.page.grid(row=1, column=0, sticky="nsew")
        self.page.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(
            self.page,
            fg_color=self.COLORS["surface_1"],
            corner_radius=12,
            border_width=1,
            border_color=self.COLORS["border"],
        )
        top.grid(row=0, column=0, sticky="ew", padx=self.SPACING_16, pady=(self.SPACING_16, self.SPACING_8))
        top.grid_columnconfigure(1, weight=1)
        top.grid_columnconfigure(3, weight=1)

        label_opts = {"text_color": self.COLORS["text_secondary"], "font": self.font_small}
        entry_opts = {
            "fg_color": self.COLORS["surface_2"],
            "border_color": self.COLORS["border"],
            "text_color": self.COLORS["text_primary"],
            "corner_radius": 10,
            "height": 32,
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

        workers_label = ctk.CTkLabel(top, text="Workers", **label_opts)
        workers_label.grid(row=2, column=0, padx=self.SPACING_12, pady=self.SPACING_8, sticky="nw")
        self.workers_frame = ctk.CTkFrame(top, fg_color="transparent")
        self.workers_frame.grid(row=2, column=1, columnspan=3, padx=self.SPACING_8, pady=self.SPACING_8, sticky="ew")
        self.workers_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.target_check_vars = {}
        self.target_open_test_vars = {}
        self._worker_enabled_badges = {}
        self._worker_health_badges = {}
        self._worker_capability_badges = {}
        self._build_target_checkboxes([])

        status_strip = ctk.CTkFrame(
            top,
            fg_color=self.COLORS["surface_2"],
            corner_radius=10,
            border_width=1,
            border_color=self.COLORS["border"],
        )
        status_strip.grid(row=3, column=0, columnspan=4, sticky="ew", padx=self.SPACING_12, pady=(self.SPACING_8, self.SPACING_12))
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
            self.page,
            fg_color=self.COLORS["surface_1"],
            corner_radius=12,
            border_width=1,
            border_color=self.COLORS["border"],
        )
        actions.grid(row=1, column=0, sticky="ew", padx=self.SPACING_16, pady=(0, self.SPACING_16))
        actions.grid_columnconfigure(0, weight=1)

        button_row = ctk.CTkFrame(actions, fg_color="transparent")
        button_row.grid(row=0, column=0, sticky="ew", padx=self.SPACING_12, pady=(self.SPACING_12, self.SPACING_8))
        button_row.grid_columnconfigure(0, weight=1)

        primary_group = ctk.CTkFrame(button_row, fg_color="transparent")
        primary_group.grid(row=0, column=0, sticky="w")
        self.save_btn = self._make_button(primary_group, "Save", self._save_settings, kind="neutral", width=94)
        self.save_btn.pack(side="left", padx=(0, self.SPACING_8))
        self.run_job_btn = self._make_button(primary_group, "Run Job", self._run_in_thread(self._run_job), kind="primary", width=114)
        self.run_job_btn.pack(side="left", padx=(0, self.SPACING_8))
        self.health_btn = self._make_button(primary_group, "Health Check", self._run_in_thread(self._health_check), kind="neutral", width=130)
        self.health_btn.pack(side="left", padx=(0, self.SPACING_8))
        self.run_btn = self._make_button(primary_group, "Run Sequence", self._run_in_thread(self._run_sequence), kind="neutral", width=128)
        self.run_btn.pack(side="left")

        secondary_group = ctk.CTkFrame(button_row, fg_color="transparent")
        secondary_group.grid(row=0, column=1, sticky="e")
        self.test_focus_btn = self._make_button(secondary_group, "Test Focus", self._run_in_thread(self._test_focus), kind="neutral", width=120)
        self.test_focus_btn.pack(side="left", padx=(0, self.SPACING_8))
        self.test_target_btn = self._make_button(secondary_group, "Test Target", self._run_in_thread(self._test_target), kind="neutral", width=120)
        self.test_target_btn.pack(side="left", padx=(0, self.SPACING_8))
        self.advanced_btn = self._make_button(secondary_group, "Show Advanced", self._toggle_advanced, kind="neutral", width=142)
        self.advanced_btn.pack(side="left")

        job_section = ctk.CTkFrame(
            actions,
            fg_color=self.COLORS["surface_2"],
            corner_radius=10,
            border_width=1,
            border_color=self.COLORS["border"],
        )
        job_section.grid(row=1, column=0, sticky="ew", padx=self.SPACING_12, pady=(0, self.SPACING_8))
        job_section.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            job_section,
            text="Job Folder",
            text_color=self.COLORS["text_secondary"],
            font=self.font_small,
        ).grid(row=0, column=0, padx=self.SPACING_12, pady=self.SPACING_8, sticky="w")
        self.job_dir_var = tk.StringVar()
        ctk.CTkEntry(job_section, textvariable=self.job_dir_var, **entry_opts).grid(
            row=0, column=1, padx=self.SPACING_8, pady=self.SPACING_8, sticky="ew"
        )
        self.browse_job_btn = self._make_button(job_section, "Browse", self._pick_job_dir, kind="neutral", width=100)
        self.browse_job_btn.grid(row=0, column=2, padx=self.SPACING_8, pady=self.SPACING_8)

        self.advanced_section = ctk.CTkFrame(
            actions,
            fg_color=self.COLORS["surface_2"],
            corner_radius=12,
            border_width=1,
            border_color=self.COLORS["border"],
        )
        self.advanced_section.grid(row=2, column=0, sticky="ew", padx=self.SPACING_12, pady=(0, self.SPACING_8))
        self.advanced_section.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            self.advanced_section,
            text="Advanced",
            text_color=self.COLORS["text_secondary"],
            font=self.font_small_bold,
        ).grid(row=0, column=0, padx=self.SPACING_12, pady=self.SPACING_8, sticky="w")

        health_options = ctk.CTkFrame(self.advanced_section, fg_color="transparent")
        health_options.grid(row=0, column=1, padx=self.SPACING_8, pady=self.SPACING_8, sticky="w")
        self.health_open_commands_var = tk.BooleanVar(value=False)
        self.health_skip_focus_var = tk.BooleanVar(value=False)
        self.health_skip_probe_var = tk.BooleanVar(value=False)
        self.health_skip_sequence_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            health_options,
            text="allow open-cmd",
            variable=self.health_open_commands_var,
            checkbox_height=18,
            checkbox_width=18,
            corner_radius=5,
            border_width=1,
            border_color=self.COLORS["border"],
            fg_color=self.COLORS["primary"],
            hover_color=self.COLORS["primary_hover"],
            text_color=self.COLORS["text_secondary"],
            font=self.font_small,
        ).pack(side="left", padx=(0, self.SPACING_12))
        ctk.CTkCheckBox(
            health_options,
            text="skip focus",
            variable=self.health_skip_focus_var,
            checkbox_height=18,
            checkbox_width=18,
            corner_radius=5,
            border_width=1,
            border_color=self.COLORS["border"],
            fg_color=self.COLORS["primary"],
            hover_color=self.COLORS["primary_hover"],
            text_color=self.COLORS["text_secondary"],
            font=self.font_small,
        ).pack(side="left", padx=(0, self.SPACING_12))
        ctk.CTkCheckBox(
            health_options,
            text="skip probe",
            variable=self.health_skip_probe_var,
            checkbox_height=18,
            checkbox_width=18,
            corner_radius=5,
            border_width=1,
            border_color=self.COLORS["border"],
            fg_color=self.COLORS["primary"],
            hover_color=self.COLORS["primary_hover"],
            text_color=self.COLORS["text_secondary"],
            font=self.font_small,
        ).pack(side="left", padx=(0, self.SPACING_12))
        ctk.CTkCheckBox(
            health_options,
            text="skip sequence",
            variable=self.health_skip_sequence_var,
            checkbox_height=18,
            checkbox_width=18,
            corner_radius=5,
            border_width=1,
            border_color=self.COLORS["border"],
            fg_color=self.COLORS["primary"],
            hover_color=self.COLORS["primary_hover"],
            text_color=self.COLORS["text_secondary"],
            font=self.font_small,
        ).pack(side="left")

        self.open_cmd_frame = ctk.CTkFrame(self.advanced_section, fg_color="transparent")
        self.open_cmd_frame.grid(row=1, column=0, columnspan=2, padx=self.SPACING_8, pady=(0, self.SPACING_8), sticky="w")

        self.record_click_btn = self._make_button(self.advanced_section, "Record Click", self._run_in_thread(self._record_click), kind="neutral", width=130)
        self.record_click_btn.grid(row=2, column=0, padx=self.SPACING_12, pady=(0, self.SPACING_8), sticky="w")
        self.record_target_click_btn = self._make_button(
            self.advanced_section,
            "Record Target Click",
            self._run_in_thread(self._record_target_click),
            kind="neutral",
            width=160,
        )
        self.record_target_click_btn.grid(row=2, column=1, padx=self.SPACING_8, pady=(0, self.SPACING_8), sticky="w")
        self.advanced_section.grid_remove()

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
        tabs.grid(row=3, column=0, sticky="ew", padx=self.SPACING_12, pady=(0, self.SPACING_12))
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
            self.run_job_btn,
            self.health_btn,
            self.run_btn,
            self.test_focus_btn,
            self.test_target_btn,
            self.advanced_btn,
            self.browse_job_btn,
            self.record_click_btn,
            self.record_target_click_btn,
            self.send_text_btn,
            self.browse_image_btn,
            self.send_image_btn,
            self.browse_seq_btn,
            self.run_seq_btn,
        ]

    def _load_health_snapshot_map(self):
        health_file = str(getattr(self.config, "target_health_file", "target_health.json"))
        if not os.path.isabs(health_file):
            health_file = os.path.join(os.getcwd(), health_file)
        if not os.path.exists(health_file):
            return {}
        try:
            with open(health_file, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except Exception:
            return {}
        targets = payload.get("targets")
        if not isinstance(targets, dict):
            return {}
        mapped = {}
        for name, value in targets.items():
            if isinstance(value, dict):
                mapped[str(name)] = value.get("healthy")
            else:
                mapped[str(name)] = bool(value)
        return mapped

    def _worker_capability_tags(self, name: str):
        tags = []
        target_payload = self.config.targets.get(name) if isinstance(self.config.targets, dict) else {}
        if isinstance(target_payload, dict):
            if bool(target_payload.get("assume_open", False)):
                tags.append("assume-open")
            if bool(target_payload.get("command_open_in_test", False)):
                tags.append("test-open")
        adapters = getattr(self.config, "worker_adapters", {})
        if isinstance(adapters, dict) and f"{name}_vscode" in adapters:
            tags.append("contract")
        if not tags:
            tags.append("basic")
        return tags

    def _update_worker_enabled_badge(self, name: str):
        badge = self._worker_enabled_badges.get(name)
        var = self.target_check_vars.get(name)
        if not badge or var is None:
            return
        if bool(var.get()):
            badge.configure(text="Enabled", fg_color=self.COLORS["success"], text_color="#111111")
        else:
            badge.configure(text="Disabled", fg_color=self.COLORS["neutral_status"], text_color="#111111")

    def _refresh_worker_health_badges(self):
        health_map = self._load_health_snapshot_map()
        for name, badge in self._worker_health_badges.items():
            state = health_map.get(name, None)
            if state is True:
                badge.configure(text="Healthy", fg_color=self.COLORS["success"], text_color="#111111")
            elif state is False:
                badge.configure(text="Degraded", fg_color=self.COLORS["error"], text_color="#111111")
            else:
                badge.configure(text="Unknown", fg_color=self.COLORS["neutral_status"], text_color="#111111")

    def _refresh_worker_capability_badges(self):
        for name, badge in self._worker_capability_badges.items():
            caps = ", ".join(self._worker_capability_tags(name))
            badge.configure(text=f"Cap: {caps}")

    def _build_target_checkboxes(self, names):
        for child in self.workers_frame.winfo_children():
            child.destroy()
        self.target_check_vars = {}
        self._worker_enabled_badges = {}
        self._worker_health_badges = {}
        self._worker_capability_badges = {}

        for index, name in enumerate(names):
            row = index // 3
            col = index % 3
            card = ctk.CTkFrame(
                self.workers_frame,
                fg_color=self.COLORS["surface_2"],
                corner_radius=10,
                border_width=1,
                border_color=self.COLORS["border"],
            )
            card.grid(row=row, column=col, padx=self.SPACING_8, pady=self.SPACING_8, sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            enable_var = tk.BooleanVar(value=False)
            self.target_check_vars[name] = enable_var

            ctk.CTkCheckBox(
                card,
                text=name,
                variable=enable_var,
                command=lambda worker=name: self._update_worker_enabled_badge(worker),
                checkbox_height=18,
                checkbox_width=18,
                corner_radius=5,
                border_width=1,
                border_color=self.COLORS["border"],
                fg_color=self.COLORS["primary"],
                hover_color=self.COLORS["primary_hover"],
                text_color=self.COLORS["text_primary"],
                font=self.font_small_bold,
            ).grid(row=0, column=0, padx=self.SPACING_8, pady=(self.SPACING_8, 4), sticky="w")

            badge_row = ctk.CTkFrame(card, fg_color="transparent")
            badge_row.grid(row=1, column=0, padx=self.SPACING_8, pady=(0, self.SPACING_8), sticky="w")

            enabled_badge = self._badge(badge_row, "Disabled", self.COLORS["neutral_status"])
            enabled_badge.pack(side="left", padx=(0, 6))
            self._worker_enabled_badges[name] = enabled_badge

            health_badge = self._badge(badge_row, "Unknown", self.COLORS["neutral_status"])
            health_badge.pack(side="left", padx=(0, 6))
            self._worker_health_badges[name] = health_badge

            caps = ", ".join(self._worker_capability_tags(name))
            cap_badge = ctk.CTkLabel(
                card,
                text=f"Cap: {caps}",
                text_color=self.COLORS["text_secondary"],
                fg_color="transparent",
                font=self.font_small,
            )
            cap_badge.grid(row=2, column=0, padx=self.SPACING_8, pady=(0, self.SPACING_8), sticky="w")
            self._worker_capability_badges[name] = cap_badge

        self._refresh_worker_health_badges()

    def _build_open_test_checkboxes(self, names):
        for child in self.open_cmd_frame.winfo_children():
            child.destroy()
        self.target_open_test_vars = {}

        if names:
            ctk.CTkLabel(
                self.open_cmd_frame,
                text="Open Cmd (test) per target",
                text_color=self.COLORS["text_secondary"],
                font=self.font_small_bold,
            ).grid(row=0, column=0, columnspan=3, padx=self.SPACING_8, pady=(0, 4), sticky="w")

        for index, name in enumerate(names):
            row = 1 + (index // 3)
            col = index % 3
            open_var = tk.BooleanVar(value=False)
            self.target_open_test_vars[name] = open_var

            ctk.CTkCheckBox(
                self.open_cmd_frame,
                text=f"{name} open",
                variable=open_var,
                checkbox_height=18,
                checkbox_width=18,
                corner_radius=5,
                border_width=1,
                border_color=self.COLORS["border"],
                fg_color=self.COLORS["primary"],
                hover_color=self.COLORS["primary_hover"],
                text_color=self.COLORS["text_secondary"],
                font=self.font_small,
            ).grid(row=row, column=col, padx=self.SPACING_8, pady=3, sticky="w")

    def _set_enabled_target_checks(self, enabled):
        enabled_set = set(enabled or [])
        for name, var in self.target_check_vars.items():
            var.set(name in enabled_set)
            self._update_worker_enabled_badge(name)

    def _selected_enabled_targets(self):
        return [name for name, var in self.target_check_vars.items() if bool(var.get())]

    def _set_open_test_target_checks(self, open_enabled):
        open_set = set(open_enabled or [])
        for name, var in self.target_open_test_vars.items():
            var.set(name in open_set)

    def _selected_open_test_targets(self):
        return [name for name, var in self.target_open_test_vars.items() if bool(var.get())]

    def _toggle_advanced(self):
        self._advanced_visible = not self._advanced_visible
        if self._advanced_visible:
            self.advanced_section.grid()
            self.advanced_btn.configure(text="Hide Advanced")
        else:
            self.advanced_section.grid_remove()
            self.advanced_btn.configure(text="Show Advanced")

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
            self._set_timeline_stage("Plan")
            try:
                fn()
                self._set_timeline_stage("Done")
                self.root.after(0, lambda: self._set_job_state("Ready"))
            except Exception as exc:
                self._set_timeline_stage(self._timeline_active or "Execute", failed=True)
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

    def _pick_job_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.job_dir_var.set(path)

    def _load_config_to_ui(self):
        self.window_title_var.set(self.config.window_title)
        self.profile_var.set(self.config.focus_profile)
        self.auto_enter_var.set(self.config.auto_enter)
        names = list(self.config.targets.keys()) if isinstance(self.config.targets, dict) and self.config.targets else ["copilot"]
        self._build_target_checkboxes(names)
        self._build_open_test_checkboxes(names)
        enabled = [name for name in getattr(self.config, "enabled_targets", []) if name in names]
        if not enabled and names:
            enabled = ["copilot"] if "copilot" in names else [names[0]]
        self._set_enabled_target_checks(enabled)
        open_enabled = [
            name
            for name in names
            if bool((self.config.targets.get(name) or {}).get("command_open_in_test", False))
        ]
        self._set_open_test_target_checks(open_enabled)
        self.target_menu.configure(values=names)
        active = self.config.active_target if self.config.active_target in enabled else enabled[0]
        self.target_var.set(active)
        default_jobs_dir = os.path.join(os.getcwd(), "jobs")
        self.job_dir_var.set(default_jobs_dir if os.path.isdir(default_jobs_dir) else os.getcwd())
        self._refresh_worker_capability_badges()
        self._refresh_worker_health_badges()
        self._refresh_status_strip()

    def _save_settings(self):
        self.config.window_title = self.window_title_var.get().strip() or "Visual Studio Code"
        self.config.focus_profile = self.profile_var.get()
        self.config.auto_enter = self.auto_enter_var.get()
        enabled_targets = self._selected_enabled_targets()
        if not enabled_targets:
            messagebox.showwarning("No Workers Selected", "Select at least one extension worker.")
            return
        active_target = self.target_var.get().strip() or self.config.active_target
        if active_target not in enabled_targets:
            active_target = enabled_targets[0]
            self.target_var.set(active_target)
        open_targets = set(self._selected_open_test_targets())
        for name, payload in self.config.targets.items():
            if not isinstance(payload, dict):
                continue
            payload["command_open_in_test"] = name in open_targets
        self.config.enabled_targets = enabled_targets
        self.config.active_target = active_target
        self.config.save()
        self._refresh_worker_capability_badges()
        self._log(
            f"Settings saved (active target: {self.config.active_target}, enabled: {', '.join(self.config.enabled_targets)})"
        )
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
        self._set_timeline_stage("Execute")
        text = self.text_box.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("No Text", "Enter text to send.")
            return
        self.sequencer.send_text(text, press_enter=self.config.auto_enter)

    def _send_image(self):
        self._save_settings()
        self._set_timeline_stage("Execute")
        image_path = self.image_path_var.get().strip()
        if not image_path:
            messagebox.showwarning("No Image", "Pick an image path first.")
            return
        self.sequencer.send_image(image_path, press_enter=self.config.auto_enter)

    def _run_sequence(self):
        self._save_settings()
        self._set_timeline_stage("Dispatch")
        sequence_file = self.sequence_path_var.get().strip()
        if not sequence_file:
            messagebox.showwarning("No Sequence", "Pick a sequence JSON file first.")
            return
        self._set_timeline_stage("Execute")
        self.sequencer.run_sequence(sequence_file)

    def _run_job(self):
        self._save_settings()
        self._set_timeline_stage("Dispatch")
        job_dir = self.job_dir_var.get().strip()
        if not job_dir:
            messagebox.showwarning("No Job Folder", "Choose a job folder first.")
            return
        if not os.path.isdir(job_dir):
            raise FileNotFoundError(f"Job folder not found: {job_dir}")
        self._set_timeline_stage("Execute")
        runner = JobRunner(self.sequencer, self.config)
        ok = runner.run_job(job_dir)
        if not ok:
            raise RuntimeError(f"run-job failed: {job_dir}")
        self._set_timeline_stage("Capture")
        self._set_timeline_stage("Validate")
        self._log(f"run-job completed: {job_dir}")

    def _health_check(self):
        self._save_settings()
        self._set_timeline_stage("Validate")
        targets = self._selected_enabled_targets() or self.sequencer.enabled_targets() or self.sequencer.list_targets()
        if not targets:
            raise ValueError("No targets available for health-check")

        open_commands = bool(self.health_open_commands_var.get())
        skip_focus = bool(self.health_skip_focus_var.get())
        skip_probe = bool(self.health_skip_probe_var.get())
        skip_sequence = bool(self.health_skip_sequence_var.get())

        overall_ok = True
        health_report = {
            "checked_at": datetime.now().isoformat(),
            "open_commands": open_commands,
            "focus": {"skipped": skip_focus, "ok": None},
            "probe": {"skipped": skip_probe},
            "sequence": {"skipped": skip_sequence},
            "targets": {},
        }

        self._log("== KS CodeOps Health Check ==")
        self._log(f"Targets: {', '.join(targets)}")

        if skip_focus:
            self._log("focus: skipped")
        else:
            focus_ok = self.sequencer.test_focus()
            self._log(f"focus: {'ok' if focus_ok else 'failed'}")
            overall_ok = overall_ok and bool(focus_ok)
            health_report["focus"]["ok"] = bool(focus_ok)

        if skip_probe:
            self._log("probe: skipped")
            for target in targets:
                entry = health_report["targets"].setdefault(target, {})
                entry["probe_ok"] = None
        else:
            probe_all_ok = True
            for target in targets:
                allow_open = bool(open_commands and self.sequencer._target_payload(target).get("command_open_in_test", False))
                probe_text = f"KS_CODEOPS_HEALTH_PROBE_{target.upper()}"
                ok = self.sequencer.probe_target_input(
                    target_name=target,
                    probe_text=probe_text,
                    clear_after=True,
                    allow_command_open=allow_open,
                )
                entry = health_report["targets"].setdefault(target, {})
                entry["probe_ok"] = bool(ok)
                probe_all_ok = probe_all_ok and bool(ok)
                self._log(f"probe[{target}]: {'ok' if ok else 'failed'}")
            overall_ok = overall_ok and probe_all_ok

        if skip_sequence:
            self._log("sequence: skipped")
            for target in targets:
                entry = health_report["targets"].setdefault(target, {})
                entry["sequence_ok"] = None
        else:
            seq_results = self.sequencer.run_target_test_sequence(
                targets=targets,
                delay_between_s=1.0,
                text_prefix="KS_CODEOPS_HEALTH",
                allow_command_open=open_commands,
            )
            seq_all_ok = True
            for target in targets:
                ok = bool(seq_results.get(target))
                entry = health_report["targets"].setdefault(target, {})
                entry["sequence_ok"] = ok
                seq_all_ok = seq_all_ok and ok
                self._log(f"sequence[{target}]: {'pass' if ok else 'fail'}")
            overall_ok = overall_ok and seq_all_ok

        healthy_targets = []
        for target in targets:
            entry = health_report["targets"].setdefault(target, {})
            probe_ok = entry.get("probe_ok")
            sequence_ok = entry.get("sequence_ok")
            healthy = True
            if probe_ok is not None:
                healthy = healthy and bool(probe_ok)
            if sequence_ok is not None:
                healthy = healthy and bool(sequence_ok)
            if probe_ok is None and sequence_ok is None:
                healthy = bool(overall_ok)
            entry["healthy"] = bool(healthy)
            if entry["healthy"]:
                healthy_targets.append(target)

        health_report["overall_ok"] = bool(overall_ok)
        health_report["healthy_targets"] = healthy_targets
        self._write_health_snapshot(health_report)
        self._refresh_worker_health_badges()

        self._log(f"health-check: {'PASS' if overall_ok else 'FAIL'}")
        if not overall_ok:
            raise RuntimeError("health-check failed")

    def _write_health_snapshot(self, payload: dict):
        health_file = str(getattr(self.config, "target_health_file", "target_health.json"))
        if not os.path.isabs(health_file):
            health_file = os.path.join(os.getcwd(), health_file)
        parent = os.path.dirname(health_file)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(health_file, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        self._log(f"health-snapshot: {health_file}")

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
