from pathlib import Path
import datetime
from collections import Counter
import re

class FileIndexer:
    
    def __init__(self, db):
        self.db = db # Get database instance from main

    def index_path(self, path):
        # I'm smelling recursivity... 
        
        # This is a Path object from the lib imported above  
        path = Path(path)

        for p in path.iterdir():

            if p.is_file():
                # TODO: Add to DB the file
                
                try:
                        file_data = {
                            'path': str(p.absolute()),
                            'filename': p.name,
                            'extension': p.suffix,
                            'size': p.stat().st_size,
                            'modified': datetime.datetime.fromtimestamp(p.stat().st_mtime),
                            'created': datetime.datetime.fromtimestamp(p.stat().st_ctime),
                        }
                            
                        # If the file is "readable", get content from it
                        # Courtesy of StackOverflow
                        if p.suffix.lower() in ['.txt', '.md', '.py', '.html', '.css', '.js']:
                            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                file_data['content'] = content
                                
                                # Extract first two paragraphs
                                paragraphs = re.split(r'\n\s*\n', content.strip(), maxsplit=2)
                                file_data['preview'] = '\n\n'.join(paragraphs[:2]) if len(paragraphs) > 1 else paragraphs[0]
                                
                                # Find 5 most frequent important words
                                # Remove common stopwords
                                stopwords = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'but', 
                                            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 
                                            'do', 'does', 'did', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 
                                            'she', 'it', 'we', 'they', 'with', 'by', 'as', 'not', 'what', 'from'}
                                words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
                                important_words = [word for word in words if word not in stopwords]
                                word_counts = Counter(important_words)
                                file_data['top_words'] = [word for word, _ in word_counts.most_common(5)]
                                
                        self.db.add_file(file_data)

                except Exception as e:
                    print(f"Error indexing {p}: {e}")

            elif p.is_dir():
                # Navigate further
                self.index_path(p) # You need self. in this case
                
            else:
                raise FileNotFoundError()
