from db.dbmanager import DBManager
import tkinter as tk
from tkinter import filedialog
import csv


class Form:
    """
    Form class. Allows to enter individual transactions, or upload a CSV file.
    """

    def __init__(self, master):
        self.master = master
        self.db = DBManager()
        self.form_fields = ["Date", "Description", "Amount", "Category", "Code"]
        self.tk_fields = []
        self.form = tk.Frame(self.master)
        self.form.pack(pady=20)
        self.create_form()

    def create_form(self):
        """
        Creates the form.
        """
        for i, field in enumerate(self.form_fields):
            tk_label = tk.Label(self.form, text=field, font=("Arial", 12), fg="white")
            tk_label.grid(row=i, column=0, sticky='w', padx=10, pady=10)
            tk_field = tk.Entry(self.form)
            tk_field.grid(row=i, column=1, padx=10, pady=10, sticky='w')
            self.tk_fields.append(tk_field)

        submit_button = tk.Button(self.form, text="Submit", command=self.submit, font=("Arial", 12), bg="white")
        submit_button.grid(row=len(self.form_fields), columnspan=2, padx=20, pady=5)

    def submit(self):
        """
        Submits the form.
        """
        data = []
        for tk_field in self.tk_fields:
            data.append(tk_field.get())
            tk_field.delete(0, "end")

        self.db.insert(
            "INSERT INTO transactions (date, description, amount, category, code) VALUES (?, ?, ?, ?, ?)",
            data,
        )

        self.clear_form()

    def clear_form(self):
        """
        Clears the form.
        """
        for tk_field in self.tk_fields:
            tk_field.delete(0, "end")


if __name__ == "__main__":
    root = tk.Tk()
    form = Form(root)

    root.mainloop()