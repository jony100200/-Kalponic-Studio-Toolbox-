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


def _ensure_file_logging():
    try:
        import logging
        from logging.handlers import RotatingFileHandler
        import os
        appdata = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        logdir = os.path.join(appdata, "KS_SnapClip", "logs")
        os.makedirs(logdir, exist_ok=True)
        logpath = os.path.join(logdir, "ks_snapclip.log")
        handler = RotatingFileHandler(logpath, maxBytes=1024*1024, backupCount=3)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        root = logging.getLogger()
        # add handler if missing
        existing = False
        for h in root.handlers:
            try:
                if getattr(h, 'baseFilename', None) == os.path.abspath(logpath):
                    existing = True
                    break
            except Exception:
                continue
        if not existing:
            handler.setLevel(logging.INFO)
            root.addHandler(handler)
        root.setLevel(logging.INFO)
        root.info('KS SnapClip starting')
    except Exception:
        pass


def main(start_minimized: bool = None, enable_hotkeys: bool = None, portable: bool = False):
    # ensure logging early
    _ensure_file_logging()
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    # Single-instance: if not primary, show a short message and exit (no IPC required)
    from instance import InstanceManager
    im = InstanceManager()
    primary = im.acquire()
    if not primary:
        try:
            import tkinter as _tk
            from tkinter import messagebox as _mb
            _root = _tk.Tk()
            _root.withdraw()
            try:
                _mb.showinfo("KS SnapClip", "App already running.")
            finally:
                try:
                    _root.destroy()
                except Exception:
                    pass
        except Exception:
            # Fallback: print
            print("KS SnapClip: App already running.")
        return

    app = ctk.CTk()
    app.title("KS SnapClip")
    app.geometry("800x480")

    # if CLI overrides provided, apply them to settings at startup
    from settings import load_settings, save_settings
    s = load_settings(portable=portable)
    if start_minimized is not None:
        s.start_minimized = bool(start_minimized)
    if enable_hotkeys is not None:
        s.hotkeys_enabled = bool(enable_hotkeys)
    save_settings(s, portable=portable)
    # reload settings used by UI
    settings = load_settings(portable=portable)

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

    # Instant paste and toast
    app._ast_widgets["instant_paste_var"] = ctk.BooleanVar(value=settings.instant_paste)
    instant_cb = ctk.CTkCheckBox(left, text="Instant Paste Mode (auto-paste after copy)", variable=app._ast_widgets["instant_paste_var"]) 
    instant_cb.grid(row=5, column=1, pady=5, sticky="w")

    app._ast_widgets["toast_var"] = ctk.BooleanVar(value=settings.toast_enabled)
    toast_cb = ctk.CTkCheckBox(left, text="Show tiny toast on copy", variable=app._ast_widgets["toast_var"]) 
    toast_cb.grid(row=6, column=1, pady=5, sticky="w")

    # Start minimized / tray and hotkeys
    app._ast_widgets["start_min_var"] = ctk.BooleanVar(value=settings.start_minimized)
    start_min_cb = ctk.CTkCheckBox(left, text="Start minimized to tray", variable=app._ast_widgets["start_min_var"]) 
    start_min_cb.grid(row=7, column=1, pady=5, sticky="w")

    app._ast_widgets["hotkeys_enabled_var"] = ctk.BooleanVar(value=settings.hotkeys_enabled)
    hotkey_cb = ctk.CTkCheckBox(left, text="Enable global hotkeys (opt-in)", variable=app._ast_widgets["hotkeys_enabled_var"]) 
    hotkey_cb.grid(row=8, column=1, pady=5, sticky="w")

    # AI optimization
    app._ast_widgets["ai_opt_var"] = ctk.BooleanVar(value=settings.ai_optimization_enabled)
    ai_cb = ctk.CTkCheckBox(left, text="AI Optimization (resize & recompress)", variable=app._ast_widgets["ai_opt_var"]) 
    ai_cb.grid(row=9, column=1, pady=5, sticky="w")
    app._ast_widgets["ai_width_var"] = ctk.IntVar(value=settings.ai_max_width)
    ctk.CTkLabel(left, text="AI max width:").grid(row=9, column=0, padx=10, pady=5, sticky="e")
    ctk.CTkEntry(left, textvariable=app._ast_widgets["ai_width_var"], width=80).grid(row=9, column=1, sticky="w")

    # callbacks to persist settings when changed
    def on_setting_change(*_):
        settings.output_folder = app._ast_widgets["output_folder_var"].get()
        settings.filename_prefix = app._ast_widgets["prefix_var"].get()
        settings.auto_save = app._ast_widgets["autosave_var"].get()
        settings.auto_copy = app._ast_widgets["autocopy_var"].get()
        settings.instant_paste = app._ast_widgets["instant_paste_var"].get()
        settings.toast_enabled = app._ast_widgets["toast_var"].get()
        settings.ai_optimization_enabled = app._ast_widgets["ai_opt_var"].get()
        try:
            settings.ai_max_width = int(app._ast_widgets["ai_width_var"].get())
        except Exception:
            pass
        settings.window_capture_mode = app._ast_widgets["window_mode_var"].get()
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
    app._ast_widgets["instant_paste_var"].trace_add("write", lambda *_: on_setting_change())
    app._ast_widgets["toast_var"].trace_add("write", lambda *_: on_setting_change())
    app._ast_widgets["ai_opt_var"].trace_add("write", lambda *_: on_setting_change())
    app._ast_widgets["ai_width_var"].trace_add("write", lambda *_: on_setting_change())
    app._ast_widgets["legacy_var"].trace_add("write", lambda *_: on_setting_change())
    app._ast_widgets["start_min_var"].trace_add("write", lambda *_: on_setting_change())
    app._ast_widgets["hotkeys_enabled_var"].trace_add("write", lambda *_: on_setting_change())

    # Window capture mode selection
    ctk.CTkLabel(left, text="Window capture mode:").grid(row=6, column=0, padx=10, pady=5, sticky="e")
    app._ast_widgets["window_mode_var"] = ctk.StringVar(value=settings.window_capture_mode)
    ctk.CTkOptionMenu(left, values=["active", "click"], variable=app._ast_widgets["window_mode_var"]).grid(row=6, column=1, sticky="w")

    # Hotkey editor
    ctk.CTkLabel(left, text="Hotkeys (pynput format):").grid(row=7, column=0, padx=10, pady=5, sticky="e")
    app._ast_widgets["hotkey_area_var"] = ctk.StringVar(value=settings.hotkey_area)
    ctk.CTkEntry(left, textvariable=app._ast_widgets["hotkey_area_var"], width=200).grid(row=7, column=1, sticky="w")
    ctk.CTkLabel(left, text="Region").grid(row=7, column=2, padx=6)

    app._ast_widgets["hotkey_window_var"] = ctk.StringVar(value=settings.hotkey_window)
    ctk.CTkEntry(left, textvariable=app._ast_widgets["hotkey_window_var"], width=200).grid(row=8, column=1, sticky="w")
    ctk.CTkLabel(left, text="Window").grid(row=8, column=2, padx=6)

    app._ast_widgets["hotkey_monitor_var"] = ctk.StringVar(value=settings.hotkey_monitor)
    ctk.CTkEntry(left, textvariable=app._ast_widgets["hotkey_monitor_var"], width=200).grid(row=9, column=1, sticky="w")
    ctk.CTkLabel(left, text="Monitor").grid(row=9, column=2, padx=6)

    hotkey_msg = ctk.CTkLabel(left, text="", text_color="orange")
    hotkey_msg.grid(row=10, column=0, columnspan=3, pady=6)

    def apply_hotkeys():
        from utils import validate_hotkeys
        hk_map = {
            'area': app._ast_widgets["hotkey_area_var"].get(),
            'window': app._ast_widgets["hotkey_window_var"].get(),
            'monitor': app._ast_widgets["hotkey_monitor_var"].get(),
        }
        ok, msg = validate_hotkeys(hk_map)
        if not ok:
            hotkey_msg.configure(text=msg, text_color="orange")
            return
        # persist
        settings.hotkey_area = hk_map['area']
        settings.hotkey_window = hk_map['window']
        settings.hotkey_monitor = hk_map['monitor']
        from settings import save_settings
        save_settings(settings)
        hotkey_msg.configure(text="Hotkeys updated", text_color="green")
        # reapply runtime hotkeys if enabled
        try:
            if app._ast_widgets["hotkeys_enabled_var"].get():
                stop_hotkeys()
                start_hotkeys()
        except Exception:
            pass

    ctk.CTkButton(left, text="Apply Hotkeys", command=apply_hotkeys).grid(row=11, column=1, pady=6, sticky="w")

    btn_full = ctk.CTkButton(left, text="Capture Fullscreen", command=lambda: do_capture(app))
    btn_full.grid(row=12, column=0, columnspan=2, pady=6)

    btn_area = ctk.CTkButton(left, text="Capture Area (overlay)", command=lambda: do_capture(app, area=True))
    btn_area.grid(row=8, column=0, columnspan=2, pady=6)

    btn_copy = ctk.CTkButton(left, text="Copy Selected", command=lambda: do_copy(app))
    btn_copy.grid(row=9, column=0, columnspan=2, pady=6)

    btn_save = ctk.CTkButton(left, text="Save Selected", command=lambda: do_save(app))
    btn_save.grid(row=10, column=0, columnspan=2, pady=6)

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
            # Add wrappers that use the capture lock wrapper to ensure hotkeys are disabled during capture
            hk.add_hotkey(hotkey_area, lambda: _capture_wrapper(do_capture, app, area=True))
            # window hotkey respects window capture mode in settings
            def _window_action():
                from settings import load_settings
                s = load_settings()
                if s.window_capture_mode == 'active':
                    from capture import capture_active_window
                    _capture_wrapper(lambda: do_capture(app, area=False, capture_callable=capture_active_window))
                else:
                    # click-to-select mode
                    def _click_capture():
                        from area_overlay import select_window
                        reg = select_window()
                        if not reg:
                            return
                        l, t, r, b = reg
                        from capture import capture_rect
                        img = capture_rect(l, t, r - l, b - t)
                        if img:
                            # mimic do_capture post-capture handling
                            item = store.add(img)
                            preview(img, app)
                            from clipboard_win import default_provider
                            default_provider.copy(img)
                            if s.toast_enabled:
                                try:
                                    show_toast(app, "✔ Copied to clipboard\nReady to paste", duration_ms=1200)
                                except Exception:
                                    pass
                    _capture_wrapper(_click_capture)
            hk.add_hotkey(hotkey_window, _window_action)
            hk.add_hotkey(hotkey_monitor, lambda: _capture_wrapper(do_capture, app, area=False))
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
                from capture import capture_active_window
                do_capture(app, capture_callable=capture_active_window)
            def on_capture_monitor():
                do_capture(app, area=False)
            def on_open_ui():
                app.deiconify()
            def on_exit():
                try:
                    app.quit()
                except Exception:
                    pass
            tray = TrayIcon(on_capture_area, on_capture_window, on_capture_monitor, on_open_ui, on_exit)
            tray.start()
            # small confirmation toast on success (delayed briefly to allow icon creation)
            import threading, logging
            def _verify_tray():
                try:
                    if tray is None or not getattr(tray, '_thread', None) or not tray._thread.is_alive() or tray.icon is None:
                        logging.error('Tray failed to initialize correctly')
                        try:
                            show_toast(app, '⚠️ System tray failed to initialize. See logs at %LOCALAPPDATA%\\KS_SnapClip\\logs', duration_ms=4000)
                        except Exception:
                            pass
                    else:
                        logging.info('Tray initialized OK')
                        try:
                            show_toast(app, '✔ KS SnapClip running in system tray\nHotkeys: Ctrl+Shift+1/2/3', duration_ms=3000)
                        except Exception:
                            pass
                except Exception:
                    logging.exception('Error while verifying tray status')
            t = threading.Timer(0.5, _verify_tray)
            t.daemon = True
            t.start()
        except Exception as e:
            import logging
            logging.exception('Failed to start system tray icon: %s', e)
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
    # capture lock to prevent double-capture
    import threading
    capture_lock = threading.Lock()

    # helper to wrap capture calls and disable hotkeys during capture
    def _capture_wrapper(func, *args, **kwargs):
        # prevent re-entrant captures
        try:
            acquired = capture_lock.acquire(blocking=False)
        except Exception:
            acquired = False
        if not acquired:
            # already capturing; ignore
            return
        try:
            # disable hotkeys while capturing
            nonlocal hk
            if hk:
                try:
                    hk.pause()
                except Exception:
                    pass
            # hide UI completely during capture
            try:
                app.withdraw()
            except Exception:
                pass
            return func(*args, **kwargs)
        finally:
            # restore UI state (respect start_minimized setting)
            try:
                if app._ast_widgets["start_min_var"].get():
                    try:
                        app.withdraw()
                    except Exception:
                        pass
                else:
                    try:
                        app.deiconify()
                    except Exception:
                        pass
            except Exception:
                pass
            if hk:
                try:
                    hk.resume()
                except Exception:
                    pass
            try:
                capture_lock.release()
            except Exception:
                pass

    if settings.hotkeys_enabled:
        start_hotkeys()

    # Always show startup toast and minimize to tray after a short delay when launched via double click/batch
    try:
        from ui import startup_sequence as _startup_sequence
        _startup_sequence(app, settings, start_tray)
    except Exception:
        # fallback to inline behavior
        try:
            msg = (
                "✔ Capture Tool Started\n"
                "Running in system tray\n\n"
                f"Hotkeys:\n{settings.hotkey_area} → Region\n{settings.hotkey_window} → Window\n{settings.hotkey_monitor} → Monitor\n\n"
                "Double-click tray or choose 'Open UI' to open settings.\n"
                "Minimizing to system tray..."
            )
            show_toast(app, msg, duration_ms=3000)
        except Exception:
            pass
        try:
            start_tray()
        except Exception:
            pass
        try:
            app.withdraw()
        except Exception:
            pass

    if settings.start_minimized:
        # if the user explicitly chose start_minimized, ensure tray started
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


