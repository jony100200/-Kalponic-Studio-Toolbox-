"""
Folder Comparison Tool
Compares two folders and finds matching files by base name.
Generates a matches.txt report with optional copy/move of selected matches.
"""

import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import List, Tuple, Dict
import customtkinter as ctk


# ──────────────────────────────────────────────
# Core Matching Logic (UI-independent)
# ──────────────────────────────────────────────

KNOWN_SUFFIXES = [
    "_basecolor", "_normal", "_roughness", "_ao", "_height", "_metallic",
    "_base_color", "_basecolour", "_normalmap", "_normal_map",
    "_roughnessmap", "_roughness_map", "_aomap", "_ao_map", "_heightmap",
    "_height_map", "_metallicmap", "_metallic_map", "_displacement",
    "_displacementmap", "_diffuse", "_diffusemap", "_specular", "_specularmap",
    "_emissive", "_emissivemap", "_opacity", "_opacitymap", "_mask",
    "_albedo", "_color", "_colour",
]


def normalize_filename(filename: str) -> str:
    """Normalize a filename by removing suffixes, extensions, normalizing spacing/case."""
    name = Path(filename).stem
    name = name.lower()

    changed = True
    while changed:
        changed = False
        for suffix in KNOWN_SUFFIXES:
            if name.endswith(suffix):
                name = name[: -len(suffix)]
                changed = True
                break

    name = name.replace("_", " ").replace("-", " ")
    name = re.sub(r"\s+", " ", name).strip()
    return name


def collect_files(folder_path: str) -> Dict[str, str]:
    """Collect all files recursively from a folder. Returns {normalized_name: full_path}."""
    files = {}
    folder = Path(folder_path)
    if not folder.exists():
        return files

    for file_path in folder.rglob("*"):
        if file_path.is_file():
            normalized = normalize_filename(file_path.name)
            if normalized and normalized not in files:
                files[normalized] = str(file_path)
    return files


def find_matches(folder_a: str, folder_b: str) -> List[Tuple[str, str, str]]:
    """Find matching files between two folders. Returns [(cleaned_name, path_a, path_b)]."""
    files_a = collect_files(folder_a)
    files_b = collect_files(folder_b)
    common_names = set(files_a.keys()) & set(files_b.keys())
    return [(name, files_a[name], files_b[name]) for name in sorted(common_names)]


def write_matches(matches: List[Tuple[str, str, str]], output_file: str) -> None:
    """Write matches to a text file."""
    with open(output_file, "w", encoding="utf-8") as f:
        for cleaned_name, path_a, path_b in matches:
            f.write(f"{cleaned_name} | {path_a} | {path_b}\n")


def _resolve_dest_path(dest_folder: str, source_path: str) -> Path:
    """
    Resolve destination path, avoiding overwrites by appending _1, _2, etc.
    """
    dest = Path(dest_folder) / Path(source_path).name
    if not dest.exists():
        return dest
    stem = Path(source_path).stem
    suffix = Path(source_path).suffix
    counter = 1
    while True:
        dest = Path(dest_folder) / f"{stem}_{counter}{suffix}"
        if not dest.exists():
            return dest
        counter += 1


def transfer_folder_a_files(
    matches: List[Tuple[str, str, str]],
    dest_folder: str,
    action: str = "copy",
) -> Tuple[int, List[str], List[str]]:
    """
    Copy or move only Folder A files into the destination folder.
    - Creates dest_folder if it does not exist.
    - Keeps original filename.
    - Renames on conflict (file_1.ext, file_2.ext, ...).
    Returns (files_transferred, copied_names, error_messages).
    """
    dest_path = Path(dest_folder)
    dest_path.mkdir(parents=True, exist_ok=True)

    transfer_func = shutil.move if action == "move" else shutil.copy2
    count = 0
    copied_names = []
    errors = []

    for _, path_a, _ in matches:
        try:
            dest = _resolve_dest_path(dest_folder, path_a)
            transfer_func(path_a, dest)
            count += 1
            copied_names.append(dest.name)
        except Exception as e:
            errors.append(f"Failed {action} {Path(path_a).name}: {e}")

    return count, copied_names, errors


# ──────────────────────────────────────────────
# UI Logic
# ──────────────────────────────────────────────


