import sqlite3
from pathlib import Path


def test_temp_db_fixture(temp_db_path: Path) -> None:
    """Verify that the temporary database fixture works and is accessible."""
    assert temp_db_path.exists()

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'")
    result = cursor.fetchone()
    conn.close()

    assert result is not None
    assert result[0] == "test_table"
