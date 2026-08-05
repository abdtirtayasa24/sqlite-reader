import sqlite3
from pathlib import Path

import pytest

from sqlite_reader.database import DatabaseConnection


def test_temp_db_fixture(temp_db_path: Path) -> None:
    """Verify that the temporary database fixture works and is accessible."""
    assert temp_db_path.exists()


def test_database_open_read_only(temp_db_path: Path) -> None:
    """Verify that read-only mode opens successfully and rejects writes."""
    db = DatabaseConnection()
    db.open(temp_db_path, read_only=True)

    assert db.is_read_only is True
    assert db.db_path == temp_db_path

    cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    assert cursor.fetchone() is not None

    with pytest.raises(sqlite3.OperationalError, match="readonly database"):
        db.execute("CREATE TABLE new_table (id INTEGER)")

    db.close()


def test_database_open_editable(temp_db_path: Path) -> None:
    """Verify that editable mode permits writes."""
    db = DatabaseConnection()
    db.open(temp_db_path, read_only=False)

    assert db.is_read_only is False

    db.execute("CREATE TABLE new_table (id INTEGER)")
    db.commit()

    cursor = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='new_table'"
    )
    assert cursor.fetchone() is not None

    db.close()


def test_database_invalid_path() -> None:
    """Verify that opening a non-existent file raises an error."""
    db = DatabaseConnection()
    with pytest.raises(FileNotFoundError):
        db.open(Path("non_existent_file.sqlite3"))
