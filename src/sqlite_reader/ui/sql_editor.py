import tkinter as tk
from collections.abc import Callable
from tkinter import ttk


class SqlEditor(ttk.Frame):
    def __init__(self, parent: tk.Widget, on_execute: Callable[[str], None]) -> None:
        super().__init__(parent)
        self.on_execute = on_execute
        self._setup_ui()

    def _setup_ui(self) -> None:
        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=(0, 2))

        lbl_title = ttk.Label(toolbar, text="SQL Query Editor", font=("", 9, "bold"))
        lbl_title.pack(side=tk.LEFT, padx=5)

        btn_execute = ttk.Button(
            toolbar, text="Execute (Ctrl+Enter)", command=self._execute_sql
        )
        btn_execute.pack(side=tk.RIGHT, padx=5)

        btn_clear = ttk.Button(toolbar, text="Clear", command=self.clear)
        btn_clear.pack(side=tk.RIGHT, padx=5)

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
        self.text_area.bind("<Control-Return>", lambda e: self._execute_sql())

    def set_sql(self, sql: str) -> None:
        """Sets the text in the SQL editor."""
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, sql)

    def get_sql(self) -> str:
        """Returns the current SQL text."""
        return self.text_area.get("1.0", tk.END).strip()

    def clear(self) -> None:
        """Clears the editor."""
        self.text_area.delete("1.0", tk.END)

    def _execute_sql(self) -> str:
        sql = self.get_sql()
        if sql:
            self.on_execute(sql)
        return "break"
