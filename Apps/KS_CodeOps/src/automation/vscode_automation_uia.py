import re

import pyautogui
import uiautomation as auto

from src.automation.vscode_automation import VSCodeAutomation


class VSCodeAutomationUIA(VSCodeAutomation):
    def __init__(self, config):
        super().__init__(config)

    def _window_control(self):
        pattern = ".*" + re.escape(self.config.window_title) + ".*"
        window = auto.WindowControl(searchDepth=1, NameRegex=pattern)
        if window.Exists(1, 0.2):
            return window
        return None

    def focus_input(self) -> bool:
        if not self.focus_window():
            return False

        try:
            window = self._window_control()
            if window:
                try:
                    window.SetFocus()
                except Exception:
                    pass

                edits = window.GetChildren()
                for child in edits:
                    try:
                        if child.ControlTypeName == "EditControl":
                            child.Click()
                            if self._verify_input_focus():
                                return True
                    except Exception:
                        continue
        except Exception:
            pass

        return super().focus_input()

    def activate_panel(self, command: str = None, focus_sequence=None, fallback_click=None) -> bool:
        ok = super().activate_panel(command=command, focus_sequence=focus_sequence, fallback_click=fallback_click)
        if ok:
            return True

        try:
            window = self._window_control()
            if window:
                window.SetFocus()
                pyautogui.press("f6")
                pyautogui.press("tab")
                if self._verify_input_focus():
                    return True
        except Exception:
            pass

        return False
