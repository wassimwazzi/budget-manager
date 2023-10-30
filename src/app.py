import tkinter as tk
from src.form.form import TransactionForm, TransactionsCsvForm


def run():
    root = tk.Tk()
    TransactionForm(root)
    TransactionsCsvForm(root)

    root.mainloop()
