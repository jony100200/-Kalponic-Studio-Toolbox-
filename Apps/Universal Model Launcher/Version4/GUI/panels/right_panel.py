"""
📊 Right Panel - Live Monitoring
=================================
Role: Real-time system monitoring and management
SOLID: Single responsibility for status display
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, 
                               QProgressBar, QListWidget, QListWidgetItem,
                               QHBoxLayout, QPushButton, QTextEdit)
from PySide6.QtCore import Signal, QTimer
from PySide6.QtGui import QFont

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))

from GUI.theme_manager import ThemeManager


class RightPanel(QWidget):
    """
    📊 Right Monitoring Panel
    =========================
    Role: Live Performance & Queue Management
    Pattern: Vertical layout with monitoring sections
    """
    
    # Signals for inter-panel communication
    queue_changed = Signal(list)
    status_changed = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        self._start_monitoring()
    
    def _setup_ui(self):
        """🏗️ Create right panel layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Live Performance Section
        self.performance_group = self._create_performance_section()
        layout.addWidget(self.performance_group)
        
        # Model Queue Section
        self.queue_group = self._create_queue_section()
        layout.addWidget(self.queue_group)
        
        # Activity Log Section
        self.log_group = self._create_log_section()
        layout.addWidget(self.log_group)
        
        # Stretch to distribute space
        layout.addStretch()
    
    def _create_performance_section(self):
        """📈 Create live performance monitoring"""
        group = QGroupBox("📈 Live Performance")
        layout = QVBoxLayout(group)
        
        # Memory Usage
        memory_layout = QVBoxLayout()
        memory_layout.addWidget(QLabel("Memory Usage:"))
        self.memory_progress = QProgressBar()
        self.memory_progress.setMaximum(100)
        self.memory_progress.setValue(0)
        self.memory_text = QLabel("0%")
        memory_layout.addWidget(self.memory_progress)
        memory_layout.addWidget(self.memory_text)
        layout.addLayout(memory_layout)
        
        # GPU Utilization
        gpu_layout = QVBoxLayout()
        gpu_layout.addWidget(QLabel("GPU Utilization:"))
        self.gpu_progress = QProgressBar()
        self.gpu_progress.setMaximum(100)
        self.gpu_progress.setValue(0)
        self.gpu_text = QLabel("0%")
        gpu_layout.addWidget(self.gpu_progress)
        gpu_layout.addWidget(self.gpu_text)
        layout.addLayout(gpu_layout)
        
        # Generation Speed
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Generation Speed:"))
        self.speed_label = QLabel("0 tok/s")
        speed_layout.addWidget(self.speed_label, 1)
        layout.addLayout(speed_layout)
        
        # Temperature
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Temperature:"))
        self.temp_label = QLabel("0°C")
        temp_layout.addWidget(self.temp_label, 1)
        layout.addLayout(temp_layout)
        
        return group
    
    def _create_queue_section(self):
        """📋 Create model queue management"""
        group = QGroupBox("📋 Model Queue")
        layout = QVBoxLayout(group)
        
        # Queue list
        self.queue_list = QListWidget()
        self.queue_list.setMaximumHeight(120)
        layout.addWidget(self.queue_list)
        
        # Queue control buttons
        buttons_layout = QHBoxLayout()
        self.move_up_button = QPushButton("⬆️")
        self.move_down_button = QPushButton("⬇️")
        self.add_button = QPushButton("➕")
        self.remove_button = QPushButton("➖")
        
        for btn in [self.move_up_button, self.move_down_button, self.add_button, self.remove_button]:
            btn.setMaximumWidth(40)
            buttons_layout.addWidget(btn)
        
        layout.addLayout(buttons_layout)
        
        # Populate with placeholder data
        self._populate_queue()
        
        return group
    
    def _create_log_section(self):
        """📝 Create activity log"""
        group = QGroupBox("📝 Activity Log")
        layout = QVBoxLayout(group)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(150)
        layout.addWidget(self.log_display)
        
        # Log controls
        controls_layout = QHBoxLayout()
        self.filter_button = QPushButton("🔍 Filter")
        self.export_button = QPushButton("📄 Export")
        self.clear_log_button = QPushButton("🗑️ Clear")
        
        controls_layout.addWidget(self.filter_button)
        controls_layout.addWidget(self.export_button)
        controls_layout.addWidget(self.clear_log_button)
        layout.addLayout(controls_layout)
        
        # Add initial log entries
        self._add_initial_logs()
        
        return group
    
    def _apply_styles(self):
        """🎨 Apply sci-fi theme styles"""
        self.setStyleSheet(self.theme_manager.get_panel_style())
        
        # Style progress bars
        for progress in [self.memory_progress, self.gpu_progress]:
            progress.setStyleSheet(self.theme_manager.get_progress_style())
        
        # Style buttons
        button_groups = [
            ([self.move_up_button, self.move_down_button], 'secondary'),
            ([self.add_button], 'primary'),
            ([self.remove_button], 'danger'),
            ([self.filter_button, self.export_button], 'secondary'),
            ([self.clear_log_button], 'danger')
        ]
        
        for buttons, style_type in button_groups:
            for button in buttons:
                button.setStyleSheet(self.theme_manager.get_button_style(style_type))
        
        # Style log display
        self.log_display.setStyleSheet(self.theme_manager.get_input_style())
    
    def _connect_signals(self):
        """🔗 Connect button signals"""
        self.move_up_button.clicked.connect(self._move_queue_item_up)
        self.move_down_button.clicked.connect(self._move_queue_item_down)
        self.add_button.clicked.connect(self._add_queue_item)
        self.remove_button.clicked.connect(self._remove_queue_item)
        self.filter_button.clicked.connect(self._filter_logs)
        self.export_button.clicked.connect(self._export_logs)
        self.clear_log_button.clicked.connect(self._clear_logs)
    
    def _start_monitoring(self):
        """⏰ Start monitoring timers"""
        # Performance update timer
        self.perf_timer = QTimer()
        self.perf_timer.timeout.connect(self._simulate_performance_update)
        self.perf_timer.start(1500)  # Update every 1.5 seconds
    
    def _populate_queue(self):
        """📋 Populate queue with placeholder data"""
        queue_items = [
            ("🟢 mistral-7b", "Loaded"),
            ("🟡 llama-13b", "Queued"),
            ("🔴 whisper-large", "Failed")
        ]
        
        for name, status in queue_items:
            item = QListWidgetItem(f"{name} ({status})")
            self.queue_list.addItem(item)
    
    def _add_initial_logs(self):
        """📝 Add initial log entries"""
        import datetime
        
        logs = [
            "14:32 Model loaded successfully",
            "14:30 Vision analysis complete",
            "14:28 Audio transcribed (7.8s)",
            "14:25 System initialized"
        ]
        
        for log in logs:
            self.log_display.append(log)
    
    def _simulate_performance_update(self):
        """📊 Simulate performance data updates"""
        import random
        
        # Simulate realistic performance fluctuations
        memory_usage = random.randint(70, 90)
        gpu_usage = random.randint(60, 80)
        generation_speed = random.randint(35, 50)
        temperature = random.randint(65, 85)
        
        self.update_performance({
            'memory_usage': memory_usage,
            'gpu_usage': gpu_usage,
            'generation_speed': generation_speed,
            'temperature': temperature
        })
    
    def update_performance(self, data: dict):
        """📊 Update performance displays"""
        try:
            # Update memory
            memory_usage = data.get('memory_usage', 0)
            self.memory_progress.setValue(memory_usage)
            self.memory_text.setText(f"{memory_usage}%")
            
            # Update GPU
            gpu_usage = data.get('gpu_usage', 0)
            self.gpu_progress.setValue(gpu_usage)
            self.gpu_text.setText(f"{gpu_usage}%")
            
            # Update generation speed
            speed = data.get('generation_speed', 0)
            self.speed_label.setText(f"{speed} tok/s")
            
            # Update temperature
            temp = data.get('temperature', 0)
            self.temp_label.setText(f"{temp}°C")
            
            # Change color based on performance
            if memory_usage > 85 or gpu_usage > 85 or temp > 80:
                color = "#ff8f00"  # Warning orange
            elif memory_usage > 95 or temp > 90:
                color = "#ff3347"  # Danger red
            else:
                color = "#00d4aa"  # Normal teal
            
            # Apply color to progress bars (simplified)
            for progress in [self.memory_progress, self.gpu_progress]:
                style = progress.styleSheet()
                if "background-color:" in style:
                    # Update existing color
                    import re
                    style = re.sub(r'background-color: [^;]+;', f'background-color: {color};', style)
                else:
                    style += f"QProgressBar::chunk {{ background-color: {color}; }}"
                progress.setStyleSheet(style)
            
        except Exception as e:
            print(f"Error updating performance: {e}")
    
    def add_log_entry(self, message: str, level: str = "info"):
        """📝 Add new log entry"""
        import datetime
        
        timestamp = datetime.datetime.now().strftime("%H:%M")
        
        # Add emoji based on level
        emoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅'
        }.get(level, 'ℹ️')
        
        log_entry = f"{timestamp} {emoji} {message}"
        self.log_display.append(log_entry)
        
        # Auto-scroll to bottom
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _move_queue_item_up(self):
        """⬆️ Move selected queue item up"""
        current_row = self.queue_list.currentRow()
        if current_row > 0:
            item = self.queue_list.takeItem(current_row)
            self.queue_list.insertItem(current_row - 1, item)
            self.queue_list.setCurrentRow(current_row - 1)
            self.add_log_entry("Queue item moved up", "info")
    
    def _move_queue_item_down(self):
        """⬇️ Move selected queue item down"""
        current_row = self.queue_list.currentRow()
        if current_row < self.queue_list.count() - 1 and current_row >= 0:
            item = self.queue_list.takeItem(current_row)
            self.queue_list.insertItem(current_row + 1, item)
            self.queue_list.setCurrentRow(current_row + 1)
            self.add_log_entry("Queue item moved down", "info")
    
    def _add_queue_item(self):
        """➕ Add new queue item"""
        item = QListWidgetItem("🟡 new-model (Queued)")
        self.queue_list.addItem(item)
        self.add_log_entry("New model added to queue", "success")
    
    def _remove_queue_item(self):
        """➖ Remove selected queue item"""
        current_row = self.queue_list.currentRow()
        if current_row >= 0:
            item = self.queue_list.takeItem(current_row)
            if item:
                self.add_log_entry(f"Removed from queue: {item.text()}", "warning")
    
    def _filter_logs(self):
        """🔍 Filter log entries"""
        self.add_log_entry("Log filter applied", "info")
    
    def _export_logs(self):
        """📄 Export log entries"""
        self.add_log_entry("Logs exported successfully", "success")
    
    def _clear_logs(self):
        """🗑️ Clear all log entries"""
        self.log_display.clear()
        self.add_log_entry("Log history cleared", "info")
