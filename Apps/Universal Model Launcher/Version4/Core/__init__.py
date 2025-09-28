"""
Core system management components for Universal Model Loader

Includes both system management and model lifecycle components:
- System Management: Hardware detection, configuration, ports, services
- Model Management: Lock enforcement, memory cleanup, lifecycle orchestration
"""

from .hardware_detector import HardwareDetector, GPUInfo, SystemInfo
from .system_config import SystemConfig, SystemLimits, ModelDefaults
from .port_allocator import PortAllocator
from .service_discovery import ServiceDiscovery, DetectedService
from .system_manager import SystemManager

# Model Management Components (SOLID approach)
from .model_lock import ModelLock, ModelInstance
from .memory_cleaner import MemoryCleaner, CleanupResult  
from .model_lifecycle import ModelLifecycle, ModelConfig, ModelState
from .backend_selector import (
    BackendSelector, 
    BackendSelection, 
    ModelCharacteristics, 
    BackendCapability,
    ModelFormat,
    BackendType
)
from .model_registry import (
    ModelRegistry,
    ModelMetadata,
    ModelStatus,
    ModelSource,
    PerformanceRecord,
    UsageRecord
)

__all__ = [
    # System Management
    'HardwareDetector', 'GPUInfo', 'SystemInfo',
    'SystemConfig', 'SystemLimits', 'ModelDefaults', 
    'PortAllocator',
    'ServiceDiscovery', 'DetectedService',
    'SystemManager',
    # Model Management  
    'ModelLock', 'ModelInstance',
    'MemoryCleaner', 'CleanupResult',
    'ModelLifecycle', 'ModelConfig', 'ModelState',
    'BackendSelector', 'BackendSelection', 'ModelCharacteristics',
    'BackendCapability', 'ModelFormat', 'BackendType',
    'ModelRegistry', 'ModelMetadata', 'ModelStatus', 'ModelSource',
    'PerformanceRecord', 'UsageRecord'
]
