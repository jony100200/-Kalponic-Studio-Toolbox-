"""
🔌 Port Allocator - Network Port Management Only
Role: "Network Coordinator" - Port allocation and availability checking
SOLID Principle: Single Responsibility - Port management only
"""

import socket
import json
from pathlib import Path
from typing import Dict, List, Optional, Set


class PortAllocator:
    """Pure port management - no service discovery or monitoring"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path("config/ports.json")
        self.allocated_ports: Dict[str, int] = {}
        self.reserved_ports: Set[int] = {22, 25, 53, 80, 110, 143, 443, 993, 995}  # Common system ports
        self.default_ranges = {
            "main_api": (8000, 8100),
            "model_servers": (8100, 8200), 
            "utility_services": (8200, 8300)
        }
        self.load_allocations()
    
    def is_port_available(self, port: int) -> bool:
        """Check if a port is available for binding"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.settimeout(0.5)
                result = sock.bind(('localhost', port))
                return True
        except (OSError, socket.error):
            return False
    
    def find_available_port(self, start_port: int = 8000, end_port: int = 9000) -> Optional[int]:
        """Find first available port in range"""
        for port in range(start_port, end_port + 1):
            if (port not in self.reserved_ports and 
                port not in self.allocated_ports.values() and 
                self.is_port_available(port)):
                return port
        return None
    
    def allocate_port(self, service_name: str, preferred_port: Optional[int] = None) -> int:
        """Allocate a port for a service"""
        # Return existing allocation
        if service_name in self.allocated_ports:
            allocated_port = self.allocated_ports[service_name]
            if self.is_port_available(allocated_port):
                return allocated_port
            else:
                # Port no longer available, need new one
                del self.allocated_ports[service_name]
        
        # Try preferred port
        if preferred_port and preferred_port not in self.reserved_ports:
            if (preferred_port not in self.allocated_ports.values() and 
                self.is_port_available(preferred_port)):
                self.allocated_ports[service_name] = preferred_port
                self.save_allocations()
                return preferred_port
        
        # Find available port in appropriate range
        range_name = self._get_service_range(service_name)
        start_port, end_port = self.default_ranges.get(range_name, (8000, 9000))
        
        port = self.find_available_port(start_port, end_port)
        if port:
            self.allocated_ports[service_name] = port
            self.save_allocations()
            return port
        
        raise RuntimeError(f"No available ports found for service '{service_name}' in range {start_port}-{end_port}")
    
    def _get_service_range(self, service_name: str) -> str:
        """Determine which port range to use for a service"""
        service_lower = service_name.lower()
        
        # Check for model services first (more specific)
        if "model" in service_lower or "llm" in service_lower:
            return "model_servers"
        elif "api" in service_lower or "server" in service_lower:
            return "main_api"
        else:
            return "utility_services"
    
    def deallocate_port(self, service_name: str) -> bool:
        """Remove port allocation for a service"""
        if service_name in self.allocated_ports:
            del self.allocated_ports[service_name]
            self.save_allocations()
            return True
        return False
    
    def get_allocated_port(self, service_name: str) -> Optional[int]:
        """Get currently allocated port for a service"""
        return self.allocated_ports.get(service_name)
    
    def get_all_allocations(self) -> Dict[str, int]:
        """Get all current port allocations"""
        return self.allocated_ports.copy()
    
    def check_port_conflicts(self) -> List[str]:
        """Check for port conflicts in current allocations"""
        conflicts = []
        for service_name, port in self.allocated_ports.items():
            if not self.is_port_available(port):
                conflicts.append(f"{service_name}:{port}")
        return conflicts
    
    def reserve_port(self, port: int) -> None:
        """Add port to reserved list (won't be allocated)"""
        self.reserved_ports.add(port)
    
    def unreserve_port(self, port: int) -> None:
        """Remove port from reserved list"""
        self.reserved_ports.discard(port)
    
    def get_port_range_usage(self) -> Dict[str, Dict]:
        """Get usage statistics for each port range"""
        usage = {}
        for range_name, (start, end) in self.default_ranges.items():
            allocated_in_range = [
                port for port in self.allocated_ports.values() 
                if start <= port <= end
            ]
            available_count = sum(
                1 for port in range(start, end + 1)
                if port not in self.reserved_ports and self.is_port_available(port)
            )
            
            usage[range_name] = {
                "range": f"{start}-{end}",
                "allocated": len(allocated_in_range),
                "available": available_count,
                "total": end - start + 1
            }
        return usage
    
    def save_allocations(self) -> None:
        """Save port allocations to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "allocated_ports": self.allocated_ports,
                "reserved_ports": list(self.reserved_ports),
                "default_ranges": self.default_ranges
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save port allocations: {e}")
    
    def load_allocations(self) -> None:
        """Load port allocations from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                self.allocated_ports = data.get("allocated_ports", {})
                self.reserved_ports.update(data.get("reserved_ports", []))
                
                # Update ranges if they exist in config
                saved_ranges = data.get("default_ranges", {})
                self.default_ranges.update(saved_ranges)
                
        except Exception as e:
            print(f"Warning: Could not load port allocations: {e}")
            self.allocated_ports = {}
    
    def get_port_summary(self) -> Dict:
        """Get complete port management summary"""
        return {
            "allocated_ports": self.allocated_ports,
            "reserved_ports": sorted(list(self.reserved_ports)),
            "default_ranges": self.default_ranges,
            "range_usage": self.get_port_range_usage(),
            "conflicts": self.check_port_conflicts()
        }
