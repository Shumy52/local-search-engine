import re
from datetime import datetime

class FileSearcher:

    def __init__(self, db):
        self.db = db
    
    def search_prompt(self, prompt) -> list:

        # Check if searching by extension
        if prompt.startswith('.'):
            print("I've searched by extension")
            results = self.db.search_by_extension(prompt)
        elif len(prompt.split(" ")) > 1 :
            print("I've searched by multiple words")
            results = self.db.search_multi_words(prompt)
        else:
            print("I've searched generally")
            results = self.db.search_by_content(prompt)
        # TODO: Search by date
        return results
