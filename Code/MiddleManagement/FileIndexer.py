from pathlib import Path
import datetime
import re
import logging

CONTENT_LIMIT = 10000

class FileIndexer:
    
    def __init__(self, db):
        self.db = db 
        self.logger = logging.getLogger(__name__)

    def index_path(self, path):
        """Indexes recursively a folder and all the files and subfolders in it"""
        path = Path(path)
        self.logger.info(f"Indexing path: {path}")

        try:
            for p in path.iterdir():
                if p.is_file():
                    try:
                        file_data = {
                            'path': str(p.absolute()),
                            'filename': p.name,
                            'extension': p.suffix.lstrip('.').lower(),  # Store without dot for better search
                            'size': p.stat().st_size,
                            'modified': datetime.datetime.fromtimestamp(p.stat().st_mtime),
                            'created': datetime.datetime.fromtimestamp(p.stat().st_ctime),
                        }
                            
                        # If the file is "readable", get content from it
                        if p.suffix.lower() in ['.txt', '.md', '.py', '.html', '.css', '.js', '.json', '.xml', '.csv']:
                            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if len(content) > CONTENT_LIMIT:  # ~10KB limit
                                    content = content[:CONTENT_LIMIT] + "... (truncated)"
                                file_data['content'] = content
                                
                                # Extract first two paragraphs for preview
                                paragraphs = re.split(r'\n\s*\n', content.strip(), maxsplit=2)
                                file_data['preview'] = '\n\n'.join(paragraphs[:2]) if len(paragraphs) > 1 else paragraphs[0]

                        # The add_file method will trigger the search_vector update
                        if not self.db.add_file(file_data):
                            self.logger.error(f"Failed to add file to database: {p}")

                    except Exception as e:
                        self.logger.error(f"Error indexing file {p}: {e}")

                elif p.is_dir():
                    self.index_path(p)  # Recurse into subdirectories
                
        except PermissionError:
            self.logger.warning(f"Permission denied: {path}")
        except Exception as e:
            self.logger.error(f"Error processing directory {path}: {e}")