import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel, Canvas
import pyautogui
from PIL import Image
from datetime import datetime
from pathlib import Path
import logging
from screeninfo import get_monitors

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# === Setup ===
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Custom Area Screenshot Saver")
app.geometry("700x400")

input_folder = ctk.StringVar()
output_folder = ctk.StringVar()
prefix = ctk.StringVar()
suffix = ctk.StringVar()
use_timestamp = ctk.BooleanVar(value=True)

counter = 1  # For sequential naming

# Retrieve monitor information
monitors = get_monitors()
monitor_options = [f"Monitor {i+1}" for i in range(len(monitors))]
selected_monitor = ctk.StringVar(value=monitor_options[0])

# === Folder Select ===
def select_input_folder():
    folder = filedialog.askdirectory(title="Select Input Folder")
    if folder:
        input_folder.set(folder)

def select_output_folder():
    folder = filedialog.askdirectory(title="Select Output Folder")
    if folder:
        output_folder.set(folder)

def validate_folders():
    if not output_folder.get():
        messagebox.showerror("Error", "Output folder is not selected.")
        return False
    return True

# === Screenshot Tool ===
def take_custom_screenshot():
    global counter
    if not validate_folders():
        return

    out_path = Path(output_folder.get())

    if not out_path.exists():
        messagebox.showerror("Error", "Please select a valid output folder.")
        return

    folder_name = Path(input_folder.get()).name if input_folder.get() else ""

    # Get selected monitor dimensions
    monitor_index = monitor_options.index(selected_monitor.get())
    monitor = monitors[monitor_index]

    # Hide app
    app.withdraw()

    # Transparent fullscreen overlay
    root = Toplevel()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.3)
    root.config(cursor="cross")
    canvas = Canvas(root, bg="black")
    canvas.pack(fill="both", expand=True)

    start_x = start_y = rect = None

    def on_mouse_down(event):
        nonlocal start_x, start_y, rect
        start_x, start_y = event.x, event.y
        rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline='red', width=2)

    def on_mouse_drag(event):
        canvas.coords(rect, start_x, start_y, event.x, event.y)

    def on_mouse_up(event):
        x1, y1 = canvas.coords(rect)[0:2]
        x2, y2 = event.x, event.y
        root.destroy()

        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])

        try:
            screenshot = pyautogui.screenshot(region=(monitor.x, monitor.y, monitor.width, monitor.height))
            cropped = screenshot.crop((x1, y1, x2, y2))

            if use_timestamp.get():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{prefix.get()}{folder_name}{suffix.get()}_{timestamp}.png"
            else:
                filename = f"{prefix.get()}{folder_name}{suffix.get()}_{counter:03}.png"
                counter += 1

            cropped.save(out_path / filename)
            logging.info(f"Screenshot saved as: {filename}")
            messagebox.showinfo("Saved", f"Screenshot saved as:\n{filename}")
        except Exception as e:
            logging.error(f"Error saving screenshot: {e}")
            messagebox.showerror("Error", f"An error occurred while saving the screenshot: {e}")
        finally:
            app.deiconify()

    def exit_screenshot_mode(event):
        root.destroy()
        app.deiconify()

    canvas.bind("<Button-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_drag)
    canvas.bind("<ButtonRelease-1>", on_mouse_up)
    root.bind("<Escape>", exit_screenshot_mode)  # Bind Escape key to exit

    root.mainloop()

# === GUI Layout ===
ctk.CTkLabel(app, text="Input Folder (for name):").grid(row=0, column=0, padx=10, pady=10, sticky="e")
ctk.CTkEntry(app, textvariable=input_folder, width=400).grid(row=0, column=1, padx=10)
ctk.CTkButton(app, text="Browse", command=select_input_folder).grid(row=0, column=2)

ctk.CTkLabel(app, text="Output Folder (save to):").grid(row=1, column=0, padx=10, pady=10, sticky="e")
ctk.CTkEntry(app, textvariable=output_folder, width=400).grid(row=1, column=1, padx=10)
ctk.CTkButton(app, text="Browse", command=select_output_folder).grid(row=1, column=2)

ctk.CTkLabel(app, text="Filename Prefix:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
ctk.CTkEntry(app, textvariable=prefix, width=200).grid(row=2, column=1, sticky="w")

ctk.CTkLabel(app, text="Filename Suffix:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
ctk.CTkEntry(app, textvariable=suffix, width=200).grid(row=3, column=1, sticky="w")

ctk.CTkCheckBox(app, text="Use Timestamp in Filename", variable=use_timestamp).grid(row=4, column=1, pady=5)

ctk.CTkLabel(app, text="Select Monitor:").grid(row=6, column=0, padx=10, pady=10, sticky="e")
ctk.CTkOptionMenu(app, variable=selected_monitor, values=monitor_options).grid(row=6, column=1, padx=10)

ctk.CTkButton(app, text="📸 Take Custom Area Screenshot", command=take_custom_screenshot, fg_color="green").grid(row=5, column=1, pady=20)

app.mainloop()
