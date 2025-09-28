"""
🎯 Main Panel - Multi-Modal Interface
=====================================
Role: Primary content area with tabbed interface
SOLID: Single responsibility for main content display
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QTextEdit,
                               QLabel, QHBoxLayout, QPushButton, QFileDialog,
                               QGridLayout, QScrollArea, QFrame)
from PySide6.QtCore import Signal, QTimer, Qt
from PySide6.QtGui import QPixmap, QFont

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))

from GUI.theme_manager import ThemeManager


class MainPanel(QWidget):
    """
    🎯 Main Content Panel
    =====================
    Role: Multi-Modal Interface Hub
    Pattern: Tabbed interface for different AI modes
    """
    
    # Signals for inter-panel communication
    performance_updated = Signal(dict)
    log_message = Signal(str, str)  # message, level
    status_changed = Signal(dict)
    model_launch_requested = Signal(dict)  # model config for loading
    models_discovered = Signal(dict)  # discovered models for left panel
    models_discovered = Signal(dict)  # discovered models for left panel
    
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        
        # Initialize model discovery system
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))
        from Core.model_discovery import ModelDiscovery
        self.model_discovery = ModelDiscovery()
        
        # Loading state management
        self.loading_states = {}  # Track loading states for different operations
        self.current_loading_model = None
        
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        
        # Start model discovery in background with a timer
        from PySide6.QtCore import QTimer
        self.discovery_timer = QTimer()
        self.discovery_timer.setSingleShot(True)
        self.discovery_timer.timeout.connect(self._discover_models)
        self.discovery_timer.start(1000)  # Start discovery after 1 second
    
    def _setup_ui(self):
        """🏗️ Create main panel layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Create tabbed interface
        self.tab_widget = QTabWidget()
        
        # Add tabs
        self.model_browser_tab = self._create_model_browser_tab()
        self.vision_tab = self._create_vision_tab()
        self.audio_tab = self._create_audio_tab()
        self.chat_tab = self._create_chat_tab()
        self.settings_tab = self._create_settings_tab()
        
        self.tab_widget.addTab(self.model_browser_tab, "🔍 Model Browser")
        self.tab_widget.addTab(self.vision_tab, "🖼️ Vision")
        self.tab_widget.addTab(self.audio_tab, "🔊 Audio")
        self.tab_widget.addTab(self.chat_tab, "🧠 Chat")
        self.tab_widget.addTab(self.settings_tab, "⚙️ Settings")
        
        layout.addWidget(self.tab_widget)
    
    def _create_model_browser_tab(self):
        """🔍 Create enhanced model browser with filtering"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header with stats
        header_layout = QHBoxLayout()
        self.browser_header = QLabel("🔍 Discovered Models")
        self.browser_header.setFont(QFont("Consolas", 12, QFont.Bold))
        self.models_count_label = QLabel("Loading...")
        self.models_count_label.setStyleSheet("color: #888; font-size: 10px;")
        header_layout.addWidget(self.browser_header)
        header_layout.addStretch()
        header_layout.addWidget(self.models_count_label)
        layout.addLayout(header_layout)
        
        # Advanced Filter Bar
        filter_frame = QFrame()
        filter_frame.setStyleSheet("QFrame { background: #2a2a2a; border-radius: 5px; padding: 5px; }")
        filter_layout = QHBoxLayout(filter_frame)
        
        # Search input
        from PySide6.QtWidgets import QLineEdit, QComboBox
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search models by name...")
        self.search_input.textChanged.connect(self._filter_models)
        filter_layout.addWidget(self.search_input, 2)
        
        # Type filter
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "🤖 Text", "💻 Code", "🖼️ Vision", "🔊 Audio", "📊 Embed"])
        self.type_filter.currentTextChanged.connect(self._filter_models)
        filter_layout.addWidget(self.type_filter)
        
        # Format filter  
        self.format_filter = QComboBox()
        self.format_filter.addItems(["All Formats", "GGUF", "SafeTensors", "PyTorch", "GGML"])
        self.format_filter.currentTextChanged.connect(self._filter_models)
        filter_layout.addWidget(self.format_filter)
        
        # Size filter
        self.size_filter = QComboBox()
        self.size_filter.addItems(["All Sizes", "< 1GB", "1-3GB", "3-7GB", "7-15GB", "> 15GB"])
        self.size_filter.currentTextChanged.connect(self._filter_models)
        filter_layout.addWidget(self.size_filter)
        
        # View mode toggle
        self.view_toggle = QPushButton("� List View")
        self.view_toggle.setCheckable(True)
        self.view_toggle.clicked.connect(self._toggle_view_mode)
        filter_layout.addWidget(self.view_toggle)
        
        # Clear filters
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self._clear_filters)
        filter_layout.addWidget(clear_btn)
        
        layout.addWidget(filter_frame)
        
        # Results container with scroll
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Models container (will switch between grid and list)
        self.models_container = QWidget()
        self.models_layout = QGridLayout(self.models_container)  # Start with grid
        self.models_layout.setSpacing(10)
        
        self.results_scroll.setWidget(self.models_container)
        layout.addWidget(self.results_scroll)
        
        # Quick stats bar
        self.stats_bar = QLabel("📊 Ready to load models...")
        self.stats_bar.setStyleSheet("background: #1a1a1a; padding: 5px; border-radius: 3px; color: #888;")
        layout.addWidget(self.stats_bar)
        
        return widget
    
    def _create_vision_tab(self):
        """🖼️ Create vision analysis interface"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("🖼️ Vision Analysis")
        header.setFont(QFont("Consolas", 12, QFont.Bold))
        layout.addWidget(header)
        
        # Upload area
        upload_frame = QFrame()
        upload_frame.setFrameStyle(QFrame.Box)
        upload_frame.setMinimumHeight(200)
        upload_layout = QVBoxLayout(upload_frame)
        
        self.image_label = QLabel("📁 Drop image here or click to browse")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px dashed #00d4aa; border-radius: 8px; padding: 20px;")
        
        self.browse_button = QPushButton("📁 Browse Images")
        
        upload_layout.addWidget(self.image_label, 1)
        upload_layout.addWidget(self.browse_button)
        layout.addWidget(upload_frame)
        
        # Analysis results
        results_label = QLabel("🔍 Analysis Results:")
        results_label.setFont(QFont("Consolas", 10, QFont.Bold))
        layout.addWidget(results_label)
        
        self.vision_results = QTextEdit()
        self.vision_results.setPlaceholderText("Upload an image to see AI analysis results...")
        layout.addWidget(self.vision_results, 1)
        
        return widget
    
    def _create_audio_tab(self):
        """🔊 Create audio transcription interface"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("🔊 Audio Transcription")
        header.setFont(QFont("Consolas", 12, QFont.Bold))
        layout.addWidget(header)
        
        # Upload controls
        controls_layout = QHBoxLayout()
        self.audio_browse_button = QPushButton("📁 Browse Audio")
        self.audio_record_button = QPushButton("🎤 Record")
        self.audio_play_button = QPushButton("▶️ Play")
        self.audio_stop_button = QPushButton("⏹️ Stop")
        
        controls_layout.addWidget(self.audio_browse_button)
        controls_layout.addWidget(self.audio_record_button)
        controls_layout.addWidget(self.audio_play_button)
        controls_layout.addWidget(self.audio_stop_button)
        layout.addLayout(controls_layout)
        
        # Waveform placeholder
        waveform_frame = QFrame()
        waveform_frame.setFrameStyle(QFrame.Box)
        waveform_frame.setMinimumHeight(100)
        waveform_layout = QVBoxLayout(waveform_frame)
        waveform_label = QLabel("🌊 Audio Waveform (Placeholder)")
        waveform_label.setAlignment(Qt.AlignCenter)
        waveform_layout.addWidget(waveform_label)
        layout.addWidget(waveform_frame)
        
        # Transcription results
        transcription_label = QLabel("📝 Transcription:")
        transcription_label.setFont(QFont("Consolas", 10, QFont.Bold))
        layout.addWidget(transcription_label)
        
        self.transcription_results = QTextEdit()
        self.transcription_results.setPlaceholderText("Upload or record audio to see transcription...")
        layout.addWidget(self.transcription_results, 1)
        
        return widget
    
    def _create_chat_tab(self):
        """🧠 Create chat interface"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("🧠 AI Chat Interface")
        header.setFont(QFont("Consolas", 12, QFont.Bold))
        layout.addWidget(header)
        
        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText("Start chatting with the AI model...")
        layout.addWidget(self.chat_history, 1)
        
        # Input area
        input_layout = QHBoxLayout()
        self.chat_input = QTextEdit()
        self.chat_input.setMaximumHeight(60)
        self.chat_input.setPlaceholderText("Type your message here...")
        
        self.send_button = QPushButton("📤 Send")
        self.clear_button = QPushButton("🗑️ Clear")
        
        input_layout.addWidget(self.chat_input, 1)
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.clear_button)
        layout.addLayout(input_layout)
        
        return widget
    
    def _create_settings_tab(self):
        """⚙️ Create settings interface"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QLabel("⚙️ Configuration & Settings")
        header.setFont(QFont("Consolas", 12, QFont.Bold))
        layout.addWidget(header)
        
        # Model Paths section
        paths_frame = QFrame()
        paths_frame.setFrameStyle(QFrame.Box)
        paths_layout = QVBoxLayout(paths_frame)
        
        paths_label = QLabel("📂 Model Discovery Paths:")
        paths_label.setFont(QFont("Consolas", 10, QFont.Bold))
        paths_layout.addWidget(paths_label)
        
        # Path management controls
        path_controls = QHBoxLayout()
        self.add_path_button = QPushButton("📁 Add Directory")
        self.refresh_models_button = QPushButton("🔄 Refresh Models")
        self.open_config_button = QPushButton("⚙️ Open Config")
        
        path_controls.addWidget(self.add_path_button)
        path_controls.addWidget(self.refresh_models_button)
        path_controls.addWidget(self.open_config_button)
        path_controls.addStretch()
        paths_layout.addLayout(path_controls)
        
        # Current paths display
        self.paths_display = QTextEdit()
        self.paths_display.setMaximumHeight(120)
        self.paths_display.setReadOnly(True)
        self._update_paths_display()
        paths_layout.addWidget(self.paths_display)
        
        layout.addWidget(paths_frame)
        
        # API Endpoints section
        api_frame = QFrame()
        api_frame.setFrameStyle(QFrame.Box)
        api_layout = QVBoxLayout(api_frame)
        
        api_label = QLabel("🌐 API Endpoints:")
        api_label.setFont(QFont("Consolas", 10, QFont.Bold))
        api_layout.addWidget(api_label)
        
        self.api_info = QTextEdit()
        self.api_info.setMaximumHeight(120)
        self.api_info.setReadOnly(True)
        self.api_info.setText("""
