import psycopg2

class DBManager:
    def __init__(self):
        # Maybe separate these between a local connection and remote
        # TODO: CONNECTION SHOULD BE CHANGEABLE
        self.conn = psycopg2.connect(database="search-engine-db",
                                     user="postgres",
                                     host="localhost",
                                     password="postgres",
                                     port=5432)
        self.cursor = self.conn.cursor()
        self.init_database()

    def init_database(self):
        """
        Initialize the database schema if tables don't exist.
        Creates the necessary tables and indexes for the search engine.
        """
        try:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'files'
                );
            """)
            tables_exist = self.cursor.fetchone()[0]
            
            if not tables_exist:
                self.cursor.execute("""
                    CREATE TABLE files (
                        id SERIAL PRIMARY KEY,
                        path TEXT UNIQUE NOT NULL,
                        filename TEXT NOT NULL,
                        extension TEXT,
                        size INTEGER,
                        modified TIMESTAMP,
                        created TIMESTAMP,
                        preview TEXT,
                        content TEXT
                    );
                    
                    CREATE TABLE file_keywords (
                        id SERIAL PRIMARY KEY,
                        file_id INTEGER,
                        word TEXT NOT NULL,
                        FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
                    );
                    
                    CREATE INDEX idx_file_path ON files(path);
                    CREATE INDEX idx_file_extension ON files(extension);
                    CREATE INDEX idx_file_keywords ON file_keywords(word);
                """)
                
                self.conn.commit()
                print("Database schema initialized successfully.")
            else:
                print("Database schema already exists.")
                
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Error initializing database schema: {e}")
            return False
    
    def add_file(self, file_data) -> bool: 
        """Add a file to the database along with its keywords"""
        try:
            self.cursor.execute("SELECT id FROM files WHERE path = %s", (file_data['path'],))
            existing = self.cursor.fetchone()
            
            # Update
            if existing:
                file_id = existing[0]
                self.cursor.execute("""
                UPDATE files SET 
                    filename = %s,
                    extension = %s,
                    size = %s,
                    modified = %s,
                    created = %s,
                    preview = %s,
                    content = %s
                WHERE id = %s
                """, (
                    file_data['filename'],
                    file_data['extension'],
                    file_data['size'],
                    file_data['modified'],
                    file_data['created'],
                    file_data.get('preview', None),
                    file_data.get('content', None),
                    file_id
                ))

                # Clear keywords, will be updated below            
                self.cursor.execute("DELETE FROM file_keywords WHERE file_id = %s", (file_id,))
            else:
                self.cursor.execute("""
                INSERT INTO files (path, filename, extension, size, modified, created, preview, content)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """, (
                    file_data['path'],
                    file_data['filename'],
                    file_data['extension'],
                    file_data['size'],
                    file_data['modified'],
                    file_data['created'],
                    file_data.get('preview', None),
                    file_data.get('content', None)
                ))
                file_id = self.cursor.fetchone()[0]
            
            # Add keywords
            if 'top_words' in file_data and file_data['top_words']:
                for word in file_data['top_words']:
                    self.cursor.execute("""
                    INSERT INTO file_keywords (file_id, word)
                    VALUES (%s, %s)
                    """, (file_id, word))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Error adding file to database: {e}")
            return False

    def search_by_extension(self, extension) -> list:
        """
        Search files by extension
        
        Args:
            extension: String extension to search for (without dot)
        
        Returns:
            List of dictionaries with filename and path of matching files
        """
        try:
            query = "SELECT filename, path FROM files WHERE extension = %s"
            
            self.cursor.execute(query, (extension,))
            results = self.cursor.fetchall()
            
            # Return list of dictionaries with filename and path
            return [{"filename": row[0], "path": row[1]} for row in results]
        except Exception as e:
            print(f"Error searching by extension: {e}")
            return []

    def search_by_content(self, search_term) -> list:
        """
        Search files by filename, preview content and keywords
        
        Args:
            search_term: Term to search for
        
        Returns:
            List of dictionaries with filename and path of matching files
        """
        try:
            search_term = f'%{search_term}%' # This will search for the term in the middle of other terms
            
            # Search in filename, preview and also by matching keywords
            query = """
            SELECT DISTINCT f.filename, f.path 
            FROM files f
            LEFT JOIN file_keywords k ON f.id = k.file_id
            WHERE 
                f.filename ILIKE %s OR 
                f.preview ILIKE %s OR 
                f.content ILIKE %s OR
                k.word ILIKE %s
            """
            
            self.cursor.execute(query, (search_term, search_term, search_term, search_term))
            results = self.cursor.fetchall()
            
            # Return list of dictionaries with filename and path, as before
            return [{"filename": row[0], "path": row[1]} for row in results]
        except Exception as e:
            print(f"Error searching by content: {e}")
            return []
        
    def search_multi_words(self, search_words: list) -> list:
        """
        Search files matching multiple words in content, filename, or keywords
        
        Args:
            search_words: List of words to search for
        
        Returns:
            List of dictionaries with filename and path of matching files
        """
        try:
            if not search_words:
                return []
                
            # Build a query that requires all words to match
            query = """
            SELECT f.filename, f.path
            FROM files f
            WHERE 
            """
            
            # For each word, check if it appears in filename, content, preview, or keywords
            conditions = []
            params = []
            
            for word in search_words:
                word_param = f'%{word}%'
                conditions.append("""
                (f.filename ILIKE %s OR 
                 f.preview ILIKE %s OR 
                 f.content ILIKE %s OR
                 EXISTS (SELECT 1 FROM file_keywords k WHERE k.file_id = f.id AND k.word ILIKE %s))
                """)
                params.extend([word_param, word_param, word_param, word_param])
            
            query += " AND ".join(conditions)
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            return [{"filename": row[0], "path": row[1]} for row in results]
        except Exception as e:
            print(f"Error searching multiple words: {e}")
            return []
    
    def get_all_files(self) -> list:
        """
        Get all files in the database
        
        Returns:
            List of dictionaries with id and path of all files
        """
        try:
            query = "SELECT id, path FROM files"
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            # Return list of dictionaries with id and path
            return [{"id": row[0], "path": row[1]} for row in results]
        except Exception as e:
            print(f"Error getting all files: {e}")
            return []

    def remove_file(self, file_id) -> bool:
        """
        Remove a file from the database by ID
        
        Args:
            file_id: The ID of the file to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First delete related keywords
            self.cursor.execute("DELETE FROM file_keywords WHERE file_id = %s", (file_id,))
            
            # Then delete the file
            self.cursor.execute("DELETE FROM files WHERE id = %s", (file_id,))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Error removing file from database: {e}")
            return False

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            
    def __del__(self):
        self.close()