from DBManager import DBManager
from FileIndexer import FileIndexer
from SearchEngine import FileSearcher
from flask import Flask, request, render_template

# @app.route("/", )

# TODO:
#   Add directory to index
#   Add exclusion rules to that indexing
#   Create the interface
#   Pretty print the results

#   I want to interface with windows explorer, easier to navigate

def main():
    db = DBManager() # Create a connection ONCE 
    indexer = FileIndexer(db) # Pass it on...
    searcher = FileSearcher(db) 

    # Test code:
    indexer.index_path(r"C:\Users\Shumy\Documents\Projects")
    results = searcher.search_prompt(".py")
    # Tuple of Filename and Path
    # print(results, '\n')

if __name__ == "__main__":
    main()
