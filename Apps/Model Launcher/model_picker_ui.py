import os
import psutil
import subprocess
import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
import json
from functools import lru_cache

@lru_cache(maxsize=1)
def get_gpu_info():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2
        )
        if result.returncode == 0 and result.stdout.strip():
            name, mem = result.stdout.strip().split('\n')[0].split(',')
            name = name.strip()
            vram_gb = int(int(mem.strip().split()[0]) / 1024)
            return name, vram_gb
    except Exception:
        pass
    return "(Unknown GPU)", 0

def get_ram_info():
    return int(psutil.virtual_memory().total / (1024**3))

def get_model_size(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    elif os.path.isdir(path):
        return sum(
            os.path.getsize(os.path.join(root, f))
            for root, _, files in os.walk(path)
            for f in files
            if os.path.isfile(os.path.join(root, f))
        )
    return 0

def size_gb(bytes):
    return round(bytes / (1024**3), 2)

def recommend(system_vram, system_ram, model_size_gb):
    if model_size_gb < 2:
        if system_vram >= 2 and system_ram >= 4:
            return "✅ System OK! Model will run fast.", "green"
    elif model_size_gb < 4:
        if system_vram >= 4 and system_ram >= 8:
            return "✅ Good fit for your GPU. Should run well.", "green"
        elif system_vram < 4:
            return "⚠️ Model is a bit heavy for your VRAM, try a smaller model for best speed.", "orange"
    elif model_size_gb < 8:
        if system_vram >= 8 and system_ram >= 16:
            return "✅ Your system can run this, but may be slower.", "orange"
        else:
            return "❌ Not enough VRAM or RAM! Pick a smaller model.", "red"
    else:
        if system_vram >= 12 and system_ram >= 24:
            return "✅ Heavy model, but your system can handle it.", "orange"
        else:
            return "❌ Model is too large for your system. Pick a much smaller model.", "red"
    return "❓ Could not determine compatibility.", "gray"

class ToolTip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, _event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, background="#ffffe0", relief="solid", borderwidth=1,
                         font=("Segoe UI", 9))
        label.pack(ipadx=4, ipady=2)

    def hide_tip(self, _event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class ModelPickerUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Pick a Model and Launch Server")
        self.geometry("570x400")
        self.model_path = ctk.StringVar()
        self.model_type = ctk.StringVar(value="file")
        self.status_var = ctk.StringVar(value="Pick a model to check...")
        self.compat_ok = False
        self.server_exe = None
        self.port = None
        self.server_process = None  # Track the launched process

        self.columnconfigure(0, weight=1)
        row = 0

        ctk.CTkLabel(self, text="Select Model Type:").grid(row=row, column=0, pady=(16, 0), sticky="w", padx=16)
        row += 1
        self.model_type_dropdown = ctk.CTkOptionMenu(self, variable=self.model_type, values=["file", "folder"], command=self.on_type_change)
        self.model_type_dropdown.grid(row=row, column=0, pady=(2, 10), sticky="w", padx=16)
        ToolTip(self.model_type_dropdown, "Select 'file' for LLMs, 'folder' for Whisper/ASR.")

        row += 1
        frame = ctk.CTkFrame(self)
        frame.grid(row=row, column=0, padx=12, pady=2, sticky="ew")
        frame.columnconfigure(1, weight=1)
        ctk.CTkLabel(frame, text="Model Path:", width=85).grid(row=0, column=0, padx=(6,0))
        self.model_path_entry = ctk.CTkEntry(frame, textvariable=self.model_path, width=320)
        self.model_path_entry.grid(row=0, column=1, padx=(4,0), sticky="ew")
        ToolTip(self.model_path_entry, "Full path to your model file (for LLM) or folder (for Whisper).")
        self.browse_button = ctk.CTkButton(frame, text="Browse", command=self.browse_model, width=70)
        self.browse_button.grid(row=0, column=2, padx=8)
        ToolTip(self.browse_button, "Browse and pick the model path.")

        row += 1
        self.load_config_button = ctk.CTkButton(self, text="Load Config", command=self.load_config)
        self.load_config_button.grid(row=row, column=0, pady=(6, 0), sticky="w", padx=16)
        ToolTip(self.load_config_button, "Load settings from a JSON configuration file.")

        row += 1
        self.status_label = ctk.CTkLabel(self, textvariable=self.status_var, text_color="white", anchor="w", font=("Segoe UI", 13))
        self.status_label.grid(row=row, column=0, pady=(18, 0), sticky="ew", padx=16)
        row += 1
        self.sysinfo_label = ctk.CTkLabel(self, text=self.get_system_info(), text_color="#A5D6A7", font=("Segoe UI", 12, "italic"))
        self.sysinfo_label.grid(row=row, column=0, pady=(10, 0), sticky="ew", padx=16)

        row += 1
        self.start_btn = ctk.CTkButton(self, text="Start Server", command=self.launch_worker, state="disabled")
        self.start_btn.grid(row=row, column=0, pady=10)
        ToolTip(self.start_btn, "Launch the server using these settings.")

        row += 1
        self.stop_btn = ctk.CTkButton(self, text="Stop Server", command=self.stop_worker)
        self.stop_btn.grid(row=row, column=0, pady=(0, 18))
        ToolTip(self.stop_btn, "Stop the running server process.")

        self.model_path.trace_add("write", lambda *_: self.check_compatibility(self.model_path.get()))

    def get_system_info(self):
        gpu_name, vram_gb = get_gpu_info()
        ram_gb = get_ram_info()
        return f"Detected GPU: {gpu_name} | VRAM: {vram_gb} GB | System RAM: {ram_gb} GB"

    def browse_model(self):
        if self.model_type.get() == "file":
            path = filedialog.askopenfilename(title="Select Model File", filetypes=[("Model Files", "*.gguf *.bin *.pth *.onnx *.ckpt *.pt"), ("All Files", "*.*")])
        else:
            path = filedialog.askdirectory(title="Select Model Folder")
        if path:
            self.model_path.set(path)

    def load_config(self):
        file_path = filedialog.askopenfilename(title="Select Config File", filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config:\n{e}")
            return
        if "model_path" in data:
            self.model_path.set(data["model_path"])
        if "model_type" in data:
            self.model_type.set(data["model_type"])
        self.server_exe = data.get("server_exe", self.server_exe)
        self.port = data.get("port", self.port)

    def check_compatibility(self, path):
        if not path or not os.path.exists(path):
            self.status_label.configure(text="Please select a valid model path.", text_color="gray")
            self.start_btn.configure(state="disabled")
            return
        gpu_name, vram_gb = get_gpu_info()
        ram_gb = get_ram_info()
        model_size_bytes = get_model_size(path)
        model_size_gb = size_gb(model_size_bytes)
        msg, color = recommend(vram_gb, ram_gb, model_size_gb)
        self.status_label.configure(text=f"Model size: {model_size_gb} GB\n{msg}", text_color=color)
        self.compat_ok = color != "red"
        self.start_btn.configure(state="normal" if self.compat_ok else "disabled")

    def on_type_change(self, _event=None):
        self.model_path.set("")
        self.status_label.configure(text="Pick a model to check...", text_color="white")
        self.start_btn.configure(state="disabled")

    def launch_worker(self):
        path = self.model_path.get()
        mtype = self.model_type.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "Please select a valid model.")
            return
        args = ["python", "run_model_server.py", mtype, path]
        if self.server_exe:
            args.append(self.server_exe)
        if self.port:
            args.append(str(self.port))
        self.server_process = subprocess.Popen(args, shell=True)
        self.status_var.set("🚀 Server launching in background.\nClose or Stop to terminate.")
        self.start_btn.configure(state="disabled")

    def stop_worker(self):
        if self.server_process and self.server_process.poll() is None:
            self.server_process.terminate()
            self.status_var.set("🛑 Server stopped.")
            self.start_btn.configure(state="normal")
        else:
            self.status_var.set("ℹ️ No active server to stop.")

if __name__ == "__main__":
    ModelPickerUI().mainloop()
