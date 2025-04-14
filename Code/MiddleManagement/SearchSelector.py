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
            
        # First we try to parse whatever we can based on iteration 2 criteria
        parsed_query, remaining_text = self._parse_query(prompt)
        logger.debug(f"Parsed query: {parsed_query}, Remaining text: '{remaining_text}'")
        
        # Considering we found anything, try to make something out of it
        # If we find anything, we'll ignore anything unparsed 
        # TODO: If requested, integrate the unparsed part of the search into something... 
            # If we just shove it in the other methods, we'll get a lot of unwanted results.
        if parsed_query:
            logger.info(f"Using parsed query: {parsed_query}")
            return self._handle_parsed_items(parsed_query)
        
        # Iteration 1 of project methods of searching from now on
        else:
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
        Process parsed query items and return search results based on qualifiers (path, content etc.).
        
        Args:
            parsed_query: Dictionary with query qualifiers as keys and their values as lists
            
        Returns:
            List of search results
        """
        if not parsed_query:
            logger.info("Empty parsed query, returning empty results")
            return []
        
        supported_qualifiers = {'path', 'content', 'extension'}
        used_qualifiers = set(parsed_query.keys())
        
        if not used_qualifiers.issubset(supported_qualifiers):
            unsupported = used_qualifiers - supported_qualifiers
            logger.warning(f"Ignoring unsupported qualifiers: {unsupported}")
        
        results = None
        
        # Process each qualifier type and progressively filter results (it's still AND)
        if 'path' in parsed_query:
            for path in parsed_query['path']:
                logger.debug(f"Filtering by path: '{path}'")
                path_results = self.db.search_by_path(path)
                results = self._filter_results(results, path_results)
                if not results:
                    logger.info("No results match path criteria")
                    return []
        
        if 'content' in parsed_query:
            for content in parsed_query['content']:
                logger.debug(f"Filtering by content: '{content}'")
                content_results = self.db.search_by_content(content)
                results = self._filter_results(results, content_results)
                if not results:
                    logger.info("No results match content criteria")
                    return []
                
        if 'extension' in parsed_query:
            for extension in parsed_query['extension']:
                logger.debug(f"Filtering by extension: '{extension}'")
                extension_results = self.db.search_by_extension(extension)
                results = self._filter_results(results, extension_results)
                if not results:
                    logger.info("No results match extension criteria")
                    return []
                
        # TODO: Add more criteria
            
        logger.info(f"Search completed with {len(results) if results else 0} results")
        return results or []
        
    def _filter_results(self, current_results, new_results):
        """Helper method to filter results based on previous results"""
        if current_results is None:
            return new_results
            
        new_dict = {result['path']: result for result in new_results}
        filtered = [result for result in current_results if result['path'] in new_dict]
        logger.debug(f"Filtered from {len(current_results)} to {len(filtered)} results")
        return filtered

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
        
        # Can match path:c\Bingus\Whatever and content:"Biggus Dickus"
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
