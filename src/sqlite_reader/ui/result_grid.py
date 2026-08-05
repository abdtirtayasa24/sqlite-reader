import tkinter as tk
from tkinter import ttk
from typing import Any

from sqlite_reader.database import DatabaseConnection
from sqlite_reader.query_service import get_table_count, get_table_data


class ResultGrid(ttk.Frame):
    def __init__(self, parent: tk.Widget, db: DatabaseConnection) -> None:
        super().__init__(parent)
        self.db = db
        self.current_table: str | None = None
        self.limit = 1000
        self.offset = 0
        self.total_rows = 0
        self._setup_ui()

    def _setup_ui(self) -> None:
        # Treeview for data
        self.tree = ttk.Treeview(self, show="headings")

        # Scrollbars
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Layout grid
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
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

        self.lbl_count = ttk.Label(ctrl_frame, text="Total: 0")
        self.lbl_count.pack(side=tk.RIGHT, padx=5)

    def load_table(self, table_name: str) -> None:
        """Loads the first page of the specified table."""
        self.current_table = table_name
        self.offset = 0
        try:
            self.total_rows = get_table_count(self.db, table_name)
        except Exception:
            self.total_rows = -1

        self._fetch_data()

    def clear(self) -> None:
        """Clears the grid and resets state."""
        self.current_table = None
        self.tree.delete(*self.tree.get_children())
        self.lbl_page.config(text="Page 1")
        self.lbl_count.config(text="Total: 0")
        self.btn_prev.state(["disabled"])
        self.btn_next.state(["disabled"])

    def _fetch_data(self) -> None:
        if not self.current_table or not self.db.db_path:
            return

        try:
            cols, rows = get_table_data(
                self.db, self.current_table, self.limit, self.offset
            )
            self._update_grid(cols, rows)
            self._update_controls(len(rows))
        except Exception as e:
            self.clear()
            self.tree["columns"] = ("Error",)
            self.tree.heading("Error", text="Error")
            self.tree.insert("", tk.END, values=(str(e),))

    def _update_grid(self, cols: list[str], rows: list[tuple[Any, ...]]) -> None:
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = cols

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor=tk.W)

        for row in rows:
            formatted_row = []
            for val in row:
                if val is None:
                    formatted_row.append("NULL")
                elif isinstance(val, bytes):
                    formatted_row.append(f"<BLOB: {len(val)} bytes")
                else:
                    str_val = str(val)
                    if len(str_val) > 2000:
                        str_val = str_val[:2000] + "..."
                    formatted_row.append(str_val)
            self.tree.insert("", tk.END, values=formatted_row)

    def _prev_page(self) -> None:
        if self.offset >= self.limit:
            self.offset -= self.limit
            self._fetch_data()

    def _next_page(self) -> None:
        self.offset += self.limit
        self._fetch_data()

    def _update_controls(self, fetched_count: int) -> None:
        self.btn_prev.state(["!disabled"] if self.offset > 0 else ["disabled"])

        has_more = fetched_count == self.limit
        self.btn_next.state(["!disabled"] if has_more else ["disabled"])

        page_num = (self.offset // self.limit) + 1
        self.lbl_page.config(text=f"Page {page_num}")

        count_text = (
            f"Total: {self.total_rows}" if self.total_rows >= 0 else "Total: Unknown"
        )
        self.lbl_count.config(text=count_text)
