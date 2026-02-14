from src.automation.vscode_automation import VSCodeAutomation


def build_automation(config):
    backend = (config.automation_backend or "pyautogui").lower()
    if backend == "uia":
        try:
            from src.automation.vscode_automation_uia import VSCodeAutomationUIA

            return VSCodeAutomationUIA(config)
        except Exception:
            return VSCodeAutomation(config)
    return VSCodeAutomation(config)
