import tkinter as tk
from src.constants import (
    TKINTER_BACKGROUND_COLOR,
    TEXT_FOREGROUND_COLOR,
    TEXT_BACKGROUND_COLOR,
)


class DefaultFrame(tk.Frame):
    """
    Use this for defaulting to background color defined in constants.py
    """

    def __init__(self, *args, **kwargs):
        if "bg" in kwargs.keys():
            background = kwargs.pop("bg")
        elif "background" in kwargs.keys():
            background = kwargs.pop("background")
        else:
            background = TKINTER_BACKGROUND_COLOR

        super().__init__(*args, background=background, **kwargs)


def set_defaults(kwargs):
    """
    Set default values in dictionary
    """
    kwargs.setdefault("fg", TEXT_FOREGROUND_COLOR)
    kwargs.setdefault("bg", TEXT_BACKGROUND_COLOR)
    kwargs.setdefault("highlightbackground", TEXT_BACKGROUND_COLOR)
    kwargs.setdefault("highlightcolor", TEXT_FOREGROUND_COLOR)


class DefaultLabel(tk.Label):
    def __init__(self, *args, **kwargs):
        set_defaults(kwargs)
        super().__init__(*args, **kwargs)


class DefaultButton(tk.Button):
    def __init__(self, *args, **kwargs):
        set_defaults(kwargs)
        super().__init__(*args, **kwargs)


class DefaultOptionMenu(tk.OptionMenu):
    pass


class DefaultEntry(tk.Entry):
    def __init__(self, *args, **kwargs):
        set_defaults(kwargs)
        super().__init__(*args, **kwargs)


class DefaultCheckButton(tk.Checkbutton):
    def __init__(self, *args, **kwargs):
        set_defaults(kwargs)
        super().__init__(*args, **kwargs)
