# IndexlessQuery

A distributed search system developed as an add-on for Assignment 2.

## Overview

This module provides an alternative search mechanism that searches files directly without requiring prior indexing in the database. It implements a distributed architecture with multiple worker processes to speed up searches across large directory structures.

## Components

- `SearchManager.py`: Coordinates the search process, distributes work among workers, and aggregates results
- `SearchWorker.py`: Performs "manual" search on assigned segment of directory

## Usage

1. Start the main application (`python -m Code.main`)
2. Start the search manager separately (`python -m Code.MiddleManagement.IndexlessQuery.SearchManager`)
3. Use the "Distributed Search" option in the web interface