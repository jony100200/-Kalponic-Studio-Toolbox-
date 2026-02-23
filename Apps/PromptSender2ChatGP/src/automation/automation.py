"""
Automation components for window detection, clipboard management, and paste control.
Handles the low-level automation tasks required for prompt sequencing.
"""

import time
import pyautogui
import pyperclip
import pygetwindow as gw
from typing import Optional, List
import logging
from PIL import Image
import os

# Configure pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

class WindowDetector:
    """Handles window detection and focusing with keyboard-driven input box focusing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.focus_strategies = [
            self._browser_focus_strategy,
            self._generic_focus_strategy,
            self._tab_navigation_strategy
        ]
    
    def find_windows(self, title_substring: str = "") -> List[str]:
        """Find windows containing the title substring"""
        try:
            windows = gw.getAllWindows()
            if title_substring:
                matching_windows = [w.title for w in windows 
                                  if title_substring.lower() in w.title.lower() 
                                  and w.title.strip()]
            else:
                matching_windows = [w.title for w in windows if w.title.strip()]
            
            return matching_windows
        except Exception as e:
            self.logger.error(f"Error finding windows: {e}")
            return []
    
    def focus_window(self, title_substring: str) -> bool:
        """Focus window containing the title substring"""
        try:
            windows = gw.getWindowsWithTitle(title_substring)
            if not windows:
                # Try partial match
                all_windows = gw.getAllWindows()
                windows = [w for w in all_windows 
                          if title_substring.lower() in w.title.lower()]
            
            if windows:
                window = windows[0]
                
                # Bring window to front
                window.activate()
                time.sleep(0.3)  # Give time for window to focus
                
                # Ensure window is maximized or restored (not minimized)
                if hasattr(window, 'maximize'):
                    try:
                        window.restore()  # Restore if minimized
                    except:
                        pass
                
                time.sleep(0.2)
                self.logger.info(f"Focused window: {window.title}")
                return True
            else:
                self.logger.warning(f"No window found with title containing: {title_substring}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error focusing window: {e}")
            return False
    
    def focus_input_box(self, retries: int = 3) -> bool:
        """Focus the input box using keyboard navigation strategies"""
        for attempt in range(retries):
            self.logger.info(f"Attempting to focus input box (attempt {attempt + 1}/{retries})")
            
            for strategy_func in self.focus_strategies:
                try:
                    if strategy_func():
                        # Verify focus with test marker
                        if self._verify_input_focus():
                            self.logger.info("Successfully focused input box")
                            return True
                        else:
                            self.logger.debug(f"Strategy {strategy_func.__name__} failed verification")
                except Exception as e:
                    self.logger.debug(f"Strategy {strategy_func.__name__} failed: {e}")
                    continue
            
            if attempt < retries - 1:
                time.sleep(0.5)  # Wait between attempts
        
        self.logger.warning("All focus strategies failed")
        return False
    
    def _browser_focus_strategy(self) -> bool:
        """Focus strategy for browser/Electron apps (ChatGPT Desktop, Chrome, etc.)"""
        # Method 1: Ctrl+L then Tab to cycle back to page content
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.1)
        pyautogui.press('tab')
        time.sleep(0.1)
        return True
    
    def _generic_focus_strategy(self) -> bool:
        """Generic focus strategies for various applications"""
        # Try common focus shortcuts
        focus_shortcuts = [
            ['ctrl', 'k'],  # Many apps use Ctrl+K for search/input focus
            ['/'],          # Discord, Slack, and others use / for focus
            ['ctrl', 'f'],  # Some apps repurpose Ctrl+F, then Escape to stay focused
        ]
        
        for shortcut in focus_shortcuts:
            try:
                if len(shortcut) == 1:
                    pyautogui.press(shortcut[0])
                else:
                    pyautogui.hotkey(*shortcut)
                time.sleep(0.1)
                
                # For Ctrl+F, press Escape to close search but keep focus
                if shortcut == ['ctrl', 'f']:
                    pyautogui.press('escape')
                    time.sleep(0.1)
                
                return True
            except:
                continue
        
        return False
    
    def _tab_navigation_strategy(self) -> bool:
        """Use Tab navigation to cycle through focusable elements"""
        # Press Tab multiple times to cycle through UI elements
        for i in range(5):  # Try up to 5 tabs
            pyautogui.press('tab')
            time.sleep(0.1)
            
            # Test if we're in a text input by typing a space and backspace
            try:
                pyautogui.press('space')
                time.sleep(0.05)
                pyautogui.press('backspace')
                time.sleep(0.05)
                return True
            except:
                continue
        
        return False
    
    def _verify_input_focus(self) -> bool:
        """Verify input box has focus using a test marker"""
        test_marker = "<<<TEST>>>"
        
        try:
            # Type the test marker
            pyautogui.typewrite(test_marker, interval=0.02)
            time.sleep(0.1)
            
            # Delete it with backspaces
            for _ in range(len(test_marker)):
                pyautogui.press('backspace')
                time.sleep(0.02)
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Input focus verification failed: {e}")
            return False
    
    def test_focus(self, title_substring: str) -> bool:
        """Test if we can focus the target window and input box"""
        if not self.focus_window(title_substring):
            return False
        
        # Test input box focusing
        return self.focus_input_box(retries=2)

class ClipboardManager:
    """Manages clipboard operations with safety"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.original_content = None
        self.original_content_saved = False
    
    def save_original_content(self):
        """Save the original clipboard content"""
        try:
            self.original_content = pyperclip.paste()
            self.original_content_saved = True
            self.logger.info("Original clipboard content saved")
        except Exception as e:
            self.logger.warning(f"Could not save original clipboard: {e}")
    
    def restore_original_content(self):
        """Restore the original clipboard content"""
        if self.original_content_saved and self.original_content is not None:
            try:
                pyperclip.copy(self.original_content)
                self.logger.info("Original clipboard content restored")
            except Exception as e:
                self.logger.warning(f"Could not restore original clipboard: {e}")
    
    def copy_text(self, text: str) -> bool:
        """Copy text to clipboard"""
        try:
            pyperclip.copy(text)
            return True
        except Exception as e:
            self.logger.error(f"Failed to copy text to clipboard: {e}")
            return False
    
    def copy_image(self, image_path: str) -> bool:
        """Copy image to clipboard"""
        try:
            # Load and copy image to clipboard
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save to temporary location and copy
            temp_path = "temp_clipboard_image.png"
            image.save(temp_path, "PNG")
            
            # Use pyautogui to copy image (Windows specific)
            import subprocess
            subprocess.run([
                'powershell', '-command',
                f'Add-Type -AssemblyName System.Windows.Forms; '
                f'$img = [System.Drawing.Image]::FromFile((Resolve-Path "{temp_path}")); '
                f'[System.Windows.Forms.Clipboard]::SetImage($img); '
                f'$img.Dispose()'
            ], check=True, capture_output=True)
            
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy image to clipboard: {e}")
            return False

