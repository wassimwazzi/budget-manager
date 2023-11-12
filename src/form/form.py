import tkinter as tk
from tkinter import messagebox
import threading
import traceback
import logging
from abc import ABC, abstractmethod
from sqlite3 import Error
from thefuzz import fuzz
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
from src.tools.text_classifier import SimpleClassifier, fuzzy_search


def confirm_selection(func):
    def wrapper(self, *args, **kwargs):
        if messagebox.askokcancel("Confirm", "Are you sure?"):
            return func(self, *args, **kwargs)
        return

    return wrapper


logger = logging.getLogger("main").getChild(__name__)


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
    @confirm_selection
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
            "Bulk Upload Transactions",
            entry_id,
            action_buttons=self.action_buttons,
        )
        super().create_form()

    def infer_category(self, row, categories):
        if not row["Description"] and not row["Code"]:
            logger.debug(
                "Using default category Other as no description or code. %s", row
            )
            return ("Other", True)

        if row["Category"] in categories:
            logger.debug(
                "Using existing category for %s: %s",
                row["Description"],
                row["Category"],
            )
            return (row["Category"], False)
        code = row["Code"]
        if code:
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
                logger.debug(
                    """Found previoius transaction with same code %s.
                    Using previous category: %s""",
                    row["Code"],
                    prev_category[0][0],
                )
                return (prev_category[0][0], True)

        if not row["Description"]:
            logger.debug(
                "Using default category Other as no description was given. %s", row
            )
            return ("Other", False)
        result = self.text_classifier.predict(row["Description"], categories)
        logger.debug("Inferred category for %s: %s", row["Description"], result)
        return (result, True)

    def infer_categories(self, df, categories):
        """
        Auto fill the category column when missing.
        If the category is already in the db, use that
        If the code is the same as a previous transaction (fuzzy search), use that category
        Otherwise, use NLP to infer category
        """
        prev_transactions = self.db.select(
            """
                SELECT description, code, category FROM transactions
                WHERE code IS NOT NULL OR description IS NOT NULL
            """,
            [],
        )
        # add was inferred column
        df["Inferred_Category"] = False
        prev_codes = {row[1]: row[2] for row in prev_transactions if row[1]}
        prev_descriptions = {row[0]: row[2] for row in prev_transactions if row[0]}
        for _, row in df.iterrows():
            logger.debug("Infering category for\n %s", row)
            if row["Category"] in categories:
                logger.debug(
                    "Using existing category %s for row",
                    row["Category"],
                )
                continue
            code = row["Code"]
            description = row["Description"]
            if not code and not description:
                logger.debug(
                    "Using default category Other as no description or code. %s", row
                )
                row["Category"] = "Other"
                row["Inferred_Category"] = True
                continue

            if code:
                # if previous transaction has same code, use that category
                prev_code = fuzzy_search(
                    code, prev_codes.keys(), scorer=fuzz.partial_token_set_ratio
                )
                if prev_code:
                    prev_category = prev_codes[prev_code]
                    logger.debug(
                        """Found previous transaction %s with similar code to %s.
                        Using previous category: %s""",
                        prev_code,
                        code,
                        prev_category,
                    )
                    row["Category"] = prev_category
                    row["Inferred_Category"] = True
                    continue

            if description:
                # if previous transaction has same description, use that category
                prev_description = fuzzy_search(
                    description,
                    prev_descriptions.keys(),
                    scorer=fuzz.partial_token_sort_ratio,
                )
                if prev_description:
                    prev_category = prev_descriptions[prev_description]
                    logger.debug(
                        """Found previous transaction %s with similar description to %s.
                        Using previous category: %s""",
                        prev_description,
                        description,
                        prev_category,
                    )
                    row["Category"] = prev_category
                    row["Inferred_Category"] = True
                    continue

                # if no previous transaction has same description, use NLP
                result = self.text_classifier.predict(description, categories)
                logger.debug(
                    "Inferred category using NLP for %s: %s", description, result
                )
                row["Category"] = result
                row["Inferred_Category"] = True
            else:
                logger.debug(
                    "Using default category Other as no description was given and couldn't match code. %s",
                    row,
                )
                row["Category"] = "Other"
                row["Inferred_Category"] = True
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
                logger.debug("create_data_from_csv: got csv with data\n: %s", df)
                # validate column names
                expected_columns = ["Date", "Description", "Amount", "Category", "Code"]
                auto_added_columns = ["Inferred_Category", "file_id"]
                missing_cols = [
                    col for col in expected_columns if col not in df.columns
                ]
                if missing_cols:
                    error_msg = f"Missing columns: {', '.join(missing_cols)}"
                    logger.error("create_data_from_csv: %s", error_msg)
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
                    logger.error(
                        "create_data_from_csv: %s", "Date cannot be in the future"
                    )
                    logger.error(
                        "create_data_from_csv: erroneous_dates: %s", erroneous_dates
                    )
                    self.update_file_status(
                        file_record_id, "Error", "Date cannot be in the future"
                    )
                    return (False, "Date cannot be in the future")
                # convert dates to YYYY-MM-DD string
                df["Date"] = df["Date"].apply(
                    lambda x: x.strftime("%Y-%m-%d") if not pd.isnull(x) else None
                )

                df["Code"] = df["Code"].apply(
                    lambda x: str(x).strip() if not pd.isnull(x) else ""
                )
                df["Category"] = df["Category"].apply(
                    lambda x: str(x).title().strip() if not pd.isnull(x) else ""
                )
                # convert nan descriptions to empty string
                df["Description"] = df["Description"].apply(
                    lambda x: str(x).strip() if not pd.isnull(x) else ""
                )
                categories = set(df["Category"])

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
                    if category and category not in existing_categories
                ]
                if missing_categories:
                    error_msg = f"Missing categories: {', '.join(missing_categories)}"
                    logger.error("create_data_from_csv: %s", error_msg)
                    self.update_file_status(file_record_id, "Error", error_msg)
                    return (
                        False,
                        error_msg,
                    )

                data = []
                cols = expected_columns + auto_added_columns
                # for _, row in df.iterrows():
                #     category, was_inferred = self.infer_category(
                #         row, existing_categories
                #     )
                #     row["Category"] = category
                #     row["Inferred_Category"] = 1 if was_inferred else 0
                #     row["file_id"] = file_record_id
                #     row_data = tuple(row[col] for col in cols)
                #     data.append(row_data)

                df = self.infer_categories(df, categories)
                df["file_id"] = file_record_id
                data = df[cols].to_records(index=False).tolist()
                logger.debug("create_data_from_csv: data to insert: %s", data)

                # TODO: make this a transaction
                self.db.insert_many(
                    f"""
                        INSERT INTO transactions ({', '.join(cols)})
                        VALUES ({', '.join(['?'] * len(cols))})
                    """,
                    data,
                )
                self.clear_form()
                logger.info("create_data_from_csv: Successfully added transactions")
                self.update_file_status(
                    file_record_id, "Success", "Successfully processed"
                )
                return (True, "Successfully added transactions")
        except Exception as e:
            logger.error("create_data_from_csv: %s", e)
            logger.error(traceback.format_exc())
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

    @confirm_selection
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
            "Transactions",
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
            logger.error("Error updating transaction: %s", e)
            return (False, str(e))
        super().notify_update()
        transaction_descriptor = data["code"] or data["description"]
        return (True, "Successfully updated transaction " + transaction_descriptor)

    @confirm_selection
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
        vals = [data[col] for col in cols]
        vals.append(0)  # inferred category
        try:
            self.db.insert(
                f"""
                    INSERT INTO transactions ({', '.join(cols)}, inferred_category)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                vals,
            )
        except Error as e:
            logger.error("Error inserting transaction: %s", e)
            self.form_message_label.config(text=str(e), fg=ABForm.ERROR_COLOR)
            return (False, str(e))
        # self.clear_form()
        super().notify_update()
        transaction_descriptor = data["code"] or data["description"]
        self.form_message_label.config(
            text="Successfully added transasction " + transaction_descriptor,
            fg=ABForm.SUCCESS_COLOR,
        )
        return (True, "Successfully added transaction " + transaction_descriptor)


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
        super().__init__(self.form, self.form_fields, "Transactions")
        super().create_form()

    def on_success(self) -> (bool, str):
        # Data is valid, proceed with insertion
        data = {}
        for field in self.form_fields:
            data[field.get_name()] = field.get_value()
        data["inferred_category"] = 0
        cols = ["date", "description", "amount", "category", "code"]
        vals = [data[col] for col in cols]
        vals.append(0)  # inferred category
        try:
            self.db.insert(
                f"""
                    INSERT INTO transactions ({', '.join(cols)}, inferred_category)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                vals,
            )
        except Error as e:
            logger.error("Error inserting transaction: %s", e)
            return (False, str(e))
        transaction_descriptor = data["code"] or data["description"]
        return (True, "Successfully added transaction " + transaction_descriptor)

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
            "Budgets",
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
            logger.error("Error updating budget: %s", e)
            return (False, str(e))
        self.notify_update()
        budget_descriptor = data["category"] + " " + data["start_date"]
        return (True, "Successfully updated budget for " + budget_descriptor)

    @confirm_selection
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
            logger.error("Error inserting budget: %s", e)
            self.form_message_label.config(text=str(e), fg=ABForm.ERROR_COLOR)
            return (False, str(e))
        # self.clear_form()
        super().notify_update()
        budget_descriptor = data["category"] + " " + data["start_date"]
        self.form_message_label.config(
            text="Successfully added budget " + budget_descriptor,
            fg=ABForm.SUCCESS_COLOR,
        )
        return (True, "Successfully added budget " + budget_descriptor)


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
        super().__init__(self.form, self.form_fields, "Budgets")
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
            logger.error("Error updating budget: %s", e)
            return (False, str(e))
        budget_descriptor = data["category"] + " " + data["start_date"]
        return (True, "Successfully added budget " + budget_descriptor)

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
            "Categories",
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
            logger.error("Error updating category: %s", e)
            return (False, str(e))
        super().notify_update()
        category_descriptor = data["category"]
        return (True, "Successfully updated category " + category_descriptor)

    @confirm_selection
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
            logger.error("Error inserting category: %s", e)
            self.form_message_label.config(text=str(e), fg=ABForm.ERROR_COLOR)
            return (False, str(e))
        # self.clear_form()
        super().notify_update()
        category_descriptor = data["category"]
        self.form_message_label.config(
            text="Successfully added category " + category_descriptor,
            fg=ABForm.SUCCESS_COLOR,
        )
        return (True, "Successfully added category " + category_descriptor)
