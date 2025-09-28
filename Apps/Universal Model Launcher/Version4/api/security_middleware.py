"""
🔒 Security Middleware - Authentication & Rate Limiting

Features:
- API key management
- Rate limiting
- Request validation
- Audit logging
- CORS handling
"""

import time
import hashlib
import logging
from collections import defaultdict, deque
from typing import Dict, Set, Optional, Callable, List
from dataclasses import dataclass
from pathlib import Path
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class RateLimitRule:
    """Rate limiting rule configuration"""
    requests_per_minute: int
    requests_per_hour: int
    burst_limit: int

@dataclass
class SecurityConfig:
    """Security configuration"""
    api_keys: Set[str]
    rate_limits: Dict[str, RateLimitRule]
    public_endpoints: Set[str]
    cors_origins: Set[str]
    audit_log_enabled: bool
    
class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.request_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: {"minute": 0, "hour": 0})
        self.last_reset: Dict[str, Dict[str, float]] = defaultdict(lambda: {"minute": time.time(), "hour": time.time()})
    
    def is_allowed(self, client_id: str, rule: RateLimitRule) -> bool:
        """Check if request is allowed under rate limits"""
        current_time = time.time()
        
        # Reset counters if needed
        if current_time - self.last_reset[client_id]["minute"] >= 60:
            self.request_counts[client_id]["minute"] = 0
            self.last_reset[client_id]["minute"] = current_time
            
        if current_time - self.last_reset[client_id]["hour"] >= 3600:
            self.request_counts[client_id]["hour"] = 0
            self.last_reset[client_id]["hour"] = current_time
        
        # Check limits
        if self.request_counts[client_id]["minute"] >= rule.requests_per_minute:
            return False
            
        if self.request_counts[client_id]["hour"] >= rule.requests_per_hour:
            return False
        
        # Check burst limit
        recent_requests = [req_time for req_time in self.requests[client_id] 
                          if current_time - req_time < 10]  # 10 second window
        if len(recent_requests) >= rule.burst_limit:
            return False
        
        # Record request
        self.request_counts[client_id]["minute"] += 1
        self.request_counts[client_id]["hour"] += 1
        self.requests[client_id].append(current_time)
        
        # Cleanup old requests
        while self.requests[client_id] and current_time - self.requests[client_id][0] > 3600:
            self.requests[client_id].popleft()
        
        return True

