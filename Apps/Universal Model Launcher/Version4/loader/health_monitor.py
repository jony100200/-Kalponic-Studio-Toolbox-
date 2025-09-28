"""
🏥 Health Monitor - Monitoring + Logging

Features:
- Real-time health monitoring
- Structured logging
- Performance metrics
- Auto-restart on failures
"""

import time
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthMetric:
    """Health metric data structure"""
    name: str
    value: float
    status: HealthStatus
    threshold: float
    timestamp: float
    unit: str = ""

class HealthMonitor:
    """
    Real-time health monitoring and logging system.
    """

    def __init__(self, monitoring_interval: int = 30, log_dir: str = "logs"):
        self.monitoring_interval = monitoring_interval
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.health_callbacks: List[Callable] = []
        self.restart_callbacks: List[Callable] = []
        
        # Health data
        self.current_metrics: Dict[str, HealthMetric] = {}
        self.health_history: List[Dict] = []
        self.alert_count = 0
        
        # Thresholds
        self.thresholds = {
            "memory_percent": 0.85,
            "gpu_memory_percent": 0.90,
            "cpu_percent": 0.80,
            "disk_percent": 0.90,
            "response_time_ms": 5000
        }
        
        # Setup structured logging
        self._setup_logging()
        
        logger.info("🏥 Health Monitor initialized")

    def _setup_logging(self):
        """Setup structured logging to files"""
        # Health log
        health_log_file = self.log_dir / "health.log"
        health_handler = logging.FileHandler(health_log_file)
        health_formatter = logging.Formatter(
            '%(asctime)s - HEALTH - %(levelname)s - %(message)s'
        )
        health_handler.setFormatter(health_formatter)
        
        # Performance log  
        perf_log_file = self.log_dir / "performance.log"
        self.perf_handler = logging.FileHandler(perf_log_file)
        perf_formatter = logging.Formatter(
            '%(asctime)s - PERF - %(message)s'
        )
        self.perf_handler.setFormatter(perf_formatter)
        
        # Create separate loggers
        self.health_logger = logging.getLogger("health")
        self.health_logger.addHandler(health_handler)
        self.health_logger.setLevel(logging.INFO)
        
        self.perf_logger = logging.getLogger("performance")  
        self.perf_logger.addHandler(self.perf_handler)
        self.perf_logger.setLevel(logging.INFO)

    def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.is_monitoring:
            logger.warning("Health monitoring already running")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"Health monitoring started (interval: {self.monitoring_interval}s)")

    def stop_monitoring(self):
        """Stop health monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Health monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect metrics
                metrics = self._collect_system_metrics()
                
                # Update current metrics
                self.current_metrics.update(metrics)
                
                # Check health status
                overall_status = self._evaluate_health(metrics)
                
                # Log health data
                self._log_health_data(metrics, overall_status)
                
                # Store in history
                self._store_health_history(metrics, overall_status)
                
                # Check for alerts
                self._check_alerts(metrics, overall_status)
                
                # Sleep until next check
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

    def _collect_system_metrics(self) -> Dict[str, HealthMetric]:
        """Collect system performance metrics"""
        import psutil
        
        metrics = {}
        current_time = time.time()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        metrics["memory_percent"] = HealthMetric(
            name="memory_percent",
            value=memory.percent / 100,
            status=self._get_status(memory.percent / 100, self.thresholds["memory_percent"]),
            threshold=self.thresholds["memory_percent"],
            timestamp=current_time,
            unit="%"
        )
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics["cpu_percent"] = HealthMetric(
            name="cpu_percent", 
            value=cpu_percent / 100,
            status=self._get_status(cpu_percent / 100, self.thresholds["cpu_percent"]),
            threshold=self.thresholds["cpu_percent"],
            timestamp=current_time,
            unit="%"
        )
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        metrics["disk_percent"] = HealthMetric(
            name="disk_percent",
            value=disk.percent / 100,
            status=self._get_status(disk.percent / 100, self.thresholds["disk_percent"]),
            threshold=self.thresholds["disk_percent"],
            timestamp=current_time,
            unit="%"
        )
        
        # GPU metrics (if available)
        gpu_metrics = self._collect_gpu_metrics(current_time)
        if gpu_metrics:
            metrics.update(gpu_metrics)
        
        return metrics

    def _collect_gpu_metrics(self, timestamp: float) -> Optional[Dict[str, HealthMetric]]:
        """Collect GPU metrics if available"""
        try:
            import torch
            if torch.cuda.is_available():
                metrics = {}
                for i in range(torch.cuda.device_count()):
                    memory_reserved = torch.cuda.memory_reserved(i)
                    memory_total = torch.cuda.get_device_properties(i).total_memory
                    gpu_percent = memory_reserved / memory_total
                    
                    metrics[f"gpu_{i}_memory_percent"] = HealthMetric(
                        name=f"gpu_{i}_memory_percent",
                        value=gpu_percent,
                        status=self._get_status(gpu_percent, self.thresholds["gpu_memory_percent"]),
                        threshold=self.thresholds["gpu_memory_percent"],
                        timestamp=timestamp,
                        unit="%"
                    )
                
                return metrics
        except ImportError:
            pass
        
        return None

    def _get_status(self, value: float, threshold: float) -> HealthStatus:
        """Determine health status based on value and threshold"""
        if value < threshold * 0.7:
            return HealthStatus.HEALTHY
        elif value < threshold * 0.9:
            return HealthStatus.WARNING
        elif value < threshold:
            return HealthStatus.CRITICAL
        else:
            return HealthStatus.CRITICAL

    def _evaluate_health(self, metrics: Dict[str, HealthMetric]) -> HealthStatus:
        """Evaluate overall system health"""
        statuses = [metric.status for metric in metrics.values()]
        
        if any(status == HealthStatus.CRITICAL for status in statuses):
            return HealthStatus.CRITICAL
        elif any(status == HealthStatus.WARNING for status in statuses):
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY

    def _log_health_data(self, metrics: Dict[str, HealthMetric], overall_status: HealthStatus):
        """Log health data to structured logs"""
        # Health log entry
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status.value,
            "metrics": {
                name: {
                    "value": metric.value,
                    "status": metric.status.value,
                    "threshold": metric.threshold
                }
                for name, metric in metrics.items()
            }
        }
        
        self.health_logger.info(json.dumps(health_data))
        
        # Performance log entry
        perf_data = {
            "timestamp": datetime.now().isoformat(),
            **{name: metric.value for name, metric in metrics.items()}
        }
        
        self.perf_logger.info(json.dumps(perf_data))

    def _store_health_history(self, metrics: Dict[str, HealthMetric], overall_status: HealthStatus):
        """Store health data in memory history"""
        history_entry = {
            "timestamp": time.time(),
            "overall_status": overall_status.value,
            "metrics": {name: metric.value for name, metric in metrics.items()}
        }
        
        self.health_history.append(history_entry)
        
        # Keep only last 100 entries
        if len(self.health_history) > 100:
            self.health_history = self.health_history[-100:]

    def _check_alerts(self, metrics: Dict[str, HealthMetric], overall_status: HealthStatus):
        """Check for alert conditions and trigger callbacks"""
        if overall_status == HealthStatus.CRITICAL:
            self.alert_count += 1
            logger.warning(f"🚨 CRITICAL health status detected (alert #{self.alert_count})")
            
            # Trigger health callbacks
            for callback in self.health_callbacks:
                try:
                    callback(metrics, overall_status)
                except Exception as e:
                    logger.error(f"Error in health callback: {e}")
            
            # Auto-restart logic
            if self.alert_count >= 3:  # 3 consecutive critical alerts
                logger.error("🔄 Triggering auto-restart due to persistent critical status")
                self._trigger_restart()
        else:
            # Reset alert count on healthy status
            if overall_status == HealthStatus.HEALTHY:
                self.alert_count = 0

    def _trigger_restart(self):
        """Trigger restart callbacks"""
        for callback in self.restart_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in restart callback: {e}")

    def add_health_callback(self, callback: Callable):
        """Add callback for health status changes"""
        self.health_callbacks.append(callback)

    def add_restart_callback(self, callback: Callable):
        """Add callback for restart triggers"""
        self.restart_callbacks.append(callback)

    def get_current_status(self) -> Dict:
        """Get current health status"""
        if not self.current_metrics:
            return {"status": "unknown", "message": "No metrics collected yet"}
        
        overall_status = self._evaluate_health(self.current_metrics)
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                name: {
                    "value": metric.value,
                    "status": metric.status.value,
                    "unit": metric.unit
                }
                for name, metric in self.current_metrics.items()
            },
            "alert_count": self.alert_count
        }

    def get_health_history(self, limit: int = 50) -> List[Dict]:
        """Get recent health history"""
        return self.health_history[-limit:]

if __name__ == "__main__":
    # Example usage
    monitor = HealthMonitor(monitoring_interval=10)
    
    # Add sample callbacks
    def health_alert(metrics, status):
        print(f"Health alert: {status.value}")
    
    def restart_system():
        print("System restart triggered")
    
    monitor.add_health_callback(health_alert)
    monitor.add_restart_callback(restart_system)
    
    # Start monitoring
    monitor.start_monitoring()
    
    try:
        # Run for a bit
        time.sleep(60)
    finally:
        monitor.stop_monitoring()
