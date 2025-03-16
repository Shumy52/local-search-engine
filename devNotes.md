*Personal notes here:*

1. The database will be hosted remotely on my work PC. Local IP: 192.168.83.202:5432
   1. ~~TODO: OPEN PORT 5432~~

Development notes: to be deleted or moved

* What do I need for a search engine?
  * I need an indexer (crawl local data, filter, STORE IN DB)
  * I need a database (postgres)
  * I need something to actually search in the database based on the user queries
* Who uses this?
  * Just me, a regular user
* What does it access?
  * Just the local filesystem. No data of needing anything else. (should think of the future somehow...)
* Where do I initialize the DBManager?
  * The indexer. On program run, the file indexer will run every time to check for updates, no matter what
  * I'll make the DBmanager a singleton, so when search engine tries to make an object, will get an instance instead.
  * Nope, that's horsecrap. Just create an instance in the main and pass the ref to everything
  * Singleton is complicated for no real usage
* What do I do with the DB schema?
  * Uh... good question. I'll put here the script to init the DB.

```sql
CREATE TABLE files (
    id SERIAL PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    extension TEXT,
    size INTEGER,
    modified TIMESTAMP,
    created TIMESTAMP,
    preview TEXT,
    content TEXT
);

CREATE TABLE file_keywords (
    id SERIAL PRIMARY KEY,
    file_id INTEGER,
    word TEXT NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

CREATE INDEX idx_file_path ON files(path);
CREATE INDEX idx_file_extension ON files(extension);
CREATE INDEX idx_file_keywords ON file_keywords(word);
```

TODO:

* I need to somehow mark the requirements that need to be installed to run this
  * For the moment I installed psycopg2-binary
* I need to isolate the project. Instead of installing libraries for the whole system, I need to create a venv (virtual environment). Do I really? Must research.
* To move these notes in an "official" place, such as a readme or a completely personal TODO list and...notes. Yeah.