class MatchCheckboxFrame(ctk.CTkScrollableFrame):
    """Scrollable frame showing checkboxes for each match."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.check_vars: Dict[int, tk.BooleanVar] = {}
        self._widgets = []

    def clear(self):
        for w in self._widgets:
            w.destroy()
        self._widgets.clear()
        self.check_vars.clear()

    def load_matches(self, matches: List[Tuple[str, str, str]]):
        """Populate the frame with checkboxes for each match."""
        self.clear()

        # Header row
        header = ctk.CTkLabel(
            self, text="Select matches to copy/move:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        header.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 5))

        # Column headers
        for col, text in enumerate(["Select", "Base Name", "Folder A", "Folder B"]):
            lbl = ctk.CTkLabel(
                self, text=text, font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#888888"
            )
            lbl.grid(row=1, column=col, padx=5, sticky="w")

        # Match rows
        for i, (name, path_a, path_b) in enumerate(matches):
            row = i + 2

            var = tk.BooleanVar(value=True)  # default checked
            self.check_vars[i] = var
            cb = ctk.CTkCheckBox(self, text="", variable=var, width=30, checkbox_width=20, checkbox_height=20)
            cb.grid(row=row, column=0, sticky="w", padx=(5, 2), pady=2)

            name_lbl = ctk.CTkLabel(self, text=name, anchor="w", font=ctk.CTkFont(size=11))
            name_lbl.grid(row=row, column=1, sticky="w", padx=5, pady=2)

            path_a_lbl = ctk.CTkLabel(
                self, text=Path(path_a).name, anchor="w",
                font=ctk.CTkFont(size=10), text_color="#999999",
                wraplength=200
            )
            path_a_lbl.grid(row=row, column=2, sticky="w", padx=5, pady=2)

            path_b_lbl = ctk.CTkLabel(
                self, text=Path(path_b).name, anchor="w",
                font=ctk.CTkFont(size=10), text_color="#999999",
                wraplength=200
            )
            path_b_lbl.grid(row=row, column=3, sticky="w", padx=5, pady=2)

        # Column weights
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)

    def get_selected(self) -> List[int]:
        """Return indices of checked matches."""
        return [i for i, var in self.check_vars.items() if var.get()]

    def select_all(self):
        for var in self.check_vars.values():
            var.set(True)

    def deselect_all(self):
        for var in self.check_vars.values():
            var.set(False)


class FolderCompareApp:
    """Main application window for folder comparison tool."""

    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Folder Comparison Tool")
        self.root.geometry("950x700")
        self.root.minsize(800, 600)

        # State
        self.folder_a = tk.StringVar()
        self.folder_b = tk.StringVar()
        self.output_file = tk.StringVar(value="matches.txt")
        self.transfer_enabled = tk.BooleanVar(value=False)
        self.transfer_action = tk.StringVar(value="copy")  # "copy" or "move"
        self.dest_folder = tk.StringVar()

        # Current matches cache
        self.current_matches: List[Tuple[str, str, str]] = []

        self._build_ui()

    def _build_ui(self):
        """Build the complete UI."""
        main = ctk.CTkFrame(self.root, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=15)

        # Title
        ctk.CTkLabel(
            main, text="Folder Comparison Tool",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(0, 12))

        # Folder pickers
        self._build_folder_picker(main, "Folder A:", self.folder_a)
        self._build_folder_picker(main, "Folder B:", self.folder_b)

        # Output file picker
        self._build_output_picker(main)

        # Transfer options (copy/move)
        self._build_transfer_options(main)

        # Compare button
        self.compare_btn = ctk.CTkButton(
            main, text="Compare Folders", command=self._run_comparison,
            font=ctk.CTkFont(size=14, weight="bold"), height=40,
        )
        self.compare_btn.pack(pady=10, fill="x")

        # Status label
        self.status_label = ctk.CTkLabel(
            main, text="Ready", font=ctk.CTkFont(size=12), text_color="gray"
        )
        self.status_label.pack(pady=(4, 8))

        # Results area (checkboxes + apply button)
        self._build_results_area(main)

    def _build_folder_picker(self, parent, label, var):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=3)

        ctk.CTkLabel(frame, text=label, width=80, anchor="w").pack(side="left", padx=(0, 5))
        ctk.CTkEntry(frame, textvariable=var, placeholder_text="Select folder...").pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(frame, text="Browse", width=80, command=lambda: self._pick_folder(var)).pack(side="left", padx=(5, 0))

    def _build_output_picker(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=3)

        ctk.CTkLabel(frame, text="Output:", width=80, anchor="w").pack(side="left", padx=(0, 5))
        ctk.CTkEntry(frame, textvariable=self.output_file, placeholder_text="matches.txt").pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(frame, text="Browse", width=80, command=self._pick_output_file).pack(side="left", padx=(5, 0))

    def _build_transfer_options(self, parent):
        """Checkbox to enable transfer + Copy/Move radio + destination picker."""
        # Enable row
        row1 = ctk.CTkFrame(parent, fg_color="transparent")
        row1.pack(fill="x", pady=(6, 2))

        ctk.CTkCheckBox(
            row1, text="Copy / Move matched files",
            variable=self.transfer_enabled, command=self._toggle_transfer_ui
        ).pack(side="left")

        # Action radio + destination (in a sub-frame that gets enabled/disabled)
        self.transfer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.transfer_frame.pack(fill="x", pady=2)

        # Copy / Move radios
        radio_frame = ctk.CTkFrame(self.transfer_frame, fg_color="transparent")
        radio_frame.pack(side="left", fill="x", padx=(0, 15))

        ctk.CTkLabel(radio_frame, text="Action:", width=50, anchor="w").pack(side="left", padx=(0, 5))

        ctk.CTkRadioButton(
            radio_frame, text="Copy", variable=self.transfer_action, value="copy"
        ).pack(side="left", padx=5)
        ctk.CTkRadioButton(
            radio_frame, text="Move", variable=self.transfer_action, value="move"
        ).pack(side="left", padx=5)

        # Destination folder
        dest_frame = ctk.CTkFrame(self.transfer_frame, fg_color="transparent")
        dest_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(dest_frame, text="To:", width=30, anchor="w").pack(side="left", padx=(0, 5))
        ctk.CTkEntry(dest_frame, textvariable=self.dest_folder, placeholder_text="Destination folder...").pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(dest_frame, text="Browse", width=80, command=lambda: self._pick_folder(self.dest_folder)).pack(side="left")

        # Initially disabled
        self._toggle_transfer_ui()

    def _toggle_transfer_ui(self):
        """Enable/disable transfer sub-controls."""
        enabled = self.transfer_enabled.get()
        state = "normal" if enabled else "disabled"
        text_color = "white" if enabled else "gray50"
        for child in self.transfer_frame.winfo_children():
            for w in child.winfo_children():
                try:
                    w.configure(state=state)
                except Exception:
                    pass
                try:
                    w.configure(text_color=text_color)
                except Exception:
                    pass

    def _build_results_area(self, parent):
        """Scrollable checkbox list of matches + Select All/Deselect All + Apply button."""
        area = ctk.CTkFrame(parent, fg_color="transparent")
        area.pack(fill="both", expand=True, pady=(8, 0))

        # Buttons row
        btn_row = ctk.CTkFrame(area, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            btn_row, text="Matches:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left")

        self.select_all_btn = ctk.CTkButton(btn_row, text="Select All", width=90, command=self._select_all)
        self.select_all_btn.pack(side="right", padx=4)

        self.deselect_all_btn = ctk.CTkButton(btn_row, text="Deselect All", width=100, command=self._deselect_all)
        self.deselect_all_btn.pack(side="right", padx=4)

        self.apply_btn = ctk.CTkButton(
            btn_row, text="Apply to Selected", width=140,
            fg_color="#2b7de9", command=self._apply_selected,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.apply_btn.pack(side="right", padx=4)

        # Scrollable match list
        self.match_frame = MatchCheckboxFrame(area, label_text="")
        self.match_frame.pack(fill="both", expand=True)

    # ── Dialog Helpers ──

    def _pick_folder(self, var: tk.StringVar):
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            var.set(folder)

    def _pick_output_file(self):
        fp = filedialog.asksaveasfilename(
            title="Save Matches Report As",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfilename="matches.txt",
        )
        if fp:
            self.output_file.set(fp)

    # ── Selection helpers ──

    def _select_all(self):
        self.match_frame.select_all()

    def _deselect_all(self):
        self.match_frame.deselect_all()

    # ── Core Action ──

    def _run_comparison(self):
        folder_a = self.folder_a.get().strip()
        folder_b = self.folder_b.get().strip()
        output_file = self.output_file.get().strip()

        if not folder_a or not folder_b:
            messagebox.showerror("Error", "Please select both Folder A and Folder B.")
            return
        if not os.path.isdir(folder_a):
            messagebox.showerror("Error", f"Folder A does not exist:\n{folder_a}")
            return
        if not os.path.isdir(folder_b):
            messagebox.showerror("Error", f"Folder B does not exist:\n{folder_b}")
            return
        if not output_file:
            messagebox.showerror("Error", "Please specify an output file.")
            return

        self.status_label.configure(text="Comparing...", text_color="yellow")
        self.compare_btn.configure(state="disabled")
        self.apply_btn.configure(state="disabled")
        self.root.update_idletasks()

        try:
            self.current_matches = find_matches(folder_a, folder_b)
            write_matches(self.current_matches, output_file)

            if self.current_matches:
                self.match_frame.load_matches(self.current_matches)
                self.status_label.configure(
                    text=f"Found {len(self.current_matches)} match(es). Report → {output_file}  |  Select matches above and click 'Apply'.",
                    text_color="green"
                )
                self.apply_btn.configure(state="normal")
            else:
                self.match_frame.clear()
                self.status_label.configure(text="No matches found.", text_color="orange")
                messagebox.showinfo("Info", "No matching files found between the two folders.")

        except Exception as e:
            self.status_label.configure(text=f"Error: {e}", text_color="red")
            messagebox.showerror("Error", f"An error occurred:\n{e}")
        finally:
            self.compare_btn.configure(state="normal")

    def _apply_selected(self):
        if not self.current_matches:
            return

        if not self.transfer_enabled.get():
            messagebox.showwarning("Warning", "Enable the Copy/Move option first.")
            return

        dest = self.dest_folder.get().strip()
        if not dest:
            messagebox.showerror("Error", "Please select a destination folder.")
            return
        if not os.path.isdir(dest):
            messagebox.showerror("Error", f"Destination folder does not exist:\n{dest}")
            return

        selected_indices = self.match_frame.get_selected()
        if not selected_indices:
            messagebox.showwarning("Warning", "No matches selected.")
            return

        selected_matches = [self.current_matches[i] for i in sorted(selected_indices)]
        action = self.transfer_action.get()  # "copy" or "move"
        verb = "Copying" if action == "copy" else "Moving"

        self.status_label.configure(text=f"{verb} {len(selected_matches)} match(es)...", text_color="yellow")
        self.apply_btn.configure(state="disabled")
        self.root.update_idletasks()

        try:
            count, copied_names, errors = transfer_folder_a_files(
                selected_matches, dest, action
            )

            # Update status
            if errors:
                err_summary = "\n".join(errors[:10])
                if len(errors) > 10:
                    err_summary += f"\n... and {len(errors) - 10} more errors"
                messagebox.showwarning(
                    "Partial Success",
                    f"{count} file(s) {action}ied.\n\nErrors:\n{err_summary}"
                )
                self.status_label.configure(
                    text=f"{count}/{len(selected_matches)} file(s) {action}ied to {dest} ({len(errors)} error(s))",
                    text_color="orange"
                )
            else:
                self.status_label.configure(
                    text=f"{count} file(s) {action}ied to {dest}",
                    text_color="green"
                )

            # Remove transferred entries from match list
            self.current_matches = [
                m for i, m in enumerate(self.current_matches)
                if i not in selected_indices
            ]

            if self.current_matches:
                self.match_frame.load_matches(self.current_matches)
            else:
                self.match_frame.clear()

        except Exception as e:
            self.status_label.configure(text=f"Error: {e}", text_color="red")
            messagebox.showerror("Error", str(e))
        finally:
            self.apply_btn.configure(state="normal")

    def run(self):
        self.root.mainloop()


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    app = FolderCompareApp()
    app.run()
