import tkinter as tk
from sqlite_reader.ui.main_window import MainWindow


def main() -> int:
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()
    return 0
