import os
from tkinter import filedialog
from PIL import Image, ImageOps
import customtkinter as ctk
import threading
from typing import Callable, Optional, Tuple


class ImageResizer:
    """Single responsibility: handle image resizing logic."""

    @staticmethod
    def _parse_dim(value: str) -> Optional[Tuple[str, float]]:
        if not value:
            return None
        value = value.strip()
        if value.endswith('%'):
            try:
                pct = float(value.rstrip('%')) / 100.0
                return ('pct', pct)
            except ValueError:
                return None
        try:
            return ('abs', int(value))
        except ValueError:
            return None

    @staticmethod
    def _compute_target(src_w: int, src_h: int, p: Optional[Tuple[str, float]], is_width: bool) -> Optional[int]:
        if p is None:
            return None
        typ, val = p
        if typ == 'pct':
            return int((src_w if is_width else src_h) * val)
        return int(val)

    @staticmethod
    def resize_folder(
        folder: str,
        output_folder: str,
        raw_w: str,
        raw_h: str,
        progress_cb: Optional[Callable[[int, int, int, int], None]] = None,
    ) -> Tuple[int, int]:
        """Resize all images in `folder`. Returns tuple (success_count, fail_count).

        progress_cb, if provided, will be called with (index, total, success_count, fail_count).
        """
        pw = ImageResizer._parse_dim(raw_w)
        ph = ImageResizer._parse_dim(raw_h)
        if pw is None and ph is None:
            raise ValueError("Width/Height must be provided (int or percentage).")

        os.makedirs(output_folder, exist_ok=True)
        files = [f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        total = len(files)
        success = 0
        fail = 0

        for i, name in enumerate(files, start=1):
            src_path = os.path.join(folder, name)
            try:
                with Image.open(src_path) as img:
                    img = ImageOps.exif_transpose(img)
                    src_w, src_h = img.size

                    target_w = ImageResizer._compute_target(src_w, src_h, pw, True)
                    target_h = ImageResizer._compute_target(src_w, src_h, ph, False)

                    # preserve aspect ratio if one dimension missing
                    if target_w is None and target_h is not None:
                        target_w = max(1, int(src_w * (target_h / src_h)))
                    elif target_h is None and target_w is not None:
                        target_h = max(1, int(src_h * (target_w / src_w)))
                    elif target_w is None and target_h is None:
                        target_w, target_h = src_w, src_h

                    resized = img.resize((target_w, target_h), Image.LANCZOS)

                    ext = os.path.splitext(name)[1].lower()
                    target_path = os.path.join(output_folder, name)
                    if ext in ('.jpg', '.jpeg') and resized.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new("RGB", resized.size, (255, 255, 255))
                        background.paste(resized, mask=resized.split()[-1])
                        background.save(target_path, quality=95)
                    else:
                        save_kwargs = {}
                        if ext in ('.jpg', '.jpeg'):
                            save_kwargs['quality'] = 95
                        resized.save(target_path, **save_kwargs)

                success += 1
            except Exception:
                fail += 1
            finally:
                if progress_cb:
                    progress_cb(i, total, success, fail)

        return success, fail


class ImageResizerApp(ctk.CTk):
    """GUI: single responsibility is to interact with the user and call ImageResizer."""

    def __init__(self):
        super().__init__()
        self.title("Batch Image Resizer")
        # let user resize window; widgets inside are scrollable
        self.geometry("640x420")

        # Variables
        self.folder_path = ctk.StringVar()
        self.output_path = ctk.StringVar()
        self.width_var = ctk.StringVar()
        self.height_var = ctk.StringVar()

        # Presets
        self.presets = {
            "Small (800x600)": (800, 600),
            "Medium (1600x1200)": (1600, 1200),
            "Large (3840x2160)": (3840, 2160),
            "Custom": (None, None),
        }

        # Build a scrollable content area so UI fits on any monitor
        container = ctk.CTkFrame(self)
        container.pack(fill='both', expand=True, padx=8, pady=8)

        scroll = ctk.CTkScrollableFrame(container)
        scroll.pack(fill='both', expand=True)

        # Input
        ctk.CTkLabel(scroll, text="Select Input Folder:").grid(row=0, column=0, sticky='w', pady=(6, 2), padx=6)
        self.folder_entry = ctk.CTkEntry(scroll, textvariable=self.folder_path, width=420)
        self.folder_entry.grid(row=1, column=0, sticky='w', padx=6)
        ctk.CTkButton(scroll, text="Browse", command=self.browse_folder).grid(row=1, column=1, padx=6)

        # Output
        ctk.CTkLabel(scroll, text="Select Output Folder (optional):").grid(row=2, column=0, sticky='w', pady=(8, 2), padx=6)
        self.output_entry = ctk.CTkEntry(scroll, textvariable=self.output_path, width=420)
        self.output_entry.grid(row=3, column=0, sticky='w', padx=6)
        ctk.CTkButton(scroll, text="Browse", command=self.browse_output_folder).grid(row=3, column=1, padx=6)

        # Width/Height
        ctk.CTkLabel(scroll, text="Width:").grid(row=4, column=0, sticky='w', pady=(8, 2), padx=6)
        self.width_entry = ctk.CTkEntry(scroll, textvariable=self.width_var, width=100)
        self.width_entry.grid(row=5, column=0, sticky='w', padx=6)

        ctk.CTkLabel(scroll, text="Height:").grid(row=4, column=1, sticky='w', pady=(8, 2), padx=6)
        self.height_entry = ctk.CTkEntry(scroll, textvariable=self.height_var, width=100)
        self.height_entry.grid(row=5, column=1, sticky='w', padx=6)

        # Presets
        ctk.CTkLabel(scroll, text="Presets:").grid(row=6, column=0, sticky='w', pady=(10, 2), padx=6)
        self.preset_menu = ctk.CTkOptionMenu(scroll, values=list(self.presets.keys()), command=self.on_preset_select)
        self.preset_menu.set("Custom")
        self.preset_menu.grid(row=7, column=0, sticky='w', padx=6)

        # Run
        self.run_button = ctk.CTkButton(scroll, text="Resize Images", command=self.on_run)
        self.run_button.grid(row=8, column=0, pady=12, padx=6, sticky='w')

        # Status
        self.status_label = ctk.CTkLabel(scroll, text="")
        self.status_label.grid(row=9, column=0, columnspan=2, sticky='w', padx=6, pady=(6, 12))

        # Make grid stretch nicely
        for i in range(2):
            scroll.grid_columnconfigure(i, weight=1)

    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_path.set(folder)

    def on_preset_select(self, value: str):
        dims = self.presets.get(value)
        if not dims:
            return
        w, h = dims
        if w is None and h is None:
            return
        self.width_var.set(str(w))
        self.height_var.set(str(h))

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def _set_controls(self, enabled: bool):
        state = 'normal' if enabled else 'disabled'
        try:
            self.folder_entry.configure(state=state)
            self.output_entry.configure(state=state)
            self.width_entry.configure(state=state)
            self.height_entry.configure(state=state)
            self.preset_menu.configure(state=state)
            self.run_button.configure(state=state)
        except Exception:
            pass

    def _progress_cb(self, i: int, total: int, ok: int, err: int):
        self.status_label.configure(text=f"Processing {i}/{total}... (OK:{ok} ERR:{err})")

    def on_run(self):
        # Start background thread to keep UI responsive
        t = threading.Thread(target=self._run_worker, daemon=True)
        t.start()

    def _run_worker(self):
        folder = self.folder_path.get().strip()
        if not folder:
            self.status_label.configure(text="Please select an input folder.")
            return

        raw_w = self.width_var.get().strip()
        raw_h = self.height_var.get().strip()
        if not raw_w and not raw_h:
            self.status_label.configure(text="Enter width or height (or percentage like 50%).")
            return

        output_folder = self.output_path.get().strip() or os.path.join(folder, "resized")
        self._set_controls(False)
        self.status_label.configure(text="Starting...")

        try:
            success, fail = ImageResizer.resize_folder(folder, output_folder, raw_w, raw_h, progress_cb=self._progress_cb)
            self.status_label.configure(text=f"Done — resized {success} images, {fail} failures. Saved in '{output_folder}'.")
        except Exception as e:
            self.status_label.configure(text=str(e))
        finally:
            self._set_controls(True)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = ImageResizerApp()
    app.mainloop()
