import tkinter as tk
from datetime import datetime
from abc import ABC, abstractmethod
from src.form.fields import FormField, DateField, TextField, NumberField, DropdownField
from src.db.dbmanager import DBManager


class FormValidator:
    def __init__(self, form_fields: list[FormField]):
        self.form_fields = form_fields

    def validate(self, data: dict[str, tk.Entry]) -> dict[str, str]:
        errors = {}
        for field_info in self.form_fields:
            field_name = field_info.get_name()
            value = data[field_name].get()
            is_valid, error = field_info.validate(value)
            if not is_valid:
                errors[field_name] = error

        return errors

    def validate_date(self, date_str: str) -> bool:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            today = datetime.now()
            if date > today:
                return (False, "Date cannot be in the future")
            return (True, None)
        except ValueError:
            return (False, "Invalid date format, must be YYYY-MM-DD")


class ABForm(ABC):
    """
    Abstract base class for forms
    """

    ERROR_COLOR = "red"
    VALID_COLOR = "SystemButtonFace"

    def __init__(self, form: tk.Frame, form_fields: list[FormField]):
        print("Form init")
        self.form_fields = form_fields
        self.tk_fields = {}
        self.error_labels = {}
        self.form = form
        self.form.pack(pady=20)
        self.validator = FormValidator(form_fields)

    def create_form(self):
        for i, field_info in enumerate(self.form_fields):
            field_name = field_info.get_name()
            tk_label = tk.Label(
                self.form, text=field_name, font=("Arial", 12), fg="white"
            )
            tk_label.grid(row=i * 2, column=0, sticky="w", padx=10, pady=10)
            tk_field = tk.Entry(self.form)
            tk_field.config(
                highlightbackground=ABForm.VALID_COLOR,
                highlightcolor=ABForm.VALID_COLOR,
            )
            tk_field.grid(row=i * 2, column=1, padx=10, pady=10, sticky="w")
            self.tk_fields[field_name] = tk_field

            error_label = tk.Label(
                self.form, text="", font=("Arial", 10), fg=ABForm.ERROR_COLOR
            )
            error_label.grid(row=i * 2 + 1, column=1, padx=10)
            self.error_labels[field_name] = error_label

        submit_button = tk.Button(
            self.form,
            text="Submit",
            command=self.submit,
            font=("Arial", 12),
            bg="white",
        )
        submit_button.grid(row=len(self.form_fields) * 2, columnspan=3, padx=20, pady=5)

    def submit(self):
        data = {}
        errors = self.validator.validate(self.tk_fields)

        for tk_field_name, tk_field in self.tk_fields.items():
            if tk_field_name in errors:
                error_label = self.error_labels[tk_field_name]
                tk_field.config(
                    highlightbackground=ABForm.ERROR_COLOR,
                    highlightcolor=ABForm.ERROR_COLOR,
                )
                error_label.config(text=errors[tk_field_name])
            else:
                data[tk_field_name] = tk_field.get()
                tk_field.config(
                    highlightbackground=ABForm.VALID_COLOR,
                    highlightcolor=ABForm.VALID_COLOR,
                )
                error_label = self.error_labels[tk_field_name]
                error_label.config(text="")

        if not errors:
            self.on_success(data)
            self.clear_form()

    def clear_form(self):
        for field_name, tk_field in self.tk_fields.items():
            error_label = self.error_labels[field_name]
            tk_field.config(
                highlightbackground=ABForm.VALID_COLOR,
                highlightcolor=ABForm.VALID_COLOR,
            )
            tk_field.delete(0, "end")
            error_label.config(text="")

    @abstractmethod
    def on_success(self, data: dict[str, str]):
        pass


class TransactionForm(ABForm):
    FORM_FIELDS = [
        DateField("Date (YYYY-MM-DD)", True),
        TextField("Description", True),
        NumberField("Amount", True),
        DropdownField("Category", True, ["Income", "Expense"]),
        TextField("Code", False),
    ]

    def __init__(self, master: tk.Tk):
        self.master = master
        self.form = tk.Frame(self.master)
        self.form.pack(pady=20)
        self.validator = FormValidator(TransactionForm.FORM_FIELDS)
        self.db = DBManager()
        super().__init__(self.form, TransactionForm.FORM_FIELDS)
        super().create_form()

    def on_success(self, data: dict[str, str]):
        # Data is valid, proceed with insertion
        self.db.insert(
            """
                INSERT INTO transactions (date, description, amount, category, code)
                VALUES (?, ?, ?, ?, ?)
            """,
            list(data.values()),
        )