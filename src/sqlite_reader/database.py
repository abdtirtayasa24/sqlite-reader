import sqlite3
from collections.abc import Sequence
from pathlib import Path


class DatabaseConnection:
    def __init__(self) -> None:
        self._connection: sqlite3.Connection | None = None
        self.db_path: Path | None = None
        self.is_read_only: bool = True

    def open(self, path: Path, read_only: bool = True) -> None:
        """Opens a connection to the SQLite database."""
        if not path.exists():
            raise FileNotFoundError(f"Database file not found: {path}")

        self.close()

        try:
            if read_only:
                uri = f"{path.absolute().as_uri()}?mode=ro"
                self._connection = sqlite3.connect(uri, uri=True, check_same_thread=False)
            else:
                self._connection = sqlite3.connect(path, check_same_thread=False)

            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA busy_timeout = 5000")

            self.db_path = path
            self.is_read_only = read_only
        except sqlite3.Error as e:
            self._connection = None
            raise RuntimeError(f"Failed to open database: {e}") from e

    def close(self) -> None:
        """Closes the database connection if it is open."""
        if self._connection:
            self._connection.close()
            self._connection = None
            self.db_path = None
            self.is_read_only = True

    def interrupt(self) -> None:
        """Interrupts any currently executing query on this connection from another thread."""
        if self._connection:
            self._connection.interrupt()

    def execute(self, sql: str, parameters: Sequence[object] = ()) -> sqlite3.Cursor:
        """Executes a SQL statement and returns the cursor."""
        if not self._connection:
            raise RuntimeError("No database connection is open.")
        return self._connection.execute(sql, parameters)

    def commit(self) -> None:
        """Commits the current transaction."""
        if not self._connection:
            raise RuntimeError("No database connection is open.")
        self._connection.commit()

    def rollback(self) -> None:
        """Rolls back the current transaction."""
        if not self._connection:
            raise RuntimeError("No database connection is open.")
        self._connection.rollback()

    def backup(self, destination: Path) -> None:
        """
        Creates an online backup using SQLite's Backup API.
        Verifies the backup file using PRAGMA integrity_check.
        """
        if not self._connection or not self.db_path:
            raise RuntimeError("No database connection is open.")

        if destination.resolve() == self.db_path.resolve():
            raise ValueError(
                "Backup destination file cannot be the same as the source database."
            )

        dest_conn = sqlite3.connect(destination)
        try:
            with dest_conn:
                self._connection.backup(dest_conn)
        finally:
            dest_conn.close()

        verify_db = DatabaseConnection()
        try:
            verify_db.open(destination, read_only=True)
            cursor = verify_db.execute("PRAGMA integrity_check")
            res = cursor.fetchone()
            if not res or res[0] != "ok":
                raise RuntimeError(
                    f"Backup verification failed: {res[0] if res else 'Unknown error'}"
                )
        finally:
            verify_db.close()
