import psycopg2
from contextlib import contextmanager
from typing import Dict


class DBConnection:
    def __init__(self, db_config: Dict[str, str]):
        """
        Manages the database connection.
        Args:
            db_config: A dictionary containing database connection parameters.
        """
        self.db_config = db_config
        self.conn = None

    def connect(self):
        if not self.conn:
            self.conn = psycopg2.connect(**self.db_config)

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None


    @contextmanager
    def cursor(self):
        """
        Provides a cursor for database operations.
        Ensures the connection is established and commits/rollbacks transactions.
        It's used within "with ... as ... " clauses, hence the need for @contextmanager
        """
        self.connect()
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()