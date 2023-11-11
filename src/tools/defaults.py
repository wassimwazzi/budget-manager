import tkinter as tk
from src.constants import TKINTER_BACKGROUND_COLOR, TEXT_FOREGROUND_COLOR, TEXT_BACKGROUND_COLOR


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


class DefaultLabel(tk.Label):
    def __init__(self, *args, **kwargs):
        fg = kwargs.pop('fg', TEXT_FOREGROUND_COLOR)
        bg = kwargs.pop('bg', TEXT_BACKGROUND_COLOR)
        hbg = kwargs.pop('highlightbackground', TEXT_BACKGROUND_COLOR)
        hc = kwargs.pop('highlightcolor', TEXT_FOREGROUND_COLOR)
        super().__init__(*args, fg=fg, bg=bg, highlightbackground=hbg, highlightcolor=hc, **kwargs)