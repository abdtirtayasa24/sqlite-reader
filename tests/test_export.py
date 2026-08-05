import csv
from collections.abc import Generator
from pathlib import Path

import pytest

from sqlite_reader.database import DatabaseConnection
from sqlite_reader.export import export_query_to_csv, export_to_csv


@pytest.fixture
def export_db(temp_db_path: Path) -> Generator[DatabaseConnection, None, None]:
    db = DatabaseConnection()
    db.open(temp_db_path, read_only=False)

    db.execute("""
        CREATE TABLE export_test (
            id INTEGER PRIMARY KEY,
            name TEXT,
            notes TEXT,
            data BLOB
        )
    """)

    db.execute(
        "INSERT INTO export_test VALUES (1, 'Alice, B.', 'Line 1\nLine 2', NULL)"
    )
    db.execute(
        "INSERT INTO export_test VALUES (2, 'Bob \"The Builder\"', 'Normal', ?)",
        (b"binary_data",),
    )
    db.commit()
    yield db
    db.close()


def test_export_to_csv(tmp_path: Path) -> None:
    csv_file = tmp_path / "test_out.csv"
    cols = ["id", "name", "notes"]
    rows = [[1, "Alice, B.", "Line 1\nLine 2"], [2, None, "Value"]]

    export_to_csv(cols, rows, csv_file, null_value="[NULL]")

    assert csv_file.exists()
    with open(csv_file, "r", encoding="utf-8-sig", newline="") as f:
        reader = list(csv.reader(f))
        assert reader[0] == ["id", "name", "notes"]
        assert reader[1] == ["1", "Alice, B.", "Line 1\nLine 2"]
        assert reader[2] == ["2", "[NULL]", "Value"]


def test_export_query_to_csv(export_db: DatabaseConnection, tmp_path: Path) -> None:
    csv_file = tmp_path / "query_out.csv"
    count = export_query_to_csv(export_db, "SELECT * FROM export_test", csv_file)

    assert count == 2
    assert csv_file.exists()
    with open(csv_file, "r", encoding="utf-8-sig", newline="") as f:
        reader = list(csv.reader(f))
        assert reader[0] == ["id", "name", "notes", "data"]
        assert reader[1][1] == "Alice, B."
        assert reader[2][3] == "<BLOB: 11 bytes>"


def test_database_backup(export_db: DatabaseConnection, tmp_path: Path) -> None:
    backup_path = tmp_path / "backup.sqlite3"
    export_db.backup(backup_path)

    assert backup_path.exists()

    backup_db = DatabaseConnection()
    backup_db.open(backup_path, read_only=True)
    try:
        cursor = backup_db.execute("SELECT COUNT(*) FROM export_test")
        assert cursor.fetchone()[0] == 2
    finally:
        backup_db.close()
