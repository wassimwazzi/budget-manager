import tkinter as tk
import threading
import traceback
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
    CheckBoxField,
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
                    font=("Arial", 15),
                    fg="dark green",
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
        self.set_form_input_vertical(i, form_field)

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

    def set_form_input_vertical(self, i, form_field):
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

    def set_form_input_horizontal(self, i, form_field, elements_per_row):
        # i is the row number of the form field. Starts at 1
        field_name = form_field.get_display_name()
        row_position = (i - 1) // elements_per_row  # 0 indexed
        tk_label = tk.Label(self.form, text=field_name, font=("Arial", 12), fg="white")
        tk_label.grid(
            row=row_position * elements_per_row + 1,
            column=(i - 1) % elements_per_row,
            sticky="w",
            padx=5,
            pady=10,
        )
        tk_field = form_field.get_tk_field()
        tk_field.config(
            highlightbackground=ABForm.VALID_COLOR,
            highlightcolor=ABForm.VALID_COLOR,
        )
        tk_field.grid(
            row=row_position * elements_per_row + 2,
            column=(i - 1) % elements_per_row,
            padx=10,
            pady=10,
            sticky="w",
        )
        self.error_labels[i - 1].grid(
            row=row_position * elements_per_row + 3,
            column=(i - 1) % elements_per_row,
            padx=10,
        )


class EditForm(ABForm):
    def __init__(
        self,
        form: tk.Frame,
        form_fields: list[FormField],
        form_title: str,
        entry_id: int | str,
        action_buttons: list[tk.Button] = None,
    ):
        if not action_buttons:
            action_buttons = [
                tk.Button(
                    form,
                    text="Update",
                    command=self.submit,
                    font=("Arial", 15),
                    fg="dark goldenrod",
                ),
                tk.Button(
                    form,
                    text="Delete",
                    command=self.delete,
                    font=("Arial", 15),
                    fg="red",
                ),
                tk.Button(
                    form,
                    text="New",
                    command=self.new,
                    font=("Arial", 15),
                    fg="dark green",
                ),
            ]
        self.action_buttons = action_buttons
        super().__init__(
            form=form,
            form_fields=form_fields,
            form_title=form_title,
            action_buttons=action_buttons,
        )
        self.listeners = []
        super().create_form()
        self.entry_id = entry_id

    def set_form_input_layout(self, i, form_field):
        return super().set_form_input_horizontal(i, form_field, 3)

    @abstractmethod
    def delete(self):
        pass

    @abstractmethod
    def new(self):
        pass

    def register_listener(self, listener):
        self.listeners.append(listener)

    def notify_update(self):
        for listener in self.listeners:
            listener.notify_update()


