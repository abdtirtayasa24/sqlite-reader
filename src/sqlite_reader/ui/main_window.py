import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from sqlite_reader.database import DatabaseConnection
from sqlite_reader.query_service import execute_user_query
from sqlite_reader.schema import quote_identifier
from sqlite_reader.ui.dialogs import confirm_mutation
from sqlite_reader.ui.result_grid import ResultGrid
from sqlite_reader.ui.schema_panel import SchemaPanel
from sqlite_reader.ui.sql_editor import SqlEditor
from sqlite_reader.validation import StatementType, classify_statement


class MainWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SQLite Reader")
        self.root.geometry("1000x650")

        self.db = DatabaseConnection()

        self._setup_menu()
        self._setup_ui()
        self._update_status("Ready")

    def _setup_menu(self) -> None:
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(
            label="Open (Read-Only)...",
            command=lambda: self._open_database(read_only=True),
        )
        file_menu.add_command(
            label="Open (Editable)...",
            command=lambda: self._open_database(read_only=False),
        )
        file_menu.add_command(
            label="Close Database", command=lambda: self._close_database
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Refresh Schema", command=self._refresh_schema)
        menubar.add_cascade(label="View", menu=view_menu)

        self.root.config(menu=menubar)

    def _setup_ui(self) -> None:
        # Main PanedWindow (Horizontal split: Left schema, Right query editor/grid)
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Left Pane: Schema Explorer
        self.schema_panel = SchemaPanel(
            self.main_paned, self.db, on_table_selected=self._on_table_selected
        )
        self.main_paned.add(self.schema_panel, weight=1)

        # Right Pane: Vertical PanedWindow (Top: SQL Editor, Bottom: Result Grid)
        self.right_paned = ttk.PanedWindow(self.main_paned, orient=tk.VERTICAL)
        self.main_paned.add(self.right_paned, weight=3)

        self.sql_editor = SqlEditor(self.right_paned, on_execute=self._execute_sql)
        self.right_paned.add(self.sql_editor, weight=1)

        self.result_grid = ResultGrid(self.right_paned, self.db)
        self.right_paned.add(self.result_grid, weight=3)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(
            self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _update_status(self, message: str) -> None:
        self.status_var.set(message)

    def _on_table_selected(self, table_name: str) -> None:
        # Generate default SELECT query in the editor and load table
        quoted_table = quote_identifier(table_name)
        self.sql_editor.set_sql(f"SELECT * FROM {quoted_table};")
        self.result_grid.load_table(table_name)
        self._update_status(f"Loaded table: {table_name}")

    def _execute_sql(self, sql: str) -> None:
        if not self.db.db_path:
            messagebox.showwarning("No Database", "Please open a database first.")
            return

        stmt_type = classify_statement(sql)

        if self.db.is_read_only and stmt_type in (
            StatementType.MUTATION,
            StatementType.SCHEMA,
            StatementType.MAINTENANCE,
        ):
            messagebox.showerror(
                "Read-Only Mode Active",
                "Cannot execute mutating operations on a Read-Only database connection.\n\n"
                "Please reopen the database in Editable mode to make changes.",
                parent=self.root,
            )
            self._update_status("Blocked mutating query in read-only mode.")
            return

        if stmt_type in (
            StatementType.MUTATION,
            StatementType.SCHEMA,
            StatementType.MAINTENANCE,
        ):
            db_name = self.db.db_path.name if self.db.db_path else "Database"
            if not confirm_mutation(self.root, sql, stmt_type, db_name):
                self._update_status("Execution cancelled by user.")
                return

        try:
            result = execute_user_query(self.db, sql)
            self.result_grid.display_query_result(result)
            self._update_status(result.message)

            if stmt_type in (StatementType.SCHEMA, StatementType.MUTATION):
                self.schema_panel.refresh()

        except (sqlite3.Error, ValueError, RuntimeError, PermissionError) as e:
            self.result_grid.display_error(str(e))
            self._update_status(f"Execution failed: {e}")

    def _open_database(self, read_only: bool) -> None:
        file_path = filedialog.askopenfilename(
            title="Open SQLite Database",
            filetypes=[
                ("SQLite Databases", "*.sqlite *.sqlite3 *.db"),
                ("All Files", "*.*"),
            ],
        )
        if not file_path:
            return

        try:
            db_path = Path(file_path)
            self.db.open(db_path, read_only=read_only)
            mode_str = "Read-Only" if read_only else "Editable"

            self.root.title(f"SQLite Reader - {db_path.name} ({mode_str})")
            self._update_status(f"Opened database successfully in {mode_str} mode.")

            self.schema_panel.refresh()
            self.sql_editor.clear()
            self.result_grid.clear()

        except (sqlite3.Error, FileNotFoundError, RuntimeError, OSError) as e:
            messagebox.showerror("Error Opening Database", str(e))
            self._update_status("Error opening database.")

    def _close_database(self) -> None:
        self.db.close()
        self.root.title("SQLite Reader")
        self.schema_panel.refresh()
        self.sql_editor.clear()
        self.result_grid.clear()
        self._update_status("Database closed.")

    def _refresh_schema(self) -> None:
        if self.db.db_path:
            self.schema_panel.refresh()
            self._update_status("Schema refreshed.")
