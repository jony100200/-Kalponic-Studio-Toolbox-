"""
Model Lock Component - Single Model Enforcement (SOLID: Single Responsibility)

This component acts as the "referee" ensuring only one model runs at a time.

🎯 Single Responsibility: Model instance enforcement and conflict prevention
🔒 Core Function: Prevent multiple models from running simultaneously
📊 Success Metrics: Zero simultaneous model conflicts, clean state transitions
"""

import threading
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ModelInstance:
    """Represents a currently loaded model instance."""
    process_id: int
    model_name: str
    port: int
    backend_type: str  # 'koboldcpp', 'text-generation-webui', etc.
    start_time: float = field(default_factory=time.time)
    memory_usage_mb: Optional[int] = None
    device: str = "auto"
    
    def get_runtime_seconds(self) -> float:
        """Get how long this model has been running."""
        return time.time() - self.start_time

class ModelLock:
    """
    SOLID Component: Single Model Enforcement
    
    Ensures only one AI model can be loaded at a time, preventing:
    - Memory conflicts and OOM errors
    - Port conflicts between backends
    - Resource competition and performance degradation
    """
    
    def __init__(self):
        self._lock = threading.RLock()  # Re-entrant lock for same-thread safety
        self._current_instance: Optional[ModelInstance] = None
        self._lock_history: list = []  # Track lock/unlock events for debugging
        
    def acquire_lock(self, model_instance: ModelInstance) -> bool:
        """
        Attempt to acquire the model lock.
        
        Args:
            model_instance: The model instance requesting the lock
            
        Returns:
            bool: True if lock acquired, False if another model is running
        """
        with self._lock:
            if self._current_instance is not None:
                logger.warning(
                    f"Model lock denied: {model_instance.model_name} "
                    f"(existing: {self._current_instance.model_name} "
                    f"running for {self._current_instance.get_runtime_seconds():.1f}s)"
                )
                return False
            
            self._current_instance = model_instance
            self._lock_history.append({
                'action': 'acquire',
                'model': model_instance.model_name,
                'timestamp': time.time(),
                'process_id': model_instance.process_id
            })
            
            logger.info(
                f"Model lock acquired: {model_instance.model_name} "
                f"(PID: {model_instance.process_id}, Port: {model_instance.port})"
            )
            return True
    
    def release_lock(self, process_id: int) -> bool:
        """
        Release the model lock for a specific process.
        
        Args:
            process_id: The process ID of the model to release
            
        Returns:
            bool: True if lock was released, False if process didn't hold lock
        """
        with self._lock:
            if self._current_instance is None:
                logger.warning(f"No model lock to release for PID {process_id}")
                return False
            
            if self._current_instance.process_id != process_id:
                logger.warning(
                    f"Lock release denied: PID {process_id} doesn't match "
                    f"current holder PID {self._current_instance.process_id}"
                )
                return False
            
            released_model = self._current_instance.model_name
            runtime = self._current_instance.get_runtime_seconds()
            
            self._current_instance = None
            self._lock_history.append({
                'action': 'release',
                'model': released_model,
                'timestamp': time.time(),
                'process_id': process_id,
                'runtime_seconds': runtime
            })
            
            logger.info(
                f"Model lock released: {released_model} "
                f"(PID: {process_id}, Runtime: {runtime:.1f}s)"
            )
            return True
    
    def force_release(self, reason: str = "forced cleanup") -> bool:
        """
        Force release the lock (emergency cleanup).
        
        Args:
            reason: Reason for forced release
            
        Returns:
            bool: True if lock was released
        """
        with self._lock:
            if self._current_instance is None:
                return False
            
            released_model = self._current_instance.model_name
            process_id = self._current_instance.process_id
            
            self._current_instance = None
            self._lock_history.append({
                'action': 'force_release',
                'model': released_model,
                'timestamp': time.time(),
                'process_id': process_id,
                'reason': reason
            })
            
            logger.warning(f"Model lock force released: {released_model} ({reason})")
            return True
    
    def get_current_model(self) -> Optional[ModelInstance]:
        """Get the currently locked model instance."""
        with self._lock:
            return self._current_instance
    
    def is_locked(self) -> bool:
        """Check if any model currently holds the lock."""
        with self._lock:
            return self._current_instance is not None
    
    def get_lock_status(self) -> Dict[str, Any]:
        """Get detailed lock status for monitoring."""
        with self._lock:
            if self._current_instance is None:
                return {
                    'locked': False,
                    'current_model': None,
                    'history_count': len(self._lock_history)
                }
            
            return {
                'locked': True,
                'current_model': {
                    'name': self._current_instance.model_name,
                    'process_id': self._current_instance.process_id,
                    'port': self._current_instance.port,
                    'backend': self._current_instance.backend_type,
                    'runtime_seconds': self._current_instance.get_runtime_seconds(),
                    'memory_mb': self._current_instance.memory_usage_mb,
                    'device': self._current_instance.device
                },
                'history_count': len(self._lock_history)
            }
    
    def update_model_memory(self, memory_mb: int) -> bool:
        """Update the memory usage of the current model."""
        with self._lock:
            if self._current_instance is None:
                return False
            
            self._current_instance.memory_usage_mb = memory_mb
            return True
