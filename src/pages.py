import tkinter as tk
from src.form.form import TransactionForm, TransactionsCsvForm


class DataEntryPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        label = tk.Label(self, text="Data Entry Page")
        label.pack(pady=10, padx=10)
        button = tk.Button(
            self,
            text="Go to Home",
            command=lambda: controller.show_frame(HomePage),
        )
        button.pack()
        TransactionForm(self)
        TransactionsCsvForm(self)


class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        label = tk.Label(self, text="Home Page")
        label.pack(pady=10, padx=10)
        button = tk.Button(
            self,
            text="Go to Data Entry Page",
            command=lambda: controller.show_frame(DataEntryPage),
        )
        button.pack()
