from collections.abc import Generator
from pathlib import Path

import pytest

from sqlite_reader.database import DatabaseConnection
from sqlite_reader.query_service import (
    execute_user_query,
    get_table_count,
    get_table_data,
)


@pytest.fixture
def data_db(temp_db_path: Path) -> Generator[DatabaseConnection, None, None]:
    """Provides a database with populated tables for testing queries."""
    db = DatabaseConnection()
    db.open(temp_db_path, read_only=False)

    db.execute("""
        CREATE TABLE items (
            id INTEGER PRIMARY KEY,
            name TEXT,
            value REAL,
            data BLOB
        )
    """)

    for i in range(1, 16):
        blob_data = b"binary" if i % 2 == 0 else None
        db.execute(
            "INSERT INTO items (name, value, data) VALUES (?, ?, ?)",
            (f"Item {i}", i * 1.5, blob_data),
        )

    db.commit()
    yield db
    db.close()


def test_get_table_count(data_db: DatabaseConnection) -> None:
    count = get_table_count(data_db, "items")
    assert count == 15


def test_get_table_data_pagination(data_db: DatabaseConnection) -> None:
    cols, rows = get_table_data(data_db, "items", limit=10, offset=0)
    assert len(cols) == 4
    assert cols == ["id", "name", "value", "data"]
    assert len(rows) == 10
    assert rows[0][1] == "Item 1"
    assert rows[9][1] == "Item 10"

    cols, rows = get_table_data(data_db, "items", limit=10, offset=10)
    assert len(rows) == 5
    assert rows[0][1] == "Item 11"
    assert rows[4][1] == "Item 15"


def test_get_table_data_types(data_db: DatabaseConnection) -> None:
    _, rows = get_table_data(data_db, "items", limit=2, offset=0)
    assert rows[0][0] == 1
    assert rows[0][2] == 1.5
    assert rows[0][3] is None
    assert isinstance(rows[1][3], bytes)


def test_execute_user_query_select(data_db: DatabaseConnection) -> None:
    res = execute_user_query(data_db, "SELECT name, value FROM items WHERE id <= 3")
    assert res.columns == ("name", "value")
    assert len(res.rows) == 3
    assert res.affected_rows == -1
    assert res.truncated is False
    assert res.execution_time_ms >= 0


def test_execute_user_query_truncation(data_db: DatabaseConnection) -> None:
    res = execute_user_query(data_db, "SELECT * FROM items", display_limit=5)
    assert len(res.rows) == 5
    assert res.truncated is True


def test_execute_user_query_mutation(data_db: DatabaseConnection) -> None:
    res = execute_user_query(data_db, "UPDATE items SET value = 0 WHERE id = 1")
    assert res.affected_rows == 1
    assert len(res.columns) == 0
    assert len(res.rows) == 0


def test_execute_user_query_empty(data_db: DatabaseConnection) -> None:
    with pytest.raises(ValueError, match="SQL statement cannot be empty"):
        execute_user_query(data_db, "   ")


def test_execute_user_query_read_only_rejection(temp_db_path: Path) -> None:
    db = DatabaseConnection()
    db.open(temp_db_path, read_only=True)
    try:
        with pytest.raises(
            PermissionError,
            match="Cannot execute mutating or schema statement on a read-only database connection.",
        ):
            execute_user_query(db, "CREATE TABLE forbidden (id INT)")
    finally:
        db.close()
