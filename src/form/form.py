import tkinter as tk
from abc import ABC, abstractmethod
from sqlite3 import Error
import pandas as pd
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
    SUCCESS_COLOR = "green"
    VALID_COLOR = "SystemButtonFace"

    def __init__(self, form: tk.Frame, form_fields: list[FormField]):
        self.form_fields = form_fields
        self.error_labels = [
            tk.Label(form, text="", font=("Arial", 10), fg=ABForm.ERROR_COLOR)
            for _ in form_fields
        ]
        self.form_message_label = tk.Label(form, text="", font=("Arial", 10))
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
        self.form_message_label.grid(
            row=len(self.form_fields) * 2 + 1, columnspan=3, padx=20
        )

    def submit(self):
        is_success = True
        self.form_message_label.config(text="")
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
            success, message = self.on_success()
            if success:
                self.clear_form()
                self.form_message_label.config(text=message, fg=ABForm.SUCCESS_COLOR)
            else:
                self.form_message_label.config(
                    text=error_message, fg=ABForm.ERROR_COLOR
                )

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
    def on_success(self) -> (bool, str):
        pass


class TransactionForm(ABForm):
    def __init__(self, master: tk.Tk):
        self.master = master
        self.form = tk.Frame(self.master)
        self.form.pack(pady=20)
        self.db = DBManager()
        self.categories = [
            c[0] for c in self.db.select("SELECT category FROM categories", [])
        ]
        self.form_fields = [
            DateField("Date (YYYY-MM-DD)", True, self.form),
            TextField("Description", True, self.form),
            NumberField("Amount", True, self.form),
            TextField("Code", False, self.form),
            DropdownField("Category", True, self.categories, self.form),
        ]
        super().__init__(self.form, self.form_fields)
        super().create_form()

    def on_success(self) -> (bool, str):
        # Data is valid, proceed with insertion
        data = [field.get_value() for field in self.form_fields]
        try:
            self.db.insert(
                """
                    INSERT INTO transactions (date, description, amount, category, code)
                    VALUES (?, ?, ?, ?, ?)
                """,
                data,
            )
        except Error as e:
            return (False, str(e))
        return (True, "Successfully added transaction")


class TransactionsCsvForm(ABForm):
    def __init__(self, master: tk.Tk):
        self.master = master
        self.form = tk.Frame(self.master)
        self.form.pack(pady=20)
        self.form_fields = [
            UploadFileField(
                "CSV File",
                True,
                self.form,
                # mac numbers csv
                [
                    ("CSV Files", "*.csv"),
                    ("Excel Files", "*.xlsx"),
                    # ("Mac numbers", "*.numbers"),
                ],
            ),
        ]
        self.db = DBManager()
        super().__init__(self.form, self.form_fields)
        super().create_form()

    def on_success(self) -> (bool, str):
        data = self.form_fields[0].get_value()
        with open(data, "r", encoding="utf-8") as f:
            df = pd.read_csv(f)
            # validate column names
            expected_columns = ["Date", "Description", "Amount", "Category", "Code"]
            if not all(col in df.columns for col in expected_columns):
                return (False, f"Invalid column names, must be {expected_columns}")
            df["Amount"] = df["Amount"].apply(
                lambda x: round(float(x.replace(",", "")), 2)
            )
            # validate data types
            df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
            # round to 2 decimal places
            # validate date
            today = pd.Timestamp.today()
            if not all(df["Date"] <= today):
                return (False, "Date cannot be in the future")
            # convert dates to YYYY-MM-DD string
            df["Date"] = df["Date"].apply(lambda x: x.strftime("%Y-%m-%d"))

            # validate category
            # categories = self.db.select("SELECT category FROM categories", [])
            # categories = [category[0] for category in categories]
            # if not all(df["Category"].isin(categories)):
            #     return (False, f"Invalid category, must be one of {categories}")

            # create category if not exists
            categories = set(df["Category"])
            for category in categories:
                self.db.insert(
                    """
                        INSERT OR IGNORE INTO categories (category)
                        VALUES (?)
                    """,
                    (category,),
                )

            data = []
            # insert into db
            for _, row in df.iterrows():
                row_data = tuple(row[col] for col in expected_columns)
                data.append(row_data)
            try:
                self.db.insert_many(
                    """
                        INSERT INTO transactions (date, description, amount, category, code)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                    data,
                )
                return (True, "Successfully added transactions")
            except Error as e:
                return (False, str(e))
