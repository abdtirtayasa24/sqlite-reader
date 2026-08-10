import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import Any


class SqlEditor(ttk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        on_execute: Callable[[str], None],
        on_cancel: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.on_execute = on_execute
        self.on_cancel = on_cancel
        self.is_running = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=(0, 2))

        lbl_title = ttk.Label(toolbar, text="SQL Query Editor", font=("", 9, "bold"))
        lbl_title.pack(side=tk.LEFT, padx=5)

        self.btn_execute = ttk.Button(
            toolbar, text="Execute (Ctrl+Enter)", command=self._execute_sql
        )
        self.btn_execute.pack(side=tk.RIGHT, padx=2)

        self.btn_cancel = ttk.Button(
            toolbar, text="⏹️ Cancel", command=self._cancel_sql, state="disabled"
        )
        self.btn_cancel.pack(side=tk.RIGHT, padx=2)

        btn_clear = ttk.Button(toolbar, text="Clear", command=self.clear)
        btn_clear.pack(side=tk.RIGHT, padx=2)

        # Multiline SQL Text Box
        self.text_area = tk.Text(self, height=6, wrap=tk.NONE, font=("Consolas", 10))
        self.text_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Scrollbars for SQL text box
        vsb = ttk.Scrollbar(
            self.text_area, orient="vertical", command=self.text_area.yview
        )
        hsb = ttk.Scrollbar(
            self.text_area, orient="horizontal", command=self.text_area.xview
        )
        self.text_area.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Bind Ctrl+Enter shortcut
        self.text_area.bind("<Control-Return>", self._execute_sql_event)

    def set_running_state(self, is_running: bool) -> None:
        """Enables/disables buttons depending on whether a query is executing."""
        self.is_running = is_running
        if is_running:
            self.btn_execute.state(["disabled"])
            self.btn_cancel.state(["!disabled"])
        else:
            self.btn_execute.state(["!disabled"])
            self.btn_cancel.state(["disabled"])

    def set_sql(self, sql: str) -> None:
        """Sets the text in the SQL editor."""
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, sql)

    def get_sql(self) -> str:
        """Returns the current SQL text."""
        return self.text_area.get("1.0", tk.END).strip()

    def clear(self) -> None:
        """Clears the editor."""
        if not self.is_running:
            self.text_area.delete("1.0", tk.END)

    def _execute_sql(self) -> None:
        """Triggered by the Execute button."""
        if not self.is_running:
            sql = self.get_sql()
            if sql:
                self.on_execute(sql)

    def _execute_sql_event(self, event: Any) -> str:
        """Triggered by Ctrl+Enter. Returns 'break' to prevent newline insertion."""
        self._execute_sql()
        return "break"

    def _cancel_sql(self) -> None:
        if self.is_running and self.on_cancel:
            self.on_cancel()