def do_capture(app, area: bool = False, capture_callable=None):
    """Perform capture using either the provided capture_callable or default area/fullscreen.

    This function loads the current settings at call time so tray/menu actions also honor them.
    """
    from settings import load_settings
    settings = load_settings()

    settings_from_ui = dict(
        output_folder=app._ast_widgets["output_folder_var"].get(),
        prefix=app._ast_widgets["prefix_var"].get(),
        autosave=app._ast_widgets["autosave_var"].get(),
        autocopy=app._ast_widgets["autocopy_var"].get(),
        legacy=app._ast_widgets["legacy_var"].get(),
    )

    # choose capture function
    if capture_callable is not None:
        try:
            img = capture_callable()
        except Exception:
            img = None
    else:
        img = capture_area() if area else capture_fullscreen()

    if img is None:
        try:
            show_toast(app, "✖ Capture failed", duration_ms=1500)
        except Exception:
            try:
                tk.messagebox.showinfo("Capture", "No capture (cancelled or failed).")
            except Exception:
                pass
        return

    item = store.add(img)
    # update preview
    preview(img, app)

    # Apply AI optimization if enabled
    proc_img = img
    if settings.ai_optimization_enabled:
        from utils import optimize_image
        try:
            proc_img = optimize_image(img, max_width=settings.ai_max_width, convert_to_png=settings.ai_convert_to_png)
        except Exception:
            proc_img = img

    # Auto-copy
    if settings_from_ui["autocopy"] or settings.auto_copy:
        from clipboard_win import default_provider
        default_provider.copy(proc_img)
        # Instant paste if enabled
        if settings.instant_paste:
            from utils import instant_paste
            try:
                instant_paste()
            except Exception:
                pass
        # toast
        if settings.toast_enabled:
            try:
                show_toast(app, "✔ Copied to clipboard\nReady to paste", duration_ms=1200)
            except Exception:
                pass

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
        proc_img.save(path)
        try:
            tk.messagebox.showinfo("Save", f"Saved to {path}")
        except Exception:
            pass


