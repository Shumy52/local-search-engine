from flask import Flask, request, jsonify
import os
import sys

app = Flask(__name__)

PORT = int(sys.argv[1])

def search_files(query, search_path):
    matches = []
    for root, _, files in os.walk(search_path):
        for filename in files:
            full_path = os.path.join(root, filename)
            if query.lower() in filename.lower():
                matches.append({
                    "filename": filename,
                    "path": full_path,
                    "size": os.path.getsize(full_path),
                    "modified": os.path.getmtime(full_path)
})
    return matches

@app.route("/api/search", methods=["GET"])
def search():
    query = request.args.get("q")
    path = request.args.get("path")
    results = search_files(query, path)
    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(port=PORT)
    print(f"Worker running on port: {PORT}")
