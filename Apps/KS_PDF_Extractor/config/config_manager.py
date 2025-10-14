"""
KS PDF Extractor - Configuration Management
==========================================

Manages configuration settings for the PDF extractor tool.
Follows KS principles for modular, reusable components.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

class ConfigManager:
    """
    Configuration management for KS PDF Extractor
    
    Handles loading, saving, and validating configuration settings
    """
    
    DEFAULT_CONFIG = {
        "extraction": {
            "method": "pdfplumber",  # "pdfplumber" or "pypdf2"
            "preserve_formatting": True,
            "clean_text": True,
            "extract_metadata": True,
            "page_separator": "\n\n---\n\n",
            "chunk_size": 1000000
        },
        "output": {
            "default_format": "md",  # "txt" or "md"
            "encoding": "utf-8",
            "add_timestamp": True,
            "add_stats": True,
            "create_index": False
        },
        "markdown": {
            "add_toc": False,
            "heading_style": "atx",  # "atx" (#) or "setext" (===)
            "code_blocks": True,
            "preserve_tables": True
        },
        "batch": {
            "parallel_processing": False,
            "max_workers": 4,
            "skip_existing": True,
            "create_summary": True
        },
        "logging": {
            "level": "INFO",
            "file_logging": False,
            "log_file": "ks_pdf_extractor.log"
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Optional path to config file. If None, uses default location.
        """
        self.config_path = Path(config_path) if config_path else self._get_default_config_path()
        self.config = self.DEFAULT_CONFIG.copy()
        self.logger = self._setup_logging()
        
        # Load existing config if available
        self.load_config()
    
    def _get_default_config_path(self) -> Path:
        """Get default configuration file path"""
        # Use the config directory relative to this file
        config_dir = Path(__file__).parent
        return config_dir / "settings.json"
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for configuration manager"""
        logger = logging.getLogger('ks_pdf_config')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def load_config(self) -> bool:
        """
        Load configuration from file
        
        Returns:
            True if config loaded successfully, False otherwise
        """
        if not self.config_path.exists():
            self.logger.info(f"📝 Config file not found, creating default: {self.config_path}")
            return self.save_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Merge with defaults (preserve any new default settings)
            self.config = self._merge_configs(self.DEFAULT_CONFIG, loaded_config)
            
            self.logger.info(f"✅ Configuration loaded from: {self.config_path}")
            return True
            
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"❌ Failed to load config: {e}")
            self.logger.info("🔄 Using default configuration")
            return False
    
    def save_config(self) -> bool:
        """
        Save current configuration to file
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ Configuration saved to: {self.config_path}")
            return True
            
        except IOError as e:
            self.logger.error(f"❌ Failed to save config: {e}")
            return False
    
    def _merge_configs(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge loaded config with defaults
        
        Args:
            default: Default configuration
            loaded: Loaded configuration
            
        Returns:
            Merged configuration
        """
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            path: Configuration path (e.g., "extraction.method")
            default: Default value if path not found
            
        Returns:
            Configuration value or default
        """
        keys = path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, path: str, value: Any) -> bool:
        """
        Set configuration value using dot notation
        
        Args:
            path: Configuration path (e.g., "extraction.method")
            value: Value to set
            
        Returns:
            True if set successfully, False otherwise
        """
        keys = path.split('.')
        config = self.config
        
        try:
            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # Set the final value
            config[keys[-1]] = value
            return True
            
        except (KeyError, TypeError) as e:
            self.logger.error(f"❌ Failed to set config value '{path}': {e}")
            return False
    
    def validate_config(self) -> List[str]:
        """
        Validate current configuration
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate extraction method
        method = self.get('extraction.method')
        if method not in ['pdfplumber', 'pypdf2']:
            errors.append(f"Invalid extraction method: {method}")
        
        # Validate output format
        format_type = self.get('output.default_format')
        if format_type not in ['txt', 'md']:
            errors.append(f"Invalid output format: {format_type}")
        
        # Validate logging level
        log_level = self.get('logging.level')
        if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            errors.append(f"Invalid logging level: {log_level}")
        
        # Validate chunk size
        chunk_size = self.get('extraction.chunk_size')
        if not isinstance(chunk_size, int) or chunk_size <= 0:
            errors.append(f"Invalid chunk size: {chunk_size}")
        
        # Validate max workers
        max_workers = self.get('batch.max_workers')
        if not isinstance(max_workers, int) or max_workers <= 0:
            errors.append(f"Invalid max workers: {max_workers}")
        
        return errors
    
    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to defaults
        
        Returns:
            True if reset successfully, False otherwise
        """
        self.config = self.DEFAULT_CONFIG.copy()
        return self.save_config()
    
    def export_config(self, export_path: str) -> bool:
        """
        Export current configuration to a different file
        
        Args:
            export_path: Path to export configuration
            
        Returns:
            True if exported successfully, False otherwise
        """
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ Configuration exported to: {export_file}")
            return True
            
        except IOError as e:
            self.logger.error(f"❌ Failed to export config: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """
        Import configuration from a file
        
        Args:
            import_path: Path to import configuration from
            
        Returns:
            True if imported successfully, False otherwise
        """
        import_file = Path(import_path)
        
        if not import_file.exists():
            self.logger.error(f"❌ Import file not found: {import_file}")
            return False
        
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Validate imported config
            temp_config = self.config.copy()
            self.config = self._merge_configs(self.DEFAULT_CONFIG, imported_config)
            
            errors = self.validate_config()
            if errors:
                self.logger.error(f"❌ Invalid imported config: {errors}")
                self.config = temp_config  # Restore previous config
                return False
            
            # Save the imported config
            self.save_config()
            self.logger.info(f"✅ Configuration imported from: {import_file}")
            return True
            
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"❌ Failed to import config: {e}")
            return False
    
    def get_extraction_config(self) -> Dict[str, Any]:
        """Get extraction-specific configuration"""
        return self.config.get('extraction', {})
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output-specific configuration"""
        return self.config.get('output', {})
    
    def get_markdown_config(self) -> Dict[str, Any]:
        """Get markdown-specific configuration"""
        return self.config.get('markdown', {})
    
    def get_batch_config(self) -> Dict[str, Any]:
        """Get batch processing configuration"""
        return self.config.get('batch', {})
    
    def __str__(self) -> str:
        """String representation of configuration"""
        return json.dumps(self.config, indent=2, ensure_ascii=False)