class PasteController:
    """Handles paste operations with retries, timing, and improved focus"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.clipboard_manager = ClipboardManager()
        self.window_detector = WindowDetector()
        self.max_retries = 3
        self.retry_delay = 0.5
        self.focus_before_paste = True
        self.focus_retries = 2

    def configure_retries(self, max_retries: int, retry_delay: float, focus_retries: int = 2):
        """Configure retry behavior."""
        try:
            self.max_retries = max(1, min(10, int(max_retries)))
        except Exception:
            self.max_retries = 3

        try:
            self.retry_delay = max(0.05, min(10.0, float(retry_delay)))
        except Exception:
            self.retry_delay = 0.5

        try:
            self.focus_retries = max(1, min(10, int(focus_retries)))
        except Exception:
            self.focus_retries = 2
    
    def paste_text(self, text: str, auto_enter: bool = True, grace_delay: int = 400, 
                   target_window: str = None) -> bool:
        """Paste text with optional Enter key and improved focus handling"""
        if not self.clipboard_manager.original_content_saved:
            self.clipboard_manager.save_original_content()
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Paste attempt {attempt + 1}/{self.max_retries}")
                
                # Focus input box before pasting (if enabled and target provided)
                if self.focus_before_paste and target_window:
                    if not self.window_detector.focus_window(target_window):
                        self.logger.warning(f"Failed to focus window on attempt {attempt + 1}")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay)
                            continue
                    
                    # Focus the input box with keyboard navigation
                    if not self.window_detector.focus_input_box(retries=self.focus_retries):
                        self.logger.warning(f"Failed to focus input box on attempt {attempt + 1}")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay)
                            continue
                
                # Copy text to clipboard
                if not self.clipboard_manager.copy_text(text):
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                
                # Small delay to ensure clipboard is ready
                time.sleep(0.15)
                
                # Paste using Ctrl+V
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.1)
                
                # Verify paste worked by checking if we can still focus
                # (This is a simple check - if the paste completely failed, 
                # the app might lose focus or behave unexpectedly)
                
                # Grace delay before Enter
                if auto_enter and grace_delay > 0:
                    time.sleep(grace_delay / 1000.0)
                    pyautogui.press('enter')
                    time.sleep(0.1)
                
                self.logger.info(f"Successfully pasted text (attempt {attempt + 1})")
                return True
                
            except Exception as e:
                self.logger.warning(f"Paste attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
        
        self.logger.error("All paste attempts failed")
        return False
    
    def paste_image(self, image_path: str, target_window: str = None) -> bool:
        """Paste image from file with improved focus handling"""
        if not self.clipboard_manager.original_content_saved:
            self.clipboard_manager.save_original_content()
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Image paste attempt {attempt + 1}/{self.max_retries}")
                
                # Focus input box before pasting (if enabled and target provided)
                if self.focus_before_paste and target_window:
                    if not self.window_detector.focus_window(target_window):
                        self.logger.warning(f"Failed to focus window on attempt {attempt + 1}")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay)
                            continue
                    
                    # Focus the input box with keyboard navigation
                    if not self.window_detector.focus_input_box(retries=self.focus_retries):
                        self.logger.warning(f"Failed to focus input box on attempt {attempt + 1}")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay)
                            continue
                
                # Copy image to clipboard
                if not self.clipboard_manager.copy_image(image_path):
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                
                # Small delay to ensure clipboard is ready
                time.sleep(0.25)
                
                # Paste using Ctrl+V
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.15)
                
                self.logger.info(f"Successfully pasted image (attempt {attempt + 1})")
                return True
                
            except Exception as e:
                self.logger.warning(f"Image paste attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
        
        self.logger.error("All image paste attempts failed")
        return False
    
    def set_focus_enabled(self, enabled: bool):
        """Enable or disable automatic focus before pasting"""
        self.focus_before_paste = enabled
        self.logger.info(f"Auto-focus before paste: {enabled}")
    
    def cleanup(self):
        """Cleanup clipboard manager"""
        self.clipboard_manager.restore_original_content()
