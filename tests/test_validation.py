from sqlite_reader.validation import (
    StatementType,
    classify_statement,
    has_missing_where_clause,
    strip_comments_and_whitespace,
)


def test_strip_comments_and_whitespace() -> None:
    assert strip_comments_and_whitespace("   SELECT * FROM x") == "SELECT * FROM x"
    assert (
        strip_comments_and_whitespace("-- comment\nSELECT * FROM x")
        == "SELECT * FROM x"
    )
    assert (
        strip_comments_and_whitespace("/* multiline \n comment */ DELETE FROM x")
        == "DELETE FROM x"
    )


def test_classify_statement() -> None:
    assert classify_statement("SELECT * FROM x") == StatementType.READ_ONLY
    assert classify_statement("EXPLAIN QUERY PLAN SELECT 1") == StatementType.READ_ONLY
    assert classify_statement("PRAGMA foreign_keys") == StatementType.READ_ONLY

    assert classify_statement("INSERT INTO x VALUES (1)") == StatementType.MUTATION
    assert classify_statement("UPDATE x SET a = 1") == StatementType.MUTATION
    assert classify_statement("DELETE FROM x") == StatementType.MUTATION

    assert classify_statement("CREATE TABLE x (id INT)") == StatementType.SCHEMA
    assert classify_statement("DROP TABLE x") == StatementType.SCHEMA

    assert classify_statement("VACUUM") == StatementType.MAINTENANCE
    assert classify_statement("BEGIN TRANSACTION") == StatementType.TRANSACTION


def test_has_missing_where_clause() -> None:
    # Unfiltered mutations
    assert has_missing_where_clause("UPDATE users SET is_active = 0") is True
    assert has_missing_where_clause("DELETE FROM users") is True
    assert has_missing_where_clause("-- comment\nUPDATE users SET name = 'a'") is True

    # Filtered mutations
    assert (
        has_missing_where_clause("UPDATE users SET is_active = 0 WHERE id = 1") is False
    )
    assert has_missing_where_clause("DELETE FROM users WHERE id > 10") is False

    # Non-mutations
    assert has_missing_where_clause("SELECT * FROM users") is False
