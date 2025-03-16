from db_manager import DBManager
from indexer import FileIndexer
from searcher import FileSearcher

def main():
    db = DBManager() # Create a connection ONCE 
    indexer = FileIndexer(db) # Pass it on...
    searcher = FileSearcher(db) 

    # Test code:
    indexer.index_subtree()

    # The user input handling will also be taken care of here...
