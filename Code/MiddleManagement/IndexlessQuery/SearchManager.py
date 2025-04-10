import atexit
from multiprocessing import Manager
import subprocess
import sys
from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

PORT = 5001
WORKER_PORTS = [5002, 5003, 5004]
WORKERS = [f"http://localhost:{port}" for port in WORKER_PORTS]

worker_processes = []

# Be advised, no caching has been implemented yet. 
# TODO: Cache search results and query for subsequenct searches

def start_workers():
    worker_file = os.path.join(os.path.dirname(__file__), "SearchWorker.py")

    for port in WORKER_PORTS:
        process = subprocess.Popen([sys.executable, worker_file, str(port)])
        worker_processes.append(process)
        print(f"Start worker port {port} PID: {process.pid}")

def cleanup_workers():
    for process in worker_processes:
        try:
            process.terminate()
            print(f"Terminated worker process PID: {process.pid}")
        except:
            pass

# The complete path would be localhost:PORT/api/search (hope)
@app.route("/api/search", methods=["GET"])
def api_search():
    query = request.args.get('q', '')
    path = request.args.get('path', '')
    
    # Get top-level directories to distribute
    try:
        # Subdirs is the list of paths + specific something in that directory
        # If that "something" is a directory
        subdirs = [os.path.join(path, d) for d in os.listdir(path) 
                  if os.path.isdir(os.path.join(path, d))]
        
        # Include base path for files in the root directory
        subdirs.append(path)
    except Exception as e:
        return jsonify({"error": f"Error reading directory: {str(e)}"}), 400
    
    # Distribute directories among workers
    worker_dirs = {}
    for i, subdir in enumerate(subdirs):
        worker_idx = i % len(WORKERS)
        # Initialize the lists of tasks for each of the workers
        if WORKERS[worker_idx] not in worker_dirs:
            worker_dirs[WORKERS[worker_idx]] = []

        worker_dirs[WORKERS[worker_idx]].append(subdir)
    
    # Query workers with their assigned directories
    results = []
    for worker, dirs in worker_dirs.items():
        for dir_path in dirs:
            try:
                response = requests.get(
                    f"{worker}/api/search", 
                    params={"q": query, "path": dir_path}
                )
                if response.status_code == 200:
                    worker_results = response.json().get("results", [])
                    results.extend(worker_results)
            except Exception as e:
                print(f"Error with {worker} searching {dir_path}: {e}")
    
    # Sorting the results by filename
    results.sort(key=lambda x: x.get("filename", ""))
    return jsonify({"results": results})

def main():
    start_workers()
    atexit.register(cleanup_workers)
    # Localhost, port 3001
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()