class TransactionsCsvForm(EditForm):
    """
    Made it an EditForm even though it doesn't edit anything.
    The methods of an EditForm are useful for this use case.
    """

    def __init__(self, master: tk.Tk, entry_id: int):
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
        self.action_buttons = [
            tk.Button(
                self.form,
                text="Submit",
                command=super().submit,
                font=("Arial", 15),
                fg="dark green",
            ),
            tk.Button(
                self.form,
                text="Delete",
                command=self.delete,
                font=("Arial", 15),
                fg="red",
            ),
        ]
        self.db = DBManager()
        self.text_classifier = SimpleClassifier()
        super().__init__(
            self.form,
            self.form_fields,
            "Upload CSV",
            entry_id,
            action_buttons=self.action_buttons,
        )
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

    def update_file_status(self, id, status, message):
        self.db.update(
            """
                UPDATE files
                SET status = ?, message = ?
                WHERE id = ?
            """,
            [status, message, id],
        )

    def create_data_from_csv(self, filename, file_record_id):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                df = pd.read_csv(f)
                # validate column names
                expected_columns = ["Date", "Description", "Amount", "Category", "Code"]
                auto_added_columns = ["Inferred_Category", "file_id"]
                missing_cols = [
                    col for col in expected_columns if col not in df.columns
                ]
                if missing_cols:
                    error_msg = f"Missing columns: {', '.join(missing_cols)}"
                    print(error_msg)
                    self.update_file_status(file_record_id, "Error", error_msg)
                    return (
                        False,
                        error_msg,
                    )
                df["Amount"] = df["Amount"].apply(
                    lambda x: float(x.replace(",", "")) if isinstance(x, str) else x
                )
                df["Amount"] = df["Amount"].apply(lambda x: round(x, 2))
                # validate data types
                df["Date"] = pd.to_datetime(df["Date"], format="mixed", dayfirst=False)
                # round to 2 decimal places
                # validate date
                today = pd.Timestamp.today()
                erroneous_dates = df[df["Date"] > today]["Date"]
                if not erroneous_dates.empty:
                    print("Date cannot be in the future")
                    print(erroneous_dates)
                    self.update_file_status(
                        file_record_id, "Error", "Date cannot be in the future"
                    )
                    return (False, "Date cannot be in the future")
                # convert dates to YYYY-MM-DD string
                df["Date"] = df["Date"].apply(
                    lambda x: x.strftime("%Y-%m-%d") if not pd.isnull(x) else None
                )

                df["Code"] = df["Code"].apply(
                    lambda x: str(x) if not pd.isnull(x) else ""
                )
                # create category if not exists
                df["Category"] = df["Category"].apply(
                    lambda x: str(x).title() if not pd.isnull(x) else x
                )
                categories = set(df["Category"])

                # self.db.insert_many(
                #     """
                #         INSERT OR IGNORE INTO categories (category)
                #         VALUES (?)
                #     """,
                #     [(category,) for category in categories if not pd.isnull(category)],
                # )

                existing_categories = [
                    category[0]
                    for category in self.db.select(
                        "SELECT category FROM categories", []
                    )
                ]

                # validate category exists
                missing_categories = [
                    category
                    for category in categories
                    if category not in existing_categories
                ]
                if missing_categories:
                    error_msg = f"Missing categories: {', '.join(missing_categories)}"
                    print(error_msg)
                    self.update_file_status(file_record_id, "Error", error_msg)
                    return (
                        False,
                        error_msg,
                    )

                data = []
                cols = expected_columns + auto_added_columns
                # insert into db
                for _, row in df.iterrows():
                    category, was_inferred = self.infer_category(row, categories)
                    row["Category"] = category
                    row["Inferred_Category"] = 1 if was_inferred else 0
                    row["file_id"] = file_record_id
                    row_data = tuple(row[col] for col in cols)
                    data.append(row_data)

                # df = self.infer_categories(df, categories)
                # TODO: make this a transaction
                self.db.insert_many(
                    f"""
                        INSERT INTO transactions ({', '.join(cols)})
                        VALUES ({', '.join(['?'] * len(cols))})
                    """,
                    data,
                )
                self.clear_form()
                print("Successfully added transactions")
                self.update_file_status(
                    file_record_id, "Success", "Successfully processed"
                )
                return (True, "Successfully added transactions")
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            self.update_file_status(file_record_id, "Error", str(e))
            return (False, str(e))

    def on_success(self) -> (bool, str):
        data = self.form_fields[0].get_value()
        # insert file into db
        file_record_id = self.db.insert(
            """
                INSERT INTO files (filename)
                VALUES (?)
            """,
            [data],
        )
        # parse csv in a separate thread
        thread = threading.Thread(
            target=self.create_data_from_csv, args=(data, file_record_id), daemon=True
        )
        thread.start()
        super().notify_update()
        return (True, "Successfully submited file: " + data)

    def delete(self):
        if not self.entry_id:
            self.form_message_label.config(
                text="Select a row first", fg=ABForm.ERROR_COLOR
            )
            return
        # delete transactions from file
        # keep file, but set state to deleted
        self.db.delete(
            f"""
                DELETE FROM transactions
                WHERE file_id = {self.entry_id}
            """,
            [],
        )
        self.db.update(
            f"""
                UPDATE files
                SET status = 'Deleted'
                WHERE id = {self.entry_id}
            """,
            [],
        )
        self.form_message_label.config(
            text="Successfully deleted file and its transactions",
            fg=ABForm.SUCCESS_COLOR,
        )
        super().notify_update()

    def new(self):
        pass


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


class EditTransactionForm(EditForm):
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
        self.transaction_id = transaction_id
        super().__init__(
            self.form,
            self.form_fields,
            "Edit Transaction",
            transaction_id,
        )

    def on_success(self) -> (bool, str):
        if not self.transaction_id:
            return (False, "Select a row first")
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
            print(e)
            return (False, str(e))
        super().notify_update()
        return (True, "Successfully updated transaction")

    def delete(self):
        if not self.transaction_id:
            self.form_message_label.config(
                text="Select a row first", fg=ABForm.ERROR_COLOR
            )
            return
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
        super().notify_update()

    def new(self):
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
            print(e)
            self.form_message_label.config(text=str(e), fg=ABForm.ERROR_COLOR)
            return (False, str(e))
        # self.clear_form()
        super().notify_update()
        self.form_message_label.config(
            text="Successfully added transasction", fg=ABForm.SUCCESS_COLOR
        )
        return (True, "Successfully added transaction")


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
            print(e)
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


