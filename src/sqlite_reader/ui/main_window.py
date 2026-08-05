import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from sqlite_reader.database import DatabaseConnection
from sqlite_reader.ui.result_grid import ResultGrid
from sqlite_reader.ui.schema_panel import SchemaPanel


class MainWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SQLite Reader")
        self.root.geometry("900x600")

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
        # Main PanewWindow to split left (schema) and right (content)
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Left Pane: Schema Explorer
        self.schema_panel = SchemaPanel(
            self.paned_window, self.db, on_table_selected=self._on_table_selected
        )
        self.paned_window.add(self.schema_panel, weight=1)

        # Right Pane: Placeholder for future Result Grid / SQL Editor
        self.right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.right_frame, weight=3)

        self.result_grid = ResultGrid(self.right_frame, self.db)
        self.result_grid.pack(expand=True, fill=tk.BOTH)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(
            self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _update_status(self, message: str) -> None:
        self.status_var.set(message)

    def _on_table_selected(self, table_name: str) -> None:
        self.result_grid.load_table(table_name)
        self._update_status(f"Loaded table: {table_name}")

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
            self.result_grid.clear()

        except Exception as e:
            messagebox.showerror("Error Opening Database", str(e))
            self._update_status("Error opening database.")

    def _close_database(self) -> None:
        self.db.close()
        self.root.title("SQLite Reader")
        self.schema_panel.refresh()
        self.result_grid.clear()
        self._update_status("Database closed.")

    def _refresh_schema(self) -> None:
        if self.db.db_path:
            self.schema_panel.refresh()
            self._update_status("Schema refreshed.")
