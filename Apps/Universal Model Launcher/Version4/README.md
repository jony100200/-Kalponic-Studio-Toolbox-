# 🚀 Universal Model Launcher V4

> **Advanced AI Model Management System with Smart Loading & Intuitive GUI**

A powerful, production-ready application for discovering, organizing, and launching AI models across multiple backends (llama.cpp, transformers, exllama) with an intelligent filtering system and beautiful sci-fi themed interface.

## ✨ Features

### 🎯 **Smart Model Discovery**
- **Automatic Scanning**: Discovers models across multiple drives and directories
- **Multi-Format Support**: GGUF, SafeTensors, PyTorch, and more
- **Intelligent Classification**: Auto-categorizes by model type (Text, Code, Vision, Audio)
- **78+ Models Supported**: Handles large model collections efficiently

### 🎨 **Professional GUI**
- **Modern Interface**: Sci-fi themed dark mode with smooth animations
- **Advanced Filtering**: Filter by type, format, and size with dropdown controls
- **Real-time Loading**: Visual progress indicators with state management
- **Multi-panel Layout**: Organized workspace with status monitoring

### ⚡ **Backend Integration**
- **Multi-Backend**: llama.cpp, transformers, exllama support
- **Smart Loading**: Automatic backend selection based on model type
- **Port Management**: Automatic port assignment and conflict resolution
- **Error Handling**: Comprehensive timeout and failure recovery

### 🛠 **Developer Friendly**
- **Modular Architecture**: Clean, maintainable codebase
- **Configuration Driven**: JSON-based settings and model paths
- **Extensible Design**: Easy to add new backends and features
- **Production Ready**: Comprehensive error handling and logging

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Windows 10/11 (primary support)
- 8GB+ RAM recommended for larger models

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-username/universal-model-launcher.git
cd universal-model-launcher/Version4
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure model paths**
   - Edit `config/uml_config.json`
   - Add your model directories to the `model_discovery_paths` array

4. **Launch the GUI**
```bash
python launch_gui.py
```

## 📖 Usage Guide

### Model Discovery
1. Launch the application
2. Models are automatically discovered from configured paths
3. Use the dropdown filter to browse by type (Text, Code, Vision, etc.)
4. Browse model cards with detailed information

### Loading Models
1. Click "Load Model" on any model card
2. Watch the loading progress with visual feedback
3. Monitor status in the right panel logs
4. Models appear in the left panel when loaded

### Configuration
- **Model Paths**: Edit `config/uml_config.json` to add your model directories
- **Backend Settings**: Configure GPU layers, context size, and backend preferences
- **Interface**: Theme and layout customization available

## 🏗 Architecture

```
Universal Model Launcher V4/
├── 🎮 GUI/                    # User interface components
│   ├── panels/               # Main, left, and right panels
│   ├── components/           # Reusable UI elements
│   └── theme_manager.py      # Visual styling system
├── 🧠 Core/                  # Business logic
│   ├── discovery/            # Model discovery engine
│   ├── backends/             # Backend integrations
│   └── config/               # Configuration management
├── 🔧 loader/                # Model loading system
├── 📡 api/                   # REST API server
└── ⚙️ config/               # Configuration files
```

## 📊 Performance

- **Discovery**: Scans 78+ models in <3 seconds
- **Memory**: ~200MB base usage (before model loading)
- **Responsiveness**: Non-blocking GUI with threaded operations
- **Scalability**: Handles 100+ models efficiently

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and test thoroughly
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Setup
- Code follows PEP 8 standards
- Use type hints where possible
- Add docstrings to public functions
- Test changes with `python launch_gui.py`

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with PySide6 for the modern GUI framework
- Supports llama.cpp, transformers, and exllama backends
- Designed for the AI model enthusiast community

## 📞 Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join community discussions in GitHub Discussions
- **Wiki**: Check the Wiki for detailed guides and tutorials

---

**⭐ Star this project if you find it useful!**

Made with ❤️ for the AI community