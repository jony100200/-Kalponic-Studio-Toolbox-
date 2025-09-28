"""
⚙️ Configuration Manager
========================
Role: Centralized configuration management with JSON support
SOLID: Single responsibility for configuration handling
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """
    ⚙️ Universal Configuration Manager
    ==================================
    Role: Load, validate, and manage all UML configurations
    Pattern: Centralized config with JSON persistence
    """
    
    def __init__(self, config_file: str = "config/uml_config.json"):
        self.config_file = Path(config_file)
        self.config_data = {}
        self._ensure_config_directory()
        self._load_configuration()
        self._validate_configuration()
    
    def _ensure_config_directory(self):
        """📁 Ensure config directory exists"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_configuration(self):
        """📥 Load configuration from JSON file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
                logger.info(f"✅ Configuration loaded from {self.config_file}")
            else:
                logger.warning(f"⚠️ Config file not found: {self.config_file}")
                self._create_default_configuration()
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            self._create_default_configuration()
    
    def _create_default_configuration(self):
        """🔧 Create default configuration"""
        self.config_data = self._get_default_config()
        self.save_configuration()
        logger.info("✅ Default configuration created")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """📋 Get default configuration structure"""
        return {
            "model_discovery": {
                "scan_directories": ["./models", "~/Downloads"],
                "file_extensions": [".gguf", ".ggml", ".bin", ".safetensors"],
                "recursive_scan": True,
                "scan_depth": 3
            },
            "model_paths": {
                "custom_locations": {},
                "fallback_directories": ["./models/{model_type}"]
            },
            "system_settings": {
                "server": {
                    "host": "127.0.0.1",
                    "port_range": {"start": 8080, "end": 8100},
                    "max_concurrent_models": 4
                }
            },
            "ui_settings": {
                "theme": {"name": "sci-fi-dark"},
                "layout": {"left_panel_width": 280, "right_panel_width": 320}
            }
        }
    
    def _validate_configuration(self):
        """✅ Validate configuration structure"""
        required_sections = ["model_discovery", "model_paths", "system_settings", "ui_settings"]
        
        for section in required_sections:
            if section not in self.config_data:
                logger.warning(f"⚠️ Missing config section: {section}")
                self.config_data[section] = {}
    
    def save_configuration(self):
        """💾 Save configuration to JSON file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"❌ Failed to save configuration: {e}")
    
    # Model Path Management
    def get_scan_directories(self) -> List[str]:
        """📂 Get directories to scan for models"""
        return self.config_data.get("model_discovery", {}).get("scan_directories", ["./models"])
    
    def add_scan_directory(self, directory: str):
        """📂 Add directory to model scan list"""
        scan_dirs = self.get_scan_directories()
        if directory not in scan_dirs:
            scan_dirs.append(directory)
            self.config_data.setdefault("model_discovery", {})["scan_directories"] = scan_dirs
            self.save_configuration()
    
    def remove_scan_directory(self, directory: str):
        """🗑️ Remove directory from scan list"""
        scan_dirs = self.get_scan_directories()
        if directory in scan_dirs:
            scan_dirs.remove(directory)
            self.config_data.setdefault("model_discovery", {})["scan_directories"] = scan_dirs
            self.save_configuration()
    
    def get_model_path(self, model_name: str) -> Optional[str]:
        """📍 Get specific path for a model"""
        custom_locations = self.config_data.get("model_paths", {}).get("custom_locations", {})
        return custom_locations.get(model_name)
    
    def set_model_path(self, model_name: str, path: str):
        """📍 Set specific path for a model"""
        self.config_data.setdefault("model_paths", {}).setdefault("custom_locations", {})[model_name] = path
        self.save_configuration()
    
    def get_file_extensions(self) -> List[str]:
        """📄 Get supported file extensions"""
        return self.config_data.get("model_discovery", {}).get("file_extensions", [".gguf", ".ggml"])
    
    # Backend Configuration
    def get_backend_config(self, backend_name: str) -> Dict[str, Any]:
        """🔧 Get backend-specific configuration"""
        return self.config_data.get("backend_configurations", {}).get(backend_name, {})
    
    def get_executable_paths(self, backend_name: str) -> List[str]:
        """🏃‍♂️ Get executable paths for backend"""
        backend_config = self.get_backend_config(backend_name)
        return backend_config.get("executable_paths", [])
    
    # Server Settings
    def get_server_config(self) -> Dict[str, Any]:
        """🌐 Get server configuration"""
        return self.config_data.get("system_settings", {}).get("server", {
            "host": "127.0.0.1",
            "port_range": {"start": 8080, "end": 8100}
        })
    
    def get_port_range(self) -> tuple:
        """🔌 Get server port range"""
        server_config = self.get_server_config()
        port_range = server_config.get("port_range", {"start": 8080, "end": 8100})
        return port_range["start"], port_range["end"]
    
    # UI Settings
    def get_ui_config(self) -> Dict[str, Any]:
        """🎨 Get UI configuration"""
        return self.config_data.get("ui_settings", {})
    
    def get_theme_config(self) -> Dict[str, Any]:
        """🎨 Get theme configuration"""
        return self.get_ui_config().get("theme", {"name": "sci-fi-dark"})
    
    def get_layout_config(self) -> Dict[str, Any]:
        """📐 Get layout configuration"""
        return self.get_ui_config().get("layout", {
            "left_panel_width": 280,
            "right_panel_width": 320,
            "window_size": [1400, 900]
        })
    
    # Smart Loading Settings
    def get_smart_loading_config(self) -> Dict[str, Any]:
        """🧠 Get smart loading configuration"""
        return self.config_data.get("smart_loading", {
            "input_analysis": {"enabled": True},
            "model_selection": {"prefer_speed": True, "memory_aware": True}
        })
    
    # External Tools
    def get_external_tools_config(self) -> Dict[str, Any]:
        """🔗 Get external tools configuration"""
        return self.config_data.get("external_tools", {
            "registry_file": "./model_registry.json",
            "openai_compatibility": True
        })
    
    # Utility Methods
    def expand_path(self, path: str) -> str:
        """🔍 Expand path with environment variables"""
        if not path:
            return ""
        
        # Expand ~ and environment variables
        expanded = os.path.expanduser(path)
        expanded = os.path.expandvars(expanded)
        
        # Handle {username} placeholder
        if "{username}" in expanded:
            username = os.getenv("USERNAME") or os.getenv("USER") or "user"
            expanded = expanded.replace("{username}", username)
        
        return expanded
    
    def get_expanded_scan_directories(self) -> List[str]:
        """📂 Get scan directories with expanded paths"""
        directories = self.get_scan_directories()
        return [self.expand_path(d) for d in directories]
    
    def validate_model_path(self, path: str) -> bool:
        """✅ Validate if model path exists and is accessible"""
        try:
            expanded_path = self.expand_path(path)
            return Path(expanded_path).exists()
        except Exception:
            return False
    
    # Configuration Updates
    def update_config_section(self, section: str, data: Dict[str, Any]):
        """🔄 Update specific configuration section"""
        if section in self.config_data:
            self.config_data[section].update(data)
        else:
            self.config_data[section] = data
        self.save_configuration()
    
    def get_config_section(self, section: str) -> Dict[str, Any]:
        """📋 Get specific configuration section"""
        return self.config_data.get(section, {})
    
    def reset_to_defaults(self):
        """🔄 Reset configuration to defaults"""
        self.config_data = self._get_default_config()
        self.save_configuration()
        logger.info("✅ Configuration reset to defaults")
    
    def export_config(self, export_path: str):
        """📤 Export configuration to file"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Configuration exported to {export_path}")
        except Exception as e:
            logger.error(f"❌ Failed to export configuration: {e}")
    
    def import_config(self, import_path: str):
        """📥 Import configuration from file"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            self.config_data = imported_config
            self._validate_configuration()
            self.save_configuration()
            logger.info(f"✅ Configuration imported from {import_path}")
        except Exception as e:
            logger.error(f"❌ Failed to import configuration: {e}")


# Global configuration instance
_config_manager = None

def get_config_manager(config_file: str = "config/uml_config.json") -> ConfigurationManager:
    """🌍 Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager(config_file)
    return _config_manager
