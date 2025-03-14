# Diagrams

## 1. System Context Diagram

```plantuml
@startuml
actor User
rectangle "Local File Search System" 
rectangle "OS Filesystem"
User --> "Local File Search System" : Runs a query
"Local File Search System" --> "OS Filesystem" : Looks in it
@enduml
```
## 2. Containers diagram
```plantuml
@startuml
actor User
rectangle "OS Filesystem"
rectangle "Local File Search System" {
    rectangle "Indexer" as Indexer
    rectangle "Search Engine" as Search
    rectangle "Database (PostgreSQL)" as DB
}
User --> Search : Runs a query
Indexer --> DB : Stores indexed files
Search --> DB : Searches for matching files
Indexer --> "OS Filesystem" : Retrieves data
@enduml
```
## 3. Components diagram
```plantuml
@startuml
package "Local File Search System" {
    class FileIndexer {
        +index_directory()
        +store_file()
    }
    
    class DBManager {
        +connect()
        +insert_file()
        +query_files()
    }
    
    class SearchEngine {
        +search()
    }
    
    FileIndexer --> DBManager : Stores file content
    SearchEngine --> DBManager : Queries indexed files
}
@enduml
```

*Personal notes here:*

1. The database will be hosted remotely on my work PC. Local IP: 192.168.83.202:5432
   1. TODO: OPEN PORT 5432


Development notes: to be deleted or moved

* What do I need for a search engine?
  * I need an indexer (crawl local data, filter, STORE IN DB)
  * I need a database (postgres)
  * I need something to actually search in the database based on the user queries
* Who uses this?
  * Just me, a regular user
* What does it access?
  * Just the local filesystem. No data of needing anything else. (should think of the future somehow...)
*
