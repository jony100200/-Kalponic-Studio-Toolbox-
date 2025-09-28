"""
🎨 Sci-Fi Theme Manager
=======================
Role: Visual style coordinator for sci-fi aesthetic
SOLID: Single responsibility for theme management
"""

from PySide6.QtCore import QObject
from PySide6.QtGui import QColor


class ThemeManager(QObject):
    """
    🎨 Professional Sci-Fi Theme Manager
    ====================================
    Role: Theme Coordinator - Manages all visual styles
    Pattern: Centralized style management
    """
    
    def __init__(self):
        super().__init__()
        self.colors = self._define_color_palette()
    
    def _define_color_palette(self):
        """🌈 Define the professional sci-fi color palette"""
        return {
            # Core backgrounds (solid, not washed out)
            'bg_primary': '#0d1117',      # GitHub-dark primary
            'bg_secondary': '#161b22',    # Panel backgrounds  
            'bg_tertiary': '#21262d',     # Component backgrounds
            
            # Accents (vibrant, high contrast)
            'accent_primary': '#00d4aa',  # Teal/cyan (primary actions)
            'accent_secondary': '#7c3aed', # Purple (secondary actions)
            'accent_success': '#00c851',   # Green (success states)
            'accent_warning': '#ff8f00',   # Orange (warnings)
            'accent_danger': '#ff3347',    # Red (errors/stop)
            
            # Text (high contrast, readable)
            'text_primary': '#f0f6fc',     # Primary text (white)
            'text_secondary': '#7d8590',   # Secondary text (gray)
            'text_muted': '#484f58',       # Muted text (darker gray)
            
            # Borders and dividers
            'border_primary': '#30363d',   # Main borders
            'border_focus': '#00d4aa',     # Focused elements
            
            # Status indicators
            'status_online': '#00c851',    # Model loaded/running
            'status_loading': '#ff8f00',   # Model loading
            'status_offline': '#7d8590',   # Model stopped
        }
    
    def get_main_window_style(self):
        """🪟 Get main window stylesheet"""
        return f"""
        QMainWindow {{
            background-color: {self.colors['bg_primary']};
            color: {self.colors['text_primary']};
            border: none;
        }}
        
        QWidget {{
            background-color: {self.colors['bg_primary']};
            color: {self.colors['text_primary']};
            font-family: 'Consolas', 'Monaco', monospace;
        }}
        
        QSplitter::handle {{
            background-color: {self.colors['border_primary']};
            width: 2px;
            height: 2px;
        }}
        
        QSplitter::handle:hover {{
            background-color: {self.colors['accent_primary']};
        }}
        """
    
    def get_panel_style(self):
        """📋 Get panel stylesheet"""
        return f"""
        QWidget {{
            background-color: {self.colors['bg_secondary']};
            border: 1px solid {self.colors['border_primary']};
            border-radius: 8px;
            margin: 4px;
        }}
        
        QGroupBox {{
            background-color: {self.colors['bg_tertiary']};
            border: 1px solid {self.colors['border_primary']};
            border-radius: 6px;
            margin: 8px;
            padding-top: 20px;
            font-weight: bold;
            color: {self.colors['text_primary']};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
            color: {self.colors['accent_primary']};
        }}
        """
    
    def get_button_style(self, button_type='primary'):
        """🔲 Get button stylesheet"""
        if button_type == 'primary':
            bg_color = self.colors['accent_primary']
            hover_color = '#00f5c4'
        elif button_type == 'secondary':
            bg_color = self.colors['accent_secondary']
            hover_color = '#9333ea'
        elif button_type == 'danger':
            bg_color = self.colors['accent_danger']
            hover_color = '#ff5470'
        elif button_type == 'success':
            bg_color = self.colors['accent_success']
            hover_color = '#00e676'
        else:
            bg_color = self.colors['bg_tertiary']
            hover_color = self.colors['border_primary']
        
        return f"""
        QPushButton {{
            background-color: {bg_color};
            color: {self.colors['text_primary']};
            border: 1px solid {self.colors['border_primary']};
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 9pt;
        }}
        
        QPushButton:hover {{
            background-color: {hover_color};
            border-color: {bg_color};
        }}
        
        QPushButton:pressed {{
            background-color: {bg_color};
            border-color: {hover_color};
        }}
        
        QPushButton:disabled {{
            background-color: {self.colors['bg_tertiary']};
            color: {self.colors['text_muted']};
            border-color: {self.colors['text_muted']};
        }}
        """
    
    def get_input_style(self):
        """📝 Get input field stylesheet"""
        return f"""
        QLineEdit, QTextEdit, QComboBox {{
            background-color: {self.colors['bg_tertiary']};
            color: {self.colors['text_primary']};
            border: 1px solid {self.colors['border_primary']};
            border-radius: 4px;
            padding: 6px;
            font-size: 9pt;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border-color: {self.colors['border_focus']};
            background-color: {self.colors['bg_secondary']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            background-color: {self.colors['accent_primary']};
            border-radius: 3px;
        }}
        
        QComboBox::down-arrow {{
            width: 12px;
            height: 12px;
        }}
        """
    
    def get_tab_style(self):
        """📑 Get tab widget stylesheet"""
        return f"""
        QTabWidget::pane {{
            background-color: {self.colors['bg_secondary']};
            border: 1px solid {self.colors['border_primary']};
            border-radius: 6px;
        }}
        
        QTabBar::tab {{
            background-color: {self.colors['bg_tertiary']};
            color: {self.colors['text_secondary']};
            border: 1px solid {self.colors['border_primary']};
            border-bottom: none;
            border-radius: 6px 6px 0 0;
            padding: 8px 16px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {self.colors['accent_primary']};
            color: {self.colors['text_primary']};
            border-color: {self.colors['accent_primary']};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {self.colors['bg_secondary']};
            color: {self.colors['text_primary']};
        }}
        """
    
    def get_progress_style(self):
        """📊 Get progress bar stylesheet"""
        return f"""
        QProgressBar {{
            background-color: {self.colors['bg_tertiary']};
            border: 1px solid {self.colors['border_primary']};
            border-radius: 4px;
            text-align: center;
            color: {self.colors['text_primary']};
            font-weight: bold;
        }}
        
        QProgressBar::chunk {{
            background-color: {self.colors['accent_primary']};
            border-radius: 3px;
        }}
        """
    
    def get_status_indicator_style(self, status='offline'):
        """🔴 Get status indicator stylesheet"""
        if status == 'online':
            color = self.colors['status_online']
        elif status == 'loading':
            color = self.colors['status_loading']
        else:
            color = self.colors['status_offline']
        
        return f"""
        QLabel {{
            background-color: {color};
            border-radius: 6px;
            min-width: 12px;
            max-width: 12px;
            min-height: 12px;
            max-height: 12px;
        }}
        """
