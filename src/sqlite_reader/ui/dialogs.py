import tkinter as tk
from functools import partial
from tkinter import messagebox, ttk
from typing import Any

from sqlite_reader.models import ColumnInfo
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
    return messagebox.askyesno(f"Confirm {action_name} Operation", msg, parent=parent)


class RecordFormDialog(tk.Toplevel):
    """Dialog form for inserting or editing a table row."""

    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        columns: list[ColumnInfo],
        initial_values: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title(title)
        self.resizable(True, True)
        self.result: dict[str, Any] | None = None
        self.columns = columns
        self.initial_values = initial_values or {}

        self.entries: dict[str, ttk.Entry] = {}
        self.null_vars: dict[str, tk.BooleanVar] = {}

        self._setup_ui()
        self.grab_set()
        self.focus_set()
        parent.wait_window(self)

    def _setup_ui(self) -> None:
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        canvas = tk.Canvas(main_frame, borderwidth=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        for row_idx, col in enumerate(self.columns):
            col_label = f"{col.name} ({col.type or 'TEXT'}):"
            lbl = ttk.Label(scrollable_frame, text=col_label, font=("", 9, "bold"))
            lbl.grid(row=row_idx, column=0, sticky=tk.W, pady=3, padx=5)
            
            val = self.initial_values.get(col.name)
            is_null = val is None
            
            null_var = tk.BooleanVar(value=is_null)
            self.null_vars[col.name] = null_var
            
            entry = ttk.Entry(scrollable_frame, width=35)
            if not is_null and val is not None:
                entry.insert(0, str(val))
            entry.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
            self.entries[col.name] = entry
            
            chk_null = ttk.Checkbutton(
                scrollable_frame, 
                text="NULL", 
                variable=null_var,
                command=partial(self._toggle_null, col.name)
            )
            chk_null.grid(row=row_idx, column=2, sticky=tk.W, pady=3, padx=5)
            
            if is_null:
                entry.state(["disabled"])
            
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action Buttons
        btn_frame = ttk.Frame(self, padding=5)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        btn_save = ttk.Button(btn_frame, text="Save", command=self._on_save)
        btn_save.pack(side=tk.RIGHT, padx=5)
        
        btn_cancel = ttk.Button(btn_frame, text="Cancel", command=self.destroy)
        btn_cancel.pack(side=tk.RIGHT, padx=5)

    def _toggle_null(self, col_name: str) -> None:
        if self.null_vars[col_name].get():
            self.entries[col_name].delete(0, tk.END)
            self.entries[col_name].state(["disabled"])
        else:
            self.entries[col_name].state(["!disabled"])

    def _on_save(self) -> None:
        res: dict[str, Any] = {}
        for col in self.columns:
            name = col.name
            if self.null_vars[name].get():
                res[name] = None
            else:
                str_val = self.entries[name].get()
                res[name] = self._parse_val(str_val, col.type)
        self.result = res
        self.destroy()

    @staticmethod
    def _parse_val(val_str: str, col_type: str) -> Any:
        col_type_upper = (col_type or "").upper()
        if "INT" in col_type_upper:
            try:
                return int(val_str)
            except ValueError:
                return val_str
        elif (
            "REAL" in col_type_upper
            or "FLOAT" in col_type_upper
            or "DOUBLE" in col_type_upper
        ):
            try:
                return float(val_str)
            except ValueError:
                return val_str
        return val_str
