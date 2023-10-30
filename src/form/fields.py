from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import filedialog


class FieldType(Enum):
    DATE = "date"
    TEXT = "text"
    NUMBER = "number"
    DROPDOWN = "dropdown"
    UPLOAD_FILE = "upload_file"


class FormField(ABC):
    def __init__(
        self, name: str, field_type: FieldType, required: bool, form: tk.Frame
    ):
        self.name = name
        self.field_type = field_type
        self.required = required
        self.form = form
        self.tk_field = None
        self.error = None

    def get_name(self) -> str:
        return self.name

    def get_type(self) -> FieldType:
        return self.field_type

    def is_required(self) -> bool:
        return self.required

    def get_form(self) -> tk.Frame:
        return self.form

    def get_value(self):
        return self.get_tk_field().get()

    def validate(self) -> bool:
        value = self.get_value()
        if self.required and not value:
            return (False, "Required field")
        valid, message = self.validate_value(value)
        if not valid:
            self.error = message
        return (valid, message)

    def get_tk_field(self):
        if self.tk_field:
            return self.tk_field
        self.tk_field = self.get_tk_field_template()
        return self.tk_field

    def get_error(self) -> str:
        return self.error

    def clear(self):
        self.get_tk_field().delete(0, "end")

    @abstractmethod
    def validate_value(self, value: str) -> (bool, str):
        """
        Should return a tuple of (bool, str)
        bool: True if valid, False if not
        str: Error message if invalid, None if valid
        """

    @abstractmethod
    def get_tk_field_template(self):
        pass


class DateField(FormField):
    def __init__(self, name: str, required: bool, form: tk.Frame):
        super().__init__(name, FieldType.DATE, required, form)

    def validate_value(self, value: str) -> (bool, str):
        try:
            date = datetime.strptime(value, "%Y-%m-%d")
            today = datetime.now()
            if date > today:
                return (False, "Date cannot be in the future")
            return (True, None)
        except ValueError:
            return (False, "Invalid date format, must be YYYY-MM-DD")

    def get_tk_field_template(self):
        return tk.Entry(self.get_form())


class TextField(FormField):
    def __init__(self, name: str, required: bool, form: tk.Frame):
        super().__init__(name, FieldType.TEXT, required, form)

    def validate_value(self, value: str) -> (bool, str):
        return (True, None)

    def get_tk_field_template(self):
        return tk.Entry(self.get_form())


class NumberField(FormField):
    def __init__(self, name: str, required: bool, form: tk.Frame):
        super().__init__(name, FieldType.NUMBER, required, form)

    def validate_value(self, value: str) -> (bool, str):
        valid = value.replace(".", "").isdigit()
        if not valid:
            return (False, "Invalid number")
        return (True, None)

    def get_tk_field_template(self):
        return tk.Entry(self.get_form())


class DropdownField(FormField):
    def __init__(self, name: str, required: bool, options: list[str], form: tk.Frame):
        super().__init__(name, FieldType.DROPDOWN, required, form)
        self.options = options
        self.clicked = tk.StringVar()

    def validate_value(self, value: str) -> (bool, str):
        valid = value in self.options
        if not valid:
            return (False, "Invalid option")
        return (True, None)

    def get_tk_field_template(self):
        if self.options:
            self.clicked.set(self.options[0])
        else:
            self.options.append("")
        return tk.OptionMenu(self.form, self.clicked, *self.options)

    def get_value(self) -> str:
        return self.clicked.get()

    def get_options(self) -> list[str]:
        return self.options

    def clear(self):
        self.clicked.set(self.options[0])


class UploadFileField(FormField):
    def __init__(
        self,
        name: str,
        required: bool,
        form: tk.Frame,
        file_types: list[(str, str)] = None,
    ):
        self.file_types = file_types or [("All", "*.*")]
        self.uploaded_file_path = None
        super().__init__(name, FieldType.UPLOAD_FILE, required, form)

    def validate_value(self, value: str) -> (bool, str):
        # Validation is done in the upload_file method
        return (True, None)

    def get_tk_field_template(self, **kwargs):
        return tk.Button(
            self.form,
            text="Upload file",
            command=self.upload_file,
            font=("Arial", 12),
            fg="black",
            **kwargs,
        )

    def upload_file(self):
        file_path = filedialog.askopenfilename(
            title="Select file", filetypes=self.file_types
        )
        self.get_tk_field().config(text=file_path, fg="black")
        self.uploaded_file_path = file_path

    def get_value(self) -> str:
        return self.uploaded_file_path

    def clear(self):
        self.uploaded_file_path = None
        self.get_tk_field().config(text="Upload file", fg="black")
