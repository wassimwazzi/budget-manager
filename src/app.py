import tkinter as tk
from src.form.form import TransactionForm, TransactionsCsvForm


class BudgetApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for Page in (HomePage, DataEntryPage):
            frame = Page(container, self)
            self.frames[Page] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(HomePage)

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.tkraise()


class DataEntryPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        label = tk.Label(self, text="Data Entry Page")
        label.pack(pady=10, padx=10)
        button = tk.Button(
            self,
            text="Go to Home",
            command=lambda: controller.show_frame(HomePage),
        )
        button.pack()
        TransactionForm(self)
        TransactionsCsvForm(self)


class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        label = tk.Label(self, text="Home Page")
        label.pack(pady=10, padx=10)
        button = tk.Button(
            self,
            text="Go to Data Entry Page",
            command=lambda: controller.show_frame(DataEntryPage),
        )
        button.pack()
        TransactionForm(self)
        TransactionsCsvForm(self)


def run():
    app = BudgetApp()
    app.mainloop()
