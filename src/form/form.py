import tkinter as tk
import threading
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
from src.tools.text_classifier import GPTClassifier, SimpleClassifier


class ABForm(ABC):
    """
    Abstract base class for forms
    """

    ERROR_COLOR = "red"
    SUCCESS_COLOR = "green"
    VALID_COLOR = "SystemButtonFace"

    def __init__(
        self,
        form: tk.Frame,
        form_fields: list[FormField],
        form_title: str,
        action_buttons: list[tk.Button] = None,
    ):
        self.form_fields = form_fields
        self.error_labels = [
            tk.Label(form, text="", font=("Arial", 10), fg=ABForm.ERROR_COLOR)
            for _ in form_fields
        ]
        self.form_message_label = tk.Label(form, text="", font=("Arial", 15))
        self.form = form
        self.form.pack(pady=20)
        if not action_buttons:
            action_buttons = [
                tk.Button(
                    form,
                    text="Submit",
                    command=self.submit,
                    font=("Arial", 12),
                    bg="white",
                )
            ]
        self.action_buttons = action_buttons
        self.form_title = form_title

    def create_form(self):
        self.set_form_title()
        for i, form_field in enumerate(self.form_fields, start=1):
            self.set_form_input_layout(i, form_field)
        self.set_action_buttons_layout()

        self.form_message_label.grid(
            row=self.form.grid_size()[1], columnspan=3, padx=20
        )

    def set_form_title(self):
        tk.Label(
            self.form,
            text=self.form_title,
            font=("Arial", 20),
            fg="white",
            bg="#2a2a2a",
        ).grid(row=0, padx=20, pady=20)

    def set_action_buttons_layout(self):
        input_row_offset = 1
        input_row_elements = 2
        for i, button in enumerate(self.action_buttons):
            columnspan = 3 // len(self.action_buttons)
            button.grid(
                row=len(self.form_fields) * input_row_elements
                + input_row_offset
                + input_row_elements,
                column=i,
                padx=20,
                pady=5,
                columnspan=columnspan,
            )

    def set_form_input_layout(self, i, form_field):
        """
        Called for each form field.
        Default layout is vertical.
        Override this method to change the layout of the form

        :param i: the row number of the form field. Starts at 1
        :param form_field: the form field to layout
        """
        field_name = form_field.get_display_name()
        tk_label = tk.Label(self.form, text=field_name, font=("Arial", 12), fg="white")
        tk_label.grid(row=i * 2, column=0, sticky="w", padx=10, pady=10)
        tk_field = form_field.get_tk_field()
        tk_field.config(
            highlightbackground=ABForm.VALID_COLOR,
            highlightcolor=ABForm.VALID_COLOR,
        )
        tk_field.grid(row=i * 2, column=1, padx=10, pady=10, sticky="w")
        self.error_labels[i - 1].grid(row=i * 2 + 1, column=1, padx=10)

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
                # self.clear_form()
                self.form_message_label.config(text=message, fg=ABForm.SUCCESS_COLOR)
            else:
                self.form_message_label.config(text=message, fg=ABForm.ERROR_COLOR)

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

    def get_form_fields(self) -> list[FormField]:
        return self.form_fields

    @abstractmethod
    def on_success(self) -> (bool, str):
        pass


