"""
⚙️ Process Manager - Process Control

Features:
- Subprocess launching and monitoring
- Process termination with graceful shutdown
- Command building for different backends
- Environment setup (CUDA, venv)
- Sequential loading pipeline
"""

import os
import sys
import json
import time
import socket
import platform
import subprocess
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ProcessManager:
    """
    Handles server processes and lifecycle management.
    """

    def __init__(self, config_dir: str = "loader_config"):
        self.config_dir = Path(config_dir)
        self.servers_file = self.config_dir / "running_servers.json"
        self.running_processes: Dict[str, Dict] = {}
        self.allocated_ports: List[int] = []
        
        # Load existing process state
        self._load_running_processes()
        
        logger.info("⚙️ Process Manager initialized")

    def launch_server(self, model_name: str, model_path: str, backend: str, 
                     port: int, **kwargs) -> Dict[str, any]:
        """Launch a model server process"""
        try:
            # Build command for the specific backend
            cmd = self._build_command(backend, model_path, port, **kwargs)
            if not cmd:
                return {"success": False, "error": f"Could not build command for backend: {backend}"}
            
            # Setup environment
            env = self._setup_environment(**kwargs)
            
            # Launch process
            logger.info(f"🚀 Launching {model_name} on port {port}")
            logger.info(f"   Command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd, 
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Wait for server to start
            if self._wait_for_server(port, timeout=30):
                # Store process info
                process_info = {
                    "name": model_name,
                    "model_path": model_path,
                    "backend": backend,
                    "port": port,
                    "process_id": process.pid,
                    "command": cmd,
                    "started_at": time.time(),
                    "url": f"http://127.0.0.1:{port}",
                    "status": "running"
                }
                
                self.running_processes[model_name] = process_info
                self.allocated_ports.append(port)
                self._save_running_processes()
                
                logger.info(f"✅ Server launched successfully: {model_name}")
                return {"success": True, **process_info}
            else:
                # Server failed to start
                self._terminate_process(process)
                return {"success": False, "error": f"Server failed to start on port {port}"}
                
        except Exception as e:
            logger.error(f"Failed to launch server: {e}")
            return {"success": False, "error": str(e)}

    def stop_server(self, model_name: str) -> bool:
        """Stop a running server process"""
        if model_name not in self.running_processes:
            logger.warning(f"Process {model_name} not found")
            return False
        
        process_info = self.running_processes[model_name]
        process_id = process_info.get("process_id")
        port = process_info.get("port")
        
        try:
            # Graceful shutdown
            if process_id:
                success = self._terminate_process_by_pid(process_id)
                if not success:
                    logger.warning(f"Could not terminate process {process_id}, may already be stopped")
            
            # Clean up tracking
            del self.running_processes[model_name]
            if port in self.allocated_ports:
                self.allocated_ports.remove(port)
            
            self._save_running_processes()
            logger.info(f"✅ Stopped server: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop server {model_name}: {e}")
            return False

    def stop_all_servers(self) -> int:
        """Stop all running servers"""
        logger.info("🛑 Stopping all running servers...")
        
        stopped_count = 0
        for model_name in list(self.running_processes.keys()):
            if self.stop_server(model_name):
                stopped_count += 1
        
        logger.info(f"✅ Stopped {stopped_count} servers")
        return stopped_count

    def restart_server(self, model_name: str) -> Dict[str, any]:
        """Restart a server process"""
        if model_name not in self.running_processes:
            return {"success": False, "error": f"Server {model_name} not found"}
        
        # Get current process info
        process_info = self.running_processes[model_name].copy()
        
        # Stop current process
        logger.info(f"🔄 Restarting server: {model_name}")
        if not self.stop_server(model_name):
            return {"success": False, "error": "Failed to stop current process"}
        
        # Wait a moment
        time.sleep(2)
        
        # Restart with same parameters
        return self.launch_server(
            model_name=process_info["name"],
            model_path=process_info["model_path"],
            backend=process_info["backend"],
            port=process_info["port"]
        )

    def check_process_health(self) -> Dict[str, bool]:
        """Check health of all running processes"""
        health_status = {}
        
        for name, info in self.running_processes.items():
            process_id = info.get("process_id")
            port = info.get("port")
            
            # Check if process is running
            process_running = False
            if process_id:
                try:
                    process = psutil.Process(process_id)
                    process_running = process.is_running()
                except psutil.NoSuchProcess:
                    process_running = False
            
            # Check if port is responding
            port_responding = self._check_port_responding(port)
            
            # Overall health
            health_status[name] = process_running and port_responding
            
            # Update status in process info
            if process_running and port_responding:
                info["status"] = "running"
            elif process_running:
                info["status"] = "starting"
            else:
                info["status"] = "stopped"
        
        self._save_running_processes()
        return health_status

    def sequential_load(self, models: List[Dict], delay_seconds: int = 2) -> Dict[str, Dict]:
        """Load models sequentially with resource clearing"""
        results = {}
        
        logger.info(f"🔄 Sequential loading of {len(models)} models")
        
        for i, model_config in enumerate(models):
            model_name = model_config["name"]
            logger.info(f"📋 Loading model {i+1}/{len(models)}: {model_name}")
            
            # Stop previous model if clear_previous is True
            if model_config.get("clear_previous", True) and i > 0:
                prev_model = models[i-1]["name"]
                self.stop_server(prev_model)
                time.sleep(1)  # Allow cleanup
            
            # Launch new model
            result = self.launch_server(**model_config)
            results[model_name] = result
            
            if result["success"]:
                logger.info(f"✅ Model {i+1} loaded successfully")
                
                # Optional delay between loads
                if delay_seconds > 0 and i < len(models) - 1:
                    logger.info(f"⏱️ Waiting {delay_seconds} seconds...")
                    time.sleep(delay_seconds)
            else:
                logger.error(f"❌ Failed to load model {i+1}: {result.get('error')}")
        
        return results

    def _build_command(self, backend: str, model_path: str, port: int, **kwargs) -> Optional[List[str]]:
        """Build command for launching model server"""
        
        if backend == "llama.cpp":
            return self._build_llama_command(model_path, port, **kwargs)
        elif backend == "transformers":
            return self._build_transformers_command(model_path, port, **kwargs)
        elif backend == "exllama":
            return self._build_exllama_command(model_path, port, **kwargs)
        else:
            logger.error(f"Unknown backend: {backend}")
            return None

    def _build_llama_command(self, model_path: str, port: int, **kwargs) -> List[str]:
        """Build llama.cpp server command"""
        # Find llama-server executable
        llama_server = self._find_executable(["llama-server.exe", "llama-server"])
        if not llama_server:
            logger.error("llama-server executable not found")
            return None
        
        cmd = [llama_server, "--model", model_path, "--port", str(port)]
        
        # Add optional parameters
        if "context_length" in kwargs:
            cmd.extend(["--ctx-size", str(kwargs["context_length"])])
        if "gpu_layers" in kwargs:
            cmd.extend(["--n-gpu-layers", str(kwargs["gpu_layers"])])
        if "threads" in kwargs:
            cmd.extend(["--threads", str(kwargs["threads"])])
        
        return cmd

    def _build_transformers_command(self, model_path: str, port: int, **kwargs) -> List[str]:
        """Build transformers server command"""
        # Use python script for transformers
        cmd = [sys.executable, "-c", f"""
import sys
sys.path.append('.')
from transformers_server import start_server
start_server('{model_path}', {port})
"""]
        return cmd

    def _build_exllama_command(self, model_path: str, port: int, **kwargs) -> List[str]:
        """Build exllama server command"""
        # Use python script for exllama
        cmd = [sys.executable, "-c", f"""
import sys
sys.path.append('.')
from exllama_server import start_server
start_server('{model_path}', {port})
"""]
        return cmd

    def _setup_environment(self, **kwargs) -> Dict[str, str]:
        """Setup environment variables for process"""
        env = os.environ.copy()
        
        # Add CUDA paths if specified
        cuda_paths = kwargs.get("cuda_paths", [])
        for cuda_path in cuda_paths:
            if os.path.isdir(cuda_path):
                env["PATH"] = f"{cuda_path}{os.pathsep}" + env.get("PATH", "")
        
        # Activate virtual environment if specified
        venv_path = kwargs.get("venv_activate")
        if venv_path and os.path.isdir(venv_path):
            self._activate_virtualenv(env, venv_path)
        
        return env

    def _activate_virtualenv(self, env: Dict[str, str], venv_path: str):
        """Activate virtual environment"""
        env["VIRTUAL_ENV"] = venv_path
        if platform.system() == "Windows":
            bin_path = os.path.join(venv_path, "Scripts")
        else:
            bin_path = os.path.join(venv_path, "bin")
        
        env["PATH"] = f"{bin_path}{os.pathsep}" + env.get("PATH", "")
        logger.info(f"📦 Activated virtual environment: {venv_path}")

    def _find_executable(self, names: List[str]) -> Optional[str]:
        """Find executable in common paths"""
        search_paths = [
            ".",
            "bin",
            "tools", 
            os.path.expanduser("~/bin"),
            "C:\\Program Files\\LlamaCpp",
            "C:\\LlamaCpp\\bin"
        ]
        
        for name in names:
            for path in search_paths:
                full_path = Path(path) / name
                if full_path.exists():
                    return str(full_path)
        
        return None

    def _wait_for_server(self, port: int, timeout: int = 30) -> bool:
        """Wait for server to start responding"""
        logger.info(f"⏳ Waiting for server on port {port}...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self._check_port_responding(port):
                logger.info(f"✅ Server responding on port {port}")
                return True
            time.sleep(1)
        
        logger.warning(f"⚠️ Server timeout after {timeout} seconds")
        return False

    def _check_port_responding(self, port: int) -> bool:
        """Check if port is responding"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                result = s.connect_ex(('127.0.0.1', port))
                return result == 0
        except:
            return False

    def _terminate_process(self, process: subprocess.Popen):
        """Terminate a subprocess"""
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        except:
            pass

    def _terminate_process_by_pid(self, pid: int) -> bool:
        """Terminate process by PID"""
        try:
            process = psutil.Process(pid)
            process.terminate()
            process.wait(timeout=5)
            return True
        except psutil.TimeoutExpired:
            try:
                process.kill()
                return True
            except:
                return False
        except psutil.NoSuchProcess:
            return True  # Already terminated
        except:
            return False

    def _load_running_processes(self):
        """Load running process information"""
        if self.servers_file.exists():
            try:
                with open(self.servers_file, 'r') as f:
                    data = json.load(f)
                    self.running_processes = data.get("processes", {})
                    self.allocated_ports = data.get("allocated_ports", [])
            except Exception as e:
                logger.warning(f"Failed to load process info: {e}")

    def _save_running_processes(self):
        """Save running process information"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.servers_file, 'w') as f:
                json.dump({
                    "processes": self.running_processes,
                    "allocated_ports": self.allocated_ports,
                    "last_update": time.time()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save process info: {e}")

    def get_process_summary(self) -> Dict[str, any]:
        """Get summary of running processes"""
        health_status = self.check_process_health()
        
        return {
            "total_processes": len(self.running_processes),
            "healthy_processes": sum(health_status.values()),
            "allocated_ports": self.allocated_ports.copy(),
            "processes": {
                name: {
                    "status": info["status"],
                    "port": info["port"],
                    "backend": info["backend"],
                    "uptime": time.time() - info["started_at"]
                }
                for name, info in self.running_processes.items()
            },
            "health": health_status
        }

if __name__ == "__main__":
    # Example usage
    manager = ProcessManager()
    
    # Test launching a server
    result = manager.launch_server(
        model_name="test_model",
        model_path="models/test.gguf", 
        backend="llama.cpp",
        port=8080,
        context_length=4096,
        gpu_layers=32
    )
    
    print(f"Launch result: {result}")
    
    # Check health
    health = manager.check_process_health()
    print(f"Health status: {health}")
    
    # Get summary
    summary = manager.get_process_summary()
    print(f"Process summary: {json.dumps(summary, indent=2)}")
