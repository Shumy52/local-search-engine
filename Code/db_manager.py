# Installed psycopg2-binary for this
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
    
    def add_file(self, file_data):
        """Add a file to the database along with its keywords"""
        try:
            # Check file exists
            self.cursor.execute("SELECT id FROM files WHERE path = %s", (file_data['path'],))
            print("I've already found file ", file_data['path'])
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
                print("I've entered a new file ", file_data['path'])
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
            return file_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error adding file to database: {e}")
            return None
    
    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Query execution failed: {e}")
            return False
            
    def fetch_one(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Error fetching one record: {e}")
            return None
            
    def fetch_all(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error fetching all records: {e}")
            return []
            
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            
    def __del__(self):
        self.close()