import re
from enum import Enum, auto


class StatementType(Enum):
    READ_ONLY = auto()
    MUTATION = auto()
    SCHEMA = auto()
    MAINTENANCE = auto()
    TRANSACTION = auto()
    UNKNOWN = auto()


def strip_comments_and_whitespace(sql: str) -> str:
    """Strips leading SQL comments (-- and /* */) and whitespace."""
    s = sql.strip()
    while True:
        if s.startswith("--"):
            nl = s.find("\n")
            if nl == -1:
                return ""
            s = s[nl + 1 :].strip()
        elif s.startswith("/*"):
            end_comment = s.find("*/")
            if end_comment == -1:
                return ""
            s = s[end_comment + 2 :].strip()
        else:
            break
    return s


def classify_statement(sql: str) -> StatementType:
    """Classifies a SQL statement based on its initial keyword."""
    clean_sql = strip_comments_and_whitespace(sql)
    if not clean_sql:
        return StatementType.UNKNOWN

    first_word = clean_sql.split()[0].upper()

    if first_word in ("SELECT", "EXPLAIN", "WITH", "PRAGMA"):
        return StatementType.READ_ONLY
    elif first_word in ("INSERT", "UPDATE", "DELETE", "REPLACE"):
        return StatementType.MUTATION
    elif first_word in ("CREATE", "ALTER", "DROP"):
        return StatementType.SCHEMA
    elif first_word in ("VACUUM", "ANALYZE", "REINDEX"):
        return StatementType.MAINTENANCE
    elif first_word in ("BEGIN", "COMMIT", "ROLLBACK", "END"):
        return StatementType.TRANSACTION
    else:
        return StatementType.UNKNOWN


def has_missing_where_clause(sql: str) -> bool:
    """
    Checks if an UPDATE or DELETE statement is missing a WHERE clause.
    This serves as a safety heuristic for unfiltered mutations.
    """
    clean_sql = strip_comments_and_whitespace(sql)
    if not clean_sql:
        return False

    first_word = clean_sql.split()[0].upper()
    return bool(
        first_word in ("UPDATE", "DELETE")
        and not re.search(r"\bWHERE\b", clean_sql, re.IGNORECASE)
    )
