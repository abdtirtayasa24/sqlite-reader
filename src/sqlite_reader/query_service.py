from typing import Any

from sqlite_reader.database import DatabaseConnection
from sqlite_reader.schema import get_table_columns, quote_identifier


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
    order_clause = ""
    if pk_cols:
        order_clause = ", ".join(quote_identifier(c) for c in pk_cols)
        order_clause = f"ORDER BY {order_clause}"

    sql = f"SELECT * FROM {quoted} {order_clause} LIMIT ? OFFSET ?"
    cursor = db.execute(sql, (limit, offset))

    col_names = [desc[0] for desc in cursor.description] if cursor.description else []
    rows = [tuple(row) for row in cursor.fetchall()]

    return col_names, rows
