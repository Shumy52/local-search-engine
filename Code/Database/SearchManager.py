from typing import List, Dict, Optional, Union, Callable
import logging
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SearchStrategy(ABC):
    """Abstract base class for different search strategies."""
    
    @abstractmethod
    def execute(self, db_connection, *args, **kwargs) -> List[Dict[str, str]]:
        """Execute the search strategy."""
        pass


class ExtensionSearchStrategy(SearchStrategy):
    def execute(self, db_connection, extension: str) -> List[Dict[str, str]]:
        logger.debug(f"Searching by extension: '{extension}'")
        query = "SELECT filename, path FROM files WHERE extension = %s"
        try:
            with db_connection.cursor() as cursor:
                cursor.execute(query, (extension,))
                results = cursor.fetchall()
                logger.debug(f"Extension search found {len(results)} results")
                return [{"filename": row[0], "path": row[1]} for row in results]
        except Exception as e:
            logger.error(f"Error searching by extension: {e}")
            return []


class ContentSearchStrategy(SearchStrategy):
    def execute(self, db_connection, search_term: str) -> List[Dict[str, str]]:
        logger.debug(f"Searching by content: '{search_term}'")
        try:
            search_query = ' & '.join(search_term.split())
            tsquery = f"to_tsquery('english', '{search_query}')"
            like_term = f'%{search_term}%'
            
            logger.debug(f"tsquery: {tsquery}")
            logger.debug(f"like_term: {like_term}")
            
            query = f"""
            SELECT DISTINCT f.filename, f.path, ts_rank(f.search_vector, {tsquery}) as rank
            FROM files f
            WHERE 
                f.search_vector @@ {tsquery} OR
                f.filename ILIKE %s OR
                f.path ILIKE %s
            ORDER BY rank DESC
            """
            with db_connection.cursor() as cursor:
                cursor.execute(query, (like_term, like_term))
                results = cursor.fetchall()
                logger.debug(f"Content search found {len(results)} results")
                return [{"filename": row[0], "path": row[1]} for row in results]
        except Exception as e:
            logger.error(f"Error searching by content: {e}")
            return []


class MultiWordSearchStrategy(SearchStrategy):
    def execute(self, db_connection, search_words: List[str]) -> List[Dict[str, str]]:
        logger.debug(f"Searching for multiple words: {search_words}")
        try:
            if not search_words:
                logger.debug("No search words provided, returning empty results")
                return []

            search_query = ' & '.join(search_words)
            tsquery = f"to_tsquery('english', '{search_query}')"
            logger.debug(f"Full-text search query: {tsquery}")
            
            # First try full-text search
            results = self._full_text_search(db_connection, tsquery)
            
            # Fallback to pattern matching if no results
            if not results:
                results = self._pattern_matching_search(db_connection, search_words)
                
            return results
        except Exception as e:
            logger.error(f"Error searching multiple words: {e}", exc_info=True)
            return []
    
    def _full_text_search(self, db_connection, tsquery: str) -> List[Dict[str, str]]:
        logger.debug("Performing full-text search")
        query = f"""
        SELECT f.filename, f.path, ts_rank(f.search_vector, {tsquery}) as rank
        FROM files f
        WHERE f.search_vector @@ {tsquery}
        ORDER BY rank DESC
        """
        with db_connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            logger.debug(f"Full-text search found {len(results)} results")
            return [{"filename": row[0], "path": row[1]} for row in results]
    
    def _pattern_matching_search(self, db_connection, search_words: List[str]) -> List[Dict[str, str]]:
        logger.debug("Falling back to pattern matching")
        fallback_query = """
        SELECT f.filename, f.path
        FROM files f
        WHERE 
        """
        conditions = []
        params = []
        for word in search_words:
            word_param = f'%{word}%'
            conditions.append("""
            (f.filename ILIKE %s OR 
             f.preview ILIKE %s OR 
             f.content ILIKE %s)
            """)
            params.extend([word_param, word_param, word_param])
        fallback_query += " AND ".join(conditions)
        
        with db_connection.cursor() as cursor:
            cursor.execute(fallback_query, params)
            results = cursor.fetchall()
            logger.debug(f"Fallback search found {len(results)} results")
            return [{"filename": row[0], "path": row[1]} for row in results]


