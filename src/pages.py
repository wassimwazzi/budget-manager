import tkinter as tk
from src.form.form import TransactionForm, TransactionsCsvForm


class DataEntryPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        TransactionForm(self)
        TransactionsCsvForm(self)


class HomePage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
