import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from sqlite_reader.database import DatabaseConnection
from sqlite_reader.models import QueryResult
from sqlite_reader.query_service import (
    delete_record,
    get_table_count,
    get_table_data,
    get_table_identifiers,
    insert_record,
    update_record,
)
from sqlite_reader.schema import get_table_columns
from sqlite_reader.ui.dialogs import RecordFormDialog


class ResultGrid(ttk.Frame):
    def __init__(self, parent: tk.Widget, db: DatabaseConnection) -> None:
        super().__init__(parent)
        self.db = db
        self.current_table: str | None = None
        self.limit = 1000
        self.offset = 0
        self.total_rows = 0
        self.current_cols: list[str] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        # Toolbar for data actions
        self.action_bar = ttk.Frame(self)
        self.action_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 2))

        self.btn_insert = ttk.Button(
            self.action_bar,
            text="+ Insert Row",
            command=self._insert_row,
            state="disabled",
        )
        self.btn_insert.pack(side=tk.LEFT, padx=2)

        self.btn_edit = ttk.Button(
            self.action_bar,
            text="✏️ Edit Selected",
            command=self._edit_selected,
            state="disabled",
        )
        self.btn_edit.pack(side=tk.LEFT, padx=2)

        self.btn_delete = ttk.Button(
            self.action_bar,
            text="🗑️ Delete Selected",
            command=self._delete_selected,
            state="disabled",
        )
        self.btn_delete.pack(side=tk.LEFT, padx=2)

        # Grid Treeview
        self.tree = ttk.Treeview(self, show="headings")
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        # Scrollbars
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Layout grid
        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # Pagination controls
        ctrl_frame = ttk.Frame(self)
        ctrl_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5, padx=5)

        self.btn_prev = ttk.Button(
            ctrl_frame, text="< Prev", command=self._prev_page, state="disabled"
        )
        self.btn_prev.pack(side=tk.LEFT, padx=5)

        self.lbl_page = ttk.Label(ctrl_frame, text="Page 1")
        self.lbl_page.pack(side=tk.LEFT, padx=5)

        self.btn_next = ttk.Button(
            ctrl_frame, text="Next >", command=self._next_page, state="disabled"
        )
        self.btn_next.pack(side=tk.LEFT, padx=5)

        self.lbl_info = ttk.Label(ctrl_frame, text="")
        self.lbl_info.pack(side=tk.RIGHT, padx=5)

    def load_table(self, table_name: str) -> None:
        """Loads the first page of the specified table."""
        self.current_table = table_name
        self.offset = 0
        try:
            self.total_rows = get_table_count(self.db, table_name)
        except (sqlite3.Error, RuntimeError):
            self.total_rows = -1

        self._update_action_buttons()
        self._fetch_table_data()

    def display_query_result(self, result: QueryResult) -> None:
        """Displays arbitrary SQL execution results."""
        self.current_table = None
        self._update_action_buttons()
        self.tree.delete(*self.tree.get_children())

        if result.columns:
            self._update_grid(list(result.columns), list(result.rows))
        else:
            self.tree["columns"] = ("Status",)
            self.tree.heading("Status", text="Execution Status")
            self.tree.insert("", tk.END, values=(result.message,))

        self.btn_prev.state(["disabled"])
        self.btn_next.state(["disabled"])
        self.lbl_page.config(text="Query Result")
        self.lbl_info.config(text=result.message)

    def display_error(self, message: str) -> None:
        """Displays an execution error in the grid."""
        self.current_table = None
        self._update_action_buttons()
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = ("Error",)
        self.tree.heading("Error", text="SQL Error")
        self.tree.insert("", tk.END, values=(message,))

        self.btn_prev.state(["disabled"])
        self.btn_next.state(["disabled"])
        self.lbl_page.config(text="Error")
        self.lbl_info.config(text=message)

    def clear(self) -> None:
        """Clears the grid and resets state."""
        self.current_table = None
        self._update_action_buttons()
        self.tree.delete(*self.tree.get_children())
        self.lbl_page.config(text="Page 1")
        self.lbl_info.config(text="")
        self.btn_prev.state(["disabled"])
        self.btn_next.state(["disabled"])

    def _fetch_table_data(self) -> None:
        if not self.current_table or not self.db.db_path:
            return

        try:
            cols, rows = get_table_data(
                self.db, self.current_table, self.limit, self.offset
            )
            self._update_grid(cols, rows)
            self._update_controls(len(rows))
        except (sqlite3.Error, RuntimeError) as e:
            self.display_error(str(e))

    def _update_grid(self, cols: list[str], rows: list[tuple[Any, ...]]) -> None:
        self.current_cols = cols
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = cols

        for col in cols:
            self.tree.heading(col, text=col)
            if col == "_rowid_":
                self.tree.column(col, width=50, anchor=tk.CENTER)
            else:
                self.tree.column(col, width=120, anchor=tk.W)

        for row in rows:
            formatted_row = []
            for val in row:
                if val is None:
                    formatted_row.append("NULL")
                elif isinstance(val, bytes):
                    formatted_row.append(f"<BLOB: {len(val)} bytes>")
                else:
                    str_val = str(val)
                    if len(str_val) > 2000:
                        str_val = str_val[:2000] + "..."
                    formatted_row.append(str_val)
            self.tree.insert("", tk.END, values=formatted_row)

    def _on_row_select(self, event: Any) -> None:
        selection = self.tree.selection()
        if selection and self.current_table and not self.db.is_read_only:
            self.btn_edit.state(["!disabled"])
            self.btn_delete.state(["!disabled"])
        else:
            self.btn_edit.state(["disabled"])
            self.btn_delete.state(["disabled"])

    def _update_action_buttons(self) -> None:
        if self.current_table and not self.db.is_read_only:
            self.btn_insert.state(["!disabled"])
        else:
            self.btn_insert.state(["disabled"])
            self.btn_edit.state(["disabled"])
            self.btn_delete.state(["disabled"])

    def _insert_row(self) -> None:
        if not self.current_table or self.db.is_read_only:
            return

        columns = get_table_columns(self.db, self.current_table)
        dlg = RecordFormDialog(self, f"Insert into {self.current_table}", columns)

        if dlg.result is not None:
            try:
                insert_record(self.db, self.current_table, dlg.result)
                self.load_table(self.current_table)
            except (sqlite3.Error, PermissionError, ValueError, RuntimeError) as e:
                messagebox.showerror("Insert Error", str(e), parent=self)

    def _edit_selected(self) -> None:
        if not self.current_table or self.db.is_read_only:
            return

        selection = self.tree.selection()
        if not selection:
            return

        selected_item = self.tree.item(selection[0])
        values = selected_item["values"]

        if not values or len(values) != len(self.current_cols):
            return

        row_dict = dict(zip(self.current_cols, values))
        identifiers = get_table_identifiers(self.db, self.current_table)

        if not identifiers:
            messagebox.showwarning(
                "Cannot Edit Row",
                "This table has no primary key or rowid identifier to target single rows safely.",
                parent=self,
            )
            return

        id_dict: dict[str, Any] = {}
        for id_col in identifiers:
            col_key = (
                "_rowid_" if id_col == "rowid" and "_rowid_" in row_dict else id_col
            )
            if col_key in row_dict:
                id_dict[id_col] = row_dict[col_key]

        columns = get_table_columns(self.db, self.current_table)
        dlg = RecordFormDialog(
            self, f"Edit Row in {self.current_table}", columns, initial_values=row_dict
        )

        if dlg.result is not None:
            try:
                update_record(self.db, self.current_table, id_dict, dlg.result)
                self.load_table(self.current_table)
            except (sqlite3.Error, PermissionError, ValueError, RuntimeError) as e:
                messagebox.showerror("Update Error", str(e), parent=self)

    def _delete_selected(self) -> None:
        if not self.current_table or self.db.is_read_only:
            return

        selection = self.tree.selection()
        if not selection:
            return

        selected_item = self.tree.item(selection[0])
        values = selected_item["values"]
        if not values or len(values) != len(self.current_cols):
            return

        row_dict = dict(zip(self.current_cols, values))
        identifiers = get_table_identifiers(self.db, self.current_table)

        if not identifiers:
            messagebox.showwarning(
                "Cannot Delete Row",
                "This table has no primary key or rowid identifier to target single rows safely.",
                parent=self,
            )
            return

        id_dict: dict[str, Any] = {}
        for id_col in identifiers:
            col_key = (
                "_rowid_" if id_col == "rowid" and "_rowid_" in row_dict else id_col
            )
            if col_key in row_dict:
                id_dict[id_col] = row_dict[col_key]

        if messagebox.askyesno(
            "Confirm Delete",
            f"Delete selected record from '{self.current_table}'?",
            parent=self,
        ):
            try:
                delete_record(self.db, self.current_table, id_dict)
                self.load_table(self.current_table)
            except (sqlite3.Error, PermissionError, ValueError, RuntimeError) as e:
                messagebox.showerror("Delete Error", str(e), parent=self)

    def _prev_page(self) -> None:
        if self.current_table and self.offset >= self.limit:
            self.offset -= self.limit
            self._fetch_table_data()

    def _next_page(self) -> None:
        if self.current_table:
            self.offset += self.limit
            self._fetch_table_data()

    def _update_controls(self, fetched_count: int) -> None:
        self.btn_prev.state(["!disabled"] if self.offset > 0 else ["disabled"])
        has_more = fetched_count == self.limit
        self.btn_next.state(["!disabled"] if has_more else ["disabled"])

        page_num = (self.offset // self.limit) + 1
        self.lbl_page.config(text=f"Page {page_num}")

        count_text = (
            f"Total: {self.total_rows}" if self.total_rows >= 0 else "Total: Unknown"
        )
        self.lbl_info.config(text=count_text)
