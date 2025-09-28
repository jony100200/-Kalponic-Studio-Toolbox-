"""
Model Lifecycle Component - Orchestration Conductor (SOLID: Single Responsibility)

This component acts as the "conductor" orchestrating model loading, running, and unloading.

🎯 Single Responsibility: Model lifecycle orchestration and state management
🎼 Core Function: Coordinate loading, running, monitoring, and safe unloading of models
📊 Success Metrics: Smooth transitions, proper state tracking, zero failed operations
"""

import asyncio
import logging
import os
import time
import threading
from enum import Enum
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import psutil

from .model_lock import ModelLock, ModelInstance
from .memory_cleaner import MemoryCleaner, CleanupResult

logger = logging.getLogger(__name__)

class ModelState(Enum):
    """Model lifecycle states."""
    IDLE = "idle"
    LOADING = "loading"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    CLEANING = "cleaning"

@dataclass
class ModelConfig:
    """Configuration for a model to be loaded."""
    name: str
    backend_type: str  # 'koboldcpp', 'text-generation-webui'
    model_path: Path
    port: int
    device: str = "auto"
    extra_args: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 300  # 5 minutes default

@dataclass
class ModelStatus:
    """Current status of model lifecycle operations."""
    state: ModelState
    model_config: Optional[ModelConfig] = None
    process_id: Optional[int] = None
    start_time: Optional[float] = None
    error_message: Optional[str] = None
    memory_usage_mb: Optional[float] = None
    last_activity: Optional[float] = None

