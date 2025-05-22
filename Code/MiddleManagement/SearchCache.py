import time
from typing import Dict, List, Tuple, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SearchCache:
    """
    A cache for storing search results to avoid repeated database queries.
    """
    
    def __init__(self, expiry_time=600):  # Default expiry time: 10 minutes
        """
        Initialize the search cache.
        
        Args:
            expiry_time: Time in seconds before a cache entry expires
        """
        self.cache: Dict[str, Tuple[List[Dict[str, Any]], float]] = {}
        self.expiry_time = expiry_time
        logger.info("Search cache initialized with expiry time: %s seconds", expiry_time)
    
    def get(self, key: str) -> List[Dict[str, Any]]:
        """
        Retrieve results from cache if they exist and are not expired.
        
        Args:
            key: The cache key (typically the search query)
            
        Returns:
            The cached results or None if not in cache or expired
        """
        if key in self.cache:
            results, timestamp = self.cache[key]
            if time.time() - timestamp < self.expiry_time:
                logger.debug("Cache hit for query: '%s'", key)
                return results
            else:
                logger.debug("Cache expired for query: '%s'", key)
                del self.cache[key]
        
        logger.debug("Cache miss for query: '%s'", key)
        return None
    
    def set(self, key: str, results: List[Dict[str, Any]]) -> None:
        """
        Store results in the cache.
        
        Args:
            key: The cache key (typically the search query)
            results: The search results to cache
        """
        self.cache[key] = (results, time.time())
        logger.debug("Cached results for query: '%s' (%d results)", key, len(results))
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def remove(self, key: str) -> None:
        """
        Remove a specific key from the cache.
        
        Args:
            key: The cache key to remove
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug("Removed cache entry for: '%s'", key)
    
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        current_time = time.time()
        active_entries = sum(1 for _, timestamp in self.cache.values() 
                            if current_time - timestamp < self.expiry_time)
        
        return {
            "total_entries": len(self.cache),
            "active_entries": active_entries,
            "expired_entries": len(self.cache) - active_entries,
            "memory_usage_estimate": self._estimate_memory_usage()
        }
    
    def _estimate_memory_usage(self) -> str:
        """Rough estimate of memory usage by the cache."""
        # This is a very rough estimate
        import sys
        try:
            size_bytes = sys.getsizeof(self.cache)
            for key, (results, _) in self.cache.items():
                size_bytes += sys.getsizeof(key)
                size_bytes += sys.getsizeof(results)
                for result in results:
                    size_bytes += sys.getsizeof(result)
            
            if size_bytes < 1024:
                return f"{size_bytes} bytes"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.2f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.2f} MB"
        except:
            return "Unknown"