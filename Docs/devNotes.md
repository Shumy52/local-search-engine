*Personal notes here:*

1. This needs better error handling. For the moment I'm wondering, how could I throw an error in the init of the DBManager?

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
