from collections.abc import Generator
from pathlib import Path

import pytest

from sqlite_reader.database import DatabaseConnection
from sqlite_reader.query_service import (
    delete_record,
    get_table_data,
    get_table_identifiers,
    insert_record,
    update_record,
)


@pytest.fixture
def edit_db(temp_db_path: Path) -> Generator[DatabaseConnection, None, None]:
    db = DatabaseConnection()
    db.open(temp_db_path, read_only=False)

    db.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL
        )
    """)

    db.execute("""
        CREATE TABLE no_pk_table (
            title TEXT,
            info TEXT
        )
    """)

    db.execute("INSERT INTO products (name, price) VALUES ('Widget', 9.99)")
    db.execute("INSERT INTO no_pk_table (title, info) VALUES ('Note', 'Sample')")
    db.commit()
    yield db
    db.close()


def test_get_table_identifiers(edit_db: DatabaseConnection) -> None:
    pk_ids = get_table_identifiers(edit_db, "products")
    assert pk_ids == ["id"]

    rowid_ids = get_table_identifiers(edit_db, "no_pk_table")
    assert rowid_ids == ["rowid"]


def test_insert_record(edit_db: DatabaseConnection) -> None:
    insert_record(edit_db, "products", {"name": "Gadget", "price": 19.99})
    _, rows = get_table_data(edit_db, "products", limit=10, offset=0)
    assert len(rows) == 2
    assert rows[1][1] == "Gadget"
    assert rows[1][2] == 19.99


def test_update_record(edit_db: DatabaseConnection) -> None:
    update_record(
        edit_db,
        "products",
        id_dict={"id": 1},
        set_dict={"name": "Super Widget", "price": 12.99},
    )
    _, rows = get_table_data(edit_db, "products", limit=10, offset=0)
    assert len(rows) == 1
    assert rows[0][1] == "Super Widget"
    assert rows[0][2] == 12.99


def test_delete_record(edit_db: DatabaseConnection) -> None:
    delete_record(edit_db, "products", id_dict={"id": 1})
    _, rows = get_table_data(edit_db, "products", limit=10, offset=0)
    assert len(rows) == 0


def test_edit_read_only_rejection(temp_db_path: Path) -> None:
    db = DatabaseConnection()
    db.open(temp_db_path, read_only=True)
    try:
        with pytest.raises(PermissionError):
            insert_record(db, "test_table", {"name": "fail"})
    finally:
        db.close()
