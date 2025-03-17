from DBManager import DBManager
from FileIndexer import FileIndexer
from SearchEngine import FileSearcher

def main():
    db = DBManager() # Create a connection ONCE 
    indexer = FileIndexer(db) # Pass it on...
    searcher = FileSearcher(db) 

    # Test code:
    indexer.index_path(r"C:\Users\Shumy\Documents\Projects")
    results = searcher.search_prompt(".py")

    print(results)

if __name__ == "__main__":
    main()
