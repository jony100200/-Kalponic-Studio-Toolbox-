"""
📊 Sci-Fi Status Bar
====================
Role: Bottom status display with real-time info
SOLID: Single responsibility for status communication
"""

from PySide6.QtWidgets import QStatusBar, QLabel, QHBoxLayout, QWidget, QProgressBar
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))

from GUI.theme_manager import ThemeManager


class SciFiStatusBar(QStatusBar):
    """
    📊 Professional Status Bar
    ==========================
    Role: System Status Display
    Pattern: Horizontal layout with status indicators
    """
    
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        
        self._setup_ui()
        self._apply_styles()
        self._start_updates()
    
    def _setup_ui(self):
        """🏗️ Create status bar layout"""
        # Main status widget
        status_widget = QWidget()
        layout = QHBoxLayout(status_widget)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # System status
        self.status_label = QLabel("🟢 Ready")
        layout.addWidget(self.status_label)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Memory info
        self.memory_label = QLabel("Memory: 15.2GB Free")
        layout.addWidget(self.memory_label)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # GPU info
        self.gpu_label = QLabel("GPU: RTX 4090 (78°C)")
        layout.addWidget(self.gpu_label)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Active models count
        self.models_label = QLabel("Models: 0 loaded")
        layout.addWidget(self.models_label)
        
        # Add stretch
        layout.addStretch()
        
        # Connection status
        self.connection_label = QLabel("🔗 Connected")
        layout.addWidget(self.connection_label)
        
        # Add to status bar
        self.addWidget(status_widget, 1)
    
    def _create_separator(self):
        """📏 Create visual separator"""
        separator = QLabel("|")
        separator.setStyleSheet(f"color: {self.theme_manager.colors['text_muted']};")
        return separator
    
    def _apply_styles(self):
        """🎨 Apply sci-fi theme"""
        self.setStyleSheet(f"""
        QStatusBar {{
            background-color: {self.theme_manager.colors['bg_secondary']};
            border-top: 1px solid {self.theme_manager.colors['border_primary']};
            color: {self.theme_manager.colors['text_primary']};
            font-family: 'Consolas', monospace;
            font-size: 9pt;
        }}
        
        QLabel {{
            color: {self.theme_manager.colors['text_primary']};
            padding: 2px 8px;
        }}
        """)
    
    def _start_updates(self):
        """⏰ Start status updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(3000)  # Update every 3 seconds
    
    def _update_status(self):
        """🔄 Update status information"""
        import random
        import datetime
        
        # Simulate real-time updates
        memory_free = random.uniform(12.0, 18.5)
        gpu_temp = random.randint(70, 85)
        
        self.memory_label.setText(f"Memory: {memory_free:.1f}GB Free")
        self.gpu_label.setText(f"GPU: RTX 4090 ({gpu_temp}°C)")
    
    def update_status(self, data: dict):
        """📊 Update status from external data"""
        component = data.get('component', '')
        
        if component == 'system':
            ram_percent = data.get('ram_percent', 0)
            gpu_available = data.get('gpu_available', False)
            
            # Update status icon based on system health
            if ram_percent > 90:
                self.status_label.setText("🟡 High Memory Usage")
            elif not gpu_available:
                self.status_label.setText("🟡 No GPU")
            else:
                self.status_label.setText("🟢 Ready")
        
        elif component == 'models':
            count = data.get('loaded_count', 0)
            self.models_label.setText(f"Models: {count} loaded")
        
        elif component == 'connection':
            connected = data.get('connected', True)
            if connected:
                self.connection_label.setText("🔗 Connected")
            else:
                self.connection_label.setText("❌ Disconnected")
    
    def update_system_info(self, performance_data: dict):
        """🖥️ Update system information display"""
        memory_usage = performance_data.get('memory_usage', 0)
        temperature = performance_data.get('temperature', 0)
        
        # Calculate free memory (assuming 32GB total)
        total_memory = 32.0
        used_memory = (memory_usage / 100) * total_memory
        free_memory = total_memory - used_memory
        
        self.memory_label.setText(f"Memory: {free_memory:.1f}GB Free")
        self.gpu_label.setText(f"GPU: RTX 4090 ({temperature}°C)")
        
        # Update status based on system health
        if memory_usage > 90 or temperature > 85:
            self.status_label.setText("🟡 System Under Load")
        elif temperature > 90:
            self.status_label.setText("🔴 High Temperature")
        else:
            self.status_label.setText("🟢 Ready")
