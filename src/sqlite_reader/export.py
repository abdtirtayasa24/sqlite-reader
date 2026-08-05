import csv
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from sqlite_reader.database import DatabaseConnection


def export_to_csv(
    columns: Sequence[str],
    rows: Iterable[Sequence[Any]],
    file_path: Path,
    null_value: str = "",
    utf8_bom: bool = True,
) -> None:
    """
    Exports column headers and row sequences to a CSV file.
    Uses UTF-8 with BOM by default for Excel compatibility on Windows.
    """
    encoding = "utf-8-sig" if utf8_bom else "utf-8"

    with open(file_path, "w", newline="", encoding=encoding) as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(columns)

        for row in rows:
            formatted_row = []
            for val in row:
                if val is None:
                    formatted_row.append(null_value)
                elif isinstance(val, bytes):
                    formatted_row.append(f"<BLOB: {len(val)} bytes>")
                else:
                    formatted_row.append(val)
            writer.writerow(formatted_row)


def export_query_to_csv(
    db: DatabaseConnection,
    sql: str,
    file_path: Path,
    parameters: Sequence[Any] = (),
    null_value: str = "",
) -> int:
    """
    Executes a query and streams the result set directly to a CSV file in batches.
    Returns total row count exported.
    """
    cursor = db.execute(sql, parameters)
    if not cursor.description:
        return 0

    columns = [desc[0] for desc in cursor.description]
    count = 0

    with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(columns)

        while True:
            batch = cursor.fetchmany(1000)
            if not batch:
                break
            for row in batch:
                formatted_row = []
                for val in row:
                    if val is None:
                        formatted_row.append(null_value)
                    elif isinstance(val, bytes):
                        formatted_row.append(f"<BLOB: {len(val)} bytes>")
                    else:
                        formatted_row.append(val)
                writer.writerow(formatted_row)
                count += 1

    return count
