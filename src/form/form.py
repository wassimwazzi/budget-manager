import tkinter as tk
from abc import ABC, abstractmethod
from src.form.fields import (
    FormField,
    DateField,
    TextField,
    NumberField,
    DropdownField,
    UploadFileField,
)
from src.db.dbmanager import DBManager


class ABForm(ABC):
    """
    Abstract base class for forms
    """

    ERROR_COLOR = "red"
    VALID_COLOR = "SystemButtonFace"

    def __init__(self, form: tk.Frame, form_fields: list[FormField]):
        self.form_fields = form_fields
        self.error_labels = [
            tk.Label(form, text="", font=("Arial", 10), fg=ABForm.ERROR_COLOR)
            for _ in form_fields
        ]
        self.form = form
        self.form.pack(pady=20)

    def create_form(self):
        for i, form_field in enumerate(self.form_fields):
            field_name = form_field.get_name()
            tk_label = tk.Label(
                self.form, text=field_name, font=("Arial", 12), fg="white"
            )
            tk_label.grid(row=i * 2, column=0, sticky="w", padx=10, pady=10)
            tk_field = form_field.get_tk_field()
            tk_field.config(
                highlightbackground=ABForm.VALID_COLOR,
                highlightcolor=ABForm.VALID_COLOR,
            )
            tk_field.grid(row=i * 2, column=1, padx=10, pady=10, sticky="w")
            self.error_labels[i].grid(row=i * 2 + 1, column=1, padx=10)

        submit_button = tk.Button(
            self.form,
            text="Submit",
            command=self.submit,
            font=("Arial", 12),
            bg="white",
        )
        submit_button.grid(row=len(self.form_fields) * 2, columnspan=3, padx=20, pady=5)

    def submit(self):
        is_success = True
        for i, form_field in enumerate(self.form_fields):
            is_valid, error_message = form_field.validate()
            if not is_valid:
                self.error_labels[i].config(text=error_message)
                tk_field = form_field.get_tk_field()
                tk_field.config(
                    highlightbackground=ABForm.ERROR_COLOR,
                    highlightcolor=ABForm.ERROR_COLOR,
                )
                is_success = False
            else:
                tk_field = form_field.get_tk_field()
                tk_field.config(
                    highlightbackground=ABForm.VALID_COLOR,
                    highlightcolor=ABForm.VALID_COLOR,
                )
                self.error_labels[i].config(text="")

        if is_success:
            self.on_success()
            self.clear_form()

    def clear_form(self):
        for i, form_field in enumerate(self.form_fields):
            form_field.clear()
            tk_field = form_field.get_tk_field()
            error_label = self.error_labels[i]
            tk_field.config(
                highlightbackground=ABForm.VALID_COLOR,
                highlightcolor=ABForm.VALID_COLOR,
            )
            error_label.config(text="")

    @abstractmethod
    def on_success(self):
        pass


class TransactionForm(ABForm):
    def __init__(self, master: tk.Tk):
        self.master = master
        self.form = tk.Frame(self.master)
        self.form.pack(pady=20)
        self.form_fields = [
            DateField("Date (YYYY-MM-DD)", True, self.form),
            TextField("Description", True, self.form),
            NumberField("Amount", True, self.form),
            DropdownField("Category", True, ["Income", "Expense"], self.form),
            TextField("Code", False, self.form),
        ]
        self.db = DBManager()
        super().__init__(self.form, self.form_fields)
        super().create_form()

    def on_success(self):
        # Data is valid, proceed with insertion
        data = [field.get_value() for field in self.form_fields]
        self.db.insert(
            """
                INSERT INTO transactions (date, description, amount, category, code)
                VALUES (?, ?, ?, ?, ?)
            """,
            data,
        )


class TransactionsCsvForm(ABForm):
    def __init__(self, master: tk.Tk):
        self.master = master
        self.form = tk.Frame(self.master)
        self.form.pack(pady=20)
        self.form_fields = [
            UploadFileField("CSV File", True, self.form, [("CSV Files", "*.csv")]),
        ]
        super().__init__(self.form, self.form_fields)
        super().create_form()

    def on_success(self):
        data = self.form_fields[0].get_value()
        self.db = DBManager()
        with open(data, "r") as f:
            for line in f:
                print(line)
