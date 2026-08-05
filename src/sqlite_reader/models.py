from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnInfo:
    cid: int
    name: str
    type: str
    notnull: int
    dflt_value: str | None
    pk: int


@dataclass(frozen=True)
class SchemaObject:
    name: str
    type: str
    sql: str | None
