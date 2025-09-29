import io
import logging
import threading
from pathlib import Path
from typing import Callable, Optional, List

import customtkinter as ctk
from PIL import Image, ImageTk
from transparent_background import Remover
from tkinter import filedialog, messagebox
from tqdm import tqdm
import numpy as np


# -----------------------------
# Configuration & Constants
# -----------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
PREVIEW_SIZE = (128, 128)


class InspyrenetRemover:
    """InSPyReNet background remover using transparent-background library.
    
    This class provides superior background removal quality compared to standard rembg.
    """
    
    def __init__(self, use_jit: bool = False, threshold: float = 0.5):
        self.use_jit = use_jit
        self.threshold = threshold
        self._remover = None
    
    def _get_remover(self):
        """Lazy initialization of remover to avoid loading model until needed."""
        if self._remover is None:
            self._remover = Remover(jit=self.use_jit)
        return self._remover
    
    def remove_background(self, image_data: bytes) -> bytes:
        """Remove background from image data and return PNG bytes."""
        # Open image from bytes
        img = Image.open(io.BytesIO(image_data))
        
        # Process with InSPyReNet
        remover = self._get_remover()
        result = remover.process(img, type='rgba', threshold=self.threshold)
        
        # Convert to bytes
        output = io.BytesIO()
        result.save(output, format='PNG')
        return output.getvalue()


class ImageProcessor:
    """Single-responsibility class to process images (removing background).

    It doesn't know about GUI details; it reports progress via callbacks.
    """

    def __init__(self, use_jit: bool = False, threshold: float = 0.5):
        self.remover = InspyrenetRemover(use_jit=use_jit, threshold=threshold)
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
                out_bytes = self.remover.remove_background(data)

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
    
    def process_folder_queue(
        self,
        folder_pairs: List[tuple[Path, Path]],
        progress_cb: Optional[Callable[[int, int, str], None]] = None,
        preview_cb: Optional[Callable[[bytes], None]] = None,
        show_preview: bool = False,
    ) -> tuple[int, int]:
        """Process multiple folder pairs (input, output).
        
        Returns (total_processed, total_files).
        """
        total_processed = 0
        total_files = 0
        
        # Count total files first
        for in_folder, _ in folder_pairs:
            files = [p for p in Path(in_folder).iterdir() if p.suffix.lower() in SUPPORTED_EXTS]
            total_files += len(files)
        
        if total_files == 0:
            raise FileNotFoundError("No supported image files found in any input folders")
        
        current_file = 0
        
        for folder_idx, (in_folder, out_folder) in enumerate(folder_pairs, 1):
            if self._cancelled:
                break
                
            folder_name = Path(in_folder).name
            logging.info(f"Processing folder {folder_idx}/{len(folder_pairs)}: {folder_name}")
            
            try:
                processed = self.process_folder(
                    in_folder, 
                    out_folder, 
                    progress_cb=lambda i, t: progress_cb(current_file + i, total_files, f"Folder: {folder_name}") if progress_cb else None,
                    preview_cb=preview_cb,
                    show_preview=show_preview
                )
                total_processed += processed
                
                # Update current file count
                files = [p for p in Path(in_folder).iterdir() if p.suffix.lower() in SUPPORTED_EXTS]
                current_file += len(files)
                
            except Exception as exc:
                logging.exception(f"Failed to process folder {folder_name}: {exc}")
                # Update current file count even on failure
                files = [p for p in Path(in_folder).iterdir() if p.suffix.lower() in SUPPORTED_EXTS]
                current_file += len(files)
        
        logging.info(f"Queue processing finished: {total_processed}/{total_files} processed from {len(folder_pairs)} folders")
        return total_processed, total_files


