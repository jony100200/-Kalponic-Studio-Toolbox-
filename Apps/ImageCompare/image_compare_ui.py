from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox

from image_compare_core import compare_folders


class ImageCompareApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Image Folder Compare")
        self.geometry("820x620")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.source_folder = ctk.StringVar()
        self.target_folder = ctk.StringVar()
        self.done_score = ctk.StringVar(value="75")
        self.maybe_score = ctk.StringVar(value="50")

        self.create_ui()

    def create_ui(self):
        ctk.CTkLabel(
            self,
            text="Image Folder Compare",
            font=("Arial", 26, "bold")
        ).pack(pady=15)

        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=20, pady=10)

        self.add_folder_row(frame, "Source Folder", self.source_folder, self.browse_source)
        self.add_folder_row(frame, "Target / Finished Folder", self.target_folder, self.browse_target)

        settings = ctk.CTkFrame(self)
        settings.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(settings, text="Done Score").pack(anchor="w", padx=10, pady=(10, 0))
        ctk.CTkEntry(settings, textvariable=self.done_score).pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(settings, text="Maybe Score").pack(anchor="w", padx=10, pady=(10, 0))
        ctk.CTkEntry(settings, textvariable=self.maybe_score).pack(fill="x", padx=10, pady=(5, 10))

        self.run_button = ctk.CTkButton(
            self,
            text="RUN COMPARE",
            height=50,
            font=("Arial", 18, "bold"),
            command=self.run_compare
        )
        self.run_button.pack(fill="x", padx=20, pady=15)

        self.log_box = ctk.CTkTextbox(self, height=260)
        self.log_box.pack(fill="both", expand=True, padx=20, pady=10)

    def add_folder_row(self, parent, label, variable, command):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=10, pady=(10, 0))

        row = ctk.CTkFrame(parent)
        row.pack(fill="x", padx=10, pady=8)

        ctk.CTkEntry(row, textvariable=variable).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 10)
        )

        ctk.CTkButton(row, text="Browse", command=command).pack(side="right")

    def browse_source(self):
        folder = filedialog.askdirectory(title="Select Source Folder")
        if folder:
            self.source_folder.set(folder)

    def browse_target(self):
        folder = filedialog.askdirectory(title="Select Target / Finished Folder")
        if folder:
            self.target_folder.set(folder)

    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.update_idletasks()

    def run_compare(self):
        self.log_box.delete("1.0", "end")

        source = self.source_folder.get().strip()
        target = self.target_folder.get().strip()

        if not source:
            messagebox.showerror("Error", "Please select a source folder.")
            return

        if not target:
            messagebox.showerror("Error", "Please select a target / finished folder.")
            return

        if not Path(source).exists():
            messagebox.showerror("Error", "Source folder does not exist.")
            return

        if not Path(target).exists():
            messagebox.showerror("Error", "Target folder does not exist.")
            return

        try:
            done_threshold = float(self.done_score.get())
            maybe_threshold = float(self.maybe_score.get())
        except ValueError:
            messagebox.showerror("Error", "Scores must be numbers.")
            return

        self.run_button.configure(state="disabled", text="Running...")

        try:
            result = compare_folders(
                source_folder=source,
                target_folder=target,
                done_threshold=done_threshold,
                maybe_threshold=maybe_threshold,
                log_callback=self.log,
            )

            self.log("")
            self.log("Done.")
            self.log(f"Report saved: {result['report_path']}")

            messagebox.showinfo(
                "Done",
                f"Done: {result['done']}\n"
                f"Maybe: {result['maybe']}\n"
                f"Not Done: {result['not_done']}\n"
                f"Total: {result['total']}\n\n"
                f"Report saved:\n{result['report_path']}"
            )

        except Exception as error:
            messagebox.showerror("Error", str(error))

        finally:
            self.run_button.configure(state="normal", text="RUN COMPARE")


if __name__ == "__main__":
    app = ImageCompareApp()
    app.mainloop()