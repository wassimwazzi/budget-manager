import tkinter as tk
from tkinter import ttk
from tkinter.constants import VERTICAL, Y, RIGHT, FALSE, LEFT, BOTH, TRUE, NW
from tkinter import messagebox
import matplotlib.pyplot as plt
from screeninfo import get_monitors
from src.pages import Home, Transactions, Budget, Files, Categories
from src.nav import NavFrame

PAGES = [
    Home,
    Transactions,
    Budget,
    Files,
    Categories,
]  # first page is the default page


class VerticalScrolledFrame(ttk.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame.
    * Construct and pack/place/grid normally.
    * This frame only allows vertical scrolling.
    """

    def __init__(self, parent, *args, **kw):
        ttk.Frame.__init__(self, parent, *args, **kw)

        # Create a canvas object and a vertical scrollbar for scrolling it.
        vscrollbar = ttk.Scrollbar(self, orient=VERTICAL)
        vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
        canvas = tk.Canvas(
            self, bd=0, highlightthickness=0, yscrollcommand=vscrollbar.set
        )
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        vscrollbar.config(command=canvas.yview)

        # Reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # Create a frame inside the canvas which will be scrolled with it.
        self.interior = interior = ttk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior, anchor=NW)

        # Track changes to the canvas and frame width and sync them,
        # also updating the scrollbar.
        def _configure_interior(event):
            # Update the scrollbars to match the size of the inner frame.
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # Update the canvas's width to fit the inner frame.
                canvas.config(width=interior.winfo_reqwidth())

        interior.bind("<Configure>", _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # Update the inner frame's width to fill the canvas.
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())

        canvas.bind("<Configure>", _configure_canvas)


class BudgetApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry(f"{self.get_display_size()[0]}x{self.get_display_size()[1]}")
        # Add navbar
        nav_frame = NavFrame(self, self, PAGES, Home)
        nav_frame.pack(side="top", fill="both", expand=False)

        container = VerticalScrolledFrame(self)
        container.pack(side="top", fill="both", expand=True)
        self.container = container

        self.frames = {}

        for Page in PAGES:
            frame = Page(container.interior)
            self.frames[Page] = frame
            frame.pack(fill="both", expand=True)

        self.current_frame = None
        self.show_frame(PAGES[0])

    def show_frame(self, frame_class):
        if self.current_frame:
            self.current_frame.pack_forget()
        frame = self.frames[frame_class]
        frame.clicked()
        frame.pack(fill="both", expand=True)
        self.current_frame = frame

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