class BatchBGRemoverApp:
    """GUI application with InSPyReNet integration and folder queue support."""

    def __init__(self):
        # Set futuristic cyberpunk theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")  # More sci-fi than regular blue

        self.root = ctk.CTk()
        self.root.title("⚡ InSPyReNet AI Background Remover ⚡")
        self.root.geometry("950x700")
        # State
        
        # Custom cyberpunk — toned down / eye-friendly colors
        # Muted teal accent and soft blue secondary to reduce eye strain
        self.cyber_accent = "#1fbf9c"  # muted teal (less flashy)
        self.cyber_secondary = "#4aa3ff"  # soft electric blue
        self.cyber_bg = "#0f1113"  # near-black with a tiny warmth
        self.cyber_frame = "#141826"  # dark slate (subtle, non-flashy)

        # State
        self.input_folders: List[str] = []
        self.output_folder = ctk.StringVar()
        self.show_preview = ctk.BooleanVar(value=False)
        self.use_jit = ctk.BooleanVar(value=False)
        self.threshold = ctk.DoubleVar(value=0.5)

        self.processor: Optional[ImageProcessor] = None
        self.worker_thread: Optional[threading.Thread] = None

        # UI elements created in method
        self._create_widgets()

    def _create_widgets(self):
        # Cyberpunk title with futuristic styling
        title_label = ctk.CTkLabel(
            self.root, 
            text="⚡ InSPyReNet AI Background Remover ⚡", 
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.cyber_accent
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(15, 25))

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            self.root,
            text="🔥 SUPERIOR AI BACKGROUND REMOVAL 🔥",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.cyber_secondary
        )
        subtitle_label.grid(row=0, column=0, columnspan=3, pady=(45, 0))

        # Input folders section with cyberpunk frame
        input_frame = ctk.CTkFrame(self.root, fg_color=self.cyber_frame, border_width=2, border_color=self.cyber_accent)
        input_frame.grid(row=1, column=0, columnspan=3, padx=20, pady=15, sticky="ew")
        
        ctk.CTkLabel(
            input_frame, 
            text="📁 INPUT FOLDERS QUEUE", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.cyber_accent
        ).pack(pady=(15, 8))
        
        # Folder list and controls with cyberpunk styling
        list_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        list_frame.pack(pady=8, padx=15, fill="both", expand=True)
        
        self.folder_listbox = ctk.CTkTextbox(
            list_frame, 
            height=100,
            font=ctk.CTkFont(size=11),
            border_width=1,
            border_color=self.cyber_secondary
        )
        self.folder_listbox.pack(pady=5, padx=5, fill="both", expand=True)
        
        button_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        button_frame.pack(pady=8, fill="x")
        
        ctk.CTkButton(
            button_frame, 
            text="➕ ADD FOLDERS", 
            command=self._add_input_folders,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.cyber_accent,
            text_color="black",
            hover_color="#00cc35"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame, 
            text="🗑️ CLEAR ALL", 
            command=self._clear_folders,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#ff3030",
            hover_color="#cc2020"
        ).pack(side="left", padx=5)
        
        # Output folder with cyberpunk styling
        output_frame = ctk.CTkFrame(self.root, fg_color=self.cyber_frame, border_width=2, border_color=self.cyber_secondary)
        output_frame.grid(row=2, column=0, columnspan=3, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(
            output_frame, 
            text="💾 OUTPUT FOLDER:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.cyber_secondary
        ).grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        ctk.CTkEntry(
            output_frame, 
            textvariable=self.output_folder, 
            width=500,
            font=ctk.CTkFont(size=11),
            border_width=1,
            border_color=self.cyber_accent
        ).grid(row=0, column=1, padx=10)
        
        ctk.CTkButton(
            output_frame, 
            text="🔍 BROWSE", 
            command=self._select_output_folder,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=self.cyber_secondary,
            hover_color="#0060cc"
        ).grid(row=0, column=2, padx=15)
        
        output_frame.columnconfigure(1, weight=1)

        # Settings frame with cyberpunk styling
        settings_frame = ctk.CTkFrame(self.root, fg_color=self.cyber_frame, border_width=2, border_color=self.cyber_accent)
        settings_frame.grid(row=3, column=0, columnspan=3, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(
            settings_frame, 
            text="⚙️ InSPyReNet AI SETTINGS", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.cyber_accent
        ).grid(row=0, column=0, columnspan=3, pady=(15, 10))
        
        # Threshold setting with cyber styling
        ctk.CTkLabel(
            settings_frame, 
            text="🎯 THRESHOLD:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.cyber_secondary
        ).grid(row=1, column=0, padx=15, pady=8, sticky="w")
        
        threshold_slider = ctk.CTkSlider(
            settings_frame, 
            from_=0.0, 
            to=1.0,
            variable=self.threshold, 
            number_of_steps=100,
            button_color=self.cyber_accent,
            progress_color=self.cyber_secondary
        )
        threshold_slider.grid(row=1, column=1, padx=10, pady=8, sticky="ew")
        
        self.threshold_label = ctk.CTkLabel(
            settings_frame, 
            text=f"{self.threshold.get():.2f}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.cyber_accent
        )
        self.threshold_label.grid(row=1, column=2, padx=15, pady=8)
        
        # Update threshold label when slider changes
        threshold_slider.configure(command=self._update_threshold_label)
        
        # JIT setting with cyber styling
        ctk.CTkCheckBox(
            settings_frame, 
            text="🚀 TorchScript JIT (slower startup, faster inference)",
            variable=self.use_jit,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.cyber_secondary,
            checkmark_color=self.cyber_accent
        ).grid(row=2, column=0, columnspan=3, padx=15, pady=8, sticky="w")
        
        # Preview setting
        ctk.CTkCheckBox(
            settings_frame, 
            text="👁️ Show Live Preview", 
            variable=self.show_preview,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.cyber_secondary,
            checkmark_color=self.cyber_accent
        ).grid(row=3, column=0, columnspan=3, padx=15, pady=(8, 15), sticky="w")
        
        settings_frame.columnconfigure(1, weight=1)

        # Action buttons with cyberpunk styling
        button_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        button_frame.grid(row=4, column=0, columnspan=3, pady=25)
        
        self.start_btn = ctk.CTkButton(
            button_frame, 
            text="🚀 START AI PROCESSING", 
            command=self.start_processing, 
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.cyber_accent,
            text_color="black",
            hover_color="#00cc35",
            height=50,
            width=200
        )
        self.start_btn.pack(side="left", padx=15)

        self.cancel_btn = ctk.CTkButton(
            button_frame, 
            text="⛔ CANCEL", 
            command=self.cancel_processing, 
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#ff3030",
            hover_color="#cc2020",
            height=50,
            width=120
        )
        self.cancel_btn.pack(side="left", padx=15)
        self.cancel_btn.configure(state="disabled")

        # Progress section with cyberpunk styling
        progress_frame = ctk.CTkFrame(self.root, fg_color=self.cyber_frame, border_width=2, border_color=self.cyber_secondary)
        progress_frame.grid(row=5, column=0, columnspan=3, padx=20, pady=15, sticky="ew")
        
        ctk.CTkLabel(
            progress_frame,
            text="📊 PROCESSING STATUS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.cyber_secondary
        ).pack(pady=(15, 5))
        
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame, 
            width=650, 
            height=25,
            progress_color=self.cyber_accent,
            border_width=1,
            border_color=self.cyber_secondary
        )
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            progress_frame, 
            text="⚡ READY FOR AI PROCESSING ⚡",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.cyber_accent
        )
        self.status_label.pack(pady=(5, 15))

        # Preview area with cyber styling
        preview_frame = ctk.CTkFrame(self.root, fg_color=self.cyber_frame, border_width=1, border_color=self.cyber_accent)
        preview_frame.grid(row=6, column=0, columnspan=3, padx=20, pady=10)
        
        ctk.CTkLabel(
            preview_frame,
            text="🖼️ LIVE PREVIEW",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.cyber_accent
        ).pack(pady=(10, 5))
        
        self.preview_label = ctk.CTkLabel(preview_frame, text="")
        self.preview_label.pack(pady=(0, 10))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1) 
        self.root.columnconfigure(2, weight=1)

    # ------------------ UI helpers ------------------
    def _add_input_folders(self):
        folders = filedialog.askdirectory(mustexist=True)
        if folders:  # Only single folder for now, but can be extended
            if folders not in self.input_folders:
                self.input_folders.append(folders)
                self._update_folder_display()
    
    def _clear_folders(self):
        self.input_folders.clear()
        self._update_folder_display()
    
    def _update_folder_display(self):
        self.folder_listbox.delete("1.0", "end")
        for i, folder in enumerate(self.input_folders, 1):
            folder_name = Path(folder).name
            self.folder_listbox.insert("end", f"{i}. {folder_name}\n    ({folder})\n\n")
    
    def _select_input_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            if folder not in self.input_folders:
                self.input_folders.append(folder)
                self._update_folder_display()

    def _select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)
    
    def _update_threshold_label(self, value):
        self.threshold_label.configure(text=f"{float(value):.2f}")

    def _set_status(self, text: str):
        self.status_label.configure(text=text)

    def _update_progress(self, idx: int, total: int, extra_info: str = ""):
        if total <= 0:
            self.progress_bar.set(0)
            return
        fraction = idx / total
        self.progress_bar.set(fraction)
        status_text = f"Processing: {idx}/{total}"
        if extra_info:
            status_text += f" - {extra_info}"
        self._set_status(status_text)
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
        if not self.input_folders:
            messagebox.showerror("Error", "Please add at least one input folder")
            return
        
        out_folder = self.output_folder.get().strip()
        if not out_folder:
            messagebox.showerror("Error", "Please select an output folder")
            return

        # Disable/enable buttons
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self._set_status("Initializing InSPyReNet...")
        self.progress_bar.set(0)

        # Create processor with current settings
        self.processor = ImageProcessor(
            use_jit=self.use_jit.get(),
            threshold=self.threshold.get()
        )

        # Create folder pairs (input -> output subfolders)
        folder_pairs = []
        for input_folder in self.input_folders:
            folder_name = Path(input_folder).name
            output_subfolder = Path(out_folder) / f"{folder_name}_cleaned"
            folder_pairs.append((Path(input_folder), output_subfolder))

        # Launch worker
        def worker():
            try:
                processed, total = self.processor.process_folder_queue(
                    folder_pairs,
                    progress_cb=lambda i, t, info: self.root.after(0, self._update_progress, i, t, info),
                    preview_cb=(lambda b: self._show_preview(b)) if self.show_preview.get() else None,
                    show_preview=self.show_preview.get(),
                )

                self.root.after(0, lambda: messagebox.showinfo("Done", 
                    f"Processed {processed}/{total} images from {len(folder_pairs)} folders."))
                self.root.after(0, lambda: self._set_status(f"Done: {processed}/{total} images processed"))

            except FileNotFoundError as fnf:
                logging.warning("%s", fnf)
                self.root.after(0, lambda: messagebox.showwarning("No Images", str(fnf)))
                self.root.after(0, lambda: self._set_status("No images found"))

            except Exception as e:
                logging.exception("Unexpected error during processing: %s", e)
                self.root.after(0, lambda: messagebox.showerror("Error", f"Processing failed: {str(e)}"))
                self.root.after(0, lambda: self._set_status("Error occurred"))

            finally:
                # Reset UI state
                self.root.after(0, lambda: self.start_btn.configure(state="normal"))
                self.root.after(0, lambda: self.cancel_btn.configure(state="disabled"))

        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()

    def cancel_processing(self):
        if self.processor:
            self.processor.cancel()
            self._set_status("Cancelling...")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = BatchBGRemoverApp()
    app.run()
