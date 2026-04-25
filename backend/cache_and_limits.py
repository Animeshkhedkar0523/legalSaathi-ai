"""
Rate Limiting, Caching, and Utilities for LegalSaathi
"""
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib
import json

# ─── Simple In-Memory Cache ───────────────────────────────────────────────────
class CacheManager:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self):
        self.cache: Dict[str, tuple[Any, float]] = {}
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            value, expiry = self.cache[key]
            if datetime.now().timestamp() < expiry:
                self.hits += 1
                return value
            else:
                del self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in cache with TTL (seconds)"""
        expiry = datetime.now().timestamp() + ttl
        self.cache[key] = (value, expiry)
    
    def clear(self) -> None:
        """Clear entire cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def stats(self) -> dict:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "items": len(self.cache),
            "total_requests": total
        }
    
    def remove(self, key: str) -> bool:
        """Remove specific key from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False


# ─── Rate Limiter ─────────────────────────────────────────────────────────────
class RateLimiter:
    """Rate limiter by IP address or user ID"""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> tuple[bool, Dict[str, Any]]:
        """Check if request is allowed"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > hour_ago
        ]
        
        # Count requests in time windows
        minute_requests = sum(1 for t in self.requests[identifier] if t > minute_ago)
        hour_requests = len(self.requests[identifier])
        
        # Check limits
        if minute_requests >= self.requests_per_minute:
            return False, {
                "reason": "Rate limit exceeded (per minute)",
                "limit": self.requests_per_minute,
                "current": minute_requests
            }
        
        if hour_requests >= self.requests_per_hour:
            return False, {
                "reason": "Rate limit exceeded (per hour)",
                "limit": self.requests_per_hour,
                "current": hour_requests
            }
        
        # Record request
        self.requests[identifier].append(now)
        
        return True, {
            "minute_requests": minute_requests,
            "hour_requests": hour_requests,
            "minute_limit": self.requests_per_minute,
            "hour_limit": self.requests_per_hour
        }
    
    def reset(self, identifier: str) -> None:
        """Reset rate limit for identifier"""
        if identifier in self.requests:
            del self.requests[identifier]
    
    def get_stats(self, identifier: str) -> dict:
        """Get rate limit statistics for an identifier"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        requests_list = self.requests.get(identifier, [])
        
        # Clean old requests
        requests_list = [req_time for req_time in requests_list if req_time > hour_ago]
        self.requests[identifier] = requests_list
        
        minute_requests = sum(1 for t in requests_list if t > minute_ago)
        hour_requests = len(requests_list)
        
        return {
            "requests_per_minute": minute_requests,
            "requests_per_hour": hour_requests,
            "minute_limit": self.requests_per_minute,
            "hour_limit": self.requests_per_hour
        }


# ─── Caching Decorators ───────────────────────────────────────────────────────
cache_manager = CacheManager()


def cached(ttl: int = 3600):
    """Decorator to cache function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name, args, and kwargs
            key_data = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Check cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


# ─── Global Instances ─────────────────────────────────────────────────────────
rate_limiter = RateLimiter(
    requests_per_minute=100,
    requests_per_hour=2000
)
