"""Simple UI prototype for KS SnapClip (CustomTkinter)

MVP: Capture fullscreen (area capture placeholder), show last thumbnail, Copy/Save buttons.
"""

import os
import tkinter as tk
import customtkinter as ctk
from PIL import ImageTk
from capture import capture_fullscreen, capture_area
from store import CaptureStore
from clipboard_win import default_provider


store = CaptureStore(max_items=20)


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    app = ctk.CTk()
    app.title("KS SnapClip")
    app.geometry("800x480")

    # Load settings
    from settings import load_settings, save_settings
    from clipboard_win import default_provider
    from utils import generate_filename

    settings = load_settings()
    # start minimized to tray option
    start_minimized = settings.start_minimized
    start_in_tray = start_minimized
    # hotkeys
    hotkeys_enabled = settings.hotkeys_enabled
    hotkey_area = settings.hotkey_area
    hotkey_window = settings.hotkey_window
    hotkey_monitor = settings.hotkey_monitor

    # Right preview
    right = ctk.CTkFrame(app)
    right.pack(side="left", fill="both", expand=True, padx=12, pady=12)

    lbl = ctk.CTkLabel(right, text="No captures yet", corner_radius=6)
    lbl.pack(fill="both", expand=True)

    # History frame (below preview)
    history_frame = ctk.CTkFrame(right)
    history_frame.pack(side="bottom", fill="x", pady=(8,0))

    # Left controls
    left = ctk.CTkFrame(app)
    left.pack(side="left", fill="y", padx=12, pady=12)

    # Output folder
    app._ast_widgets = {"preview_label": lbl, "last_image_tk": None, "history_frame": history_frame, "selected_index": None, "thumb_refs": []}

    def select_output_folder(app):
        p = tk.filedialog.askdirectory(title="Select Output Folder")
        if not p:
            return
        app._ast_widgets["output_folder_var"].set(p)
        settings.output_folder = p
        save_settings(settings)

    app._ast_widgets["output_folder_var"] = ctk.StringVar(value=settings.output_folder)
    ctk.CTkLabel(left, text="Output Folder (save to):").grid(row=0, column=0, padx=10, pady=10, sticky="e")
    ctk.CTkEntry(left, textvariable=app._ast_widgets["output_folder_var"], width=300).grid(row=0, column=1, padx=10)
    ctk.CTkButton(left, text="Browse", command=lambda: select_output_folder(app)).grid(row=0, column=2)

    # filename prefix & pattern preview
    ctk.CTkLabel(left, text="Filename prefix:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
    app._ast_widgets["prefix_var"] = ctk.StringVar(value=settings.filename_prefix)
    ctk.CTkEntry(left, textvariable=app._ast_widgets["prefix_var"], width=200).grid(row=1, column=1, sticky="w")

    app._ast_widgets["autosave_var"] = ctk.BooleanVar(value=settings.auto_save)
    autosave_cb = ctk.CTkCheckBox(left, text="Auto-save captures to output folder", variable=app._ast_widgets["autosave_var"])
    autosave_cb.grid(row=2, column=1, pady=5, sticky="w")

    app._ast_widgets["autocopy_var"] = ctk.BooleanVar(value=settings.auto_copy)
    autocopy_cb = ctk.CTkCheckBox(left, text="Auto-copy to clipboard after capture", variable=app._ast_widgets["autocopy_var"])
    autocopy_cb.grid(row=3, column=1, pady=5, sticky="w")

    # advanced legacy option (hidden by default)
    app._ast_widgets["legacy_var"] = ctk.BooleanVar(value=settings.use_legacy_input_folder)
    legacy_cb = ctk.CTkCheckBox(left, text="Use legacy input-folder for naming (advanced)", variable=app._ast_widgets["legacy_var"]) 
    legacy_cb.grid(row=4, column=1, pady=5, sticky="w")

    # Start minimized / tray and hotkeys
    app._ast_widgets["start_min_var"] = ctk.BooleanVar(value=settings.start_minimized)
    start_min_cb = ctk.CTkCheckBox(left, text="Start minimized to tray", variable=app._ast_widgets["start_min_var"]) 
    start_min_cb.grid(row=5, column=1, pady=5, sticky="w")

    app._ast_widgets["hotkeys_enabled_var"] = ctk.BooleanVar(value=settings.hotkeys_enabled)
    hotkey_cb = ctk.CTkCheckBox(left, text="Enable global hotkeys (opt-in)", variable=app._ast_widgets["hotkeys_enabled_var"]) 
    hotkey_cb.grid(row=6, column=1, pady=5, sticky="w")

    # callbacks to persist settings when changed
    def on_setting_change(*_):
        settings.output_folder = app._ast_widgets["output_folder_var"].get()
        settings.filename_prefix = app._ast_widgets["prefix_var"].get()
        settings.auto_save = app._ast_widgets["autosave_var"].get()
        settings.auto_copy = app._ast_widgets["autocopy_var"].get()
        settings.use_legacy_input_folder = app._ast_widgets["legacy_var"].get()
        settings.start_minimized = app._ast_widgets["start_min_var"].get()
        settings.hotkeys_enabled = app._ast_widgets["hotkeys_enabled_var"].get()
        from settings import save_settings
        save_settings(settings)

    # attach traces
    app._ast_widgets["output_folder_var"].trace_add("write", lambda *_: on_setting_change())
    app._ast_widgets["prefix_var"].trace_add("write", lambda *_: on_setting_change())
    app._ast_widgets["autosave_var"].trace_add("write", lambda *_: on_setting_change())
    app._ast_widgets["autocopy_var"].trace_add("write", lambda *_: on_setting_change())
    app._ast_widgets["legacy_var"].trace_add("write", lambda *_: on_setting_change())
    app._ast_widgets["start_min_var"].trace_add("write", lambda *_: on_setting_change())
    app._ast_widgets["hotkeys_enabled_var"].trace_add("write", lambda *_: on_setting_change())

    btn_full = ctk.CTkButton(left, text="Capture Fullscreen", command=lambda: do_capture(app))
    btn_full.grid(row=6, column=0, columnspan=2, pady=6)

    btn_area = ctk.CTkButton(left, text="Capture Area (overlay)", command=lambda: do_capture(app, area=True))
    btn_area.grid(row=7, column=0, columnspan=2, pady=6)

    btn_copy = ctk.CTkButton(left, text="Copy Selected", command=lambda: do_copy(app))
    btn_copy.grid(row=8, column=0, columnspan=2, pady=6)

    btn_save = ctk.CTkButton(left, text="Save Selected", command=lambda: do_save(app))
    btn_save.grid(row=9, column=0, columnspan=2, pady=6)

    # populate initial history
    rebuild_history(app)

    # start tray if configured (deferred until settings applied)
    tray = None

    # manage hotkey & tray lifecycle helpers
    hk = None

    def start_hotkeys():
        nonlocal hk
        if hk is not None:
            return
        try:
            from hotkey import HotkeyManager
            hk = HotkeyManager()
            hk.add_hotkey(hotkey_area, lambda: do_capture(app, area=True))
            hk.add_hotkey(hotkey_window, lambda: do_capture(app, area=False))
            hk.add_hotkey(hotkey_monitor, lambda: do_capture(app, area=False))
            hk.start()
        except Exception:
            pass

    def stop_hotkeys():
        nonlocal hk
        if hk:
            try:
                hk.stop()
            except Exception:
                pass
            hk = None

    def start_tray():
        nonlocal tray
        if tray is not None:
            return
        try:
            from tray import TrayIcon
            def on_capture_area():
                do_capture(app, area=True)
            def on_capture_window():
                # map to active window capture
                from capture import capture_active_window
                img = capture_active_window()
                if img:
                    store.add(img)
                    preview(img, app)
            def on_capture_monitor():
                img = capture_fullscreen()
                if img:
                    store.add(img)
                    preview(img, app)
            def on_open_ui():
                app.deiconify()
            def on_exit():
                try:
                    app.quit()
                except Exception:
                    pass
            tray = TrayIcon(on_capture_area, on_capture_window, on_capture_monitor, on_open_ui, on_exit)
            tray.start()
        except Exception:
            tray = None

    def stop_tray():
        nonlocal tray
        if tray:
            try:
                tray.stop()
            except Exception:
                pass
            tray = None

    # initialize based on settings
    if settings.hotkeys_enabled:
        start_hotkeys()
    if settings.start_minimized:
        start_tray()
        app.withdraw()

    # attach change hooks to toggle hotkeys/tray
    def apply_runtime_settings(*_):
        if app._ast_widgets["hotkeys_enabled_var"].get():
            start_hotkeys()
        else:
            stop_hotkeys()
        if app._ast_widgets["start_min_var"].get():
            start_tray()
            app.withdraw()
        else:
            stop_tray()
            app.deiconify()

    app._ast_widgets["hotkeys_enabled_var"].trace_add("write", lambda *_: apply_runtime_settings())
    app._ast_widgets["start_min_var"].trace_add("write", lambda *_: apply_runtime_settings())

    app.mainloop()

    # cleanup
    if hk:
        hk.stop()
    if tray:
        tray.stop()

    app.mainloop()

    # cleanup
    if hk:
        hk.stop()
    if tray:
        tray.stop()


def do_capture(app, area: bool = False):
    settings_from_ui = dict(
        output_folder=app._ast_widgets["output_folder_var"].get(),
        prefix=app._ast_widgets["prefix_var"].get(),
        autosave=app._ast_widgets["autosave_var"].get(),
        autocopy=app._ast_widgets["autocopy_var"].get(),
        legacy=app._ast_widgets["legacy_var"].get(),
    )

    img = capture_area() if area else capture_fullscreen()
    if img is None:
        tk.messagebox.showinfo("Capture", "No capture (cancelled or failed).")
        return

    item = store.add(img)
    # update preview
    preview(img, app)

    # Auto-copy
    if settings_from_ui["autocopy"]:
        from clipboard_win import default_provider
        default_provider.copy(img)

    # Auto-save
    if settings_from_ui["autosave"]:
        # generate filename
        from utils import generate_filename
        ts = item.timestamp
        # attempt to get active window title if available
        try:
            import win32gui
            win_title = win32gui.GetWindowText(win32gui.GetForegroundWindow())
        except Exception:
            win_title = ""
        fname = generate_filename(settings_from_ui["prefix"], win_title, ts)
        out_folder = settings_from_ui["output_folder"] or os.path.join(os.getcwd(), "captures")
        os.makedirs(out_folder, exist_ok=True)
        path = os.path.join(out_folder, fname)
        item.image.save(path)
        tk.messagebox.showinfo("Save", f"Saved to {path}")


def preview(img, app):
    w = app._ast_widgets["preview_label"]
    # resize thumbnail
    thumb = img.copy()
    thumb.thumbnail((640, 360))
    tk_img = ImageTk.PhotoImage(thumb)
    app._ast_widgets["last_image_tk"] = tk_img
    w.configure(image=tk_img, text="")


def rebuild_history(app):
    frame = app._ast_widgets["history_frame"]
    # clear
    for w in frame.winfo_children():
        w.destroy()
    app._ast_widgets["thumb_refs"].clear()

    items = store.recent()
    for idx, item in enumerate(items):
        thumb = item.image.copy()
        thumb.thumbnail((160, 120))
        tk_img = ImageTk.PhotoImage(thumb)
        btn = ctk.CTkButton(frame, image=tk_img, text="", width=170, height=130, command=(lambda i=idx: select_index(app, i)))
        btn.pack(side="left", padx=6)
        # bind right-click menu
        def on_right(event, i=idx):
            menu = tk.Menu(frame, tearoff=0)
            menu.add_command(label="Copy", command=lambda: copy_index(app, i))
            menu.add_command(label="Save", command=lambda: save_index(app, i))
            menu.add_command(label="Delete", command=lambda: delete_index(app, i))
            menu.tk_popup(event.x_root, event.y_root)
        btn.bind("<Button-3>", on_right)
        app._ast_widgets["thumb_refs"].append(tk_img)


def select_index(app, index: int):
    items = store.recent()
    if index < 0 or index >= len(items):
        return
    app._ast_widgets["selected_index"] = index
    preview(items[index].image, app)


def copy_index(app, index: int):
    items = store.recent()
    if index < 0 or index >= len(items):
        return
    from clipboard_win import default_provider
    res = default_provider.copy(items[index].image)
    tk.messagebox.showinfo("Copy", res.get("message"))


def save_index(app, index: int):
    items = store.recent()
    if index < 0 or index >= len(items):
        return
    out = items[index]
    folder = os.path.join(os.getcwd(), "captures")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"capture_{out.timestamp.strftime('%Y%m%d_%H%M%S')}.png")
    out.image.save(path)
    tk.messagebox.showinfo("Save", f"Saved to {path}")


def delete_index(app, index: int):
    items = store.recent()
    if index < 0 or index >= len(items):
        return
    # simple delete from internal list
    del store._items[index]
    rebuild_history(app)
    tk.messagebox.showinfo("Delete", "Deleted.")


def do_copy(app):
    idx = app._ast_widgets.get("selected_index")
    if idx is None:
        # fallback to last
        items = store.recent(1)
        if not items:
            return
        res = default_provider.copy(items[0].image)
        tk.messagebox.showinfo("Copy", res.get("message"))
        return
    copy_index(app, idx)


def do_save(app):
    idx = app._ast_widgets.get("selected_index")
    if idx is None:
        items = store.recent(1)
        if not items:
            return
        out = items[0]
        folder = os.path.join(os.getcwd(), "captures")
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"capture_{out.timestamp.strftime('%Y%m%d_%H%M%S')}.png")
        out.image.save(path)
        tk.messagebox.showinfo("Save", f"Saved to {path}")
        return
    save_index(app, idx)
