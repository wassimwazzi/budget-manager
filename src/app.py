import tkinter as tk
from src.form import TransactionForm

def run():
    root = tk.Tk()
    form = TransactionForm(root)

    root.mainloop()