class EditBudgetForm(EditForm):
    def __init__(self, master: tk.Tk, budget_id: int):
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
            DateField(
                "start_date",
                True,
                self.form,
                display_name="Date (YYYY-MM)",
                date_format="YYYY-MM",
            ),
            NumberField("amount", True, self.form, display_name="Amount"),
            DropdownField(
                "category", True, self.categories, self.form, display_name="Category"
            ),
        ]
        self.budget_id = budget_id
        super().__init__(
            self.form,
            self.form_fields,
            "Edit Budget",
            budget_id,
        )

    def on_success(self) -> (bool, str):
        if not self.budget_id:
            return (False, "Selct a row first")
        # Data is valid, proceed with insertion
        data = {}
        for field in self.form_fields:
            data[field.get_name()] = field.get_value()
        try:
            statement = f"""
                    UPDATE budgets
                    SET start_date = '{data["start_date"]}', amount = {data["amount"]},
                        category = '{data["category"]}'
                    WHERE id = {self.budget_id}
            """

            self.db.update(statement, [])
        except Error as e:
            print(e)
            return (False, str(e))
        self.notify_update()
        return (True, "Successfully updated budget")

    def delete(self):
        if not self.budget_id:
            self.form_message_label.config(
                text="Select a row first", fg=ABForm.ERROR_COLOR
            )
            return
        self.db.delete(
            f"""
                DELETE FROM budgets
                WHERE id = {self.budget_id}
            """,
            [],
        )
        self.clear_form()
        self.form_message_label.config(
            text="Successfully deleted row", fg=ABForm.SUCCESS_COLOR
        )
        self.notify_update()

    def new(self):
        # Data is valid, proceed with insertion
        data = {}
        for field in self.form_fields:
            data[field.get_name()] = field.get_value()
        try:
            self.db.insert(
                """
                    INSERT INTO budgets (category, amount, start_date)
                    VALUES (?, ?, ?)
                """,
                [data["category"], data["amount"], data["start_date"]],
            )
        except Error as e:
            print(e)
            self.form_message_label.config(text=str(e), fg=ABForm.ERROR_COLOR)
            return (False, str(e))
        # self.clear_form()
        super().notify_update()
        self.form_message_label.config(
            text="Successfully added budget", fg=ABForm.SUCCESS_COLOR
        )
        return (True, "Successfully added budget")


class AddBudgetForm(ABForm):
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
            DropdownField(
                "category", True, self.categories, self.form, display_name="Category"
            ),
            NumberField("amount", True, self.form, display_name="Budget"),
            DateField(
                "start_date",
                True,
                self.form,
                display_name="Month (YYYY-MM)",
                date_format="YYYY-MM",
            ),
        ]
        super().__init__(self.form, self.form_fields, "Add Budget")
        super().create_form()

    def on_success(self) -> (bool, str):
        # Data is valid, proceed with insertion
        data = {}
        for field in self.form_fields:
            data[field.get_name()] = field.get_value()
        try:
            self.db.insert(
                """
                    INSERT INTO budgets (category, amount, start_date)
                    VALUES (?, ?, ?)
                """,
                [data["category"], data["amount"], data["start_date"]],
            )
        except Error as e:
            print(e)
            return (False, str(e))
        return (True, "Successfully added budget")

    def set_form_input_layout(self, i, form_field):
        self.set_form_input_vertical(i, form_field)


class EditCategoryForm(EditForm):
    def __init__(self, master: tk.Tk, category_name: str):
        self.master = master
        self.form = tk.Frame(self.master)
        self.form.pack(pady=20)
        self.db = DBManager()
        self.form_fields = [
            TextField("category", True, self.form, display_name="Category"),
            TextField("description", True, self.form, display_name="Description"),
            CheckBoxField("income", False, self.form, display_name="Is Income"),
        ]
        self.category_name = category_name
        super().__init__(
            self.form,
            self.form_fields,
            "Edit Budget",
            category_name,
        )

    def on_success(self) -> (bool, str):
        if not self.category_name:
            return (False, "Selct a row first")
        # Data is valid, proceed with insertion
        data = {}
        for field in self.form_fields:
            data[field.get_name()] = field.get_value()
        try:
            statement = f"""
                    UPDATE categories
                    Set category = '{data["category"]}', description = '{data["description"]}',
                        income = {1 if data["income"] else 0}
                    WHERE category = '{self.category_name}'
            """

            self.db.update(statement, [])
        except Error as e:
            print(e)
            return (False, str(e))
        super().notify_update()
        return (True, "Successfully updated category")

    def delete(self):
        if not self.category_name:
            self.form_message_label.config(
                text="Select a row first", fg=ABForm.ERROR_COLOR
            )
            return
        self.db.delete(
            f"""
                DELETE FROM categories
                WHERE category = '{self.category_name}'
            """,
            [],
        )
        self.clear_form()
        self.form_message_label.config(
            text="Successfully deleted row", fg=ABForm.SUCCESS_COLOR
        )
        super().notify_update()

    def new(self):
        # Data is valid, proceed with insertion
        data = {}
        for field in self.form_fields:
            data[field.get_name()] = field.get_value()
        try:
            self.db.insert(
                """
                    INSERT INTO categories (category, description, income)
                    VALUES (?, ?, ?)
                """,
                [data["category"], data["description"], data["income"]],
            )
        except Error as e:
            print(e)
            self.form_message_label.config(text=str(e), fg=ABForm.ERROR_COLOR)
            return (False, str(e))
        # self.clear_form()
        super().notify_update()
        self.form_message_label.config(
            text="Successfully added category", fg=ABForm.SUCCESS_COLOR
        )
        return (True, "Successfully added category")
