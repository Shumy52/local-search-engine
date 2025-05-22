import logging
from typing import Dict, List, Any
from .SearchSelector import SearchSelector
from .SearchCache import SearchCache

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SearchSelectorProxy:
    """
    A proxy for SearchSelector that adds caching functionality.
    Implements the Proxy design pattern to transparently add caching.
    """
    
    def __init__(self, real_selector: SearchSelector, cache_expiry=600):
        """
        Initialize the proxy with the real search selector and a cache.
        
        Args:
            real_selector: The actual SearchSelector instance to proxy
            cache_expiry: Time in seconds before cache entries expire(default 600)
        """
        self.real_selector = real_selector
        self.cache = SearchCache(expiry_time=cache_expiry)
        logger.info("SearchSelectorProxy initialized with cache expiry: %s seconds", cache_expiry)
    
    def search_prompt(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Search with caching. Checks cache first before forwarding to real selector.
        
        Args:
            prompt: The search query string
            
        Returns:
            List of search results
        """
        if not prompt or prompt.strip() == '':
            logger.info("Empty search prompt, returning empty results")
            return []
        
        # Normalize the prompt to ensure consistent cache keys
        normalized_prompt = prompt.strip().lower()
        
        # Try to get results from cache
        cached_results = self.cache.get(normalized_prompt)
        if cached_results is not None:
            logger.info("Returning cached results for query: '%s'", prompt)
            return cached_results
        
        # If not in cache, forward to real selector
        logger.info("Cache miss for query: '%s', forwarding to real selector", prompt)
        results = self.real_selector.search_prompt(prompt)
        
        # Cache the results if there are any
        if results:
            self.cache.set(normalized_prompt, results)
        
        return results
    
    def clear_cache(self) -> None:
        """Clear the entire cache."""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        return self.cache.stats()
    
    def invalidate_cache(self) -> None:
        """
        Invalidate the cache. Used when files are indexed or modified.
        """
        logger.info("Invalidating search cache due to file system changes")
        self.clear_cache()