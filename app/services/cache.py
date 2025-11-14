"""Caching service for predictions."""
import hashlib
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PredictionCache:
    """
    In-memory cache for predictions.
    
    Uses a simple dict-based cache with LRU eviction policy.
    In production, consider using Redis or Memcached.
    """
    
    def __init__(self, max_size: int = 10000, ttl_seconds: int = 3600):
        """
        Initialize prediction cache.
        
        Args:
            max_size: Maximum number of items in cache
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_order: list[str] = []
    
    def _generate_key(self, features: Dict[str, Any]) -> str:
        """Generate cache key from features."""
        # Sort keys for consistent hashing
        sorted_features = json.dumps(features, sort_keys=True)
        return hashlib.md5(sorted_features.encode()).hexdigest()
    
    def get(self, features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get cached prediction.
        
        Args:
            features: Customer features
        
        Returns:
            Cached prediction or None if not found
        """
        key = self._generate_key(features)
        
        if key in self._cache:
            # Check if expired
            import time
            entry = self._cache[key]
            if time.time() - entry["timestamp"] > self.ttl_seconds:
                self._remove(key)
                return None
            
            # Update access order (LRU)
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            logger.debug("Cache hit for key: %s", key)
            return entry["prediction"]
        
        logger.debug("Cache miss for key: %s", key)
        return None
    
    def set(self, features: Dict[str, Any], prediction: Dict[str, Any]) -> None:
        """
        Store prediction in cache.
        
        Args:
            features: Customer features
            prediction: Prediction result
        """
        key = self._generate_key(features)
        
        # Evict oldest if at max size
        if len(self._cache) >= self.max_size and key not in self._cache:
            oldest_key = self._access_order[0]
            self._remove(oldest_key)
        
        import time
        self._cache[key] = {
            "prediction": prediction,
            "timestamp": time.time()
        }
        
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        
        logger.debug("Cached prediction for key: %s", key)
    
    def _remove(self, key: str) -> None:
        """Remove item from cache."""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._access_order.clear()
        logger.info("Cache cleared")
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "utilization": len(self._cache) / self.max_size if self.max_size > 0 else 0
        }


# Global cache instance
_cache: Optional[PredictionCache] = None


def get_cache() -> PredictionCache:
    """Get or create global cache instance."""
    global _cache
    if _cache is None:
        _cache = PredictionCache()
    return _cache


def clear_cache() -> None:
    """Clear global cache."""
    global _cache
    if _cache is not None:
        _cache.clear()

