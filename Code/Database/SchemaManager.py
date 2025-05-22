class SchemaManager:
    def __init__(self, db_connection):
        """
        Handles database schema initialization and updates.
        Args:
            db_connection: An instance of DBConnection.
        """
        self.db_connection = db_connection

    def init_database(self):
        """
        Initialize the database schema if tables don't exist.
        Creates the necessary tables, indexes, and triggers for the search engine.
        """
        try:
            with self.db_connection.cursor() as cursor:
                # Check if the 'files' table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'files'
                    );
                """)
                tables_exist = cursor.fetchone()[0]

                if not tables_exist:
                    self._create_schema(cursor)
                else:
                    self._update_schema_if_needed(cursor)

            print("Database schema initialized successfully.")
        except Exception as e:
            print(f"Error initializing database schema: {e}")
            raise Exception(f"Error connecting to DB to init schema {e}")

    def _create_schema(self, cursor):
        """Creates the database schema."""
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        cursor.execute("""
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
        """)
        cursor.execute("""
            CREATE INDEX idx_file_path ON files(path);
            CREATE INDEX idx_file_extension ON files(extension);
            CREATE INDEX idx_file_content_gin ON files USING GIN(search_vector);
            CREATE INDEX idx_file_filename_gin ON files USING GIN(filename gin_trgm_ops);
            CREATE INDEX idx_file_preview_gin ON files USING GIN(preview gin_trgm_ops);
        """)
        self._create_trigger(cursor)

    def _update_schema_if_needed(self, cursor):
        """Updates the schema if necessary (e.g., adds missing columns or indexes)."""
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'files' AND column_name = 'search_vector'
            );
        """)
        has_search_vector = cursor.fetchone()[0]

        if not has_search_vector:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            cursor.execute("ALTER TABLE files ADD COLUMN search_vector tsvector;")
            cursor.execute("""
                CREATE INDEX idx_file_content_gin ON files USING GIN(search_vector);
                CREATE INDEX idx_file_filename_gin ON files USING GIN(filename gin_trgm_ops);
                CREATE INDEX idx_file_preview_gin ON files USING GIN(preview gin_trgm_ops);
            """)
            self._create_trigger(cursor)
            cursor.execute("""
                UPDATE files SET 
                search_vector = 
                    setweight(to_tsvector('english', COALESCE(filename, '')), 'A') ||
                    setweight(to_tsvector('english', COALESCE(preview, '')), 'B') ||
                    setweight(to_tsvector('english', COALESCE(content, '')), 'C');
            """)

    def _create_trigger(self, cursor):
        """Creates a trigger to update the search vector."""
        cursor.execute("""
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