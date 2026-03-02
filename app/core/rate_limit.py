from datetime import datetime, timezone
from typing import Dict
import time

# Simple in-memory rate limiter
class RateLimiter:
    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        from app.core.config import settings
        
        if not settings.RATE_LIMIT_ENABLED:
            self.max_requests = 999999  # Effectively disabled
        else:
            self.max_requests = max_requests
        
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, key: str) -> bool:
        from app.core.config import settings
        
        if not settings.RATE_LIMIT_ENABLED:
            return True
            
        now = time.time()
        
        # Clean old requests
        if key in self.requests:
            self.requests[key] = [t for t in self.requests[key] if now - t < self.window_seconds]
        
        # Check limit
        if key not in self.requests or len(self.requests[key]) < self.max_requests:
            if key not in self.requests:
                self.requests[key] = []
            self.requests[key].append(now)
            return True
        
        return False


# Rate limiters for different endpoints
login_limiter = RateLimiter(max_requests=5, window_seconds=60)  # 5 login attempts per minute
register_limiter = RateLimiter(max_requests=3, window_seconds=60)  # 3 registrations per minute