class ModelLifecycle:
    """
    SOLID Component: Model Lifecycle Orchestration
    
    Coordinates the complete model lifecycle:
    - Loading: Spawn model processes with proper configuration
    - Running: Monitor health, track resources, handle requests
    - Stopping: Graceful shutdown with comprehensive cleanup
    
    Integrates with ModelLock for single-model enforcement and 
    MemoryCleaner for thorough resource cleanup.
    """
    
    def __init__(self, model_lock: ModelLock, memory_cleaner: MemoryCleaner):
        self.model_lock = model_lock
        self.memory_cleaner = memory_cleaner
        
        self._status = ModelStatus(state=ModelState.IDLE)
        self._status_lock = threading.RLock()
        self._lifecycle_hooks: Dict[str, List[Callable]] = {
            'before_load': [],
            'after_load': [],
            'before_stop': [],
            'after_stop': [],
            'on_error': []
        }
        
        # Monitoring
        self._monitor_task: Optional[asyncio.Task] = None
        self._monitoring_active = False
        
    def register_hook(self, event: str, hook: Callable) -> None:
        """Register a lifecycle hook for specific events."""
        if event in self._lifecycle_hooks:
            self._lifecycle_hooks[event].append(hook)
            logger.debug(f"Registered {event} hook: {hook.__name__}")
        else:
            raise ValueError(f"Unknown event: {event}")
    
    async def load_model(self, config: ModelConfig) -> bool:
        """
        Load a model with comprehensive lifecycle management.
        
        Args:
            config: Model configuration
            
        Returns:
            bool: True if model loaded successfully
        """
        async with self._get_status_context():
            if self._status.state != ModelState.IDLE:
                logger.error(f"Cannot load model: current state is {self._status.state}")
                return False
            
            self._update_status(state=ModelState.LOADING, model_config=config)
            
            try:
                # Run before_load hooks
                await self._run_hooks('before_load', config)
                
                # 1. Validate configuration
                if not await self._validate_config(config):
                    raise ValueError("Invalid model configuration")
                
                # 2. Check for existing models and acquire lock
                if not await self._acquire_model_lock(config):
                    raise RuntimeError("Could not acquire model lock")
                
                # 3. Spawn model process
                process = await self._spawn_model_process(config)
                if not process:
                    raise RuntimeError("Failed to spawn model process")
                
                # 4. Wait for model to be ready
                if not await self._wait_for_model_ready(config, process):
                    raise RuntimeError("Model failed to become ready")
                
                # 5. Start monitoring
                await self._start_monitoring(config, process)
                
                # 6. Update status to running
                self._update_status(
                    state=ModelState.RUNNING,
                    process_id=process.pid,
                    start_time=time.time(),
                    last_activity=time.time()
                )
                
                # Run after_load hooks
                await self._run_hooks('after_load', config, process)
                
                logger.info(f"Model loaded successfully: {config.name} (PID: {process.pid})")
                return True
                
            except Exception as e:
                error_msg = f"Failed to load model {config.name}: {str(e)}"
                logger.error(error_msg)
                
                self._update_status(state=ModelState.ERROR, error_message=error_msg)
                
                # Run error hooks
                await self._run_hooks('on_error', config, e)
                
                # Cleanup on failure
                await self._cleanup_failed_load(config)
                
                return False
    
    async def stop_model(self, force: bool = False) -> bool:
        """
        Stop the currently running model with cleanup.
        
        Args:
            force: Whether to force stop without graceful shutdown
            
        Returns:
            bool: True if model stopped successfully
        """
        async with self._get_status_context():
            if self._status.state not in [ModelState.RUNNING, ModelState.ERROR]:
                logger.warning(f"No model to stop (current state: {self._status.state})")
                return True
            
            self._update_status(state=ModelState.STOPPING)
            
            try:
                config = self._status.model_config
                process_id = self._status.process_id
                
                # Run before_stop hooks
                await self._run_hooks('before_stop', config, force)
                
                # 1. Stop monitoring
                await self._stop_monitoring()
                
                # 2. Graceful or force shutdown
                if force or not await self._graceful_shutdown(process_id):
                    await self._force_shutdown(process_id)
                
                # 3. Release model lock
                if process_id:
                    self.model_lock.release_lock(process_id)
                
                # 4. Comprehensive cleanup
                self._update_status(state=ModelState.CLEANING)
                cleanup_result = await self._comprehensive_cleanup(config, process_id)
                
                # 5. Update status to idle
                self._update_status(state=ModelState.IDLE)
                
                # Run after_stop hooks
                await self._run_hooks('after_stop', config, cleanup_result)
                
                logger.info(f"Model stopped successfully: {config.name if config else 'unknown'}")
                return True
                
            except Exception as e:
                error_msg = f"Error stopping model: {str(e)}"
                logger.error(error_msg)
                
                self._update_status(state=ModelState.ERROR, error_message=error_msg)
                return False
    
    async def _validate_config(self, config: ModelConfig) -> bool:
        """Validate model configuration."""
        try:
            # Check model file exists
            if not config.model_path.exists():
                logger.error(f"Model file not found: {config.model_path}")
                return False
            
            # Check port availability (basic check)
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                result = sock.connect_ex(('localhost', config.port))
                if result == 0:
                    logger.error(f"Port {config.port} is already in use")
                    return False
            finally:
                sock.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Config validation error: {e}")
            return False
    
    async def _acquire_model_lock(self, config: ModelConfig) -> bool:
        """Acquire the model lock for this configuration."""
        # Create a temporary model instance for lock acquisition
        temp_instance = ModelInstance(
            process_id=0,  # Will be updated after process creation
            model_name=config.name,
            port=config.port,
            backend_type=config.backend_type,
            device=config.device
        )
        
        return self.model_lock.acquire_lock(temp_instance)
    
    async def _spawn_model_process(self, config: ModelConfig) -> Optional[subprocess.Popen]:
        """Spawn the model process based on backend type."""
        try:
            # Build command based on backend type
            cmd = self._build_command(config)
            if not cmd:
                return None
            
            # Prepare environment
            env = dict(os.environ)
            env.update(config.environment)
            
            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=config.model_path.parent
            )
            
            # Update the model lock with the actual process ID
            if self.model_lock._current_instance:
                self.model_lock._current_instance.process_id = process.pid
            
            logger.info(f"Model process spawned: PID {process.pid}")
            return process
            
        except Exception as e:
            logger.error(f"Failed to spawn model process: {e}")
            return None
    
    def _build_command(self, config: ModelConfig) -> Optional[List[str]]:
        """Build the command to start the model based on backend type."""
        if config.backend_type == 'koboldcpp':
            cmd = [
                'python', 'koboldcpp.py',
                '--model', str(config.model_path),
                '--port', str(config.port),
                '--host', '0.0.0.0'
            ]
            
            # Add extra arguments
            for key, value in config.extra_args.items():
                if value is True:
                    cmd.append(f'--{key}')
                elif value is not False:
                    cmd.extend([f'--{key}', str(value)])
            
            return cmd
            
        elif config.backend_type == 'text-generation-webui':
            cmd = [
                'python', 'server.py',
                '--model', str(config.model_path),
                '--listen-port', str(config.port),
                '--listen'
            ]
            
            # Add extra arguments  
            for key, value in config.extra_args.items():
                if value is True:
                    cmd.append(f'--{key}')
                elif value is not False:
                    cmd.extend([f'--{key}', str(value)])
            
            return cmd
        
        else:
            logger.error(f"Unknown backend type: {config.backend_type}")
            return None
    
    async def _wait_for_model_ready(self, config: ModelConfig, process: subprocess.Popen) -> bool:
        """Wait for the model to be ready to accept requests."""
        import aiohttp
        
        start_time = time.time()
        url = f"http://localhost:{config.port}/api/v1/model"
        
        while time.time() - start_time < config.timeout_seconds:
            # Check if process is still running
            if process.poll() is not None:
                logger.error("Model process terminated during startup")
                return False
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            logger.info(f"Model ready: {config.name}")
                            return True
            except:
                pass  # Expected during startup
            
            await asyncio.sleep(2)
        
        logger.error(f"Model failed to become ready within {config.timeout_seconds}s")
        return False
    
    async def _start_monitoring(self, config: ModelConfig, process: subprocess.Popen) -> None:
        """Start monitoring the model process."""
        self._monitoring_active = True
        self._monitor_task = asyncio.create_task(self._monitor_model(config, process))

    async def _monitor_model(self, config: ModelConfig, process: subprocess.Popen) -> None:
        """Monitor the model process health and resources."""
        try:
            while self._monitoring_active and process.poll() is None:
                try:
                    # Update memory usage
                    ps_process = psutil.Process(process.pid)
                    memory_mb = ps_process.memory_info().rss / 1024 / 1024

                    with self._status_lock:
                        self._status.memory_usage_mb = memory_mb
                        self._status.last_activity = time.time()

                    # Update model lock with memory info
                    self.model_lock.update_model_memory(int(memory_mb))

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    logger.warning("Lost access to model process during monitoring")
                    break

                await asyncio.sleep(10)  # Monitor every 10 seconds

        except Exception as e:
            logger.error(f"Model monitoring error: {e}")

    async def _stop_monitoring(self) -> None:
        """Stop model monitoring."""
        self._monitoring_active = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

    async def _graceful_shutdown(self, process_id: Optional[int]) -> bool:
        """Attempt graceful shutdown of the model process."""
        if not process_id:
            return False

        try:
            process = psutil.Process(process_id)
            process.terminate()

            # Wait for graceful termination
            try:
                process.wait(timeout=30)
                logger.info(f"Model process {process_id} terminated gracefully")
                return True
            except psutil.TimeoutExpired:
                return False

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return True  # Process already gone

    async def _force_shutdown(self, process_id: Optional[int]) -> None:
        """Force shutdown of the model process."""
        if not process_id:
            return

        try:
            process = psutil.Process(process_id)
            process.kill()
            logger.warning(f"Model process {process_id} force killed")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass  # Process already gone

    async def _comprehensive_cleanup(self, config: Optional[ModelConfig], process_id: Optional[int]) -> CleanupResult:
        """Perform comprehensive cleanup after model stop."""
        return self.memory_cleaner.cleanup_after_model(
            process_id=process_id,
            model_name=config.name if config else None,
            aggressive=True
        )

    async def _cleanup_failed_load(self, config: ModelConfig) -> None:
        """Cleanup after a failed model load."""
        try:
            # Force release model lock
            self.model_lock.force_release("failed load cleanup")

            # Basic cleanup
            self.memory_cleaner.cleanup_after_model(
                model_name=config.name,
                aggressive=False
            )

        except Exception as e:
            logger.error(f"Cleanup after failed load error: {e}")

    async def _run_hooks(self, event: str, *args, **kwargs) -> None:
        """Run lifecycle hooks for a specific event."""
        for hook in self._lifecycle_hooks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(*args, **kwargs)
                else:
                    hook(*args, **kwargs)
            except Exception as e:
                logger.error(f"Lifecycle hook {hook.__name__} failed: {e}")

    def _update_status(self, **kwargs) -> None:
        """Thread-safe status update."""
        with self._status_lock:
            for key, value in kwargs.items():
                if hasattr(self._status, key):
                    setattr(self._status, key, value)

    def _get_status_context(self):
        """Get status lock context manager."""
        return self._status_lock

    def get_status(self) -> ModelStatus:
        """Get current model status."""
        with self._status_lock:
            # Return a copy to prevent external modification
            return ModelStatus(
                state=self._status.state,
                model_config=self._status.model_config,
                process_id=self._status.process_id,
                start_time=self._status.start_time,
                error_message=self._status.error_message,
                memory_usage_mb=self._status.memory_usage_mb,
                last_activity=self._status.last_activity
            )

    def is_model_running(self) -> bool:
        """Check if a model is currently running."""
        with self._status_lock:
            return self._status.state == ModelState.RUNNING

# Fix aiohttp import error
try:
    import aiohttp
except ImportError:
    logger.error("aiohttp library is not installed. Please install it using 'pip install aiohttp'.")
