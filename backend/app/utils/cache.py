"""
Caching utilities for performance optimization

Provides in-memory caching for:
- Pattern library queries
- LLM responses for common requests
- Database query results

Implements Requirement 17.4: Request caching with appropriate TTLs
"""
import hashlib
import json
import time
from typing import Any, Optional, Dict, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class CacheEntry:
    """Represents a single cache entry with TTL"""
    
    def __init__(self, value: Any, ttl: int):
        """
        Initialize cache entry
        
        Args:
            value: Cached value
            ttl: Time-to-live in seconds
        """
        self.value = value
        self.expiry = time.time() + ttl
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() > self.expiry


class Cache:
    """
    Simple in-memory cache with TTL support
    
    Implements Requirement 17.4: Cache pattern library queries and LLM responses
    """
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired():
                self._hits += 1
                logger.debug(f"Cache hit: {key}")
                return entry.value
            else:
                # Remove expired entry
                del self._cache[key]
                logger.debug(f"Cache expired: {key}")
        
        self._misses += 1
        logger.debug(f"Cache miss: {key}")
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        ttl = ttl if ttl is not None else self.default_ttl
        self._cache[key] = CacheEntry(value, ttl)
        logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    def delete(self, key: str):
        """
        Delete value from cache
        
        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted: {key}")
    
    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("Cache cleared")
    
    def cleanup_expired(self):
        """Remove all expired entries from cache"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2f}%"
        }


# Global cache instances
pattern_cache = Cache(default_ttl=3600)  # 1 hour for pattern library
llm_cache = Cache(default_ttl=1800)  # 30 minutes for LLM responses
query_cache = Cache(default_ttl=300)  # 5 minutes for database queries


def generate_cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from function arguments
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    # Create a deterministic string representation
    key_data = {
        "args": [str(arg) for arg in args],
        "kwargs": {k: str(v) for k, v in sorted(kwargs.items())}
    }
    
    key_string = json.dumps(key_data, sort_keys=True)
    
    # Hash for shorter keys
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(cache_instance: Cache, ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator for caching function results
    
    Args:
        cache_instance: Cache instance to use
        ttl: Time-to-live in seconds (uses cache default if not specified)
        key_prefix: Prefix for cache keys
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = cache_instance.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            cache_instance.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = cache_instance.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache_instance.set(cache_key, result, ttl)
            
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def invalidate_project_cache(project_id: str):
    """
    Invalidate all cache entries for a project
    
    Args:
        project_id: Project ID
    """
    # This is a simple implementation - in production, you might want
    # to track cache keys by project for more efficient invalidation
    query_cache.clear()
    logger.info(f"Invalidated cache for project {project_id}")


def get_cache_stats() -> Dict[str, Any]:
    """
    Get statistics for all cache instances
    
    Returns:
        Dictionary with cache statistics
    """
    return {
        "pattern_cache": pattern_cache.get_stats(),
        "llm_cache": llm_cache.get_stats(),
        "query_cache": query_cache.get_stats()
    }
