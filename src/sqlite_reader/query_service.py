import sqlite3
import time
from typing import Any

from sqlite_reader.database import DatabaseConnection
from sqlite_reader.models import QueryResult
from sqlite_reader.schema import get_table_columns, quote_identifier
from sqlite_reader.validation import StatementType, classify_statement


def get_table_identifiers(db: DatabaseConnection, table_name: str) -> list[str]:
    """
    Returns list of column names that uniquely identify a row.
    Returns declared PK columns if available, else ['rowid'] if supported, else [].
    """
    columns = get_table_columns(db, table_name)
    pk_cols = [
        col.name for col in sorted([c for c in columns if c.pk > 0], key=lambda x: x.pk)
    ]
    if pk_cols:
        return pk_cols

    try:
        quoted = quote_identifier(table_name)
        db.execute(f"SELECT rowid FROM {quoted} LIMIT 0")
        return ["rowid"]
    except (sqlite3.Error, RuntimeError):
        return []


def get_table_count(db: DatabaseConnection, table_name: str) -> int:
    """Returns the total number of rows in a table or view."""
    quoted = quote_identifier(table_name)
    cursor = db.execute(f"SELECT COUNT(*) FROM {quoted}")
    row = cursor.fetchone()
    return row[0] if row else 0


def get_table_data(
    db: DatabaseConnection, table_name: str, limit: int, offset: int
) -> tuple[list[str], list[tuple[Any, ...]]]:
    """
    Retrieves paginated rows from a table.
    Attempts to order by primary key for stable pagination.
    """
    quoted = quote_identifier(table_name)
    columns = get_table_columns(db, table_name)

    pk_cols = [col.name for col in columns if col.pk]
    identifiers = get_table_identifiers(db, table_name)

    select_clause = "*"
    if not pk_cols and "rowid" in identifiers:
        select_clause = "rowid AS _rowid_, *"

    order_clause = ""
    if pk_cols:
        order_cols = ", ".join(quote_identifier(c) for c in pk_cols)
        order_clause = f"ORDER BY {order_cols}"
    elif "rowid" in identifiers:
        order_clause = "ORDER BY rowid"

    sql = f"SELECT {select_clause} FROM {quoted} {order_clause} LIMIT ? OFFSET ?"
    cursor = db.execute(sql, (limit, offset))

    col_names = [desc[0] for desc in cursor.description] if cursor.description else []
    rows = [tuple(row) for row in cursor.fetchall()]

    return col_names, rows


def execute_user_query(
    db: DatabaseConnection, sql: str, display_limit: int = 1000
) -> QueryResult:
    """
    Executes a single SQL statement provided by the user and returns structured results.
    Uses display_limit + 1 to detect result truncation without fetching excessive memory.
    """
    stripped_sql = sql.strip()
    if not stripped_sql:
        raise ValueError("SQL statement cannot be empty.")

    stmt_type = classify_statement(stripped_sql)

    if db.is_read_only and stmt_type in (
        StatementType.MUTATION,
        StatementType.SCHEMA,
        StatementType.MAINTENANCE,
    ):
        raise PermissionError(
            "Cannot execute mutating or schema statement on a read-only database connection."
        )

    is_mutation = stmt_type in (StatementType.MUTATION, StatementType.SCHEMA)
    start_time = time.perf_counter()

    try:
        cursor = db.execute(stripped_sql)
        if is_mutation:
            db.commit()
    except (sqlite3.Error, ValueError, RuntimeError, PermissionError):
        if is_mutation:
            db.rollback()
        raise

    execution_time_ms = (time.perf_counter() - start_time) * 1000.0

    if cursor.description:
        columns = tuple(desc[0] for desc in cursor.description)
        fetched_rows = cursor.fetchmany(display_limit + 1)
        truncated = len(fetched_rows) > display_limit
        rows = tuple(tuple(row) for row in fetched_rows[:display_limit])
        affected_rows = -1
        message = (
            f"Returned {len(rows)} row(s)"
            + (" (truncated at limit)" if truncated else "")
            + f" in {execution_time_ms:.2f} ms"
        )
    else:
        columns = ()
        rows = ()
        affected_rows = cursor.rowcount
        truncated = False
        message = f"Query executed successfully. Affected rows: {affected_rows} in {execution_time_ms:.2f} ms"

    return QueryResult(
        columns=columns,
        rows=rows,
        affected_rows=affected_rows,
        execution_time_ms=execution_time_ms,
        truncated=truncated,
        message=message,
    )


def insert_record(
    db: DatabaseConnection, table_name: str, row_dict: dict[str, Any]
) -> None:
    """Inserts a new record into table_name using parameterized query."""
    if db.is_read_only:
        raise PermissionError("Cannot insert record in read-only mode.")
    if not row_dict:
        raise ValueError("No column values provided for insert.")

    quoted_table = quote_identifier(table_name)
    col_names = [quote_identifier(k) for k in row_dict]
    placeholders = [
        f"cast(? as {get_blob_cast(v)})" if isinstance(v, bytes) else "?"
        for v in row_dict.values()
    ]

    sql = f"INSERT INTO {quoted_table} ({', '.join(col_names)}) VALUES ({', '.join(placeholders)})"
    try:
        db.execute(sql, tuple(row_dict.values()))
        db.commit()
    except (sqlite3.Error, RuntimeError):
        db.rollback()
        raise


def update_record(
    db: DatabaseConnection,
    table_name: str,
    id_dict: dict[str, Any],
    set_dict: dict[str, Any],
) -> None:
    """Updates a record identified by id_dict in table_name using parameterized query."""
    if db.is_read_only:
        raise PermissionError("Cannot update record in read-only mode.")
    if not id_dict:
        raise ValueError("Record identification required for update.")
    if not set_dict:
        raise ValueError("No changes specified for update.")

    quoted_table = quote_identifier(table_name)
    set_clauses = [f"{quote_identifier(k)} = ?" for k in set_dict]
    where_clauses = [f"{quote_identifier(k)} = ?" for k in id_dict]

    sql = f"UPDATE {quoted_table} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
    params = tuple(set_dict.values()) + tuple(id_dict.values())

    try:
        db.execute(sql, params)
        db.commit()
    except (sqlite3.Error, RuntimeError):
        db.rollback()
        raise


def delete_record(
    db: DatabaseConnection, table_name: str, id_dict: dict[str, Any]
) -> None:
    """Deletes a record identified by id_dict from table_name using parameterized query."""
    if db.is_read_only:
        raise PermissionError("Cannot delete record in read-only mode.")
    if not id_dict:
        raise ValueError("Record identification required for deletion.")

    quoted_table = quote_identifier(table_name)
    where_clauses = [f"{quote_identifier(k)} = ?" for k in id_dict]
    sql = f"DELETE FROM {quoted_table} WHERE {' AND '.join(where_clauses)}"

    try:
        db.execute(sql, tuple(id_dict.values()))
        db.commit()
    except (sqlite3.Error, RuntimeError):
        db.rollback()
        raise


def get_blob_cast(val: Any) -> str:
    return "BLOB" if isinstance(val, bytes) else "TEXT"
