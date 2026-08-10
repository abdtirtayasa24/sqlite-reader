# SQLite Reader

A simple, lightweight, local SQLite reader and data-management application built with Python and Tkinter. 

This tool is designed to be minimal, fast, and safe. It uses Python's standard library without requiring heavy third-party database drivers or complex web frameworks.

## Features

- **Read-Only by Default**: Protects your data from accidental modifications.
- **Schema Explorer**: Browse tables, views, indexes, and triggers.
- **Table Browsing**: Paginated data grid with support for large tables.
- **SQL Editor**: Execute custom queries with background execution and cancellation.
- **Data Editing**: Insert, update, and delete records safely using parameterized queries.
- **Export & Backup**: Export query results to CSV and create safe online database backups.
- **Mutation Safety**: Explicit warnings for unfiltered `UPDATE` or `DELETE` statements.

## Requirements

- Python 3.11 or higher
- Tkinter (usually included with standard Python installations)

## Installation

You can install the application locally using `pip`:

```bash
pip install .
```

Or for an isolated environment, use `pipx`:

```bash
pipx install .
```

## Usage

If installed via `pip` or `pipx`, you can launch the application directly from your terminal:

```bash
sqlite-reader
```

Alternatively, you can run it as a Python module without installing:

```bash
python -m sqlite_reader
```

## Development

To set up the development environment:

1. Clone the repository.
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment.
4. Install development dependencies: `pip install -e ".[dev]"`

## Running Tests and Checks

```bash
# Run unit tests
python -m pytest

# Run static type checking
mypy src

# Run linter
ruff check .
```

---