from sqlite_reader.database import DatabaseConnection
from sqlite_reader.models import ColumnInfo, SchemaObject


def quote_identifier(identifier: str) -> str:
    """Safely quotes an SQLite identifier (table name, column name, etc.)."""
    return '"' + identifier.replace('"', '""') + '"'


def get_schema_objects(db: DatabaseConnection) -> list[SchemaObject]:
    """Retrieves all tables, views, indexes, and triggers from the database."""
    sql = """
        SELECT name, type, sql
        FROM sqlite_schema
        WHERE name NOT LIKE 'sqlite_%'
        ORDER BY type, name;
    """
    cursor = db.execute(sql)
    return [
        SchemaObject(name=row["name"], type=row["type"], sql=row["sql"])
        for row in cursor.fetchall()
    ]


def get_table_columns(db: DatabaseConnection, table_name: str) -> list[ColumnInfo]:
    """Retrieves column definitions for a specific table or view."""
    quoted_name = quote_identifier(table_name)
    cursor = db.execute(f"PRAGMA table_info({quoted_name});")
    return [
        ColumnInfo(
            cid=row["cid"],
            name=row["name"],
            type=row["type"],
            notnull=row["notnull"],
            dflt_value=row["dflt_value"],
            pk=row["pk"],
        )
        for row in cursor.fetchall()
    ]
