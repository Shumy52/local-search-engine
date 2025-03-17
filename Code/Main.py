from Code.DBManager import DBManager
from Code.FileIndexer import FileIndexer
from Code.SearchEngine import FileSearcher

def main():
    db = DBManager() # Create a connection ONCE 
    indexer = FileIndexer(db) # Pass it on...
    # searcher = FileSearcher(db) 

    print("Dicks")
    # Test code:
    indexer.index_path(r"C:\Users\Shumy\Documents\Projects")

    # The user input handling will also be taken care of here...

if __name__ == "__main__":
    main()
