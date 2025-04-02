from DBManager import DBManager
from FileIndexer import FileIndexer
from SearchEngine import FileSearcher
from flask import Flask, flash, jsonify, request, render_template, redirect, url_for
import os
from dotenv import load_dotenv
import requests

app = Flask(__name__, template_folder='Templates')
# Load secret key from .env file

load_dotenv()
app.secret_key = os.getenv('FLASK_SECRET_KEY', "default")  # Default fallback if not in .env

db = DBManager()
indexer = FileIndexer(db)
searcher = FileSearcher(db)

@app.route('/')
def home():
    default_path = r"C:\Users\Shumy\Documents\Projects"
    return render_template('search-form.html', current_path = default_path)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    # Now you can use the searcher object here
    results = searcher.search_prompt(query)
    
    return render_template('search-result.html', results=results, query=query)

# Bad practice. TODO: Do something...
MANAGER_ADDRESS = "http://localhost:5001/api/search"

@app.route("/api/search", methods=["GET"])
def api_search(): 
    query = request.args.get('q', '')
    path = request.args.get('path')

    try:
        response = requests.get(MANAGER_ADDRESS, params={"q": query, "path": path})
        if response.status_code == 200:
            # TODO: Return as result page
            return render_template('search-result.html', results=response.json().get("results", []), query=query)
            #return jsonify(response.json())
        else:
            return jsonify({"error": f"Manager returned status {response.status_code}"}), response.status_code
    except Exception as e:
        return jsonify({"error": f"Error connecting to search manager: {str(e)}"}), 500
    

@app.route('/open_file')
def open_file():
    path = request.args.get('path')
    os.startfile(path) 
    return redirect(url_for('search', q=request.args.get('q', '')))

@app.route('/set_index_path', methods=['POST'])
def set_index_path():
    new_path = request.form.get('path', '')

    # Cleanup
    existing_files = db.get_all_files()  # Only ID and path
    for f in existing_files:
        if not os.path.exists(f['path']):
            db.remove_file(f['id'])  

    indexer.index_path(new_path)
    flash(f"Successfully indexed path: {new_path}")
    return redirect(url_for('home'))
    
def main():
    app.run(debug=True)

if __name__ == "__main__":
    main()
