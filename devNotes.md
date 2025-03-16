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

TODO:

* I need to somehow mark the requirements that need to be installed to run this
  * For the moment I installed psycopg2-binary
* I need to isolate the project. Instead of installing libraries for the whole system, I need to create a venv (virtual environment). Do I really? Must research.
* To move these notes in an "official" place, such as a readme or a completely personal TODO list and...notes. Yeah.
*
