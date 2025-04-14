from flask import Flask, flash, jsonify, request, render_template, redirect, url_for
from dotenv import load_dotenv
import os
import requests

from .Database.DBConnection import DBConnection
from .Database.FileManager import FileManager
from .Database.SearchManager import SearchManager
from .Database.SchemaManager import SchemaManager

from .MiddleManagement.FileIndexer import FileIndexer
from .MiddleManagement.SearchSelector import SearchSelector


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
search_selector = SearchSelector(search_manager)


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
    query = request.args.get('q', '')
    results = search_selector.search_prompt(query)
    return render_template('search-result.html', results=results, query=query)


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
    new_path = request.form.get('path', '')

    # Cleanup: Remove files from the database that no longer exist
    existing_files = file_manager.get_all_files()
    for f in existing_files:
        if not os.path.exists(f['path']):
            file_manager.remove_file(f['id'])

    file_indexer.index_path(new_path)
    flash(f"Successfully indexed path: {new_path}")
    return redirect(url_for('home'))


def main():
    schema_manager.init_database()
    app.run(debug=True)


if __name__ == "__main__":
    main()