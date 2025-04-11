from collections import defaultdict
import re
import logging
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SearchSelector:

    def __init__(self, db):
        self.db = db
        logger.info("SearchSelector initialized")
    
    def search_prompt(self, prompt: str) -> list:
        """
        Process a search prompt and return matching results.
        
        Args:
            prompt: Search query string
            
        Returns:
            List of search results
        """
        logger.info(f"Received search prompt: '{prompt}'")
        
        if not prompt or prompt.strip() == '':
            logger.info("Empty search prompt, returning empty results")
            return []
            
        # First we try to parse whatever we can
        parsed_query, remaining_text = self._parse_query(prompt)
        logger.debug(f"Parsed query: {parsed_query}, Remaining text: '{remaining_text}'")
        
        if parsed_query:
            logger.info(f"Using parsed query: {parsed_query}")
            return self._handle_parsed_items(parsed_query)
        
        if remaining_text.startswith('.'):
            extension = remaining_text[1:]  # Remove the dot
            logger.info(f"Searching by file extension: '{extension}'")
            return self.db.search_by_extension(extension)
                
        if len(remaining_text.split()) > 1:
            search_words = remaining_text.split()
            logger.info(f"Searching multiple words: {search_words}")
            return self.db.search_multi_words(search_words)
        else:
            logger.info(f"Searching by content: '{remaining_text}'")
            return self.db.search_by_content(remaining_text)


    def _handle_parsed_items(self, parsed_query):
        """
        Process parsed query items and return search results based on qualifiers.
        
        Args:
            parsed_query: Dictionary with query qualifiers as keys and their values as lists
            
        Returns:
            List of search results
        """
        if not parsed_query:
            logger.info("Empty parsed query, returning empty results")
            return []
        
        # Handle different combinations of qualifiers
        if 'path' in parsed_query and 'content' in parsed_query:
            # For path + content combinations, search by both
            # Take the first value from each qualifier for simplicity (for now)
            path = parsed_query['path'][0]
            content = parsed_query['content'][0]
            logger.info(f"Searching by path '{path}' and content '{content}'")
            return self.db.search_by_path_and_content(path, content)
        
        elif 'path' in parsed_query:
            # Path-only search
            # If multiple path values, each narrows down the results (AND operation)
            results = []
            first_search = True
            
            for path in parsed_query['path']:
                logger.debug(f"Processing path filter: '{path}'")
                if first_search:
                    results = self.db.search_by_path(path)
                    logger.debug(f"First path search returned {len(results)} results")
                    first_search = False
                else:
                    # Filter the current results further
                    path_results = self.db.search_by_path(path)
                    logger.debug(f"Additional path search returned {len(path_results)} results")
                    path_dict = {result['path']: result for result in path_results}
                    results = [result for result in results if result['path'] in path_dict]
                    logger.debug(f"After filtering, {len(results)} results remain")
                
                # If we've filtered to nothing, no need to continue
                if not results:
                    logger.info("Path filtering resulted in no matches")
                    return []
            
            logger.info(f"Path search completed with {len(results)} results")
            return results
        
        elif 'content' in parsed_query:
            # Content-only search
            # If multiple content values, each narrows down the results (AND operation)
            results = []
            first_search = True
            
            for content in parsed_query['content']:
                logger.debug(f"Processing content filter: '{content}'")
                if first_search:
                    results = self.db.search_by_content(content)
                    logger.debug(f"First content search returned {len(results)} results")
                    first_search = False
                else:
                    # Same as before, filter down
                    content_results = self.db.search_by_content(content)
                    logger.debug(f"Additional content search returned {len(content_results)} results")
                    content_dict = {result['path']: result for result in content_results}
                    results = [result for result in results if result['path'] in content_dict]
                    logger.debug(f"After filtering, {len(results)} results remain")
                    
                # Same as before
                if not results:
                    logger.info("Content filtering resulted in no matches")
                    return []
                    
            logger.info(f"Content search completed with {len(results)} results")
            return results
        
        else:
            # Potential to add later here.
            logger.info("No handlers for the provided query qualifiers")
            return []

    def _parse_query(self, query: str) -> tuple[Dict[str, str], str]:
        """
        Parse a structured query string into components (e.g., 'path:A/B content:C').
        
        Args:
            query: The query string to parse
            
        Returns:
            A tuple containing:
            - A dictionary with parsed qualifiers as keys and their values
            - The remaining unparsed text from the query
        """
        logger.debug(f"Parsing query: '{query}'")
        if not query or query.strip() == '':
            logger.debug("Empty query, returning empty result")
            return {}, ''
            
        parsed_query = defaultdict(list)
        
        # Can match path:c\Bingus\Whatever and path:"Biggus Dickus"
        pattern = r'(\w+):(?:"([^"]+)"|([^\s]+))'

        #This returns 3 matches: match[0,1,2]. 
        # 0 - what is asked
        # 1 - the unquoted value (if any)
        # 2 - the quoted value (if any)
        matches = re.findall(pattern, query)
        logger.debug(f"Regex matches: {matches}")
        
        # Split what we found
        for match in matches:
            qualifier = match[0].lower() # path: / size: / content: / whatever
            value = match[1] if match[1] else match[2]
            parsed_query[qualifier].append(value)
            logger.debug(f"Added qualifier: {qualifier}={value}")
        
        # Handle remaining unmatched text. Clean it up and prepare for "shipping"
        remaining_text = query
        for match in matches:
            full_match = f"{match[0]}:{match[1] if match[1] else match[2]}"
            remaining_text = remaining_text.replace(full_match, "")
        
        remaining_text = remaining_text.strip()
        logger.debug(f"Parsed query: {parsed_query}, remaining text: '{remaining_text}'")
        
        # We're now returning the unparsed part too
        return parsed_query, remaining_text
