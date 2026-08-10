import sqlite3
import threading
import time
from collections.abc import Generator
from pathlib import Path

import pytest

from sqlite_reader.database import DatabaseConnection
from sqlite_reader.query_service import execute_user_query


@pytest.fixture
def slow_db(temp_db_path: Path) -> Generator[DatabaseConnection, None, None]:
    db = DatabaseConnection()
    db.open(temp_db_path, read_only=False)
    yield db
    db.close()


def test_query_interruption(slow_db: DatabaseConnection) -> None:
    # Heavy recursive CTE query that runs for a long time
    heavy_sql = """
        WITH RECURSIVE cnt(x) AS (
            SELECT 1
            UNION ALL
            SELECT x+1 FROM cnt WHERE x < 100000000
        )
        SELECT COUNT(*) FROM cnt;
    """

    exception_raised = []
    started_event = threading.Event()

    def worker() -> None:
        try:
            started_event.set()
            execute_user_query(slow_db, heavy_sql)
        except sqlite3.OperationalError as e:
            exception_raised.append(e)

    t = threading.Thread(target=worker)
    t.start()

    # Wait for the worker thread to signal it has started
    started_event.wait(timeout=2.0)

    # Give SQLite a moment to enter the execution engine
    time.sleep(0.2)

    # Trigger cancellation from main thread
    slow_db.interrupt()
    t.join(timeout=5.0)

    assert not t.is_alive(), "Worker thread did not terminate in time after interrupt"
    assert len(exception_raised) == 1, f"Expected 1 exception, got {len(exception_raised)}"
    assert "interrupted" in str(exception_raised[0]).lower()
