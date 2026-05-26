"""
Redis Cache Manager - Production Grade
"""
import redis
import json
import os
from typing import Optional, Any
from datetime import timedelta

class CacheManager:
    """Centralized cache management using Redis"""
    
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            
            # Test connection
            self.redis_client.ping()
            print("✅ Redis connection successful")
            self.connected = True
        except redis.ConnectionError as e:
            print(f"⚠️ Redis connection failed: {e} - caching disabled")
            self.connected = False
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache"""
        if not self.connected:
            return False
        try:
            json_value = json.dumps(value)
            self.redis_client.setex(key, ttl, json_value)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.connected:
            return None
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.connected:
            return False
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def cache_user(self, user_id: str, user_data: dict, ttl: int = 86400):
        """Cache user for 24 hours"""
        self.set(f"user:{user_id}", user_data, ttl)
    
    def get_cached_user(self, user_id: str) -> Optional[dict]:
        """Get cached user"""
        return self.get(f"user:{user_id}")
    
    def cache_document(self, doc_id: str, doc_data: dict, ttl: int = 604800):
        """Cache document for 7 days"""
        self.set(f"doc:{doc_id}", doc_data, ttl)
    
    def get_cached_document(self, doc_id: str) -> Optional[dict]:
        """Get cached document"""
        return self.get(f"doc:{doc_id}")
    
    def increment_rate_limit(self, key: str, limit: int, window: int = 60) -> int:
        """Increment rate limit counter"""
        if not self.connected:
            return 0
        try:
            count = self.redis_client.incr(key)
            if count == 1:
                self.redis_client.expire(key, window)
            return count
        except:
            return 0
    
    def get_rate_limit(self, key: str) -> int:
        """Get current rate limit count"""
        if not self.connected:
            return 0
        try:
            count = self.redis_client.get(key)
            return int(count) if count else 0
        except:
            return 0
    
    def clear_cache(self, pattern: str = "*") -> int:
        """Clear cache entries matching pattern"""
        if not self.connected:
            return 0
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except:
            return 0

# Global cache instance
cache_manager = CacheManager()
