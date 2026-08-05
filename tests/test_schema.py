from collections.abc import Generator
from pathlib import Path

import pytest

from sqlite_reader.database import DatabaseConnection
from sqlite_reader.schema import get_schema_objects, get_table_columns, quote_identifier


@pytest.fixture
def schema_db(temp_db_path: Path) -> Generator[DatabaseConnection, None, None]:
    """Provides a database connection with various schema objects for testing."""
    db = DatabaseConnection()
    db.open(temp_db_path, read_only=False)

    # Create a table with various column types and constraints
    db.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    """)

    # Create a table with a weird name to test quoting
    db.execute('CREATE TABLE "weird "" name" (col1 TEXT)')

    # Create a view
    db.execute("CREATE VIEW active_users AS SELECT * FROM users WHERE is_active = 1")

    # Create an index
    db.execute("CREATE INDEX idx_users_username ON users(username)")

    # Create a trigger
    db.execute("""
        CREATE TRIGGER user_insert_trigger
        AFTER INSERT ON users
        BEGIN
            SELECT 1;
        END;
    """)

    db.commit()

    yield db

    # Close the connection so the temp file can be deleted on Windows
    db.close()


def test_quote_identifier() -> None:
    assert quote_identifier("users") == '"users"'
    assert quote_identifier('weird " name') == '"weird "" name"'


def test_get_schema_objects(schema_db: DatabaseConnection) -> None:
    objects = get_schema_objects(schema_db)

    # We expect: test_table (from conftest), users, weird " name, active_users, idx_users_username, user_insert_trigger
    names = {obj.name for obj in objects}

    assert "users" in names
    assert "active_users" in names
    assert "idx_users_username" in names
    assert "user_insert_trigger" in names
    assert 'weird " name' in names

    # Verify types
    users_table = next(obj for obj in objects if obj.name == "users")
    assert users_table.type == "table"
    assert users_table.sql is not None
    assert "CREATE TABLE users" in users_table.sql


def test_get_table_columns(schema_db: DatabaseConnection) -> None:
    columns = get_table_columns(schema_db, "users")

    assert len(columns) == 3

    id_col = next(col for col in columns if col.name == "id")
    assert id_col.type == "INTEGER"
    assert id_col.pk == 1

    username_col = next(col for col in columns if col.name == "username")
    assert username_col.type == "TEXT"
    assert username_col.notnull == 1
    assert username_col.pk == 0

    # Test quoting works on the weird table
    weird_columns = get_table_columns(schema_db, 'weird " name')
    assert len(weird_columns) == 1
    assert weird_columns[0].name == "col1"
