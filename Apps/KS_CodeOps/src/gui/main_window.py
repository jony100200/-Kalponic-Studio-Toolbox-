import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk


class VSCodePromptSenderGUI:
    def __init__(self, config, sequencer):
        self.config = config
        self.sequencer = sequencer
        self.sequencer.set_log_callback(self._log)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("KS CodeOps")
        self.root.geometry("980x760")
        self.root.minsize(900, 620)

        self._build_ui()
        self._load_config_to_ui()

    def _build_ui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self.root)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top, text="Window Title").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.window_title_var = tk.StringVar()
        ctk.CTkEntry(top, textvariable=self.window_title_var).grid(row=0, column=1, padx=8, pady=8, sticky="ew")

        ctk.CTkLabel(top, text="Focus Profile").grid(row=1, column=0, padx=8, pady=8, sticky="w")
        self.profile_var = tk.StringVar(value="chat_panel")
        ctk.CTkOptionMenu(top, variable=self.profile_var, values=["chat_panel", "editor"]).grid(
            row=1, column=1, padx=8, pady=8, sticky="w"
        )

        ctk.CTkLabel(top, text="Active Target").grid(row=2, column=0, padx=8, pady=8, sticky="w")
        self.target_var = tk.StringVar(value="copilot")
        self.target_menu = ctk.CTkOptionMenu(top, variable=self.target_var, values=["copilot"])
        self.target_menu.grid(row=2, column=1, padx=8, pady=8, sticky="w")

        self.auto_enter_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(top, text="Auto Enter", variable=self.auto_enter_var).grid(row=3, column=1, padx=8, pady=8, sticky="w")

        actions = ctk.CTkFrame(self.root)
        actions.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_rowconfigure(1, weight=1)

        button_row = ctk.CTkFrame(actions)
        button_row.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

        ctk.CTkButton(button_row, text="Save Settings", command=self._save_settings).pack(side="left", padx=4, pady=4)
        ctk.CTkButton(button_row, text="Test Focus", command=self._run_in_thread(self._test_focus)).pack(side="left", padx=4, pady=4)
        ctk.CTkButton(button_row, text="Record Click", command=self._run_in_thread(self._record_click)).pack(side="left", padx=4, pady=4)
        ctk.CTkButton(button_row, text="Test Target", command=self._run_in_thread(self._test_target)).pack(side="left", padx=4, pady=4)
        ctk.CTkButton(button_row, text="Record Target Click", command=self._run_in_thread(self._record_target_click)).pack(side="left", padx=4, pady=4)

        tabs = ctk.CTkTabview(actions)
        tabs.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        tabs.add("Text")
        tabs.add("Image")
        tabs.add("Sequence")
        tabs.add("Logs")

        text_tab = tabs.tab("Text")
        text_tab.grid_columnconfigure(0, weight=1)
        self.text_box = ctk.CTkTextbox(text_tab, height=220)
        self.text_box.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        ctk.CTkButton(text_tab, text="Send Text", command=self._run_in_thread(self._send_text)).grid(row=1, column=0, padx=8, pady=8, sticky="e")

        image_tab = tabs.tab("Image")
        image_tab.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(image_tab, text="Image Path").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.image_path_var = tk.StringVar()
        ctk.CTkEntry(image_tab, textvariable=self.image_path_var).grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        ctk.CTkButton(image_tab, text="Browse", command=self._pick_image).grid(row=0, column=2, padx=8, pady=8)
        ctk.CTkButton(image_tab, text="Send Image", command=self._run_in_thread(self._send_image)).grid(row=1, column=2, padx=8, pady=8)

        seq_tab = tabs.tab("Sequence")
        seq_tab.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(seq_tab, text="Sequence File").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.sequence_path_var = tk.StringVar()
        ctk.CTkEntry(seq_tab, textvariable=self.sequence_path_var).grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        ctk.CTkButton(seq_tab, text="Browse", command=self._pick_sequence).grid(row=0, column=2, padx=8, pady=8)
        ctk.CTkButton(seq_tab, text="Run Sequence", command=self._run_in_thread(self._run_sequence)).grid(row=1, column=2, padx=8, pady=8)

        logs_tab = tabs.tab("Logs")
        logs_tab.grid_columnconfigure(0, weight=1)
        logs_tab.grid_rowconfigure(0, weight=1)
        self.log_box = ctk.CTkTextbox(logs_tab)
        self.log_box.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    def _run_in_thread(self, fn):
        def runner():
            try:
                fn()
            except Exception as exc:
                self._log(f"Error: {exc}")
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

    def _save_settings(self):
        self.config.window_title = self.window_title_var.get().strip() or "Visual Studio Code"
        self.config.focus_profile = self.profile_var.get()
        self.config.auto_enter = self.auto_enter_var.get()
        self.config.active_target = self.target_var.get().strip() or self.config.active_target
        self.config.save()
        self._log(f"Settings saved (active target: {self.config.active_target})")

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
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")

    def run(self):
        self.root.mainloop()
