"""
📋 Left Panel - System Control Center
=====================================
Role: System status and model management
SOLID: Single responsibility for left-side controls
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, 
                               QPushButton, QComboBox, QLineEdit, QListWidget,
                               QListWidgetItem, QHBoxLayout, QProgressBar)
from PySide6.QtCore import Signal, QTimer
from PySide6.QtGui import QFont

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))

from Core.hardware_detector import HardwareDetector
from GUI.theme_manager import ThemeManager


class LeftPanel(QWidget):
    """
    📋 Left Control Panel
    =====================
    Role: System Status & Quick Launch
    Pattern: Vertical layout with grouped sections
    """
    
    # Signals for inter-panel communication
    model_launch_requested = Signal(dict)  # Emit model config to launch
    model_stop_requested = Signal(str)     # Emit model ID to stop
    status_update = Signal(str)            # Emit status updates
    model_type_filter_changed = Signal(str)  # Emit when model type filter changes
    status_changed = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.hardware_detector = HardwareDetector()
        
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        self._start_monitoring()
    
    def _setup_ui(self):
        """🏗️ Create left panel layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # System Status Section
        self.system_group = self._create_system_status_section()
        layout.addWidget(self.system_group)
        
        # Quick Launch Section
        self.launch_group = self._create_quick_launch_section()
        layout.addWidget(self.launch_group)
        
        # Active Models Section
        self.models_group = self._create_active_models_section()
        layout.addWidget(self.models_group)
        
        # Stretch to push everything to top
        layout.addStretch()
    
    def _create_system_status_section(self):
        """🖥️ Create system status display"""
        group = QGroupBox("🖥️ System Status")
        layout = QVBoxLayout(group)
        
        # Platform info
        self.platform_label = QLabel("🖥️ Platform: Windows 11")
        layout.addWidget(self.platform_label)
        
        # RAM status with progress bar
        ram_layout = QHBoxLayout()
        self.ram_label = QLabel("🧠 RAM:")
        self.ram_progress = QProgressBar()
        self.ram_progress.setMaximum(100)
        self.ram_progress.setValue(0)
        self.ram_text = QLabel("0.0 / 0.0 GB")
        
        ram_layout.addWidget(self.ram_label)
        ram_layout.addWidget(self.ram_progress, 1)
        ram_layout.addWidget(self.ram_text)
        layout.addLayout(ram_layout)
        
        # GPU status
        self.gpu_label = QLabel("🎮 GPU: Detecting...")
        layout.addWidget(self.gpu_label)
        
        # CUDA status
        self.cuda_label = QLabel("⚡ CUDA: Checking...")
        layout.addWidget(self.cuda_label)
        
        return group
    
    def _create_quick_launch_section(self):
        """🚀 Create improved quick launch controls with dropdown organization"""
        group = QGroupBox("🚀 Model Launcher")
        layout = QVBoxLayout(group)
        
        # Model Type Selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("📂 Model Type:"))
        self.model_type_combo = QComboBox()
        self.model_type_combo.addItems([
            "🤖 Text Models (LLM)",
            "💻 Code Models", 
            "🖼️ Vision Models",
            "🔊 Audio Models (TTS/STT)",
            "📊 Embedding Models",
            "🧠 All Models"
        ])
        self.model_type_combo.currentTextChanged.connect(self._on_model_type_changed)
        type_layout.addWidget(self.model_type_combo)
        layout.addLayout(type_layout)
        
        # Model Format Filter
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("📁 Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "All Formats",
            "GGUF (llama.cpp)", 
            "SafeTensors (HF)",
            "PyTorch (bin)",
            "GGML (legacy)"
        ])
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)
        
        # Model Selection Dropdown
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("🎯 Model:"))
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(200)
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)
        
        # Model Info Display
        self.model_info_label = QLabel("ℹ️ Select a model to see details")
        self.model_info_label.setWordWrap(True)
        self.model_info_label.setStyleSheet("color: #888; font-size: 11px; padding: 5px;")
        layout.addWidget(self.model_info_label)
        
        # Launch Controls
        button_layout = QHBoxLayout()
        self.launch_btn = QPushButton("🚀 Load Model")
        self.launch_btn.clicked.connect(self._launch_selected_model)
        self.stop_btn = QPushButton("⏹️ Unload")
        self.stop_btn.clicked.connect(self._stop_current_model)
        self.stop_btn.setEnabled(False)
        
        button_layout.addWidget(self.launch_btn)
        button_layout.addWidget(self.stop_btn)
        layout.addLayout(button_layout)
        
        # Initialize model list
        self._load_available_models()
        
        return group
    
    def _load_available_models(self):
        """📋 Initialize model dropdown"""
        # This will be populated when model discovery completes
        self.model_combo.addItem("Loading models...")
    
    def populate_models(self, discovered_models):
        """📋 Populate model dropdown with discovered models"""
        self.model_combo.clear()
        self.model_combo.addItem("Select a model...")
        
        current_filter = self.model_type_combo.currentText()
        format_filter = self.format_combo.currentText()
        
        for model_type, models in discovered_models.items():
            # Filter by type if not "All Models"
            if current_filter != "🧠 All Models":
                filter_map = {
                    "🤖 Text Models (LLM)": "text",
                    "💻 Code Models": "code", 
                    "🖼️ Vision Models": "vision",
                    "🔊 Audio Models (TTS/STT)": "audio",
                    "📊 Embedding Models": "embedding"
                }
                if model_type != filter_map.get(current_filter):
                    continue
            
            # Add models of this type
            for model in models:
                model_name = model.get('name', 'Unknown Model')
                model_size = model.get('size_gb', 0)
                display_name = f"{model_name} ({model_size:.1f}GB)"
                self.model_combo.addItem(display_name)
                
        # Update model info
        if self.model_combo.count() > 1:
            self.model_info_label.setText(f"ℹ️ {self.model_combo.count()-1} models available")
        else:
            self.model_info_label.setText("ℹ️ No models found matching filters")
        
    def _on_model_type_changed(self, model_type):
        """Handle model type filter change"""
        # Emit signal to main panel to filter models
        self.model_type_filter_changed.emit(model_type)
        self._update_model_dropdown()
        
    def _on_format_changed(self, format_filter):
        """Handle format filter change"""
        self._update_model_dropdown()
        
    def _update_model_dropdown(self):
        """Update model dropdown based on filters"""
        # Clear current items
        self.model_combo.clear()
        
        # Add filtered models (will be implemented with model discovery)
        self.model_combo.addItem("Select a model...")
        
    def _launch_selected_model(self):
        """Launch the selected model"""
        selected_model = self.model_combo.currentText()
        if selected_model and selected_model != "Select a model...":
            # Emit signal to load model
            model_config = {'name': selected_model}
            self.model_launch_requested.emit(model_config)
            self.stop_btn.setEnabled(True)
            self.launch_btn.setText("🔄 Loading...")
            
    def _stop_current_model(self):
        """Stop the current model"""
        self.model_stop_requested.emit("current")
        self.stop_btn.setEnabled(False)
        self.launch_btn.setText("🚀 Load Model")
    
    def _create_active_models_section(self):
        """📊 Create active models display"""
        group = QGroupBox("📊 Active Models")
        layout = QVBoxLayout(group)
        
        # Models list
        self.models_list = QListWidget()
        self.models_list.setMaximumHeight(120)
        layout.addWidget(self.models_list)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        self.stop_all_button = QPushButton("🛑 Stop All")
        self.refresh_button = QPushButton("🔄 Refresh")
        
        buttons_layout.addWidget(self.stop_all_button)
        buttons_layout.addWidget(self.refresh_button)
        layout.addLayout(buttons_layout)
        
        return group
    
    def _apply_styles(self):
        """🎨 Apply sci-fi theme styles"""
        self.setStyleSheet(self.theme_manager.get_panel_style())
        
        # Style buttons (launch_btn styling handled in quick launch section)
        self.launch_btn.setStyleSheet(self.theme_manager.get_button_style('primary'))
        self.stop_btn.setStyleSheet(self.theme_manager.get_button_style('danger'))
        self.stop_all_button.setStyleSheet(self.theme_manager.get_button_style('danger'))
        self.refresh_button.setStyleSheet(self.theme_manager.get_button_style('secondary'))
        
        # Style inputs
        self.model_combo.setStyleSheet(self.theme_manager.get_input_style())
        
        # Style progress bar
        self.ram_progress.setStyleSheet(self.theme_manager.get_progress_style())
    
    def _connect_signals(self):
        """🔗 Connect button signals"""
        # Note: launch_btn signals are connected in _create_quick_launch_section
        self.stop_all_button.clicked.connect(self._on_stop_all_clicked)
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
    
    def _start_monitoring(self):
        """⏰ Start system monitoring"""
        # Update system info immediately
        self._update_system_info()
        
        # Set up timer for regular updates
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._update_system_info)
        self.monitor_timer.start(2000)  # Update every 2 seconds
    
    def _update_system_info(self):
        """📊 Update system information display"""
        try:
            # Get hardware info
            hw_info = self.hardware_detector.get_hardware_summary()
            
            # Update platform
            self.platform_label.setText(f"🖥️ Platform: {hw_info.get('platform', 'Unknown')}")
            
            # Update RAM
            ram_total = hw_info.get('ram_total_gb', 0)
            ram_used = hw_info.get('ram_used_gb', 0)
            ram_percent = int((ram_used / ram_total * 100) if ram_total > 0 else 0)
            
            self.ram_progress.setValue(ram_percent)
            self.ram_text.setText(f"{ram_used:.1f} / {ram_total:.1f} GB")
            
            # Update GPU
            gpu_info = hw_info.get('gpu_name', 'No GPU detected')
            gpu_memory = hw_info.get('gpu_memory_gb', 0)
            if gpu_memory > 0:
                self.gpu_label.setText(f"🎮 GPU: {gpu_info} ({gpu_memory:.0f}GB)")
            else:
                self.gpu_label.setText(f"🎮 GPU: {gpu_info}")
            
            # Update CUDA
            cuda_available = hw_info.get('cuda_available', False)
            cuda_version = hw_info.get('cuda_version', 'N/A')
            if cuda_available:
                self.cuda_label.setText(f"⚡ CUDA: {cuda_version} Available")
            else:
                self.cuda_label.setText("⚡ CUDA: Not Available")
            
            # Emit status update
            self.status_changed.emit({
                'component': 'system',
                'ram_percent': ram_percent,
                'gpu_available': cuda_available
            })
            
        except Exception as e:
            print(f"Error updating system info: {e}")
    
    def _on_stop_all_clicked(self):
        """🛑 Handle stop all button click"""
        self.model_stop_requested.emit("all")
        self.models_list.clear()
    
    def _on_refresh_clicked(self):
        """🔄 Handle refresh button click"""
        self._update_system_info()
        self.status_changed.emit({'component': 'refresh', 'action': 'manual_refresh'})
    
    def _add_active_model(self, model_name: str, port: int, status: str = 'running'):
        """📊 Add model to active models list"""
        status_icon = {
            'running': '🟢',
            'loading': '🟡',
            'error': '🔴',
            'stopped': '⚫'
        }.get(status, '🟡')
        
        item_text = f"{status_icon} {model_name} (Port: {port})"
        item = QListWidgetItem(item_text)
        self.models_list.addItem(item)
    
    def update_active_models(self, models_data: list):
        """🔄 Update active models from external source"""
        self.models_list.clear()
        for model in models_data:
            self._add_active_model(
                model.get('name', 'Unknown'),
                model.get('port', 0),
                model.get('status', 'unknown')
            )