class PathSearchStrategy(SearchStrategy):
    def execute(self, db_connection, path: str) -> List[Dict[str, str]]:
        logger.debug(f"Searching by path: '{path}'")
        try:
            # Normalize the search path
            search_path = path.replace('\\', '/').lower()
            
            # Different search strategies
            if search_path.startswith('/') or search_path.startswith('\\'):
                like_path = f"{search_path}%"  # Absolute path prefix search
            elif '/' in search_path or '\\' in search_path:
                like_path = f"%{search_path}%"  # Path component search
            else:
                like_path = f"%/{search_path}%"  # Directory or file name search
                
            query = """
            SELECT filename, path
            FROM files
            WHERE LOWER(REPLACE(path, '\\', '/')) LIKE %s
            ORDER BY path, filename
            """
            
            with db_connection.cursor() as cursor:
                cursor.execute(query, (like_path,))
                results = cursor.fetchall()
                logger.debug(f"Path search found {len(results)} results")
                return [{"filename": row[0], "path": row[1]} for row in results]
        except Exception as e:
            logger.error(f"Error searching by path: {e}")
            return []


class PathAndContentSearchStrategy(SearchStrategy):
    def execute(self, db_connection, path: str, content: Union[str, List[str]]) -> List[Dict[str, str]]:
        logger.debug(f"Searching by path: '{path}' and content: '{content}'")
        try:
            # First get path results using the path search strategy
            path_strategy = PathSearchStrategy()
            path_matches = path_strategy.execute(db_connection, path)
            
            if not path_matches:
                logger.debug("No path matches found, returning empty results")
                return []
                
            # Extract file paths to filter with content search
            path_ids = [result["path"] for result in path_matches]
            
            # Handle content search
            if isinstance(content, list):
                search_query = " & ".join(content)
            else:
                search_query = " & ".join(content.split())
                
            tsquery = f"to_tsquery('english', '{search_query}')"
            like_content = f"%{content}%" if not isinstance(content, list) else "%"
            
            query = f"""
            SELECT DISTINCT f.filename, f.path
            FROM files f
            WHERE f.path = ANY(%s) AND (
                f.search_vector @@ {tsquery} OR
                f.filename ILIKE %s OR
                f.content ILIKE %s
            )
            ORDER BY filename
            """
            
            with db_connection.cursor() as cursor:
                cursor.execute(query, (path_ids, like_content, like_content))
                results = cursor.fetchall()
                logger.debug(f"Path and content search found {len(results)} results")
                return [{"filename": row[0], "path": row[1]} for row in results]
        except Exception as e:
            logger.error(f"Error searching by path and content: {e}")
            return []


class SearchManager:
    def __init__(self, db_connection):
        """
        Handles search-related operations in the database.
        Args:
            db_connection: An instance of DBConnection.
        """
        self.db_connection = db_connection
        self.strategies = {
            'extension': ExtensionSearchStrategy(),
            'content': ContentSearchStrategy(),
            'multi_word': MultiWordSearchStrategy(),
            'path': PathSearchStrategy(),
            'path_and_content': PathAndContentSearchStrategy()
        }
    
    def search(self, strategy_name: str, *args, **kwargs) -> List[Dict[str, str]]:
        """
        Execute a search using the specified strategy.
        
        Args:
            strategy_name: Name of the search strategy to use
            *args, **kwargs: Parameters to pass to the strategy
            
        Returns:
            List of dictionaries with search results
        """
        if strategy_name not in self.strategies:
            logger.error(f"Unknown search strategy: {strategy_name}")
            return []
        
        strategy = self.strategies[strategy_name]
        return strategy.execute(self.db_connection, *args, **kwargs)
    
    # Convenience methods to maintain backward compatibility
    def search_by_extension(self, extension: str) -> List[Dict[str, str]]:
        return self.search('extension', extension)
        
    def search_by_content(self, search_term: str) -> List[Dict[str, str]]:
        return self.search('content', search_term)
    
    def search_multi_words(self, search_words: List[str]) -> List[Dict[str, str]]:
        return self.search('multi_word', search_words)
    
    def search_by_path(self, path: str) -> List[Dict[str, str]]:
        return self.search('path', path)
        
    def search_by_path_and_content(self, path: str, content: Union[str, List[str]]) -> List[Dict[str, str]]:
        return self.search('path_and_content', path, content)
    
    def register_strategy(self, name: str, strategy: SearchStrategy) -> None:
        """
        Register a new search strategy.
        
        Args:
            name: Name to identify the strategy
            strategy: The strategy implementation
        """
        self.strategies[name] = strategy