class SecurityMiddleware:
    """
    Security middleware for API authentication and protection.
    """
    
    def __init__(self, config_path: str = "config/security.json"):
        self.config_path = Path(config_path)
        self.rate_limiter = RateLimiter()
        self.audit_log: deque = deque(maxlen=1000)
        
        # Default configuration
        self.config = SecurityConfig(
            api_keys=set(),
            rate_limits={
                "default": RateLimitRule(60, 1000, 10),
                "premium": RateLimitRule(120, 5000, 20)
            },
            public_endpoints={
                "/health", "/models", "/v1/models", "/docs", "/redoc", "/openapi.json"
            },
            cors_origins={"*"},
            audit_log_enabled=True
        )
        
        self._load_config()
        logger.info("🔒 Security Middleware initialized")
    
    def _load_config(self):
        """Load security configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    
                self.config.api_keys = set(data.get("api_keys", []))
                self.config.cors_origins = set(data.get("cors_origins", ["*"]))
                self.config.audit_log_enabled = data.get("audit_log_enabled", True)
                
                # Load rate limits
                rate_limits_data = data.get("rate_limits", {})
                for tier, limits in rate_limits_data.items():
                    self.config.rate_limits[tier] = RateLimitRule(
                        requests_per_minute=limits.get("requests_per_minute", 60),
                        requests_per_hour=limits.get("requests_per_hour", 1000),
                        burst_limit=limits.get("burst_limit", 10)
                    )
                
                logger.info(f"Security config loaded: {len(self.config.api_keys)} API keys")
                
            except Exception as e:
                logger.warning(f"Failed to load security config: {e}")
    
    def _save_config(self):
        """Save security configuration to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "api_keys": list(self.config.api_keys),
                "cors_origins": list(self.config.cors_origins),
                "audit_log_enabled": self.config.audit_log_enabled,
                "rate_limits": {
                    tier: {
                        "requests_per_minute": rule.requests_per_minute,
                        "requests_per_hour": rule.requests_per_hour,
                        "burst_limit": rule.burst_limit
                    }
                    for tier, rule in self.config.rate_limits.items()
                }
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save security config: {e}")
    
    def validate_api_key(self, authorization_header: Optional[str]) -> bool:
        """Validate API key from Authorization header"""
        if not self.config.api_keys:
            return True  # No API keys configured, allow all
        
        if not authorization_header:
            return False
        
        if not authorization_header.startswith("Bearer "):
            return False
        
        api_key = authorization_header[7:]  # Remove "Bearer " prefix
        return api_key in self.config.api_keys
    
    def check_rate_limit(self, client_ip: str, api_key: Optional[str] = None) -> bool:
        """Check if request is within rate limits"""
        # Determine rate limit tier
        tier = "premium" if api_key and api_key in self.config.api_keys else "default"
        rule = self.config.rate_limits.get(tier, self.config.rate_limits["default"])
        
        # Use API key hash for identification if available, otherwise IP
        client_id = hashlib.md5((api_key or client_ip).encode()).hexdigest()
        
        return self.rate_limiter.is_allowed(client_id, rule)
    
    def is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (no authentication required)"""
        return path in self.config.public_endpoints
    
    def log_request(self, client_ip: str, method: str, path: str, 
                   api_key: Optional[str] = None, status_code: int = 200):
        """Log API request for audit purposes"""
        if not self.config.audit_log_enabled:
            return
        
        log_entry = {
            "timestamp": time.time(),
            "client_ip": client_ip,
            "method": method,
            "path": path,
            "api_key_hash": hashlib.md5(api_key.encode()).hexdigest() if api_key else None,
            "status_code": status_code
        }
        
        self.audit_log.append(log_entry)
    
    def get_cors_headers(self, origin: str) -> Dict[str, str]:
        """Get CORS headers for response"""
        headers = {}
        
        if "*" in self.config.cors_origins or origin in self.config.cors_origins:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            headers["Access-Control-Allow-Credentials"] = "true"
        
        return headers
    
    def add_api_key(self, api_key: str) -> bool:
        """Add new API key"""
        if not api_key or len(api_key) < 20:
            return False
        
        self.config.api_keys.add(api_key)
        self._save_config()
        logger.info(f"API key added: ****{api_key[-4:]}")
        return True
    
    def remove_api_key(self, api_key: str) -> bool:
        """Remove API key"""
        if api_key in self.config.api_keys:
            self.config.api_keys.remove(api_key)
            self._save_config()
            logger.info(f"API key removed: ****{api_key[-4:]}")
            return True
        return False
    
    def get_audit_logs(self, limit: int = 100) -> List[Dict]:
        """Get recent audit logs"""
        return list(self.audit_log)[-limit:]
    
    def get_rate_limit_status(self, client_id: str) -> Dict:
        """Get current rate limit status for client"""
        counts = self.rate_limiter.request_counts.get(client_id, {"minute": 0, "hour": 0})
        return {
            "requests_this_minute": counts["minute"],
            "requests_this_hour": counts["hour"],
            "limits": {
                "minute": self.config.rate_limits["default"].requests_per_minute,
                "hour": self.config.rate_limits["default"].requests_per_hour
            }
        }

# FastAPI middleware integration
def create_fastapi_middleware(security: SecurityMiddleware):
    """Create FastAPI middleware function"""
    
    async def security_middleware(request, call_next):
        """FastAPI middleware function"""
        start_time = time.time()
        client_ip = request.client.host
        method = request.method
        path = request.url.path
        
        # Skip security for public endpoints
        if security.is_public_endpoint(path):
            response = await call_next(request)
            security.log_request(client_ip, method, path, status_code=response.status_code)
            return response
        
        # Check rate limits
        api_key = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            api_key = auth_header[7:]
        
        if not security.check_rate_limit(client_ip, api_key):
            from fastapi import HTTPException
            security.log_request(client_ip, method, path, api_key, 429)
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Validate API key if required
        if not security.validate_api_key(auth_header):
            from fastapi import HTTPException
            security.log_request(client_ip, method, path, api_key, 401)
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers
        origin = request.headers.get("Origin", "")
        cors_headers = security.get_cors_headers(origin)
        for key, value in cors_headers.items():
            response.headers[key] = value
        
        # Log request
        security.log_request(client_ip, method, path, api_key, response.status_code)
        
        return response
    
    return security_middleware

if __name__ == "__main__":
    # Example usage
    security = SecurityMiddleware()
    
    # Add some test API keys
    security.add_api_key("sk-test-key-1234567890abcdef1234567890abcdef")
    security.add_api_key("sk-prod-key-abcdef1234567890abcdef1234567890")
    
    # Test authentication
    print("Testing API key validation:")
    print(f"Valid key: {security.validate_api_key('Bearer sk-test-key-1234567890abcdef1234567890abcdef')}")
    print(f"Invalid key: {security.validate_api_key('Bearer invalid-key')}")
    print(f"No key: {security.validate_api_key(None)}")
    
    # Test rate limiting
    print("\nTesting rate limits:")
    for i in range(5):
        allowed = security.check_rate_limit("127.0.0.1")
        print(f"Request {i+1}: {'✅ Allowed' if allowed else '❌ Rate limited'}")
    
    print(f"\nAudit logs: {len(security.get_audit_logs())} entries")