def _to_ctk_image(img, size=None):
    """Convert a PIL.Image to a customtkinter.CTkImage with optional size."""
    try:
        # CTkImage accepts PIL Image objects for light_image/dark_image
        if size is None:
            size = img.size
        return ctk.CTkImage(light_image=img.copy(), size=size)
    except Exception:
        # fallback: return None
        return None


def preview(img, app):
    w = app._ast_widgets["preview_label"]
    # resize thumbnail
    thumb = img.copy()
    thumb.thumbnail((640, 360))
    ctk_img = _to_ctk_image(thumb, size=(640, 360))
    if ctk_img is not None:
        app._ast_widgets["last_image_ctk"] = ctk_img
        w.configure(image=ctk_img, text="")
    else:
        # fallback to PhotoImage
        tk_img = ImageTk.PhotoImage(thumb)
        app._ast_widgets["last_image_tk"] = tk_img
        w.configure(image=tk_img, text="")


def _compute_toast_geometry(monitor, width: int, height: int) -> str:
    """Return a geometry string to center a toast of size (width,height) on the given monitor."""
    try:
        mx = getattr(monitor, 'x', 0)
        my = getattr(monitor, 'y', 0)
        mw = getattr(monitor, 'width', 800)
        mh = getattr(monitor, 'height', 600)
        x = int(mx + (mw - width) / 2)
        y = int(my + (mh - height) / 2)
        return f"{width}x{height}+{x}+{y}"
    except Exception:
        return f"{width}x{height}+0+0"


