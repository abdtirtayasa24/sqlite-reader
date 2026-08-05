import sqlite3
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_db_path() -> Generator[Path, None, None]:
    """Provides a path to a temporary SQLite database."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as f:
        db_path = Path(f.name)

    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
    conn.commit()
    conn.close()

    yield db_path

    if db_path.exists():
        db_path.unlink()
