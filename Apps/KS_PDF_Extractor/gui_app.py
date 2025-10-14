#!/usr/bin/env python3
"""
KS PDF Extractor - GUI Interface
================================

Modern GUI interface for the KS PDF Extractor CLI tool.
Built with CustomTkinter for a professional appearance.

Features:
- File and directory browsing
- Format selection (txt/md)
- Batch processing support
- Real-time progress feedback
- Error handling and status updates
- Modern dark/light theme support
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
import subprocess
import threading
from pathlib import Path
from typing import Optional

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from core.pdf_processor import PDFExtractor
    from config.config_manager import ConfigManager
    CLI_AVAILABLE = True
except ImportError:
    CLI_AVAILABLE = False
    print("⚠️  CLI modules not available - running in standalone mode")

class KSPDFExtractorGUI(ctk.CTk):
    """
    Modern GUI interface for KS PDF Extractor
    """

    def __init__(self):
        super().__init__()

        # Configure window
        self.title("🔧 KS PDF Extractor v1.0")
        self.geometry("700x600")
        self.resizable(True, True)

        # Initialize variables
        self.input_path = ""
        self.output_path = ""
        self.is_processing = False
        self.config_manager = ConfigManager() if CLI_AVAILABLE else None

        # Create the GUI
        self.create_widgets()
        self.setup_layout()

        # Set appearance
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

    def create_widgets(self):
        """Create all GUI widgets"""

        # Header
        self.header_label = ctk.CTkLabel(
            self,
            text="📄 KS PDF Extractor",
            font=ctk.CTkFont(size=24, weight="bold")
        )

        self.subtitle_label = ctk.CTkLabel(
            self,
            text="Extract PDF content to Text or Markdown",
            font=ctk.CTkFont(size=12)
        )

        # Input section
        self.input_frame = ctk.CTkFrame(self)
        self.input_label = ctk.CTkLabel(
            self.input_frame,
            text="📁 Input PDF(s):",
            font=ctk.CTkFont(weight="bold")
        )

        self.input_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Select PDF file or directory...",
            width=400
        )

        self.browse_file_button = ctk.CTkButton(
            self.input_frame,
            text="📄 Browse File",
            command=self.browse_file,
            width=120
        )

        self.browse_dir_button = ctk.CTkButton(
            self.input_frame,
            text="📁 Browse Directory",
            command=self.browse_directory,
            width=120
        )

        # Output section
        self.output_frame = ctk.CTkFrame(self)
        self.output_label = ctk.CTkLabel(
            self.output_frame,
            text="💾 Output Settings:",
            font=ctk.CTkFont(weight="bold")
        )

        # Format selection
        self.format_label = ctk.CTkLabel(self.output_frame, text="Format:")
        self.format_var = ctk.StringVar(value="md")
        self.format_menu = ctk.CTkOptionMenu(
            self.output_frame,
            variable=self.format_var,
            values=["md", "txt"],
            width=100
        )

        # Output directory
        self.output_dir_label = ctk.CTkLabel(self.output_frame, text="Output Directory:")
        self.output_dir_entry = ctk.CTkEntry(
            self.output_frame,
            placeholder_text="Leave empty to use input directory...",
            width=300
        )

        self.browse_output_button = ctk.CTkButton(
            self.output_frame,
            text="📂 Browse",
            command=self.browse_output_dir,
            width=80
        )

        # Options
        self.options_frame = ctk.CTkFrame(self)
        self.options_label = ctk.CTkLabel(
            self.options_frame,
            text="⚙️ Options:",
            font=ctk.CTkFont(weight="bold")
        )

        # Batch processing checkbox
        self.batch_var = ctk.BooleanVar(value=False)
        self.batch_checkbox = ctk.CTkCheckBox(
            self.options_frame,
            text="Batch process directory",
            variable=self.batch_var,
            command=self.toggle_batch_mode
        )

        # Add statistics checkbox
        self.stats_var = ctk.BooleanVar(value=True)
        self.stats_checkbox = ctk.CTkCheckBox(
            self.options_frame,
            text="Include document statistics",
            variable=self.stats_var
        )

        # Control buttons
        self.control_frame = ctk.CTkFrame(self)
        self.extract_button = ctk.CTkButton(
            self.control_frame,
            text="🚀 Extract",
            command=self.start_extraction,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )

        self.stop_button = ctk.CTkButton(
            self.control_frame,
            text="⏹️ Stop",
            command=self.stop_extraction,
            height=40,
            state="disabled",
            fg_color="red"
        )

        # Progress section
        self.progress_frame = ctk.CTkFrame(self)
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="📊 Progress:",
            font=ctk.CTkFont(weight="bold")
        )

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=500,
            height=20
        )
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            self.progress_frame,
            text="Ready to extract PDFs...",
            wraplength=600
        )

        # Log section
        self.log_frame = ctk.CTkFrame(self)
        self.log_label = ctk.CTkLabel(
            self.log_frame,
            text="📝 Log:",
            font=ctk.CTkFont(weight="bold")
        )

        self.log_textbox = ctk.CTkTextbox(
            self.log_frame,
            wrap="word",
            height=150
        )
        self.log_textbox.insert("0.0", "Welcome to KS PDF Extractor GUI!\n")
        self.log_textbox.configure(state="disabled")

    def setup_layout(self):
        """Setup the layout of all widgets"""

        # Header
        self.header_label.pack(pady=(20, 5))
        self.subtitle_label.pack(pady=(0, 20))

        # Input section
        self.input_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.input_label.pack(anchor="w", padx=15, pady=(15, 5))
        self.input_entry.pack(side="left", padx=15, pady=(0, 10), expand=True, fill="x")
        self.browse_file_button.pack(side="left", padx=(0, 5), pady=(0, 10))
        self.browse_dir_button.pack(side="right", padx=15, pady=(0, 10))

        # Output section
        self.output_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.output_label.pack(anchor="w", padx=15, pady=(15, 5))

        # Format selection
        format_frame = ctk.CTkFrame(self.output_frame, fg_color="transparent")
        format_frame.pack(fill="x", padx=15, pady=(0, 10))
        self.format_label.pack(side="left")
        self.format_menu.pack(side="left", padx=(10, 0))

        # Output directory
        output_dir_frame = ctk.CTkFrame(self.output_frame, fg_color="transparent")
        output_dir_frame.pack(fill="x", padx=15, pady=(0, 15))
        self.output_dir_label.pack(anchor="w", pady=(0, 5))
        self.output_dir_entry.pack(side="left", expand=True, fill="x")
        self.browse_output_button.pack(side="right", padx=(10, 0))

        # Options section
        self.options_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.options_label.pack(anchor="w", padx=15, pady=(15, 10))
        self.batch_checkbox.pack(anchor="w", padx=15, pady=(0, 5))
        self.stats_checkbox.pack(anchor="w", padx=15, pady=(0, 15))

        # Control buttons
        self.control_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.extract_button.pack(side="left", padx=15, pady=15, expand=True)
        self.stop_button.pack(side="right", padx=15, pady=15, expand=True)

        # Progress section
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.progress_label.pack(anchor="w", padx=15, pady=(15, 5))
        self.progress_bar.pack(padx=15, pady=(0, 10))
        self.status_label.pack(padx=15, pady=(0, 15))

        # Log section
        self.log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.log_label.pack(anchor="w", padx=15, pady=(15, 5))
        self.log_textbox.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def browse_file(self):
        """Browse for a single PDF file"""
        file_path = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if file_path:
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, file_path)
            self.input_path = file_path
            self.log_message(f"Selected file: {Path(file_path).name}")

    def browse_directory(self):
        """Browse for a directory containing PDFs"""
        dir_path = filedialog.askdirectory(title="Select Directory with PDFs")
        if dir_path:
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, dir_path)
            self.input_path = dir_path
            self.batch_var.set(True)  # Auto-enable batch mode for directories
            self.log_message(f"Selected directory: {Path(dir_path).name}")

    def browse_output_dir(self):
        """Browse for output directory"""
        dir_path = filedialog.askdirectory(title="Select Output Directory")
        if dir_path:
            self.output_dir_entry.delete(0, "end")
            self.output_dir_entry.insert(0, dir_path)
            self.output_path = dir_path
            self.log_message(f"Output directory: {Path(dir_path).name}")

    def toggle_batch_mode(self):
        """Handle batch mode toggle"""
        if self.batch_var.get():
            self.log_message("Batch mode enabled - will process all PDFs in directory")
        else:
            self.log_message("Single file mode - will process only selected PDF")

    def log_message(self, message: str):
        """Add a message to the log"""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        self.update()

    def start_extraction(self):
        """Start the PDF extraction process"""
        if self.is_processing:
            return

        input_path = self.input_entry.get().strip()
        if not input_path:
            messagebox.showerror("Error", "Please select an input PDF file or directory")
            return

        if not os.path.exists(input_path):
            messagebox.showerror("Error", "Selected input path does not exist")
            return

        # Check if it's a directory and batch mode is enabled
        if os.path.isdir(input_path) and not self.batch_var.get():
            messagebox.showwarning(
                "Warning",
                "You selected a directory but batch mode is disabled.\n"
                "Enable batch mode to process all PDFs in the directory."
            )
            return

        # Check if it's a file and batch mode is enabled
        if os.path.isfile(input_path) and self.batch_var.get():
            messagebox.showwarning(
                "Warning",
                "You selected a file but batch mode is enabled.\n"
                "Disable batch mode to process a single file."
            )
            return

        # Start processing in a separate thread
        self.is_processing = True
        self.extract_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.progress_bar.set(0)
        self.status_label.configure(text="Starting extraction...")

        extraction_thread = threading.Thread(target=self.run_extraction)
        extraction_thread.daemon = True
        extraction_thread.start()

    def stop_extraction(self):
        """Stop the current extraction process"""
        if self.is_processing:
            self.is_processing = False
            self.log_message("🛑 Extraction stopped by user")
            self.status_label.configure(text="Extraction stopped")
            self.reset_ui()

    def run_extraction(self):
        """Run the extraction process in a separate thread"""
        try:
            input_path = self.input_entry.get().strip()
            output_format = self.format_var.get()
            output_dir = self.output_dir_entry.get().strip() or None
            is_batch = self.batch_var.get()

            self.log_message(f"🚀 Starting extraction...")
            self.log_message(f"Input: {input_path}")
            self.log_message(f"Format: {output_format}")
            self.log_message(f"Batch mode: {is_batch}")

            # Build command arguments
            cmd = [sys.executable, str(current_dir / "ks_pdf_extract.py")]
            cmd.extend(["--input", input_path])
            cmd.extend(["--format", output_format])

            if output_dir:
                cmd.extend(["--output", output_dir])

            if is_batch:
                cmd.append("--batch")

            # Run the CLI tool
            self.log_message(f"Running command: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(current_dir)
            )

            # Monitor progress
            while self.is_processing and process.poll() is None:
                # Check for output (this is a simple implementation)
                # In a real app, you'd want more sophisticated progress tracking
                self.update_progress(0.5)  # Placeholder progress
                self.after(100)  # Small delay to prevent UI freezing

            # Get results
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                self.log_message("✅ Extraction completed successfully!")
                self.status_label.configure(text="Extraction completed successfully!")
                self.update_progress(1.0)

                # Show success message
                self.after(0, lambda: messagebox.showinfo(
                    "Success",
                    "PDF extraction completed successfully!\n\n"
                    f"Check the output directory for the extracted files."
                ))
            else:
                error_msg = stderr.strip() or "Unknown error occurred"
                self.log_message(f"❌ Extraction failed: {error_msg}")
                self.status_label.configure(text="Extraction failed")

                self.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Extraction failed:\n\n{error_msg}"
                ))

        except Exception as e:
            error_msg = str(e)
            self.log_message(f"❌ Error: {error_msg}")
            self.status_label.configure(text="Error occurred")

            self.after(0, lambda: messagebox.showerror(
                "Error",
                f"An unexpected error occurred:\n\n{error_msg}"
            ))

        finally:
            self.reset_ui()

    def update_progress(self, value: float):
        """Update the progress bar"""
        self.progress_bar.set(value)
        self.update()

    def reset_ui(self):
        """Reset the UI to ready state"""
        self.is_processing = False
        self.extract_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.progress_bar.set(0)

def main():
    """Main entry point"""
    # Set appearance
    ctk.set_appearance_mode("system")  # Modes: "System", "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

    # Create and run the app
    app = KSPDFExtractorGUI()
    app.mainloop()

if __name__ == "__main__":
    main()