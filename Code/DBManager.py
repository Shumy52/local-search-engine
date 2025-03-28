import psycopg2
import os 
from dotenv import load_dotenv

class DBManager:
    def __init__(self):
        load_dotenv()

        
        self.conn = psycopg2.connect(database=os.getenv('DB_NAME'),
                                     user=os.getenv('DB_USER'),
                                     host=os.getenv("DB_HOST"),
                                     password=os.getenv("DB_PASSWORD"),
                                     port=os.getenv("DB_PORT")
                                    )
        self.cursor = self.conn.cursor()
        self.init_database()

    # TODO: Move all the SQL in a directory

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
                # Enable the pg_trgm extension for better text search
                self.cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
                
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
                        content TEXT,
                        search_vector tsvector
                    );
                    
                    -- Basic indexes
                    CREATE INDEX idx_file_path ON files(path);
                    CREATE INDEX idx_file_extension ON files(extension);
                    
                    -- GIN indexes for text search
                    CREATE INDEX idx_file_content_gin ON files USING GIN(search_vector);
                    CREATE INDEX idx_file_filename_gin ON files USING GIN(filename gin_trgm_ops);
                    CREATE INDEX idx_file_preview_gin ON files USING GIN(preview gin_trgm_ops);
                """)
                
                # Create trigger to update search_vector when content changes
                self.cursor.execute("""
                    CREATE OR REPLACE FUNCTION update_search_vector_trigger() RETURNS trigger AS $$
                    BEGIN
                        NEW.search_vector = 
                            setweight(to_tsvector('english', COALESCE(NEW.filename, '')), 'A') ||
                            setweight(to_tsvector('english', COALESCE(NEW.preview, '')), 'B') ||
                            setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'C');
                        RETURN NEW;
                    END
                    $$ LANGUAGE plpgsql;
                    
                    CREATE TRIGGER update_files_search_vector
                    BEFORE INSERT OR UPDATE ON files
                    FOR EACH ROW EXECUTE FUNCTION update_search_vector_trigger();
                """)
                
                self.conn.commit()
                print("Database schema initialized successfully.")
            else:
                # Check if search_vector column exists, add if not
                self.cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'files' AND column_name = 'search_vector'
                    );
                """)
                has_search_vector = self.cursor.fetchone()[0]
                
                if not has_search_vector:
                    # Enable the pg_trgm extension
                    self.cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
                    
                    # Add search_vector column
                    self.cursor.execute("ALTER TABLE files ADD COLUMN search_vector tsvector;")
                    
                    # Create GIN indexes
                    self.cursor.execute("""
                        CREATE INDEX idx_file_content_gin ON files USING GIN(search_vector);
                        CREATE INDEX idx_file_filename_gin ON files USING GIN(filename gin_trgm_ops);
                        CREATE INDEX idx_file_preview_gin ON files USING GIN(preview gin_trgm_ops);
                    """)
                    
                    # Create trigger
                    self.cursor.execute("""
                        CREATE OR REPLACE FUNCTION update_search_vector_trigger() RETURNS trigger AS $$
                        BEGIN
                            NEW.search_vector = 
                                setweight(to_tsvector('english', COALESCE(NEW.filename, '')), 'A') ||
                                setweight(to_tsvector('english', COALESCE(NEW.preview, '')), 'B') ||
                                setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'C');
                            RETURN NEW;
                        END
                        $$ LANGUAGE plpgsql;
                        
                        CREATE TRIGGER update_files_search_vector
                        BEFORE INSERT OR UPDATE ON files
                        FOR EACH ROW EXECUTE FUNCTION update_search_vector_trigger();
                    """)
                    
                    # Initialize search_vector for existing records
                    self.cursor.execute("""
                        UPDATE files SET 
                        search_vector = 
                            setweight(to_tsvector('english', COALESCE(filename, '')), 'A') ||
                            setweight(to_tsvector('english', COALESCE(preview, '')), 'B') ||
                            setweight(to_tsvector('english', COALESCE(content, '')), 'C');
                    """)
                    
                    self.conn.commit()
                    print("Database schema updated with full text search capabilities.")
                else:
                    print("Database schema already exists with full text search capabilities.")
                
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Error initializing database schema: {e}")
            return False
    
    def add_file(self, file_data) -> bool: 
        """Add a file to the database"""
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
            else:
                self.cursor.execute("""
                INSERT INTO files (path, filename, extension, size, modified, created, preview, content)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
        Search files by filename, path, preview content using full text search
        
        Args:
            search_term: Term to search for
        
        Returns:
            List of dictionaries with filename and path of matching files
        """
        try:
            # Convert search term to tsquery
            search_query = ' & '.join(search_term.split())
            tsquery = f"to_tsquery('english', '{search_query}')"
            
            # Use GIN index for full text search
            query = f"""
            SELECT DISTINCT f.filename, f.path, ts_rank(f.search_vector, {tsquery}) as rank
            FROM files f
            WHERE 
                f.search_vector @@ {tsquery} OR
                f.filename ILIKE %s OR
                f.path ILIKE %s
            ORDER BY rank DESC
            """
            
            like_term = f'%{search_term}%'
            self.cursor.execute(query, (like_term, like_term))
            results = self.cursor.fetchall()
            
            return [{"filename": row[0], "path": row[1]} for row in results]
        except Exception as e:
            print(f"Error searching by content: {e}")
            # Fallback to simpler search if full text search fails
            try:
                search_term = f'%{search_term}%'
                query = """
                SELECT DISTINCT f.filename, f.path 
                FROM files f
                WHERE 
                    f.filename ILIKE %s OR 
                    f.path ILIKE %s OR
                    f.preview ILIKE %s OR 
                    f.content ILIKE %s
                """
                
                self.cursor.execute(query, (search_term, search_term, search_term, search_term))
                results = self.cursor.fetchall()
                
                return [{"filename": row[0], "path": row[1]} for row in results]
            except Exception as e2:
                print(f"Error in fallback search: {e2}")
                return []
        
    def search_multi_words(self, search_words: list) -> list:
        """
        Search files matching multiple words using full text search
        
        Args:
            search_words: List of words to search for
        
        Returns:
            List of dictionaries with filename and path of matching files
        """
        try:
            if not search_words:
                return []
                
            # Create a tsquery from all search words
            search_query = ' & '.join(search_words)
            tsquery = f"to_tsquery('english', '{search_query}')"
            
            # Use GIN index for efficient search
            query = f"""
            SELECT f.filename, f.path, ts_rank(f.search_vector, {tsquery}) as rank
            FROM files f
            WHERE f.search_vector @@ {tsquery}
            ORDER BY rank DESC
            """
            
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            # If no results with full text search, fallback to pattern matching
            if not results:
                query = """
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
            # Delete the file
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
