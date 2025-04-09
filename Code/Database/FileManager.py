from typing import List, Dict


class FileManager:
    def __init__(self, db_connection):
        """
        Handles file-related database operations.
        Args:
            db_connection: An instance of DBConnection.
        """
        self.db_connection = db_connection

    def add_file(self, file_data: Dict[str, str]) -> bool:
        """Adds or updates a file in the database."""
        query = """
        INSERT INTO files (path, filename, extension, size, modified, created, preview, content)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (path) DO UPDATE SET
            filename = EXCLUDED.filename,
            extension = EXCLUDED.extension,
            size = EXCLUDED.size,
            modified = EXCLUDED.modified,
            created = EXCLUDED.created,
            preview = EXCLUDED.preview,
            content = EXCLUDED.content
        """
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (
                    file_data['path'], file_data['filename'], file_data['extension'],
                    file_data['size'], file_data['modified'], file_data['created'],
                    file_data.get('preview'), file_data.get('content')
                ))
            return True
        except Exception as e:
            print(f"Error adding file: {e}")
            return False

    def get_all_files(self) -> List[Dict[str, str]]:
        """Retrieves all files from the database."""
        query = "SELECT id, path FROM files"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query)
                return [{"id": row[0], "path": row[1]} for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error retrieving all files: {e}")
            return []

    def remove_file(self, file_id: int) -> bool:
        """Removes a file from the database by ID."""
        query = "DELETE FROM files WHERE id = %s"
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, (file_id,))
            return True
        except Exception as e:
            print(f"Error removing file: {e}")
            return False