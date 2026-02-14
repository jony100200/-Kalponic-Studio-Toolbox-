import os
import time
from typing import List, Dict

import pyautogui
import pygetwindow as gw
import pyperclip
from PIL import Image

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


class VSCodeAutomation:
    def __init__(self, config):
        self.config = config

    def _candidate_window_titles(self) -> List[str]:
        preferred_title = str(self.config.window_title or "").strip()
        candidate_titles = []
        if preferred_title:
            candidate_titles.append(preferred_title)
        else:
            candidate_titles.extend([
                "Visual Studio Code",
                "Code - OSS",
                "Code - Insiders",
            ])
        return candidate_titles

    def _is_vscode_title(self, title: str) -> bool:
        if not title:
            return False
        lowered = title.lower()
        for candidate in self._candidate_window_titles():
            if candidate.lower() in lowered:
                return True
        return False

    def _active_window(self):
        try:
            return gw.getActiveWindow()
        except Exception:
            return None

    def _is_vscode_active(self) -> bool:
        window = self._active_window()
        title = getattr(window, "title", "") if window else ""
        return self._is_vscode_title(title)

    def _wait_for_vscode_active(self, timeout_s: float = 1.2, poll_s: float = 0.08) -> bool:
        end = time.time() + max(0.1, timeout_s)
        while time.time() < end:
            if self._is_vscode_active():
                return True
            time.sleep(max(0.02, poll_s))
        return False

    def list_windows(self) -> List[str]:
        return [window.title for window in gw.getAllWindows() if window.title.strip()]

    def _target_window(self):
        candidate_titles = self._candidate_window_titles()

        all_windows = [window for window in gw.getAllWindows() if window.title.strip()]
        for title in candidate_titles:
            exact = gw.getWindowsWithTitle(title)
            if exact:
                return exact[0]
            lowered = title.lower()
            partial = [window for window in all_windows if lowered in window.title.lower()]
            if partial:
                return partial[0]
        return None

    def focus_window(self) -> bool:
        window = self._target_window()
        if not window:
            return False
        try:
            is_minimized = bool(getattr(window, "isMinimized", False))
            if is_minimized:
                try:
                    window.restore()
                    time.sleep(0.15)
                except Exception:
                    pass
            if bool(getattr(self.config, "maximize_on_focus", True)):
                try:
                    is_maximized = bool(getattr(window, "isMaximized", False))
                except Exception:
                    is_maximized = False
                if not is_maximized:
                    try:
                        window.maximize()
                        time.sleep(0.15)
                    except Exception:
                        pass
            window.activate()
            time.sleep(0.25)
            return self._wait_for_vscode_active(timeout_s=1.5)
        except Exception:
            return False

    def _verify_input_focus(self) -> bool:
        if not self._is_vscode_active():
            return False
        marker = self.config.verify_marker or "<<<TEST>>>"
        try:
            pyautogui.typewrite(marker, interval=0.015)
            time.sleep(0.05)
            for _ in marker:
                pyautogui.press("backspace")
                time.sleep(0.01)
            if not self._wait_for_vscode_active(timeout_s=0.5):
                return False
            return True
        except Exception:
            return False

    def _focus_editor_profile(self) -> bool:
        pyautogui.hotkey("ctrl", "1")
        time.sleep(0.1)
        pyautogui.press("escape")
        time.sleep(0.05)
        return self._verify_input_focus()

    def _focus_chat_panel_profile(self) -> bool:
        if not self._is_vscode_active():
            return False
        pyautogui.hotkey("ctrl", "j")
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "shift", "p")
        time.sleep(0.2)
        pyautogui.typewrite("View: Focus Chat")
        time.sleep(0.2)
        pyautogui.press("enter")
        time.sleep(0.2)
        if self._verify_input_focus():
            return True
        for _ in range(8):
            pyautogui.press("tab")
            time.sleep(0.06)
            if self._verify_input_focus():
                return True
        return False

    def _fallback_click_focus(self) -> bool:
        window = self._target_window()
        if not window:
            return False
        x_rel, y_rel = self._normalize_click_rel(self.config.fallback_click)
        click_x = int(window.left + (window.width * x_rel))
        click_y = int(window.top + (window.height * y_rel))
        pyautogui.click(click_x, click_y)
        time.sleep(0.15)
        if not self._wait_for_vscode_active(timeout_s=0.5):
            return False
        return self._verify_input_focus()

    def _normalize_click_rel(self, rel: Dict[str, float]):
        rel = rel or {}
        x_rel = float(rel.get("x_rel", 0.86))
        y_rel = float(rel.get("y_rel", 0.96))
        if x_rel < 0.1 or x_rel > 0.95:
            x_rel = 0.86
        if y_rel < 0.80 or y_rel > 0.995:
            y_rel = 0.96
        return x_rel, y_rel

    def focus_target_input(self, fallback_click: Dict[str, float] = None) -> bool:
        if not self.focus_window():
            return False
        window = self._target_window()
        if not window:
            return False
        rel = fallback_click or self.config.fallback_click
        x_rel, y_rel = self._normalize_click_rel(rel)
        y_candidates = [y_rel, 0.94, 0.92, 0.90]
        for y_try in y_candidates:
            click_x = int(window.left + (window.width * x_rel))
            click_y = int(window.top + (window.height * y_try))
            pyautogui.click(click_x, click_y)
            time.sleep(0.10)
            if self._wait_for_vscode_active(timeout_s=0.6):
                return True
        return False

    def focus_input(self) -> bool:
        if not self.focus_window():
            return False
        profile = (self.config.focus_profile or "chat_panel").lower()
        for _ in range(2):
            if profile == "editor":
                if self._focus_editor_profile():
                    return True
            else:
                if self._focus_chat_panel_profile():
                    return True
            if self._fallback_click_focus():
                return True
        return False

    def activate_panel(self, command: str = None, focus_sequence: List[str] = None, fallback_click: Dict[str, float] = None) -> bool:
        """
        Activate/open an extension panel.
        - Try command (Command Palette) if provided
        - Try focus_sequence (list of key strings) if provided
        - Fallback to relative click
        Returns True if input focus verification succeeded.
        """
        # Ensure window focused first
        if not self.focus_window():
            return False

        # 1) Try command-palette command
        try:
            if command:
                pyautogui.hotkey("ctrl", "shift", "p")
                time.sleep(0.12)
                if not self._is_vscode_active():
                    return False
                pyautogui.typewrite(command, interval=0.02)
                time.sleep(0.08)
                pyautogui.press("enter")
                time.sleep(0.25)
                if self._verify_input_focus():
                    return True
        except Exception:
            pass

        # 2) Try a focus sequence of keys
        try:
            if focus_sequence:
                for item in focus_sequence:
                    if not self._is_vscode_active():
                        return False
                    # allow items like 'ctrl+j' or 'tab'
                    parts = item.split("+")
                    if len(parts) > 1:
                        pyautogui.hotkey(*parts)
                    else:
                        pyautogui.press(parts[0])
                    time.sleep(0.08)
                time.sleep(0.15)
                if self._verify_input_focus():
                    return True
        except Exception:
            pass

        # 3) Try provided fallback_click, else use configured fallback
        fclick = fallback_click or self.config.fallback_click
        if fclick:
            x_rel, y_rel = self._normalize_click_rel(fclick)
            window = self._target_window()
            if window:
                click_x = int(window.left + (window.width * x_rel))
                click_y = int(window.top + (window.height * y_rel))
                pyautogui.click(click_x, click_y)
                time.sleep(0.15)
                if not self._wait_for_vscode_active(timeout_s=0.5):
                    return False
                if self._verify_input_focus():
                    return True

        return False

    def record_fallback_click(self, seconds: int = 4):
        if not self.focus_window():
            raise RuntimeError("Could not focus VS Code window")
        time.sleep(seconds)
        x, y = pyautogui.position()
        window = self._target_window()
        if not window:
            raise RuntimeError("Window disappeared while recording")
        x_rel = max(0.0, min(1.0, (x - window.left) / max(1, window.width)))
        y_rel = max(0.0, min(1.0, (y - window.top) / max(1, window.height)))
        self.config.fallback_click = {"x_rel": round(x_rel, 5), "y_rel": round(y_rel, 5)}
        self.config.save()
        return self.config.fallback_click

    def send_text(self, text: str, press_enter: bool = False) -> bool:
        if not self.focus_input():
            return False
        if not self._is_vscode_active():
            return False
        pyperclip.copy(text)
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.1)
        if not self._is_vscode_active():
            return False
        if press_enter:
            pyautogui.press("enter")
        return True

    def probe_type_text(self, text: str, clear_after: bool = True) -> bool:
        if not self._is_vscode_active():
            return False
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            old_clipboard = None

        try:
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.03)
            pyautogui.press("backspace")
            time.sleep(0.03)
            pyperclip.copy(text)
            time.sleep(0.05)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.1)
            if not self._is_vscode_active():
                return False
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.03)
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.08)
            selected_text = pyperclip.paste() or ""
            exact_probe = selected_text.strip() == text

            if clear_after:
                pyautogui.press("backspace")
                time.sleep(0.03)
                if not self._is_vscode_active():
                    return False

            return exact_probe
        finally:
            if old_clipboard is not None:
                try:
                    pyperclip.copy(old_clipboard)
                except Exception:
                    pass

    def _copy_image_to_clipboard(self, image_path: str):
        image = Image.open(image_path)
        if image.mode != "RGB":
            image = image.convert("RGB")
        temp_path = "temp_clipboard_image.png"
        image.save(temp_path, "PNG")
        command = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "Add-Type -AssemblyName System.Drawing; "
            f"$img = [System.Drawing.Image]::FromFile((Resolve-Path '{temp_path}')); "
            "[System.Windows.Forms.Clipboard]::SetImage($img); "
            "$img.Dispose()"
        )
        result = os.system(f'powershell -NoProfile -Command "{command}"')
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if result != 0:
            raise RuntimeError("Failed to copy image to clipboard")

    def send_image(self, image_path: str, press_enter: bool = False) -> bool:
        if not os.path.exists(image_path):
            raise FileNotFoundError(image_path)
        if not self.focus_input():
            return False
        if not self._is_vscode_active():
            return False
        self._copy_image_to_clipboard(image_path)
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(max(0.0, float(self.config.image_upload_delay)))
        if press_enter:
            pyautogui.press("enter")
        return True
