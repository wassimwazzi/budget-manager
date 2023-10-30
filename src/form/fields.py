from enum import Enum
from abc import ABC, abstractmethod
import tkinter as tk


class FieldType(Enum):
    DATE = "date"
    TEXT = "text"
    NUMBER = "number"
    DROPDOWN = "dropdown"


class FormField(ABC):
    def __init__(self, name: str, field_type: FieldType, required: bool):
        self.name = name
        self.field_type = field_type
        self.required = required

    def get_name(self) -> str:
        return self.name

    def get_type(self) -> FieldType:
        return self.field_type

    def is_required(self) -> bool:
        return self.required

    def validate(self, value: str) -> bool:
        if self.required and not value:
            return (False, "Required field")
        return self.validate_value(value)

    @abstractmethod
    def validate_value(self, value: str) -> bool:
        pass

    @abstractmethod
    def get_tk_field(self, form: tk.Frame):
        pass


class DateField(FormField):
    def __init__(self, name: str, required: bool):
        super().__init__(name, FieldType.DATE, required)

    def validate_value(self, value: str) -> bool:
        try:
            date = datetime.strptime(value, "%Y-%m-%d")
            today = datetime.now()
            if date > today:
                return (False, "Date cannot be in the future")
            return (True, None)
        except ValueError:
            return (False, "Invalid date format, must be YYYY-MM-DD")

    def get_tk_field(self, form: tk.Frame):
        tk_field = tk.Entry(form)
        return tk_field


class TextField(FormField):
    def __init__(self, name: str, required: bool):
        super().__init__(name, FieldType.TEXT, required)

    def validate_value(self, value: str) -> bool:
        return (True, None)

    def get_tk_field(self, form: tk.Frame):
        tk_field = tk.Entry(form)
        return tk_field


class NumberField(FormField):
    def __init__(self, name: str, required: bool):
        super().__init__(name, FieldType.NUMBER, required)

    def validate_value(self, value: str) -> bool:
        valid = value.replace(".", "").isdigit()
        if not valid:
            return (False, "Invalid number")
        return (True, None)

    def get_tk_field(self, form: tk.Frame):
        tk_field = tk.Entry(form)
        return tk_field


class DropdownField(FormField):
    def __init__(self, name: str, required: bool, options: list[str]):
        super().__init__(name, FieldType.DROPDOWN, required)
        self.options = options

    def validate_value(self, value: str) -> bool:
        valid = value in self.options
        if not valid:
            return (False, "Invalid option")
        return (True, None)

    def get_tk_field(self, form: tk.Frame):
        tk_field = tk.OptionMenu(form, *self.options)
        return tk_field

    def get_options(self) -> list[str]:
        return self.options