class TransactionsCsvForm(ABForm):
    def __init__(self, master: tk.Tk):
        self.master = master
        self.form = tk.Frame(self.master)
        self.form.pack(pady=20)
        self.form_fields = [
            UploadFileField(
                "filename",
                True,
                self.form,
                # mac numbers csv
                [
                    ("CSV Files", "*.csv"),
                    ("Excel Files", "*.xlsx"),
                    # ("Mac numbers", "*.numbers"),
                ],
                display_name="CSV File",
            ),
        ]
        self.db = DBManager()
        self.text_classifier = SimpleClassifier()
        super().__init__(self.form, self.form_fields, "Upload CSV")
        super().create_form()

    def infer_category(self, row, categories):
        # TODO: make this take all rows, and batch process
        if row["Category"] in categories:
            print(
                f"Using existing category for {row['Description']}: {row['Category']}"
            )
            return (row["Category"], False)
        code = row["Code"]
        # if previous transaction has same code, use that category
        prev_category = self.db.select(
            """
                SELECT category FROM transactions
                WHERE code = ? AND category != 'Other'
                ORDER BY date DESC
                LIMIT 1
            """,
            [code],
        )
        if prev_category:
            print(
                f"Using previous category for {row['Description']}: {prev_category[0][0]}"
            )
            return (prev_category[0][0], True)
        if not row["Description"]:
            print(f"Using default category for {row['Description']}: Other")
            return ("Other", False)
        result = self.text_classifier.predict(row["Description"], categories)
        print(f"Inferred category for {row['Description']}: {result}")
        return (result, True)

    def infer_categories(self, df, categories):
        """
        Auto fill the category column when missing.
        If the category is already in the db, use that
        If the code is the same as a previous transaction, use that category
        Otherwise, use NLP to infer category
        """
        descriptions_to_infer = {}
        df["Inferred_Category"] = 0  # 0 = not inferred, 1 = inferred
        for i, row in df.iterrows():
            if row["Category"] in categories:
                # already correct, do nothing
                row["Inferred_Category"] = 0
                continue
            code = row["Code"]
            # if previous transaction has same code, use that category
            prev_category = self.db.select(
                """
                    SELECT category FROM transactions
                    WHERE code = ? AND category != 'Other'
                    ORDER BY date DESC
                    LIMIT 1
                """,
                [code],
            )
            if prev_category:
                # use previous category
                row["Inferred_Category"] = 1
                row["Category"] = prev_category[0][0]
            elif not row["Description"]:
                # No information to infer category, use default
                row["Inferred_Category"] = 0
                row["Category"] = "Other"
            else:
                row["Inferred_Category"] = 1
                descriptions_to_infer[i] = row["Description"]
        # batch process rows to infer
        print(f"{len(descriptions_to_infer)} descriptions to infer")
        descriptions = list(descriptions_to_infer.values())
        results = self.text_classifier.predict_batch(descriptions, categories)
        for i, row in df.iterrows():
            if i in descriptions_to_infer:
                result = results.pop(0)
                print(f"Inferred category for {row['Description']}: {result}")
                row["Category"] = result
        return df

    def create_data_from_csv(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            df = pd.read_csv(f)
            # validate column names
            expected_columns = ["Date", "Description", "Amount", "Category", "Code"]
            auto_added_columns = ["Inferred_Category"]
            if not all(col in df.columns for col in expected_columns):
                return (
                    False,
                    f"Invalid column names {df.columns}, must be {expected_columns}",
                )
            df["Amount"] = df["Amount"].apply(
                lambda x: float(x.replace(",", "")) if isinstance(x, str) else x
            )
            df["Amount"] = df["Amount"].apply(lambda x: round(x, 2))
            # validate data types
            df["Date"] = pd.to_datetime(df["Date"])
            # round to 2 decimal places
            # validate date
            today = pd.Timestamp.today()
            if not all(df["Date"] <= today):
                return (False, "Date cannot be in the future")
            # convert dates to YYYY-MM-DD string
            df["Date"] = df["Date"].apply(lambda x: x.strftime("%Y-%m-%d"))

            df["Code"] = df["Code"].apply(lambda x: str(x) if not pd.isnull(x) else "")
            # validate category
            # categories = self.db.select("SELECT category FROM categories", [])
            # categories = [category[0] for category in categories]
            # if not all(df["Category"].isin(categories)):
            #     return (False, f"Invalid category, must be one of {categories}")

            # create category if not exists
            df["Category"] = df["Category"].apply(
                lambda x: str(x).title() if not pd.isnull(x) else x
            )
            categories = set(df["Category"])

            self.db.insert_many(
                """
                    INSERT OR IGNORE INTO categories (category)
                    VALUES (?)
                """,
                [(category,) for category in categories if not pd.isnull(category)],
            )

            categories = [
                category[0]
                for category in self.db.select("SELECT category FROM categories", [])
            ]

            data = []
            cols = expected_columns + auto_added_columns
            # insert into db
            for _, row in df.iterrows():
                category, was_inferred = self.infer_category(row, categories)
                row["Category"] = category
                row["Inferred_Category"] = 1 if was_inferred else 0
                row_data = tuple(row[col] for col in cols)
                data.append(row_data)

            # df = self.infer_categories(df, categories)
            try:
                # TODO: make this a transaction
                self.db.insert_many(
                    f"""
                        INSERT INTO transactions ({', '.join(cols)})
                        VALUES ({', '.join(['?'] * len(cols))})
                    """,
                    data,
                )
                self.db.insert(
                    """
                        INSERT INTO FILES (filename)
                        VALUES (?)
                    """,
                    [filename],
                )
                self.clear_form()
                print("Successfully added transactions")
                return (True, "Successfully added transactions")
            except Error as e:
                print(e)
                return (False, str(e))

    def on_success(self) -> (bool, str):
        data = self.form_fields[0].get_value()
        # parse csv in a separate thread
        thread = threading.Thread(
            target=self.create_data_from_csv, args=(data,), daemon=True
        )
        thread.start()
        return (True, "Successfully submited file: " + data)


class GenerateMonthlySummaryForm(ABForm):
    def __init__(self, master: tk.Tk):
        self.master = master
        self.form = tk.Frame(self.master)
        self.form.pack(pady=20)
        self.form_fields = [
            DateField(
                "month",
                True,
                self.form,
                date_format="YYYY-MM",
                display_name="Month (YYYY-MM)",
            )
        ]
        self.db = DBManager()
        self.listeners = []
        super().__init__(self.form, self.form_fields, "Generate Monthly Summary")
        super().create_form()

    def register_listener(self, listener):
        self.listeners.append(listener)

    def on_success(self) -> (bool, str):
        month = self.form_fields[0].get_value()
        for listener in self.listeners:
            listener.notify(month)
        return (True, "Successfully generated summary")


class EditTransactionForm(ABForm):
    def __init__(self, master: tk.Tk, transaction_id: int):
        self.master = master
        self.form = tk.Frame(self.master)
        self.form.pack(pady=20)
        self.db = DBManager()
        self.categories = [
            c[0]
            for c in self.db.select(
                "SELECT category FROM categories  ORDER BY category ASC", []
            )
        ]
        self.form_fields = [
            DateField("date", True, self.form, display_name="Date (YYYY-MM-DD)"),
            TextField("description", True, self.form, display_name="Description"),
            NumberField("amount", True, self.form, display_name="Amount"),
            TextField("code", False, self.form, display_name="Code"),
            DropdownField(
                "category", True, self.categories, self.form, display_name="Category"
            ),
        ]
        self.action_buttons = [
            tk.Button(
                self.form,
                text="Update",
                command=self.submit,
                font=("Arial", 12),
                bg="white",
            ),
            tk.Button(
                self.form,
                text="Delete",
                command=self.delete,
                font=("Arial", 12),
                bg="white",
            ),
        ]
        self.transaction_id = transaction_id
        super().__init__(
            self.form,
            self.form_fields,
            "Edit Transaction",
            action_buttons=self.action_buttons,
        )
        self.listeners = []
        super().create_form()

    def on_success(self) -> (bool, str):
        if not self.transaction_id:
            return (False, "Invalid transaction id")
        # Data is valid, proceed with insertion
        data = {}
        for field in self.form_fields:
            data[field.get_name()] = field.get_value()
        try:
            statement = f"""
                    UPDATE transactions
                    SET date = '{data["date"]}', description = '{data["description"]}',
                        amount = {data["amount"]}, category = '{data["category"]}', code = '{data["code"]}', inferred_category = 0
                    WHERE id = {self.transaction_id}
            """

            self.db.update(statement, [])
        except Error as e:
            return (False, str(e))
        self.notify_update()
        return (True, "Successfully updated transaction")

    def set_form_input_layout(self, i, form_field):
        # i is the row number of the form field. Starts at 1
        # Show three inputs per row, or 2 if not enough.
        # Entry under label, error label under entry
        field_name = form_field.get_display_name()
        row_position = (i - 1) // 3  # 0 indexed
        tk_label = tk.Label(self.form, text=field_name, font=("Arial", 12), fg="white")
        tk_label.grid(
            row=row_position * 3 + 1, column=(i - 1) % 3, sticky="w", padx=5, pady=10
        )
        tk_field = form_field.get_tk_field()
        tk_field.config(
            highlightbackground=ABForm.VALID_COLOR,
            highlightcolor=ABForm.VALID_COLOR,
        )
        tk_field.grid(
            row=row_position * 3 + 2, column=(i - 1) % 3, padx=10, pady=10, sticky="w"
        )
        self.error_labels[i - 1].grid(
            row=row_position * 3 + 3, column=(i - 1) % 3, padx=10
        )

    def delete(self):
        if not self.transaction_id:
            self.form_message_label.config(
                text="Invalid transaction id", fg=ABForm.ERROR_COLOR
            )
            return
        print(f"Deleting transaction {self.transaction_id}")
        self.db.delete(
            f"""
                DELETE FROM transactions
                WHERE id = {self.transaction_id}
            """,
            [],
        )
        self.clear_form()
        self.form_message_label.config(
            text="Successfully deleted row", fg=ABForm.SUCCESS_COLOR
        )
        self.notify_update()

    def register_listener(self, listener):
        self.listeners.append(listener)

    def notify_update(self):
        for listener in self.listeners:
            listener.notify_update()


class AddTransactionForm(ABForm):
    def __init__(self, master: tk.Tk):
        self.master = master
        self.form = tk.Frame(self.master)
        self.form.pack(pady=20)
        self.db = DBManager()
        self.categories = [
            c[0]
            for c in self.db.select(
                "SELECT category FROM categories  ORDER BY category ASC", []
            )
        ]
        self.form_fields = [
            DateField("date", True, self.form, display_name="Date (YYYY-MM-DD)"),
            TextField("description", True, self.form, display_name="Description"),
            NumberField("amount", True, self.form, display_name="Amount"),
            TextField("code", False, self.form, display_name="Code"),
            DropdownField(
                "category", True, self.categories, self.form, display_name="Category"
            ),
        ]
        super().__init__(self.form, self.form_fields, "Add Transaction")
        super().create_form()

    def on_success(self) -> (bool, str):
        # Data is valid, proceed with insertion
        data = {}
        for field in self.form_fields:
            data[field.get_name()] = field.get_value()
        data["inferred_category"] = 0
        cols = ["date", "description", "amount", "category", "code"]
        data = [data[col] for col in cols]
        data.append(0)  # inferred category
        try:
            self.db.insert(
                f"""
                    INSERT INTO transactions ({', '.join(cols)}, inferred_category)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                data,
            )
        except Error as e:
            return (False, str(e))
        return (True, "Successfully added transaction")

    def set_form_input_layout(self, i, form_field):
        # i is the row number of the form field. Starts at 1
        # Show three inputs per row, or 2 if not enough.
        # Entry under label, error label under entry
        field_name = form_field.get_display_name()
        row_position = (i - 1) // 3  # 0 indexed
        tk_label = tk.Label(self.form, text=field_name, font=("Arial", 12), fg="white")
        tk_label.grid(
            row=row_position * 3 + 1, column=(i - 1) % 3, sticky="w", padx=5, pady=10
        )
        tk_field = form_field.get_tk_field()
        tk_field.config(
            highlightbackground=ABForm.VALID_COLOR,
            highlightcolor=ABForm.VALID_COLOR,
        )
        tk_field.grid(
            row=row_position * 3 + 2, column=(i - 1) % 3, padx=10, pady=10, sticky="w"
        )
        self.error_labels[i - 1].grid(
            row=row_position * 3 + 3, column=(i - 1) % 3, padx=10
        )