def show_toast(app, text: str, duration_ms: int = 1000, center_on_monitor: bool = True):
    """Show a modern centered toast using customtkinter styles.

    If center_on_monitor is True, attempt to center on the primary monitor (or monitor under cursor when available).
    """
    try:
        # try to determine monitor to center on
        monitor = None
        try:
            from area_overlay import monitors
            # try to pick monitor under cursor if possible
            try:
                sx = app.winfo_pointerx()
                sy = app.winfo_pointery()
                for m in monitors:
                    mx = getattr(m, 'x', 0)
                    my = getattr(m, 'y', 0)
                    mw = getattr(m, 'width', 0)
                    mh = getattr(m, 'height', 0)
                    if sx >= mx and sx <= mx + mw and sy >= my and sy <= my + mh:
                        monitor = m
                        break
            except Exception:
                monitor = None
            if monitor is None:
                monitor = monitors[0]
        except Exception:
            monitor = None

        # create top-level toast
        t = tk.Toplevel(app)
        t.overrideredirect(True)
        t.attributes("-topmost", True)
        # use CTkLabel for nicer appearance
        lbl = ctk.CTkLabel(t, text=text, width=320, corner_radius=12, fg_color=("#222222", "#f2f2f2"), text_color="#ffffff", anchor="center", justify="center")
        lbl.pack(padx=12, pady=12, fill="both", expand=True)

        # compute geometry
        w = 360
        h = 120
        if center_on_monitor and monitor is not None:
            geo = _compute_toast_geometry(monitor, w, h)
        else:
            # center on the main app window
            app.update_idletasks()
            ax = app.winfo_rootx()
            ay = app.winfo_rooty()
            aw = app.winfo_width()
            ah = app.winfo_height()
            x = int(ax + (aw - w) / 2)
            y = int(ay + (ah - h) / 2)
            geo = f"{w}x{h}+{x}+{y}"

        t.geometry(geo)
        # fade animation: simple approach using after to simulate fade-in/out is complex; keep simple appearance
        t.after(duration_ms, t.destroy)
    except Exception:
        pass


