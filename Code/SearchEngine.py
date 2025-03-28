import re
from datetime import datetime

class FileSearcher:

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
