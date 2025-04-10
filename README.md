## Local search engine

---

GALBAZA ALEXANDRU-MIHAI

This project was made during my studies at UTCN, in order to learn some OOP stuff.

It's a simple index'n search tool with a web interface. All it does it crawl through a given folder recursively, adding all it can to a database, then running queries in said database.

For the moment only for windows.

---

### Install instuctions

1. Clone the repo to your desired location
2. Setup a venv for that, using: (assuming you have venv installed)

```bash
python -m venv myvenv
```

3. Install the requirements using:

```bash
pip install -r requirements.txt
```

4. Being at the root of the project, run
   ```bash
   python -m Code.main
   ```

### MUST DOs BEFORE RUNNING:

1. Have a postgres DB up and running. Change the connection details in DBManager.py
2. Change the default indexing path in main.py.

### Enjoy!

1. Go to localhost:5000
2. There the menus should be self-explanatory, not quite rocket science yet

---

### Regarding the index-less search:

- 2 separate apps will need to be run. One is main.py and the other is SearchManager.py, found in Code/IndexlessQuery.
- These will occupy ports 5000 - 5004
