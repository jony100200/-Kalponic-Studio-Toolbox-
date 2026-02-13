import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel, Canvas
import pyautogui
from PIL import Image
from datetime import datetime
from pathlib import Path
import logging

# screeninfo is optional; use if available
try:
    from screeninfo import get_monitors
except Exception:
    get_monitors = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# === Setup ===
# Note: this module provides a reusable `select_region` function for area selection which
# can be called by `capture.capture_area()` to receive an (left, top, right, bottom) tuple.

# Keep CTk demo UI variables for legacy demo usage, but do not run the app on import.
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Demo UI state (only created when run as a script, not on import)
# Avoid creating CTk widgets at import time so this module is safe to import.
counter = 1  # For sequential naming (used by demo only)

# Retrieve monitor information (use get_monitors if available; fallback to primary screen)
try:
    monitors = get_monitors()
except Exception:
    # fallback: create a single monitor using tkinter screen size
    import tkinter as _tk
    _r = _tk.Tk()
    w = _r.winfo_screenwidth()
    h = _r.winfo_screenheight()
    _r.destroy()
    class _M:
        pass
    m = _M()
    m.x = 0
    m.y = 0
    m.width = w
    m.height = h
    monitors = [m]
monitor_options = [f"Monitor {i+1}" for i in range(len(monitors))]
# Avoid creating tkinter variables at import time; use plain default
selected_monitor = monitor_options[0] if monitor_options else "Monitor 1"


# === Reusable overlay function (non-CTk) ===
import tkinter as tk


def select_region(monitor_index: int = 0):
    """Show a transparent overlay on the requested monitor and let the user select a rectangle.

    Returns an (left, top, right, bottom) tuple in absolute screen coordinates, or None if cancelled.
    """
    try:
        m = monitors[monitor_index]
    except Exception:
        # Fallback to primary monitor
        m = monitors[0]

    root = tk.Tk()
    root.overrideredirect(True)
    root.geometry(f"{m.width}x{m.height}+{m.x}+{m.y}")
    root.attributes("-topmost", True)
    # semi-transparent overlay
    root.attributes("-alpha", 0.25)
    root.config(cursor="cross")

    canvas = tk.Canvas(root, bg="black")
    canvas.pack(fill="both", expand=True)

    start_x = start_y = None
    rect = None
    result = {"coords": None}

    def on_mouse_down(event):
        nonlocal start_x, start_y, rect
        start_x, start_y = event.x, event.y
        rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline='red', width=2)

    def on_mouse_drag(event):
        if rect is not None:
            canvas.coords(rect, start_x, start_y, event.x, event.y)

    def on_mouse_up(event):
        nonlocal rect
        if rect is None:
            root.destroy()
            return
        x1, y1 = canvas.coords(rect)[0:2]
        x2, y2 = event.x, event.y
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        left = int(m.x + x1)
        top = int(m.y + y1)
        right = int(m.x + x2)
        bottom = int(m.y + y2)
        result['coords'] = (left, top, right, bottom)
        root.destroy()

    def on_escape(event=None):
        root.destroy()

    canvas.bind("<Button-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_drag)
    canvas.bind("<ButtonRelease-1>", on_mouse_up)
    root.bind("<Escape>", on_escape)

    # Run modal loop
    root.mainloop()

    return result['coords']


# === Window click-to-select ===

def select_window(monitor_index: int = 0):
    """Allow the user to click a window to select it. Returns (left, top, right, bottom) or None if cancelled."""
    try:
        m = monitors[monitor_index]
    except Exception:
        m = monitors[0]

    # If win32 is not available, fallback to select_region
    try:
        import win32gui
        import win32con
    except Exception:
        return select_region(monitor_index=monitor_index)

    root = tk.Tk()
    root.overrideredirect(True)
    root.geometry(f"{m.width}x{m.height}+{m.x}+{m.y}")
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.0)
    root.config(cursor="cross")

    canvas = tk.Canvas(root, bg="", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    highlight = None
    result = {"coords": None}

    def draw_highlight(rect_coords):
        nonlocal highlight
        # rect_coords is (l,t,r,b) in screen coords
        l, t, r, b = rect_coords
        # convert to canvas coordinates
        x1 = l - m.x
        y1 = t - m.y
        x2 = r - m.x
        y2 = b - m.y
        if highlight is None:
            highlight = canvas.create_rectangle(x1, y1, x2, y2, outline='cyan', width=3)
        else:
            canvas.coords(highlight, x1, y1, x2, y2)

    def on_motion(event):
        try:
            # get absolute screen coordinates
            sx = root.winfo_pointerx()
            sy = root.winfo_pointery()
            hwnd = win32gui.WindowFromPoint((sx, sy))
            if not hwnd:
                return
            # get top-level ancestor
            try:
                anc = win32gui.GetAncestor(hwnd, win32con.GA_ROOTOWNER)
            except Exception:
                anc = hwnd
            rect = win32gui.GetWindowRect(anc)
            left, top, right, bottom = rect
            # ensure rect intersects monitor
            if right < m.x or left > (m.x + m.width) or bottom < m.y or top > (m.y + m.height):
                return
            draw_highlight((left, top, right, bottom))
        except Exception:
            pass

    def on_click(event):
        try:
            sx = root.winfo_pointerx()
            sy = root.winfo_pointery()
            hwnd = win32gui.WindowFromPoint((sx, sy))
            if not hwnd:
                root.destroy()
                return
            try:
                anc = win32gui.GetAncestor(hwnd, win32con.GA_ROOTOWNER)
            except Exception:
                anc = hwnd
            rect = win32gui.GetWindowRect(anc)
            left, top, right, bottom = rect
            result['coords'] = (left, top, right, bottom)
        except Exception:
            result['coords'] = None
        finally:
            root.destroy()

    def on_escape(event=None):
        root.destroy()

    canvas.bind("<Motion>", on_motion)
    canvas.bind("<Button-1>", on_click)
    root.bind("<Escape>", on_escape)

    root.mainloop()

    return result['coords']



# Legacy demo GUI removed from import-time behavior. If you want to run a demo GUI for manual testing,
# run this module directly (python area_overlay.py) which will launch a small demo UI.


def _demo_main():
    # Lightweight demo UI showing how area overlay can be used; kept behind a main guard.
    demo_app = ctk.CTk()
    demo_app.title("KS SnapClip Area Overlay Demo")
    demo_app.geometry("640x200")

    def on_demo():
        reg = select_region()
        tk.messagebox.showinfo("Selected", str(reg))

    ctk.CTkButton(demo_app, text="Select Area", command=on_demo).pack(pady=30)
    demo_app.mainloop()


if __name__ == "__main__":
    _demo_main()

