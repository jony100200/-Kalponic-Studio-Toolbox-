#!/usr/bin/env python3
"""
🚀 Universal Model Launcher V4 - Installation Script
===================================================
Quick setup script for first-time installation
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_banner():
    """Display welcome banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🚀 Universal Model Launcher V4 - Setup                  ║
║                                                              ║
║     Advanced AI Model Management System                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required. Current version:", sys.version_info)
        sys.exit(1)
    print("✅ Python version check passed")

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        sys.exit(1)

def setup_config():
    """Setup initial configuration"""
    print("⚙️ Setting up configuration...")
    
    config_path = Path("config/uml_config.json")
    config_dir = config_path.parent
    
    # Create config directory if it doesn't exist
    config_dir.mkdir(exist_ok=True)
    
    # Default configuration
    default_config = {
        "model_discovery_paths": [
            "models/",
            "~/.cache/huggingface/transformers/",
            "C:/AI_Models/",
            "D:/AI_Models/",
            "E:/AI_Models/"
        ],
        "backends": {
            "llama.cpp": {
                "enabled": True,
                "gpu_layers": "auto",
                "context_length": 4096
            },
            "transformers": {
                "enabled": True,
                "device": "auto"
            },
            "exllama": {
                "enabled": True,
                "gpu_split": "auto"
            }
        },
        "gui": {
            "theme": "sci-fi-dark",
            "auto_discovery": True,
            "show_performance_metrics": True
        }
    }
    
    # Write config if it doesn't exist
    if not config_path.exists():
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
        print("✅ Configuration file created")
    else:
        print("✅ Configuration file already exists")

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    directories = ["logs", "models", "config"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Directories created")

def run_test():
    """Run a quick test to verify installation"""
    print("🧪 Running installation test...")
    try:
        # Import test
        from GUI.main_window import UniversalModelLauncherUI
        print("✅ GUI components imported successfully")
        
        from Core.model_discovery import ModelDiscovery  
        print("✅ Core components imported successfully")
        
        print("✅ Installation test passed")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Main setup function"""
    print_banner()
    
    try:
        # Setup steps
        check_python_version()
        install_requirements()
        create_directories()
        setup_config()
        
        # Test installation
        if run_test():
            print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🎉 Installation Complete!                               ║
║                                                              ║
║     Ready to launch:                                         ║
║     python launch_gui.py                                     ║
║                                                              ║
║     Configure your model paths in:                           ║
║     config/uml_config.json                                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
        else:
            print("❌ Installation verification failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()