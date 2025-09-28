"""
🚀 Universal Model Launcher V4 - Main Window
==============================================
Role: Main UI orchestrator with sci-fi aesthetic
SOLID: Single responsibility for window management
"""

import sys
import asyncio
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                               QVBoxLayout, QTabWidget, QSplitter, QStatusBar)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QObject
from PySide6.QtGui import QFont, QPalette, QColor

# Add Version4 to path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from .theme_manager import ThemeManager
from .panels.left_panel import LeftPanel
from .panels.main_panel import MainPanel
from .panels.right_panel import RightPanel
from .panels.status_bar import SciFiStatusBar
from .animations.ui_animator import UIAnimator

# Backend integration
from main import UniversalModelLauncher
from Core.hybrid_smart_loader import HybridSmartLoader


class BackendWorker(QObject):
    """Worker thread for backend operations"""
    
    # Signals for communication with GUI
    backend_ready = Signal()
    model_loaded = Signal(dict)  # model info
    model_unloaded = Signal(str)  # model id
    performance_update = Signal(dict)  # performance data
    error_occurred = Signal(str)  # error message
    
    def __init__(self):
        super().__init__()
        self.backend = None
        self.hybrid_loader = None
    
    async def initialize_backend(self):
        """Initialize the backend system"""
        try:
            self.backend = UniversalModelLauncher()
            success = await self.backend.initialize(enable_api=True)
            
            if success:
                # Get hybrid smart loader
                if hasattr(self.backend, '_components'):
                    self.hybrid_loader = self.backend._components.get('hybrid_smart_loader')
                
                self.backend_ready.emit()
                return True
            else:
                self.error_occurred.emit("Backend initialization failed")
                return False
                
        except Exception as e:
            self.error_occurred.emit(f"Backend error: {e}")
            return False
    
    async def load_model_smart(self, input_data: str, config: dict = None):
        """Load model using hybrid smart loader"""
        try:
            if self.hybrid_loader:
                # Create smart loading plan
                plan = await self.hybrid_loader.create_smart_loading_plan(input_data)
                
                # Execute the plan (simplified)
                if plan.selected_model:
                    model_info = {
                        'name': plan.selected_model.name,
                        'size': plan.selected_model.size,
                        'type': plan.selected_model.model_type,
                        'port': config.get('port', 8080) if config else 8080,
                        'status': 'loaded'
                    }
                    self.model_loaded.emit(model_info)
                    return True
            
            return False
            
        except Exception as e:
            self.error_occurred.emit(f"Model loading error: {e}")
            return False


