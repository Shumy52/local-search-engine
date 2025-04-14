# Local Search Engine

My legal name for my TA: GALBAZA ALEXANDRU-MIHAI, GROUP 3043**3**, 2024-2025

A file indexing and searching tool with a web interface that allows you to crawl through directories, store file information in a database, and perform powerful searches.

## Features

- Recursive directory crawling and file indexing
- Full-text search with PostgreSQL (with GIN indexing)
- Path-based, content-based, and extension-based search
- Distributed search capabilities with multiple worker processes
- Simple web interface for searching and browsing results

## Requirements

- Python 3.6+
- PostgreSQL database
- Windows OS (currently)

## Installation

1. Clone the repository

```bash
git clone https://github.com/Shumy52/local-search-engine.git
cd local-search-engine
```

2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on `.env.example`

```
DB_NAME=your_db_name
DB_USER=your_username
DB_HOST=your_host
DB_PASSWORD=your_password
DB_PORT=5432
FLASK_SECRET_KEY=your_random_key
```

## Configuration

Before running the application:

1. Ensure your PostgreSQL database is running
2. Make sure your PC is on... I guess

## Usage

### Standard Search

1. Start the main application

```bash
python -m Code.main
```

2. Open your browser and navigate to `http://localhost:5000`
3. Index a directory by entering its path and clicking "Index"
4. Search for files using the search bar

### Distributed Search (Index-less)

1. Start the main application

```bash
python -m Code.main
```

2. Start the search manager (in a separate terminal)

```bash
python -m Code.MiddleManagement.IndexlessQuery.SearchManager
```

3. Use the "Distributed Search" option in the web interface

## Project Structure

- `Code/`: Main application code
  - `Database/`: Database connection and management
  - `MiddleManagement/`: File indexing and search utilities
  - `IndexlessQuery/`: Distributed search system
- `Templates/`: HTML templates for web interface
- `Docs/`: Documentation and architecture diagrams

## License

My licence is that I made it the fuck up. GNU open-source or some stuff.
