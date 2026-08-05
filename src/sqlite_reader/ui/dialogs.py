import tkinter as tk
from tkinter import messagebox

from sqlite_reader.validation import StatementType, has_missing_where_clause


def confirm_mutation(
    parent: tk.Misc, sql: str, stmt_type: StatementType, db_name: str
) -> bool:
    """
    Displays a confirmation dialog before executing mutating SQL statements.
    Warns explicitly if an UPDATE or DELETE statement lacks a WHERE clause.
    """
    missing_where = has_missing_where_clause(sql)

    warning_prefix = ""
    if missing_where:
        warning_prefix = (
            "⚠️ CRITICAL WARNING: Unfiltered Mutation Detected!\n"
            "This statement has NO WHERE clause and will affect ALL rows in the table.\n\n"
        )

    action_name = stmt_type.name.title()
    snippet = sql[:300] + ("..." if len(sql) > 300 else "")

    msg = (
        f"{warning_prefix}"
        f"Are you sure you want to execute this {action_name} query on '{db_name}'?\n\n"
        f"Statement:\n{snippet}"
    )

    if missing_where:
        return messagebox.askyesno(
            "CRITICAL WARNING: Missing WHERE Clause", msg, icon="warning", parent=parent
        )
    else:
        return messagebox.askyesno(
            f"Confirm {action_name} Operation", msg, parent=parent
        )
