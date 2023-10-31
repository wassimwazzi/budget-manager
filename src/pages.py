import tkinter as tk
from tkinter import ttk
from src.form.form import TransactionForm, TransactionsCsvForm
from src.db.data_summarizer import (
    get_transactions_df,
    get_budget_summary_df,
    get_monthly_income_df,
)


class DataEntryPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        TransactionForm(self)
        TransactionsCsvForm(self)


class HomePage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        df = get_budget_summary_df("2023-10")
        frame = tk.Frame(self)
        frame.pack(pady=10)
        # Create a Treeview widget to display the DataFrame
        tree = ttk.Treeview(self, columns=list(df.columns), show="headings")

        # Add column headings
        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)  # Adjust the width as needed

        # Insert data into the Treeview
        for index, row in df.iterrows():
            tree.insert("", "end", values=list(row))

        tree.pack()
