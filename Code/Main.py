from flask import Flask, flash, jsonify, request, render_template, redirect, url_for
from dotenv import load_dotenv
import os
import psycopg2
import requests

from .Database.DBConnection import DBConnection
from .Database.FileManager import FileManager
from .Database.SearchManager import SearchManager
from .Database.SchemaManager import SchemaManager

from .MiddleManagement.FileIndexer import FileIndexer
from .MiddleManagement.SearchSelector import SearchSelector
from .MiddleManagement.WidgetManager import WidgetManager
from .MiddleManagement.SearchSelectorProxy import SearchSelectorProxy

# Initialize Flask app
app = Flask(__name__, template_folder='../Templates')


# Load environment variables
load_dotenv()
app.secret_key = os.getenv('FLASK_SECRET_KEY', "default")  # Default fallback if not in .env


# Database configuration
db_config = {
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "host": os.getenv("DB_HOST"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT"),
}


# Initialize database connection and managers
db_connection = DBConnection(db_config)
schema_manager = SchemaManager(db_connection)
file_manager = FileManager(db_connection)
search_manager = SearchManager(db_connection)
file_indexer = FileIndexer(file_manager)
real_search_selector = SearchSelector(search_manager)
search_selector = SearchSelectorProxy(real_search_selector)
widget_manager = WidgetManager()


# Default path for indexing
current_file = os.path.abspath(__file__)
project_dir = os.path.dirname(os.path.dirname(current_file)) # ../../WhereIamRightNow , so basically the file downloaded by git clone. Always safe.
DEFAULT_PATH = project_dir

MANAGER_ADDRESS = "http://localhost:5001/api/search"

@app.route('/')
def home():
    """
    Render the home page with the default path.
    """
    return render_template('search-form.html', current_path=DEFAULT_PATH)


@app.route('/search', methods=['GET'])
def search():
    """
    Handle search requests and render the search results.
    """
    try:
        query = request.args.get('q', '')
        results = search_selector.search_prompt(query)
        
        widgets = widget_manager.get_widgets_for_query(query)
        
        return render_template('search-result.html', 
                            results=results, 
                            query=query,
                            widgets=widgets)  
    except Exception as e:
        app.logger.error(f"Search error: {e}")
        # Pass the error to the template
        return render_template('search-result.html',
                              query=query, # Could mean trouble. What if we don't init query?
                              results=[], # I think we will most of the time...
                              system_error=f"Error performing search: {str(e)}")

@app.route("/api/search", methods=["GET"])
def api_search():
    """
    Route for IndexlessQueries. Assignment 2
    """
    query = request.args.get('q', '')
    path = request.args.get('path')

    try:
        response = requests.get(MANAGER_ADDRESS, params={"q": query, "path": path})
        if response.status_code == 200:
            return jsonify({"results": response.json().get("results", [])})
        else:
            return jsonify({"error": f"Manager returned status {response.status_code}"}), response.status_code
    except Exception as e:
        return jsonify({"error": f"Error connecting to search manager: {str(e)}"}), 500


@app.route('/open_file')
def open_file():
    """
    Open a file on the local system based on the provided path.
    """
    path = request.args.get('path')
    os.startfile(path)
    return redirect(url_for('search', q=request.args.get('q', '')))


@app.route('/set_index_path', methods=['POST'])
def set_index_path():
    """
    Set a new index path and re-index the files in the database.
    """
    try:
        new_path = request.form.get('path', '')

        # Cleanup: Remove files from the database that no longer exist
        existing_files = file_manager.get_all_files()
        for f in existing_files:
            if not os.path.exists(f['path']):
                file_manager.remove_file(f['id'])

        file_indexer.index_path(new_path)
        flash(f"Successfully indexed path: {new_path}")
        return redirect(url_for('home'))
    except Exception as e:
        app.logger.error(f"Search error: {e}")
        # Pass the error to the template
        flash(f"There's something wrong with the indexing: {e}")
        return redirect(url_for('home'))


@app.route('/cache/stats')
def cache_stats():
    """
    Display cache statistics.
    """
    stats = search_selector.get_cache_stats()
    return jsonify(stats)

@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """
    Clear the search cache.
    """
    search_selector.clear_cache()
    flash("Search cache cleared successfully")
    return redirect(url_for('home'))

def main():
    schema_manager.init_database()
    app.run(debug=True)

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all uncaught exceptions"""
    app.logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    
    # For database connection errors
    if isinstance(e, psycopg2.OperationalError):
        error_message = "Database connection failed. Please check your configuration."
    else:
        error_message = f"An unexpected error occurred: {str(e)}"
    
    # Return different responses based on request type
    if request.path.startswith('/api/'):
        return jsonify({"error": error_message}), 500
    else:
        return render_template('search-form.html', 
                              current_path=DEFAULT_PATH, 
                              system_error=error_message), 500

if __name__ == "__main__":
    main()