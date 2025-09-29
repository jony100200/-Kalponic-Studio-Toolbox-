"""
Configuration module initialization
"""

from .settings import config, ConfigManager, RemovalSettings, UISettings, ProcessingSettings

__all__ = [
    'config',
    'ConfigManager',
    'RemovalSettings',
    'UISettings',
    'ProcessingSettings',
]