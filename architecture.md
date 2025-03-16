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

### Explanation

* We have a single actor, being a generic user, not authorization is done, what will interact with a "search engine" which will in turn interact with the filesystem of the OS it will run on. 
* (I'm planning to make this work on both Win and Unix, since development will be done on both... long story)

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

### Explanation

* Starting from the right side, we have the indexer which will do the "heavy lifting" of handling the files (both get from OS and put in DB).
* I've chosen PostgreSQL mainly because you can't go wrong with it if you have enough time to get it working. I was tempted to use MongoDB just for the hell of learning something new, but I've stuck with ol' reliable for now.
* The search engine will send prompts to the DB and return the results (in a pretty way) to the user.

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
### Explanation

* This is the diagram I'm most doubtful about. I don't know what to say except that the names chosen portrait their use in quite an efficient way.


# Lots of words and stuff

## 1. Nothing yet.