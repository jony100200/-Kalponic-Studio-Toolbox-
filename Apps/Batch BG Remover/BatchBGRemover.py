import io
import logging
import threading
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk
from PIL import Image, ImageTk
from rembg import remove
from tkinter import filedialog, messagebox


# -----------------------------
# Configuration & Constants
# -----------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
PREVIEW_SIZE = (128, 128)


class ImageProcessor:
    """Single-responsibility class to process images (removing background).

    It doesn't know about GUI details; it reports progress via callbacks.
    """

    def __init__(self, remover=remove):
        self.remover = remover
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def process_folder(
        self,
        in_folder: Path,
        out_folder: Path,
        progress_cb: Optional[Callable[[int, int], None]] = None,
        preview_cb: Optional[Callable[[bytes], None]] = None,
        show_preview: bool = False,
    ) -> int:
        """Process all supported images in in_folder and write cleaned PNGs to out_folder.

        Returns number of successfully processed images.
        """
        in_folder = Path(in_folder)
        out_folder = Path(out_folder)
        out_folder.mkdir(parents=True, exist_ok=True)

        files = sorted([p for p in in_folder.iterdir() if p.suffix.lower() in SUPPORTED_EXTS])
        total = len(files)
        if total == 0:
            raise FileNotFoundError("No supported image files found in input folder")

        processed = 0
        logging.info("Starting processing %d files", total)

        for idx, p in enumerate(files, start=1):
            if self._cancelled:
                logging.info("Processing cancelled by user")
                break

            try:
                data = p.read_bytes()
                out_bytes = self.remover(data)

                # Always save as PNG to preserve alpha
                out_name = p.stem + "_cleaned.png"
                (out_folder / out_name).write_bytes(out_bytes)

                processed += 1

                if show_preview and preview_cb:
                    preview_cb(out_bytes)

                if progress_cb:
                    progress_cb(idx, total)

            except Exception as exc:
                logging.exception("Failed to process %s: %s", p, exc)

        logging.info("Processing finished: %d/%d processed", processed, total)
        return processed


class BatchBGRemoverApp:
    """GUI application. Keeps GUI logic separate from processing logic (SOLID: single responsibility)."""

    def __init__(self):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Batch AI Background Remover")
        self.root.geometry("720x420")

        # State
        self.input_folder = ctk.StringVar()
        self.output_folder = ctk.StringVar()
        self.show_preview = ctk.BooleanVar(value=False)

        self.processor = ImageProcessor()
        self.worker_thread: Optional[threading.Thread] = None

        # UI elements created in method
        self._create_widgets()

    def _create_widgets(self):
        # Input
        ctk.CTkLabel(self.root, text="Input Folder:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        ctk.CTkEntry(self.root, textvariable=self.input_folder, width=420).grid(row=0, column=1, padx=10)
        ctk.CTkButton(self.root, text="Browse", command=self._select_input_folder).grid(row=0, column=2, padx=10)

        # Output
        ctk.CTkLabel(self.root, text="Output Folder:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        ctk.CTkEntry(self.root, textvariable=self.output_folder, width=420).grid(row=1, column=1, padx=10)
        ctk.CTkButton(self.root, text="Browse", command=self._select_output_folder).grid(row=1, column=2, padx=10)

        # Options
        ctk.CTkCheckBox(self.root, text="Show Preview", variable=self.show_preview).grid(row=2, column=1, pady=10)

        # Action buttons
        self.start_btn = ctk.CTkButton(self.root, text="Start", command=self.start_processing, fg_color="green")
        self.start_btn.grid(row=3, column=1, pady=6, sticky="w", padx=(40, 0))

        self.cancel_btn = ctk.CTkButton(self.root, text="Cancel", command=self.cancel_processing, fg_color="#b22222")
        self.cancel_btn.grid(row=3, column=1, pady=6, sticky="e", padx=(0, 40))
        self.cancel_btn.configure(state="disabled")

        # Progress
        self.progress_bar = ctk.CTkProgressBar(self.root, width=520)
        self.progress_bar.grid(row=4, column=1, pady=10)
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self.root, text="Ready")
        self.status_label.grid(row=5, column=1, pady=4)

        # Preview area
        self.preview_label = ctk.CTkLabel(self.root, text="")
        self.preview_label.grid(row=6, column=1, pady=6)

    # ------------------ UI helpers ------------------
    def _select_input_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_folder.set(folder)

    def _select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)

    def _set_status(self, text: str):
        self.status_label.configure(text=text)

    def _update_progress(self, idx: int, total: int):
        if total <= 0:
            self.progress_bar.set(0)
            return
        fraction = idx / total
        self.progress_bar.set(fraction)
        # Ensure UI updates on main thread
        self.root.update_idletasks()

    def _show_preview(self, image_bytes: bytes):
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.thumbnail(PREVIEW_SIZE)
            tk_img = ImageTk.PhotoImage(img)
            # must update on main thread
            def _set():
                self.preview_label.configure(image=tk_img)
                self.preview_label.image = tk_img

            self.root.after(0, _set)
        except Exception:
            logging.exception("Failed to update preview")

    # ------------------ Control flow ------------------
    def start_processing(self):
        in_folder = self.input_folder.get().strip()
        out_folder = self.output_folder.get().strip()

        if not in_folder:
            messagebox.showerror("Error", "Please select an input folder")
            return
        if not out_folder:
            messagebox.showerror("Error", "Please select an output folder")
            return

        # Disable/enable buttons
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self._set_status("Processing...")
        self.progress_bar.set(0)

        # Reset cancel flag
        self.processor = ImageProcessor()

        # Launch worker
        def worker():
            try:
                processed = self.processor.process_folder(
                    Path(in_folder),
                    Path(out_folder),
                    progress_cb=lambda i, t: self.root.after(0, self._update_progress, i, t),
                    preview_cb=(lambda b: self._show_preview(b)) if self.show_preview.get() else None,
                    show_preview=self.show_preview.get(),
                )

                self.root.after(0, lambda: messagebox.showinfo("Done", f"Processed {processed} image(s)."))
                self.root.after(0, lambda: self._set_status("Done"))

            except FileNotFoundError as fnf:
                logging.warning("%s", fnf)
                self.root.after(0, lambda: messagebox.showwarning("No Images", str(fnf)))
                self.root.after(0, lambda: self._set_status("No images"))

            except Exception as e:
                logging.exception("Unexpected error during processing: %s", e)
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.root.after(0, lambda: self._set_status("Error"))

            finally:
                # Reset UI state
                self.root.after(0, lambda: self.start_btn.configure(state="normal"))
                self.root.after(0, lambda: self.cancel_btn.configure(state="disabled"))

        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()

    def cancel_processing(self):
        self.processor.cancel()
        self._set_status("Cancelling...")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = BatchBGRemoverApp()
    app.run()
