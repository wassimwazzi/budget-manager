import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from screeninfo import get_monitors
from src.pages import HomePage, DataEntryPage
from src.nav import NavFrame

PAGES = [HomePage, DataEntryPage]  # first page is the default page


class BudgetApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.minsize(*self.get_display_size())
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=9)  # 10% for the navbar
        container.grid_columnconfigure(0, weight=1)

        # Add navbar
        nav_frame = NavFrame(container, self, PAGES, HomePage)
        nav_frame.grid(row=0, column=0, sticky="nsew")

        self.frames = {}

        for Page in PAGES:
            frame = Page(container)
            self.frames[Page] = frame
            frame.grid(row=1, column=0, sticky="nsew")

        self.show_frame(PAGES[0])

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.tkraise()

    def get_display_size(self):
        # get the height and width of the display

        monitor = get_monitors()[0]
        return monitor.width, monitor.height


def run():
    app = BudgetApp()
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            app.destroy()
            plt.close("all")
    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()
