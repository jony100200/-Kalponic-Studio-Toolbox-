"""
🔍 Service Discovery - External AI Service Detection
Role: "Service Scout" - Find and monitor running AI services
SOLID Principle: Single Responsibility - Service discovery only
"""

import socket
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class DetectedService:
    """Information about a detected external service"""
    name: str
    port: int
    url: str
    service_type: str  # "ai_model", "api_server", "unknown"
    status: str  # "running", "unreachable", "error"
    response_time_ms: Optional[float] = None
    api_info: Optional[Dict] = None


class ServiceDiscovery:
    """Pure service discovery - no port allocation or configuration"""
    
    def __init__(self, cache_path: Optional[str] = None):
        self.cache_path = Path(cache_path) if cache_path else Path("config/discovered_services.json")
        self.detected_services: Dict[str, DetectedService] = {}
        self.scan_ports = [
            8000, 8001, 8080, 8081, 8100, 8101, 8181,  # Common AI service ports
            3000, 5000, 7860,  # Gradio/Streamlit defaults
            11434,  # Ollama default
            1234,   # text-generation-webui
            5001    # KoboldCpp alternate
        ]
        self.load_cache()
    
    def scan_for_services(self, timeout_seconds: float = 0.5) -> Dict[str, DetectedService]:
        """Quick scan for running services on known ports"""
        self.detected_services.clear()
        
        for port in self.scan_ports:
            service = self._check_port(port, timeout_seconds)
            if service:
                service_key = f"service_{port}"
                self.detected_services[service_key] = service
        
        self.save_cache()
        return self.detected_services.copy()
    
    def _check_port(self, port: int, timeout: float) -> Optional[DetectedService]:
        """Check if a specific port has a running service"""
        import time
        start_time = time.time()
        
        # Quick socket check
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                result = sock.connect_ex(('localhost', port))
                
                if result != 0:  # Port not open
                    return None
                
                response_time = (time.time() - start_time) * 1000
                
                # Try to identify service type via HTTP
                service_info = self._identify_service(port, timeout)
                
                return DetectedService(
                    name=service_info.get("name", f"Service on port {port}"),
                    port=port,
                    url=f"http://localhost:{port}",
                    service_type=service_info.get("type", "unknown"),
                    status="running",
                    response_time_ms=round(response_time, 2),
                    api_info=service_info.get("api_info")
                )
                
        except Exception:
            return None
    
    def _identify_service(self, port: int, timeout: float) -> Dict:
        """Try to identify what type of service is running"""
        service_info = {
            "name": f"Unknown Service ({port})",
            "type": "unknown",
            "api_info": None
        }
        
        # Try common endpoints to identify service
        endpoints_to_try = [
            ("/", "GET"),
            ("/api/v1/models", "GET"),  # OpenAI-compatible
            ("/v1/models", "GET"),      # Alternative OpenAI path
            ("/api/extra/version", "GET"),  # KoboldCpp
            ("/docs", "GET"),           # FastAPI docs
            ("/health", "GET"),         # Health check
        ]
        
        for endpoint, method in endpoints_to_try:
            try:
                url = f"http://localhost:{port}{endpoint}"
                response = requests.request(method, url, timeout=timeout)
                
                if response.status_code == 200:
                    service_info.update(self._analyze_response(response, port))
                    break
                    
            except Exception:
                continue
        
        return service_info
    
    def _analyze_response(self, response: requests.Response, port: int) -> Dict:
        """Analyze HTTP response to determine service type"""
        service_info = {"name": f"HTTP Service ({port})", "type": "api_server"}
        
        try:
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            
            # Check for JSON APIs
            if 'application/json' in content_type:
                try:
                    data = response.json()
                    
                    # OpenAI-compatible API
                    if isinstance(data, dict) and 'data' in data:
                        service_info.update({
                            "name": "OpenAI-Compatible API",
                            "type": "ai_model",
                            "api_info": {"format": "openai", "models": len(data.get('data', []))}
                        })
                    
                    # KoboldCpp API
                    elif 'version' in str(data).lower() and 'kobold' in str(data).lower():
                        service_info.update({
                            "name": "KoboldCpp Server",
                            "type": "ai_model",
                            "api_info": {"format": "koboldcpp", "version": data.get('version')}
                        })
                        
                except:
                    pass
            
            # Check for Gradio (common in AI UIs)
            elif 'text/html' in content_type:
                text_content = response.text.lower()
                if 'gradio' in text_content:
                    service_info.update({
                        "name": "Gradio AI Interface",
                        "type": "ai_model"
                    })
                elif 'text generation' in text_content:
                    service_info.update({
                        "name": "Text Generation WebUI",
                        "type": "ai_model"
                    })
        
        except Exception:
            pass
        
        return service_info
    
    def get_ai_services(self) -> List[DetectedService]:
        """Get only detected AI/ML services"""
        return [
            service for service in self.detected_services.values()
            if service.service_type == "ai_model"
        ]
    
    def get_service_by_port(self, port: int) -> Optional[DetectedService]:
        """Get detected service by port number"""
        for service in self.detected_services.values():
            if service.port == port:
                return service
        return None
    
    def check_service_health(self, port: int, timeout: float = 2.0) -> Dict[str, any]:
        """Check if a specific service is still healthy"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                result = sock.connect_ex(('localhost', port))
                
                if result == 0:
                    return {"status": "healthy", "reachable": True}
                else:
                    return {"status": "unreachable", "reachable": False}
                    
        except Exception as e:
            return {"status": "error", "reachable": False, "error": str(e)}
    
    def refresh_service_status(self) -> None:
        """Refresh status of all detected services"""
        for service_key, service in self.detected_services.items():
            health = self.check_service_health(service.port)
            service.status = health["status"]
        
        self.save_cache()
    
    def add_custom_scan_port(self, port: int) -> None:
        """Add custom port to scan list"""
        if port not in self.scan_ports:
            self.scan_ports.append(port)
            self.scan_ports.sort()
    
    def remove_scan_port(self, port: int) -> None:
        """Remove port from scan list"""
        if port in self.scan_ports:
            self.scan_ports.remove(port)
    
    def save_cache(self) -> None:
        """Save discovered services to cache"""
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            cache_data = {
                "detected_services": {
                    key: asdict(service) for key, service in self.detected_services.items()
                },
                "scan_ports": self.scan_ports
            }
            
            with open(self.cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save service cache: {e}")
    
    def load_cache(self) -> None:
        """Load discovered services from cache"""
        try:
            if self.cache_path.exists():
                with open(self.cache_path, 'r') as f:
                    data = json.load(f)
                
                # Load detected services
                services_data = data.get("detected_services", {})
                for key, service_dict in services_data.items():
                    self.detected_services[key] = DetectedService(**service_dict)
                
                # Load scan ports
                self.scan_ports = data.get("scan_ports", self.scan_ports)
                
        except Exception as e:
            print(f"Warning: Could not load service cache: {e}")
    
    def get_discovery_summary(self) -> Dict:
        """Get complete service discovery summary"""
        return {
            "total_services": len(self.detected_services),
            "ai_services": len(self.get_ai_services()),
            "scan_ports": self.scan_ports,
            "detected_services": {
                key: asdict(service) for key, service in self.detected_services.items()
            }
        }
