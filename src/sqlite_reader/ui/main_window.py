import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from sqlite_reader.database import DatabaseConnection


class MainWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SQLite Reader")
        self.root.geometry("800x600")

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
        self.root.config(menu=menubar)

    def _setup_ui(self) -> None:
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        self.placeholder_label = tk.Label(self.main_frame, text="No database open.")
        self.placeholder_label.pack(expand=True)

        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(
            self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _update_status(self, message: str) -> None:
        self.status_var.set(message)

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
            self.placeholder_label.config(text=f"Opened: {db_path}\nMode: {mode_str}")
            self._update_status(f"Opened database successfully in {mode_str} mode.")

        except Exception as e:
            messagebox.showerror("Error Opening Database", str(e))
            self._update_status("Error opening database.")

    def _close_database(self) -> None:
        self.db.close()
        self.root.title("SQLite Reader")
        self.placeholder_label.config(text="No database open.")
        self._update_status("Database closed.")
