from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SearchManager:
    def __init__(self, db_connection):
        """
        Handles search-related operations in the database.
        Args:
            db_connection: An instance of DBConnection.
        """
        self.db_connection = db_connection

    def search_by_extension(self, extension: str) -> List[   Dict[str, str]]:
        """
        Search files by extension.
        Args:
            extension: String extension to search for (without dot).
        Returns:
            List of dictionaries with filename and path of matching files.
        """
        logger.debug(f"Searching by extension: '{extension}'")
        query = "SELECT filename, path FROM files WHERE extension = %s"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (extension,))
                results = cursor.fetchall()
                logger.debug(f"Extension search found {len(results)} results")
                return [{"filename": row[0], "path": row[1]} for row in results]
        except Exception as e:
            logger.error(f"Error searching by extension: {e}")
            return []

    def search_by_content(self, search_term: str) -> List[Dict[str, str]]:
        """
        Search files by filename, path, preview content using full-text search.
        Args:
            search_term: Term to search for.
        Returns:
            List of dictionaries with filename and path of matching files.
        """
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
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (like_term, like_term))
                results = cursor.fetchall()
                logger.debug(f"Content search found {len(results)} results")
                return [{"filename": row[0], "path": row[1]} for row in results]
        except Exception as e:
            logger.error(f"Error searching by content: {e}")
            return []

    def search_multi_words(self, search_words: List[str]) -> List[Dict[str, str]]:
        """
        Search files matching multiple words using full-text search.
        Args:
            search_words: List of words to search for.
        Returns:
            List of dictionaries with filename and path of matching files.
        """
        logger.debug(f"Searching for multiple words: {search_words}")
        try:
            if not search_words:
                logger.debug("No search words provided, returning empty results")
                return []

            search_query = ' & '.join(search_words)
            tsquery = f"to_tsquery('english', '{search_query}')"
            logger.debug(f"Full-text search query: {tsquery}")
            
            query = f"""
            SELECT f.filename, f.path, ts_rank(f.search_vector, {tsquery}) as rank
            FROM files f
            WHERE f.search_vector @@ {tsquery}
            ORDER BY rank DESC
            """
            with self.db_connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                logger.debug(f"Full-text search found {len(results)} results")

                # Fallback to pattern matching if no results
                if not results:
                    logger.debug("No full-text results, falling back to pattern matching")
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
                    logger.debug(f"Fallback query conditions: {' AND '.join(conditions)}")
                    logger.debug(f"Fallback query params: {params}")
                    
                    cursor.execute(fallback_query, params)
                    results = cursor.fetchall()
                    logger.debug(f"Fallback search found {len(results)} results")

                return [{"filename": row[0], "path": row[1]} for row in results]
        except Exception as e:
            logger.error(f"Error searching multiple words: {e}", exc_info=True)
            return []
        
    # TODO: Need to find a better solution. I can't keep slapping on methods with SQL for every combination I search for
    def search_by_path(self, path: str) -> List[Dict[str, str]]:
        """
        Search files by path with improved path matching.
        
        Args:
            path: Path pattern to search for
        
        Returns:
            List of dictionaries with filename and path of matching files
        """
        logger.debug(f"Searching by path: '{path}'")
        try:
            # Normalize the search path
            search_path = path.replace('\\', '/').lower()
            
            # Different search strategies
            if search_path.startswith('/') or search_path.startswith('\\'):
                # Absolute path prefix search
                like_path = f"{search_path}%"
            elif '/' in search_path or '\\' in search_path:
                # Path component search
                like_path = f"%{search_path}%"
            else:
                # Directory or file name search
                like_path = f"%/{search_path}%"
                
            query = """
            SELECT filename, path
            FROM files
            WHERE LOWER(REPLACE(path, '\\', '/')) LIKE %s
            ORDER BY path, filename
            """
            
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (like_path,))
                results = cursor.fetchall()
                logger.debug(f"Path search found {len(results)} results")
                return [{"filename": row[0], "path": row[1]} for row in results]
        except Exception as e:
            logger.error(f"Error searching by path: {e}")
            return []

    def search_by_path_and_content(self, path: str, content: str) -> List[Dict[str, str]]:
        """
        Search files by both path and content.
        
        Args:
            path: Path pattern to search for
            content: Content to search for
        
        Returns:
            List of dictionaries with filename and path of matching files
        """
        logger.debug(f"Searching by path: '{path}' and content: '{content}'")
        try:
            # Get path matches first using the existing method
            path_matches = self.search_by_path(path)
            
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
            
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (path_ids, like_content, like_content))
                results = cursor.fetchall()
                logger.debug(f"Path and content search found {len(results)} results")
                return [{"filename": row[0], "path": row[1]} for row in results]
        except Exception as e:
            logger.error(f"Error searching by path and content: {e}")
            return []