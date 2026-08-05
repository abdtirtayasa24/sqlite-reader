from collections.abc import Generator
from pathlib import Path

import pytest

from sqlite_reader.database import DatabaseConnection
from sqlite_reader.query_service import get_table_count, get_table_data


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

    # Insert 15 rows
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
    # Page 1: Limit 10, Offset 0
    cols, rows = get_table_data(data_db, "items", limit=10, offset=0)
    assert len(cols) == 4
    assert cols == ["id", "name", "value", "data"]
    assert len(rows) == 10
    assert rows[0][1] == "Item 1"
    assert rows[9][1] == "Item 10"

    # Page 2: Limit 10, Offset 10 (should return remaining 5 rows)
    cols, rows = get_table_data(data_db, "items", limit=10, offset=10)
    assert len(rows) == 5
    assert rows[0][1] == "Item 11"
    assert rows[4][1] == "Item 15"


def test_get_table_data_types(data_db: DatabaseConnection) -> None:
    _, rows = get_table_data(data_db, "items", limit=2, offset=0)

    # Row 1 (id=1): data is NULL
    assert rows[0][0] == 1
    assert rows[0][2] == 1.5
    assert rows[0][3] is None

    # Row 2 (id=2): data is BLOB
    assert rows[1][0] == 2
    assert rows[1][2] == 3.0
    assert isinstance(rows[1][3], bytes)
    assert rows[1][3] == b"binary"
