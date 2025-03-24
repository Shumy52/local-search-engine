from DBManager import DBManager
from FileIndexer import FileIndexer
from SearchEngine import FileSearcher
from flask import Flask, flash, request, render_template, redirect, url_for
import os


app = Flask(__name__, template_folder='Templates')
app.secret_key = "I'm-Very-Fond-Of-Bananas" # Key used for flash messages
# The prompt that appears when you successfuly index uses this
# Used for anything that involves user sessions


# Initialize these variables at module level
# Thanks ChatGPT, I used to do this in the main(), but once I added flask
# that clearly wasn't going to work. 
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
    
    # This is how you can pass variables from python to the page
    # There you have a {{value}} and here you mention it in the return 
    return render_template('search-result.html', results=results, query=query)

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
    # Default path indexed before starting the app
    indexer.index_path(r"C:\Users\Shumy\Documents\Projects")
    app.run(debug=True)

if __name__ == "__main__":
    main()
