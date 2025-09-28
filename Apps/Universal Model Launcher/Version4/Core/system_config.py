"""
⚙️ System Config - Configuration Management Only
Role: "Configuration Manager" - System settings and safe limits
SOLID Principle: Single Responsibility - Configuration only
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class SystemLimits:
    """System resource limits"""
    max_ram_usage_percent: float = 80.0
    max_vram_usage_percent: float = 90.0
    min_free_ram_gb: float = 2.0
    min_free_vram_gb: float = 1.0
    cpu_thread_multiplier: float = 1.0


@dataclass
class ModelDefaults:
    """Default model loading settings"""
    max_context_size: int = 4096
    default_gpu_layers: int = -1  # Auto
    fallback_to_cpu: bool = True
    enable_mmap: bool = True


class SystemConfig:
    """Pure configuration management - no hardware detection"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path("config/system.json")
        self.limits = SystemLimits()
        self.model_defaults = ModelDefaults()
        self.custom_settings: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                # Load limits
                if 'limits' in data:
                    for key, value in data['limits'].items():
                        if hasattr(self.limits, key):
                            setattr(self.limits, key, value)
                
                # Load model defaults
                if 'model_defaults' in data:
                    for key, value in data['model_defaults'].items():
                        if hasattr(self.model_defaults, key):
                            setattr(self.model_defaults, key, value)
                
                # Load custom settings
                self.custom_settings = data.get('custom_settings', {})
                
            except Exception as e:
                print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def save_config(self) -> None:
        """Save configuration to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = {
                "limits": asdict(self.limits),
                "model_defaults": asdict(self.model_defaults),
                "custom_settings": self.custom_settings
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save config to {self.config_path}: {e}")
    
    def get_memory_limits(self, total_ram_gb: float, total_vram_gb: float) -> Dict[str, float]:
        """Calculate memory limits based on current settings"""
        return {
            "max_ram_gb": total_ram_gb * (self.limits.max_ram_usage_percent / 100),
            "max_vram_gb": total_vram_gb * (self.limits.max_vram_usage_percent / 100),
            "min_free_ram_gb": self.limits.min_free_ram_gb,
            "min_free_vram_gb": self.limits.min_free_vram_gb,
            "safe_ram_gb": max(0, total_ram_gb * (self.limits.max_ram_usage_percent / 100) - self.limits.min_free_ram_gb),
            "safe_vram_gb": max(0, total_vram_gb * (self.limits.max_vram_usage_percent / 100) - self.limits.min_free_vram_gb)
        }
    
    def get_cpu_threads(self, cpu_cores: int) -> int:
        """Get recommended CPU threads"""
        return max(1, int(cpu_cores * self.limits.cpu_thread_multiplier))
    
    def update_limits(self, **kwargs) -> None:
        """Update system limits"""
        for key, value in kwargs.items():
            if hasattr(self.limits, key):
                setattr(self.limits, key, value)
        self.save_config()
    
    def update_model_defaults(self, **kwargs) -> None:
        """Update model defaults"""
        for key, value in kwargs.items():
            if hasattr(self.model_defaults, key):
                setattr(self.model_defaults, key, value)
        self.save_config()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get custom setting"""
        return self.custom_settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set custom setting"""
        self.custom_settings[key] = value
        self.save_config()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get complete configuration summary"""
        return {
            "limits": asdict(self.limits),
            "model_defaults": asdict(self.model_defaults),
            "custom_settings": self.custom_settings,
            "config_path": str(self.config_path)
        }