� INTERNAL MODE: Smart inference for controlled apps
📡 EXTERNAL MODE: Fixed ports for external tools
🌐 POST /smart_inference - Smart model selection
📊 WS /ws - Real-time streaming
🔗 OpenAI Compatible endpoints available
        """)
        api_layout.addWidget(self.api_info)
        layout.addWidget(api_frame)
        
        # Performance settings
        perf_frame = QFrame()
        perf_frame.setFrameStyle(QFrame.Box)
        perf_layout = QVBoxLayout(perf_frame)
        
        perf_label = QLabel("⚡ Performance Settings:")
        perf_label.setFont(QFont("Consolas", 10, QFont.Bold))
        perf_layout.addWidget(perf_label)
        
        self.perf_settings = QTextEdit()
        self.perf_settings.setMaximumHeight(80)
        self.perf_settings.setText("""
🎯 Smart Model Selection: Input analysis + hardware optimization
⚡ GPU Acceleration: Auto-detected (CUDA/Metal/OpenCL)
🔧 Port Range: 8080-8090 (configurable in uml_config.json)
        """)
        perf_layout.addWidget(self.perf_settings)
        layout.addWidget(perf_frame)
        
        # Add stretch
        layout.addStretch()
        
        return widget
    
    def _populate_model_browser(self):
        """📋 Populate model browser with discovered models"""
        # Clear existing models
        for i in reversed(range(self.models_layout.count())):
            child = self.models_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Check if models have been discovered
        discovered_models = getattr(self, 'discovered_models', {})
        
        if not discovered_models:
            # Show placeholder message
            placeholder = QLabel("🔍 Discovering models... Please wait.")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: #848d97; font-style: italic; padding: 20px;")
            self.models_layout.addWidget(placeholder, 0, 0, 1, 2)
            return
        
        # Get models list from the new data structure
        models_list = discovered_models.get('models', [])
        
        # Populate with discovered models (limit to first 20 for performance)
        max_models_to_show = 20
        model_count = 0
        
        for i, model in enumerate(models_list):
            if model_count >= max_models_to_show:
                break
                
            # Format display name with emoji based on model type
            emoji_map = {
                "text": "🧠",
                "vision": "🖼️", 
                "audio": "🔊",
                "code": "💻"
            }
            emoji = emoji_map.get(model.get('type', 'unknown'), "🤖")
            display_name = f"{emoji} {model.get('name', 'Unknown Model')}"
            
            # Create description
            size_gb = model.get('size_gb', 0)
            description_parts = []
            if model.get('parameters'):
                description_parts.append(model['parameters'])
            if size_gb > 0:
                description_parts.append(f"{size_gb:.2f} GB")
            
            description = " • ".join(description_parts) if description_parts else "AI Model"
            
            card = self._create_model_card(display_name, description, model.get('backend', 'Unknown'), model.get('path', ''))
            row = model_count // 2
            col = model_count % 2
            self.models_layout.addWidget(card, row, col)
            model_count += 1
        
        # Add info label if there are more models
        if len(models_list) > max_models_to_show:
            info_label = QLabel(f"📊 Showing {max_models_to_show} of {len(models_list)} models. Use search to filter.")
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setStyleSheet("color: #00d4aa; font-style: italic; padding: 10px;")
            row = (model_count + 1) // 2
            self.models_layout.addWidget(info_label, row, 0, 1, 2)
    
    def _create_model_card(self, name: str, description: str, backend: str, model_path: str = ""):
        """🃏 Create a model card widget with real functionality"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet("""
        QFrame {
            background-color: #21262d;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 12px;
        }
        QFrame:hover {
            border-color: #00d4aa;
            background-color: #2d333b;
        }
        """)
        
        layout = QVBoxLayout(card)
        
        # Model name
        name_label = QLabel(name)
        name_label.setFont(QFont("Consolas", 10, QFont.Bold))
        layout.addWidget(name_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #7d8590;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Backend info
        backend_label = QLabel(f"Backend: {backend}")
        backend_label.setStyleSheet("color: #7c3aed; font-size: 8pt;")
        layout.addWidget(backend_label)
        
        # Load button with real functionality
        load_button = QPushButton("📥 Load Model")
        load_button.setStyleSheet(self.theme_manager.get_button_style('primary'))
        
        # Connect to actual model loading - safely extract model name
        if name and isinstance(name, str):
            name_parts = name.split(' ', 1)
            model_name_clean = name_parts[1] if len(name_parts) > 1 else name_parts[0]
        else:
            model_name_clean = str(name) if name else "Unknown Model"
            
        load_button.clicked.connect(
            lambda: self._load_model_with_progress(model_name_clean, backend, load_button)
        )
        
        layout.addWidget(load_button)
        
        return card
    
    def _request_model_load(self, model_name: str, backend: str):
        """📥 Request model loading through main window"""
        config = {
            'model': model_name,
            'backend': backend,
            'gpu_layers': 'auto',
            'context': 4096
        }
        
        # Emit signal to main window for processing
        self.log_message.emit(f"Requesting load: {model_name} ({backend})", "info")
        
        # Emit signal to trigger actual model loading
        self.model_launch_requested.emit(config)
        
        self.log_message.emit(f"Model load request sent: {model_name}", "success")
    
    def _apply_styles(self):
        """🎨 Apply sci-fi theme styles"""
        self.setStyleSheet(self.theme_manager.get_panel_style())
        
        # Style tab widget
        self.tab_widget.setStyleSheet(self.theme_manager.get_tab_style())
        
        # Style buttons
        for button in [self.browse_button, self.audio_browse_button,
                      self.audio_record_button, self.audio_play_button, self.audio_stop_button,
                      self.send_button, self.clear_button]:
            button.setStyleSheet(self.theme_manager.get_button_style('primary'))
        
        # Style text inputs
        for text_widget in [self.search_input, self.vision_results, self.transcription_results,
                           self.chat_history, self.chat_input, self.api_info, self.perf_settings]:
            text_widget.setStyleSheet(self.theme_manager.get_input_style())
    
    def _connect_signals(self):
        """🔗 Connect UI signals"""
        self.browse_button.clicked.connect(self._browse_image)
        self.audio_browse_button.clicked.connect(self._browse_audio)
        self.send_button.clicked.connect(self._send_chat_message)
        self.clear_button.clicked.connect(self._clear_chat)
        
        # Settings tab signals
        if hasattr(self, 'add_path_button'):
            self.add_path_button.clicked.connect(self._add_model_path)
        if hasattr(self, 'refresh_models_button'):
            self.refresh_models_button.clicked.connect(self.refresh_models)
        if hasattr(self, 'open_config_button'):
            self.open_config_button.clicked.connect(self._open_config_file)
    
    def _browse_image(self):
        """📁 Browse for image file and analyze with vision model"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.image_label.setText(f"📁 Selected: {Path(file_path).name}")
            self.log_message.emit(f"Image selected: {file_path}", "info")
            
            # Process image with vision model
            self._process_image(file_path)
    
    def _process_image(self, file_path: str):
        """🖼️ Process image through vision model system"""
        self.vision_results.clear()
        self.vision_results.append("🔍 Analyzing image with optimal vision model...")
        
        # In real implementation, this would:
        # 1. Send to hybrid smart loader with image input
        # 2. Auto-select best vision model (CLIP, BakLLaVA, etc.)
        # 3. Get analysis results
        
        # Simulate processing delay
        QTimer.singleShot(2000, lambda: self._display_vision_results(file_path))
    
    def _display_vision_results(self, file_path: str):
        """🔍 Display vision analysis results"""
        # Simulate vision analysis results
        results = f"""
🔍 Vision Analysis Complete

📁 File: {Path(file_path).name}
🤖 Model: BakLLaVA-7B (auto-selected for image analysis)
📊 Confidence: 94.7%

📝 Description:
The image appears to show [simulated analysis]. The optimal vision model was automatically selected based on image properties and current system resources.

🏷️ Detected Objects:
• Object 1 (confidence: 92%)
• Object 2 (confidence: 87%)
• Object 3 (confidence: 76%)

⚡ Processing Time: 1.8 seconds
🧠 Memory Used: 2.3 GB
        """
        
        self.vision_results.clear()
        self.vision_results.append(results)
        
        # Update performance
        self.performance_updated.emit({
            'memory_usage': 88,
            'gpu_usage': 92,
            'generation_speed': 35
        })
    
    def _browse_audio(self):
        """📁 Browse for audio file and transcribe"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio", "", "Audio (*.wav *.mp3 *.flac *.ogg)"
        )
        if file_path:
            self.log_message.emit(f"Audio selected: {file_path}", "info")
            
            # Process audio with transcription model
            self._process_audio(file_path)
    
    def _process_audio(self, file_path: str):
        """🔊 Process audio through transcription system"""
        self.transcription_results.clear()
        self.transcription_results.append("🎤 Transcribing audio with optimal model...")
        
        # In real implementation, this would:
        # 1. Send to hybrid smart loader with audio input
        # 2. Auto-select best audio model (Whisper variants)
        # 3. Get transcription results
        
        # Simulate processing delay
        QTimer.singleShot(3000, lambda: self._display_transcription_results(file_path))
    
    def _display_transcription_results(self, file_path: str):
        """📝 Display transcription results"""
        # Simulate transcription results
        results = f"""
