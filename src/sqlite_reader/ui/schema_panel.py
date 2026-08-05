import tkinter as tk
from tkinter import ttk
from typing import Any

from sqlite_reader.database import DatabaseConnection
from sqlite_reader.schema import get_schema_objects, get_table_columns


class SchemaPanel(ttk.Frame):
    def __init__(self, parent: tk.Widget, db: DatabaseConnection) -> None:
        super().__init__(parent)
        self.db = db
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.tree = ttk.Treeview(self, show="tree")
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.details = tk.Text(self, height=12, state=tk.DISABLED, wrap=tk.WORD)
        self.details.pack(side=tk.BOTTOM, fill=tk.X)

    def refresh(self) -> None:
        """Reloads the schema objects from the database."""
        self.tree.delete(*self.tree.get_children())
        self._set_details("")

        if not self.db.db_path:
            return

        try:
            objects = get_schema_objects(self.db)
            categories = {
                "table": "Tables",
                "view": "Views",
                "index": "Indexes",
                "trigger": "Triggers",
            }
            nodes: dict[str, str] = {}

            for obj in objects:
                cat_name = categories.get(obj.type, obj.type.capitalize())
                if cat_name not in nodes:
                    nodes[cat_name] = self.tree.insert(
                        "", tk.END, text=cat_name, open=True
                    )

                    self.tree.insert(
                        nodes[cat_name],
                        tk.END,
                        text=obj.name,
                        values=(obj.type, obj.name),
                    )
        except Exception as e:
            self._set_details(f"Error loading schema:\n{e}")

    def _on_select(self, event: Any) -> None:
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        values = item.get("values")

        if not values:
            self._set_details("")
            return

        obj_type, obj_name = values[0], values[1]
        details_text = f"-- {obj_type.upper()}: {obj_name}\n\n"

        try:
            if obj_type in ("table", "view"):
                columns = get_table_columns(self.db, obj_name)
                if columns:
                    details_text += "-- Columns:\n"
                    for col in columns:
                        pk_str = " PK" if col.pk else ""
                        notnull_str = " NOT NULL" if col.notnull else ""
                        details_text += (
                            f"--   {col.name} ({col.type}){pk_str}{notnull_str}\n"
                        )
                    details_text += "\n"

            objects = get_schema_objects(self.db)
            for obj in objects:
                if obj.name == obj_name and obj.type == obj_type:
                    if obj.sql:
                        details_text += obj.sql
                    break

        except Exception as e:
            details_text += f"\nError loading details: {e}"

        self._set_details(details_text)

    def _set_details(self, text: str) -> None:
        self.details.config(state=tk.NORMAL)
        self.details.delete("1.0", tk.END)
        self.details.insert(tk.END, text)
        self.details.config(state=tk.DISABLED)