def startup_sequence(app, settings, start_tray_fn, delay_sec: float = 3.0):
    """Show a startup toast with hotkeys and minimize to tray after delay_sec seconds."""
    try:
        # compose message, make it readable for multi-line
        msg = (
            "✔ Capture Tool Started\n"
            "Running in system tray\n\n"
            f"Hotkeys:\nCtrl+Shift+1 → Region\nCtrl+Shift+2 → Window\nCtrl+Shift+3 → Monitor\n\n"
            "Double-click tray (or use 'Open UI') to open settings.\n"
            "Minimizing to system tray..."
        )
        show_toast(app, msg, duration_ms=int(delay_sec * 1000))
    except Exception:
        pass

    # persist first_run flag
    try:
        settings.first_run = False
        from settings import save_settings
        save_settings(settings)
    except Exception:
        pass

    # schedule minimize to tray
    def _min():
        try:
            start_tray_fn()
        except Exception:
            pass
        try:
            app.withdraw()
        except Exception:
            pass

    try:
        t = threading.Timer(delay_sec, _min)
        t.daemon = True
        t.start()
    except Exception:
        _min()


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
        ctk_img = _to_ctk_image(thumb, size=(160, 120))
        if ctk_img is not None:
            btn = ctk.CTkButton(frame, image=ctk_img, text="", width=170, height=130, command=(lambda i=idx: select_index(app, i)))
            app._ast_widgets["thumb_refs"].append(ctk_img)
        else:
            tk_img = ImageTk.PhotoImage(thumb)
            btn = ctk.CTkButton(frame, image=tk_img, text="", width=170, height=130, command=(lambda i=idx: select_index(app, i)))
            app._ast_widgets["thumb_refs"].append(tk_img)
        btn.pack(side="left", padx=6)
        # bind right-click menu
        def on_right(event, i=idx):
            menu = tk.Menu(frame, tearoff=0)
            menu.add_command(label="Copy", command=lambda: copy_index(app, i))
            menu.add_command(label="Save", command=lambda: save_index(app, i))
            menu.add_command(label="Delete", command=lambda: delete_index(app, i))
            menu.tk_popup(event.x_root, event.y_root)
        btn.bind("<Button-3>", on_right)

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