🎤 Audio Transcription Complete

📁 File: {Path(file_path).name}
🤖 Model: Whisper-Large (auto-selected for audio transcription)
🌐 Language: English (auto-detected)
📊 Confidence: 96.2%

📝 Transcription:
[Simulated transcription text would appear here. The system automatically selected the optimal Whisper model variant based on audio properties and quality requirements.]

📈 Analysis:
• Duration: 7.8 seconds
• Quality: High (16kHz sample rate)
• Background noise: Low
• Speaker count: 1

⚡ Processing Time: 2.1 seconds
🧠 Memory Used: 1.9 GB
        """
        
        self.transcription_results.clear()
        self.transcription_results.append(results)
        
        # Update performance
        self.performance_updated.emit({
            'memory_usage': 79,
            'gpu_usage': 68,
            'generation_speed': 52
        })
    
    def _send_chat_message(self):
        """📤 Send chat message with smart model integration"""
        message = self.chat_input.toPlainText().strip()
        if message:
            self.chat_history.append(f"👤 You: {message}")
            self.chat_input.clear()
            
            # Use hybrid smart loader for response
            self._process_chat_message(message)
            
            self.log_message.emit(f"Chat message sent: {message}", "info")
    
    def _process_chat_message(self, message: str):
        """🧠 Process chat message through smart model system"""
        # Simulate smart model processing
        self.chat_history.append("🤖 AI: Processing with optimal model...")
        
        # In real implementation, this would:
        # 1. Send to hybrid smart loader
        # 2. Auto-select best model for the input
        # 3. Get response and display
        
        # Simulate response delay
        QTimer.singleShot(1500, lambda: self._display_ai_response(message))
    
    def _display_ai_response(self, original_message: str):
        """🤖 Display AI response"""
        # Simulate smart response
        response = f"I understand you said: '{original_message}'. I selected the optimal model for this response based on your input type and current system resources."
        self.chat_history.append(f"🤖 AI: {response}")
        
        # Update performance metrics
        self.performance_updated.emit({
            'memory_usage': 82,
            'gpu_usage': 75,
            'generation_speed': 48
        })
    
    def _clear_chat(self):
        """🗑️ Clear chat history"""
        self.chat_history.clear()
        self.log_message.emit("Chat history cleared", "info")
    
    def handle_model_launch(self, config: dict):
        """🚀 Handle model launch request from left panel"""
        model_name = config.get('model', 'Unknown')
        self.log_message.emit(f"Launching model: {model_name}", "info")
        
        # Update performance (placeholder)
        self.performance_updated.emit({
            'memory_usage': 85,
            'gpu_usage': 70,
            'generation_speed': 42
        })
    
    def handle_model_stop(self, model_id: str):
        """🛑 Handle model stop request"""
        self.log_message.emit(f"Stopping model: {model_id}", "warning")
    
    def _discover_models(self):
        """🔍 Discover models in background"""
        try:
            self.log_message.emit("🔍 Starting model discovery...", "info")
            
            # Discover models (this runs synchronously for now)
            self.discovered_models = self.model_discovery.discover_models(force_rescan=False)
            
            # Log discovery results
            model_count = len(self.discovered_models)
            self.log_message.emit(f"📊 Found {model_count} models", "info")
            
            # Update the model browser
            self._populate_model_browser()
            
            # Log final results
            stats = self.model_discovery.get_model_stats()
            self.log_message.emit(
                f"✅ Discovery complete: Found {stats['total_models']} models "
                f"({stats['total_size_gb']:.1f} GB total)", 
                "success"
            )
            
        except Exception as e:
            import traceback
            error_msg = f"❌ Model discovery failed: {str(e)}"
            self.log_message.emit(error_msg, "error")
            print(f"Discovery Error: {e}")
            print(traceback.format_exc())
            self.discovered_models = {}
            self._populate_model_browser()
    
    def _filter_models(self):
        """🔍 Filter models based on current filter settings"""
        if not hasattr(self, 'discovered_models') or not self.discovered_models:
            return
            
        # Get filter values
        search_text = self.search_input.text().lower()
        type_filter = self.type_filter.currentText()
        format_filter = self.format_filter.currentText()
        size_filter = self.size_filter.currentText()
        
        # Apply filters
        filtered_models = []
        
        # Handle both dictionary and list formats
        models_to_filter = self.discovered_models
        if isinstance(models_to_filter, dict):
            models_to_filter = list(models_to_filter.values())
        
        for model in models_to_filter:
            # Convert model to dict if it's a dataclass
            if hasattr(model, 'name'):
                model_dict = {
                    'name': model.name,
                    'type': model.model_type,
                    'path': model.path,
                    'size_gb': model.size_bytes / (1024**3),
                    'backend': model.backend_type,
                    'file_type': model.file_type
                }
            elif isinstance(model, dict):
                model_dict = model
            else:
                # Skip invalid model format
                continue
                
            # Search filter
            if search_text and search_text not in model_dict['name'].lower():
                continue
                
            # Type filter - more flexible matching
            if type_filter != "All Types":
                type_emoji = type_filter.split()[1] if len(type_filter.split()) > 1 else ""
                model_type = model_dict.get('type', '').lower()
                
                # More flexible type matching
                should_include = False
                if type_emoji == "Text":
                    # Match text, language, completion models
                    should_include = any(keyword in model_type for keyword in ['text', 'language', 'completion', 'instruct', 'chat'])
                elif type_emoji == "Code": 
                    # Match coding/programming models
                    should_include = any(keyword in model_type for keyword in ['code', 'programming', 'codegen', 'starcoder', 'deepseek-coder'])
                elif type_emoji == "Vision":
                    # Match vision/image models  
                    should_include = any(keyword in model_type for keyword in ['vision', 'image', 'multimodal', 'clip', 'blip'])
                elif type_emoji == "Audio":
                    # Match audio/speech models
                    should_include = any(keyword in model_type for keyword in ['audio', 'speech', 'whisper', 'voice'])
                elif type_emoji == "Embed":
                    # Match embedding models
                    should_include = any(keyword in model_type for keyword in ['embed', 'retrieval', 'bge', 'sentence'])
                
                if not should_include:
                    continue
                    
            # Format filter
            if format_filter != "All Formats":
                file_type = model_dict.get('file_type', '').upper()
                if format_filter.upper() not in file_type:
                    continue
                    
            # Size filter
            if size_filter != "All Sizes":
                size_gb = model_dict.get('size_gb', 0)
                if size_filter == "< 1GB" and size_gb >= 1:
                    continue
                elif size_filter == "1-3GB" and (size_gb < 1 or size_gb > 3):
                    continue
                elif size_filter == "3-7GB" and (size_gb < 3 or size_gb > 7):
                    continue
                elif size_filter == "7-15GB" and (size_gb < 7 or size_gb > 15):
                    continue
                elif size_filter == "> 15GB" and size_gb <= 15:
                    continue
                    
            filtered_models.append(model_dict)
            
        # Update display
        self._display_filtered_models(filtered_models)
        
        # Update stats
        total_size = sum(m.get('size_gb', 0) for m in filtered_models)
        self.models_count_label.setText(f"{len(filtered_models)} models ({total_size:.1f}GB)")
        
    def _clear_filters(self):
        """🗑️ Clear all filters"""
        self.search_input.clear()
        self.type_filter.setCurrentText("All Types")
        self.format_filter.setCurrentText("All Formats")
        self.size_filter.setCurrentText("All Sizes")
        self._filter_models()
        
    def set_type_filter(self, model_type):
        """🎯 Set type filter from external source (like left panel)"""
        # Map the left panel types to main panel filter types
        type_mapping = {
            "All Types": "All Types",
            "🧠 Text Models": "🧠 Text",
            "💻 Code Models": "💻 Code", 
            "🖼️ Vision Models": "🖼️ Vision",
            "🔊 Audio Models": "🔊 Audio"
        }
        
        mapped_type = type_mapping.get(model_type, "All Types")
        self.type_filter.setCurrentText(mapped_type)
        self._filter_models()
        
    def _toggle_view_mode(self):
        """📋 Toggle between grid and list view"""
        is_list_mode = self.view_toggle.isChecked()
        
        if is_list_mode:
            self.view_toggle.setText("🔲 Grid View")
            # Switch to list layout
            self._switch_to_list_view()
        else:
            self.view_toggle.setText("📋 List View")  
            # Switch to grid layout
            self._switch_to_grid_view()
            
        # Refresh display
        self._filter_models()
        
    def _switch_to_list_view(self):
        """Switch to compact list view"""
        # Clear current layout
        while self.models_layout.count():
            child = self.models_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Switch to vertical layout for list
        self.models_container.setLayout(QVBoxLayout())
        self.models_layout = self.models_container.layout()
        
    def _switch_to_grid_view(self):
        """Switch to card grid view"""
        # Clear current layout
        while self.models_layout.count():
            child = self.models_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Switch to grid layout
        self.models_container.setLayout(QGridLayout())
        self.models_layout = self.models_container.layout()
        self.models_layout.setSpacing(10)
        
    def _display_filtered_models(self, filtered_models):
        """Display filtered models in current view mode"""
        # Clear existing widgets
        while self.models_layout.count():
            child = self.models_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        if self.view_toggle.isChecked():  # List view
            self._display_models_as_list(filtered_models)
        else:  # Grid view
            self._display_models_as_grid(filtered_models)
            
    def _display_models_as_list(self, models):
        """Display models in compact list format"""
        for model in models:
            list_item = self._create_model_list_item(model)
            self.models_layout.addWidget(list_item)
            
    def _display_models_as_grid(self, models):
        """Display models in card grid format"""
        row, col = 0, 0
        max_cols = 2
        
        for model in models:
            # Extract model info from the model dict
            name = model.get('name', 'Unknown Model')
            description = f"Type: {model.get('type', 'Unknown')} | Size: {model.get('size_gb', 0):.1f} GB"
            backend = model.get('backend', 'Unknown')
            model_path = model.get('path', '')
            
            card = self._create_model_card(name, description, backend, model_path)
            self.models_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
    def _create_model_list_item(self, model):
        """Create compact list item for a model"""
        item = QFrame()
        item.setStyleSheet("QFrame { background: #2a2a2a; border-radius: 3px; padding: 5px; margin: 1px; }")
        item.setMaximumHeight(40)
        
        layout = QHBoxLayout(item)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Model info (compact)
        info_text = f"{self._get_type_emoji(model.get('type', ''))} {model['name']}"
        size_text = f"({model.get('size_gb', 0):.1f}GB)"
        
        name_label = QLabel(info_text)
        size_label = QLabel(size_text)
        size_label.setStyleSheet("color: #888; font-size: 10px;")
        
        # Load button (small)
        load_btn = QPushButton("⚡")
        load_btn.setMaximumWidth(30)
        load_btn.setToolTip("Load Model")
        load_btn.clicked.connect(lambda: self._load_model(model))
        
        layout.addWidget(name_label, 1)
        layout.addWidget(size_label)
        layout.addWidget(load_btn)
        
        return item
    
    def _get_type_emoji(self, model_type):
        """Get emoji for model type"""
        type_map = {
            'text': '🤖',
            'code': '💻', 
            'vision': '🖼️',
            'audio': '🔊',
            'embedding': '📊'
        }
        return type_map.get(model_type.lower(), '❓')
        
    def _load_model(self, model):
        """Load selected model"""
        self.log_message.emit(f"🚀 Loading model: {model['name']}", "info")
        
        # Create model configuration
        model_config = {
            'path': model['path'],
            'name': model['name'],
            'type': model.get('type', 'text'),
            'backend': model.get('backend', 'llama.cpp')
        }
        
        # Emit signal to trigger actual model loading in main window
        self.model_launch_requested.emit(model_config)
        
    def refresh_models(self):
        """🔄 Refresh model discovery"""
        self.log_message.emit("🔄 Refreshing model discovery...", "info")
        self.discovered_models = {}
        self._populate_model_browser()  # Show loading state
        self._discover_models()
    
    def add_model_directory(self, directory: str):
        """📂 Add new model directory"""
        if self.model_discovery.add_scan_directory_interactive(directory):
            self.refresh_models()
            return True
        return False
    
    def _add_model_path(self):
        """📁 Browse and add new model directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Model Directory", "", QFileDialog.ShowDirsOnly
        )
        if directory:
            if self.add_model_directory(directory):
                self.log_message.emit(f"✅ Added model directory: {directory}", "success")
                self._update_paths_display()
            else:
                self.log_message.emit(f"❌ Failed to add directory: {directory}", "error")
    
    def _open_config_file(self):
        """⚙️ Open configuration file in default editor"""
        try:
            import subprocess
            import platform
            
            config_path = Path("./config/uml_config.json").resolve()
            
            if platform.system() == "Windows":
                subprocess.run(["notepad.exe", str(config_path)], check=False)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(config_path)], check=False)
            else:  # Linux
                subprocess.run(["xdg-open", str(config_path)], check=False)
            
            self.log_message.emit(f"📝 Opened config file: {config_path}", "info")
        except Exception as e:
            self.log_message.emit(f"❌ Failed to open config file: {str(e)}", "error")
    
    def _update_paths_display(self):
        """📂 Update the paths display with current configuration"""
        try:
            scan_dirs = self.model_discovery.config.get_expanded_scan_directories()
            extensions = self.model_discovery.config.get_file_extensions()
            
            paths_text = "📂 Current Scan Directories:\n"
            for i, path in enumerate(scan_dirs, 1):
                paths_text += f"  {i}. {path}\n"
            
            paths_text += f"\n📄 File Extensions: {', '.join(extensions)}\n"
            paths_text += f"\n📊 Models Found: {len(getattr(self, 'discovered_models', {}))}"
            
            self.paths_display.setText(paths_text)
        except Exception as e:
            self.paths_display.setText(f"❌ Error loading configuration: {str(e)}")
    
    def _search_models(self):
        """🔍 Search discovered models"""
        if hasattr(self, 'search_input'):
            query = self.search_input.toPlainText().strip()
            if query:
                results = self.model_discovery.search_models(query)
                self.log_message.emit(f"🔍 Search '{query}': Found {len(results)} models", "info")
                
    def _load_model_with_progress(self, model_name, backend, button):
        """🔄 Load model with visual progress feedback"""
        # Update button to show loading state
        original_text = button.text()
        button.setText("🔄 Loading...")
        button.setEnabled(False)
        button.setStyleSheet(self.theme_manager.get_button_style('secondary'))
        
        # Store loading state
        self.loading_states[model_name] = {
            'button': button,
            'original_text': original_text,
            'start_time': time.time()
        }
        self.current_loading_model = model_name
        
        # Emit status update
        self.log_message.emit(f"🚀 Loading model: {model_name}", "info")
        
        # Start the actual loading process
        self._request_model_load(model_name, backend)
        
        # Set timer to reset button after timeout (in case of failure)
        QTimer.singleShot(30000, lambda: self._reset_loading_state(model_name, "timeout"))
    
    def _reset_loading_state(self, model_name, reason="completed"):
        """🔄 Reset loading state for a model"""
        if model_name in self.loading_states:
            state = self.loading_states[model_name]
            button = state['button']
            
            if reason == "completed":
                button.setText("✅ Loaded")
                button.setStyleSheet(self.theme_manager.get_button_style('success'))
                # Reset to original state after 3 seconds
                QTimer.singleShot(3000, lambda: self._restore_button_state(model_name))
            elif reason == "error":
                button.setText("❌ Failed")
                button.setStyleSheet(self.theme_manager.get_button_style('danger'))
                # Reset to original state after 5 seconds
                QTimer.singleShot(5000, lambda: self._restore_button_state(model_name))
            elif reason == "timeout":
                button.setText("⏱️ Timeout")
                button.setStyleSheet(self.theme_manager.get_button_style('warning'))
                # Reset to original state after 3 seconds
                QTimer.singleShot(3000, lambda: self._restore_button_state(model_name))
            
            button.setEnabled(True)
            
    def _restore_button_state(self, model_name):
        """🔄 Restore button to original state"""
        if model_name in self.loading_states:
            state = self.loading_states[model_name]
            button = state['button']
            button.setText(state['original_text'])
            button.setStyleSheet(self.theme_manager.get_button_style('default'))
            del self.loading_states[model_name]
            
    def _discover_models(self):
        """🔍 Discover and populate models"""
        try:
            # Discover models from configured paths
            discovered = self.model_discovery.discover_all_models()
            self.discovered_models = discovered
            
            # Update model browser display
            self._populate_model_browser()
            
            # Emit signal to notify other panels about discovered models
            model_count = discovered.get('count', 0)
            self.log_message.emit(f"🔍 Discovery complete: {model_count} models found", "success")
            self.models_discovered.emit(discovered)  # Notify left panel
            
        except Exception as e:
            self.log_message.emit(f"❌ Model discovery failed: {e}", "error")
            self.discovered_models = {}