class UniversalModelLauncherUI(QMainWindow):
    """
    🎯 Main Application Window
    ===========================
    Role: UI Team Captain - Coordinates all panels
    Pattern: Modular 3-panel layout with animations
    """
    
    # Signals for inter-panel communication
    model_loaded = Signal(str)
    model_unloaded = Signal(str)
    system_status_updated = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 Universal Model Launcher V4")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Core components
        self.theme_manager = ThemeManager()
        self.animator = UIAnimator()
        
        # Backend integration
        self.backend_worker = BackendWorker()
        self.backend_thread = QThread()
        self.backend_worker.moveToThread(self.backend_thread)
        
        # Model registry for port management
        self.loaded_models = {}  # model_name -> {port, status, info}
        self.next_port = 8080
        
        # Initialize UI
        self._setup_ui()
        self._apply_theme()
        self._setup_animations()
        self._connect_signals()
        self._connect_backend()
        
        # Start systems
        self._setup_timers()
        self._start_backend()
    
    def _start_backend(self):
        """🔧 Start the backend system"""
        print("🚀 Starting backend integration...")
        self.backend_thread.start()
        
        # Initialize backend asynchronously
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def init_backend():
            await self.backend_worker.initialize_backend()
        
        # Run backend initialization in thread
        self.backend_thread.started.connect(
            lambda: asyncio.run(init_backend())
        )
    
    def _setup_ui(self):
        """🏗️ Create the main UI layout"""
        # Central widget with 3-panel layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal splitter
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Create panels
        self.left_panel = LeftPanel()
        self.main_panel = MainPanel()
        self.right_panel = RightPanel()
        
        # Add panels to splitter
        main_splitter.addWidget(self.left_panel)
        main_splitter.addWidget(self.main_panel)
        main_splitter.addWidget(self.right_panel)
        
        # Set panel sizes (280px | flexible | 320px)
        main_splitter.setSizes([280, 800, 320])
        main_splitter.setCollapsible(0, False)  # Left panel always visible
        main_splitter.setCollapsible(2, False)  # Right panel always visible
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_splitter)
        
        # Custom status bar
        self.sci_fi_status_bar = SciFiStatusBar()
        self.setStatusBar(self.sci_fi_status_bar)
    
    def _apply_theme(self):
        """🎨 Apply sci-fi theme to the application"""
        self.setStyleSheet(self.theme_manager.get_main_window_style())
        
        # Set application font
        font = QFont("Consolas", 9)  # Sci-fi monospace font
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
    
    def _setup_animations(self):
        """✨ Setup UI animations and transitions"""
        # Animate window appearance
        self.animator.fade_in_widget(self, duration=800)
        
        # Setup panel animations
        self.animator.setup_panel_transitions(self.left_panel)
        self.animator.setup_panel_transitions(self.main_panel)
        self.animator.setup_panel_transitions(self.right_panel)
    
    def _connect_signals(self):
        """🔗 Connect inter-panel communication signals"""
        # Left panel to main panel - MODEL LOADING
        self.left_panel.model_launch_requested.connect(self._handle_model_launch)
        self.left_panel.model_stop_requested.connect(self._handle_model_stop)
        
        # Main panel to right panel
        self.main_panel.performance_updated.connect(self.right_panel.update_performance)
        self.main_panel.log_message.connect(self.right_panel.add_log_entry)
        
        # Right panel to left panel
        self.right_panel.queue_changed.connect(self.left_panel.update_active_models)
        
        # Status bar updates
        self.left_panel.status_changed.connect(self.sci_fi_status_bar.update_status)
        self.main_panel.status_changed.connect(self.sci_fi_status_bar.update_status)
        self.right_panel.status_changed.connect(self.sci_fi_status_bar.update_status)
    
    def _connect_backend(self):
        """🔗 Connect backend worker signals"""
        self.backend_worker.backend_ready.connect(self._on_backend_ready)
        self.backend_worker.model_loaded.connect(self._on_model_loaded)
        self.backend_worker.model_unloaded.connect(self._on_model_unloaded)
        self.backend_worker.error_occurred.connect(self._on_backend_error)
    
    def _handle_model_launch(self, config: dict):
        """🚀 Handle model launch request from GUI"""
        model_name = config.get('model', 'unknown')
        
        # Assign port for external access
        port = self._get_next_port()
        config['port'] = port
        
        # Add to loading queue
        self.loaded_models[model_name] = {
            'port': port,
            'status': 'loading',
            'config': config
        }
        
        # Update GUI immediately
        self._update_model_displays()
        
        # Start backend loading
        input_data = f"Load {model_name} for general use"
        
        # Use smart loader for automatic model selection
        async def load_model():
            await self.backend_worker.load_model_smart(input_data, config)
        
        # Execute in background
        import asyncio
        asyncio.create_task(load_model())
        
        # Log action
        self.right_panel.add_log_entry(f"Loading model: {model_name} on port {port}", "info")
    
    def _handle_model_stop(self, model_id: str):
        """🛑 Handle model stop request"""
        if model_id == "all":
            # Stop all models
            for model_name in list(self.loaded_models.keys()):
                self._stop_single_model(model_name)
        else:
            self._stop_single_model(model_id)
    
    def _stop_single_model(self, model_name: str):
        """🛑 Stop a single model"""
        if model_name in self.loaded_models:
            port = self.loaded_models[model_name]['port']
            del self.loaded_models[model_name]
            
            self._update_model_displays()
            self.right_panel.add_log_entry(f"Stopped model: {model_name} (port {port})", "warning")
    
    def _get_next_port(self) -> int:
        """🔌 Get next available port"""
        port = self.next_port
        self.next_port += 1
        return port
    
    def _update_model_displays(self):
        """🔄 Update all model displays in GUI"""
        # Convert to format expected by panels
        model_list = []
        for name, info in self.loaded_models.items():
            model_list.append({
                'name': name,
                'port': info['port'],
                'status': info['status']
            })
        
        # Update left panel active models
        self.left_panel.update_active_models(model_list)
        
        # Update status bar
        self.sci_fi_status_bar.update_status({
            'component': 'models',
            'loaded_count': len([m for m in model_list if m['status'] == 'running'])
        })
    
    def _on_backend_ready(self):
        """✅ Backend is ready"""
        self.right_panel.add_log_entry("Backend system initialized successfully", "success")
        self.sci_fi_status_bar.update_status({
            'component': 'connection',
            'connected': True
        })
    
    def _on_model_loaded(self, model_info: dict):
        """✅ Model loaded successfully"""
        model_name = model_info.get('name', 'unknown')
        port = model_info.get('port', 0)
        
        if model_name in self.loaded_models:
            self.loaded_models[model_name]['status'] = 'running'
            self._update_model_displays()
            
            self.right_panel.add_log_entry(
                f"Model loaded: {model_name} (port {port}) - Ready for connections", 
                "success"
            )
            
            # Create port registry file for external tools
            self._update_port_registry()
    
    def _on_model_unloaded(self, model_id: str):
        """🛑 Model unloaded"""
        self.right_panel.add_log_entry(f"Model unloaded: {model_id}", "info")
    
    def _on_backend_error(self, error_msg: str):
        """❌ Backend error occurred"""
        self.right_panel.add_log_entry(f"Backend error: {error_msg}", "error")
    
    def _update_port_registry(self):
        """📝 Update port registry for external tools"""
        registry = {}
        for name, info in self.loaded_models.items():
            if info['status'] == 'running':
                registry[name] = {
                    'port': info['port'],
                    'status': info['status'],
                    'endpoint': f"http://localhost:{info['port']}",
                    'type': info['config'].get('model', 'unknown')
                }
        
        # Write to file for external tools to read
        import json
        registry_path = Path(__file__).parent.parent / "model_registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
        
        self.right_panel.add_log_entry("Port registry updated for external tools", "info")
    
    def _setup_timers(self):
        """⏰ Setup real-time update timers"""
        # Performance monitoring timer
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self._update_performance)
        self.performance_timer.start(1000)  # Update every second
        
        # Animation timer for smooth effects
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animations)
        self.animation_timer.start(16)  # 60 FPS for smooth animations
    
    def _update_performance(self):
        """📊 Update real-time performance data"""
        # Get system performance data
        performance_data = {
            'memory_usage': 78,  # Placeholder - integrate with hardware_detector
            'gpu_usage': 65,
            'temperature': 78,
            'generation_speed': 45
        }
        
        # Emit to right panel
        self.right_panel.update_performance(performance_data)
        
        # Update status bar
        self.sci_fi_status_bar.update_system_info(performance_data)
    
    def _update_animations(self):
        """✨ Update animation states for smooth effects"""
        self.animator.update_frame()
    
    def closeEvent(self, event):
        """🔚 Handle application shutdown"""
        # Animate window closing
        self.animator.fade_out_widget(self, duration=400)
        
        # Stop timers
        self.performance_timer.stop()
        self.animation_timer.stop()
        
        # Accept close event after animation
        QTimer.singleShot(400, lambda: event.accept())
        event.ignore()  # Ignore initially to allow animation


def main():
    """🚀 Launch the Universal Model Launcher UI"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Universal Model Launcher V4")
    app.setApplicationVersion("4.0.0")
    app.setOrganizationName("Kalponic Studio")
    
    # Create and show main window
    window = UniversalModelLauncherUI()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
