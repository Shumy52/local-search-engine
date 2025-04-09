import re
from datetime import datetime

class SearchSelector:

    def __init__(self, db):
        self.db = db
    
    def search_prompt(self, prompt) -> list:
        # Check if searching by extension
        if prompt.startswith('.'):
            extension = prompt[1:] # Remove the dot, since we changed that in DBManager
            results = self.db.search_by_extension(extension)
        # Multi-word query
        elif len(prompt.split()) > 1:
            search_words = prompt.split()
            results = self.db.search_multi_words(search_words)
        # Search by preview, content and path
        else:
            results = self.db.search_by_content(prompt)
        
        return results

    def search_advanced(self, query_string):
        """
        Parse and execute an advanced search query with qualifiers
        
        Supported qualifiers:
        - path: Search in file paths
        - content: Search in file contents
        - name: Search in filenames
        - ext: Search by extension
        
        Examples:
        - path:documents content:python
        - name:report ext:pdf
        
        Args:
            query_string: Advanced search query with qualifiers
            
        Returns:
            List of dictionaries with filename and path of matching files
        """
        # Extract qualifiers and their values using regex
        path_pattern = r'path:([^\s]+)'
        content_pattern = r'content:([^\s]+)'
        name_pattern = r'name:([^\s]+)'
        ext_pattern = r'ext:([^\s]+)'
        
        path_terms = re.findall(path_pattern, query_string)
        content_terms = re.findall(content_pattern, query_string)
        name_terms = re.findall(name_pattern, query_string)
        ext_terms = re.findall(ext_pattern, query_string)
        
        # If there's only extension qualifier, use the existing search_by_extension method
        if ext_terms and not (path_terms or content_terms or name_terms):
            results = []
            for ext in ext_terms:
                ext_results = self.db.search_by_extension(ext)
                results.extend(ext_results)
            return results
            
        # If only content/names are specified, we can use search_multi_words
        if (content_terms or name_terms) and not (path_terms or ext_terms):
            search_words = content_terms + name_terms
            return self.db.search_multi_words(search_words)
        
        # For more complex queries with mixed criteria, use search_by_content
        # for each term and then filter results
        all_results = []
        all_terms = path_terms + content_terms + name_terms
        
        # Start with extension search as it's most restrictive
        if ext_terms:
            for ext in ext_terms:
                ext_results = self.db.search_by_extension(ext)
                all_results.extend(ext_results)
            
            # If we only have extension terms, return results
            if not all_terms:
                return all_results
        
        # Otherwise search for each term and filter results
        term_results = []
        for term in all_terms:
            term_results.extend(self.db.search_by_content(term))
        
        # If we didn't search for extensions, use content search results
        if not ext_terms:
            all_results = term_results
        
        # Filter results by criteria
        filtered_results = []
        for result in all_results:
            matches_all = True
            
            # Filter by path
            if path_terms:
                if not any(path_term.lower() in result["path"].lower() for path_term in path_terms):
                    matches_all = False
                    
            # Filter by filename (can use existing results since filename is included)
            if name_terms and matches_all:
                if not any(name_term.lower() in result["filename"].lower() for name_term in name_terms):
                    matches_all = False
            
            # We don't need to filter by content or extension since those were used in the searches
            
            if matches_all:
                filtered_results.append(result)
                
        return filtered_results