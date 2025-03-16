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