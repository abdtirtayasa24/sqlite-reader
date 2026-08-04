import tkinter as tk


class MainWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SQLite Reader")
        self.root.geometry("800x600")

        label = tk.Label(self.root, text="SQLite Reader - Phase 1 Foundation")
        label.pack(expand=True)
