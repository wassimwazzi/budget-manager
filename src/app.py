import tkinter as tk
from src.pages import HomePage, DataEntryPage
from src.nav import NavFrame

PAGES = [HomePage, DataEntryPage]  # first page is the default page


class BudgetApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        # add navbar
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


def run():
    app = BudgetApp()
    app.mainloop()
