import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from abc import ABC, abstractmethod
from src.form.form import (
    TransactionForm,
    TransactionsCsvForm,
    GenerateMonthlySummaryForm,
)
from src.db.data_summarizer import (
    get_transactions_df,
    get_budget_summary_df,
    get_monthly_income_df,
    get_budget_summary_plt,
)


class ABPage(tk.Frame, ABC):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.was_setup = False

    def clicked(self):
        if not self.was_setup:
            self.setup()
            self.was_setup = True
        self.on_click()

    @abstractmethod
    def setup(self):
        pass

    def on_click(self):
        pass


class DataEntry(ABPage):
    def setup(self):
        TransactionForm(self)
        TransactionsCsvForm(self)



class Home(ABPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.budget_frames = []
        # self.setup()

    def notify(self, month):
        self.budget_summary(month)

    def budget_summary(self, month):
        df = get_budget_summary_df(month)
        if self.budget_frames:
            for frame in self.budget_frames:
                frame.destroy()
        upper_frame = tk.Frame(self)
        self.budget_frames.append(upper_frame)
        upper_frame.pack(fill="both", expand=True)
        upper_frame.pack(pady=10)
        # Create a Treeview widget to display the DataFrame
        tree = ttk.Treeview(upper_frame, columns=list(df.columns), show="headings")

        # Add column headings
        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        # Insert data into the Treeview
        for _, row in df.iterrows():
            tree.insert("", "end", values=list(row))

        tree.pack(side="left", fill="both", expand=True)

        # create frame for plot
        plot_frame = tk.Frame(upper_frame)
        self.budget_frames.append(plot_frame)
        plot_frame.pack(pady=10)
        fig = get_budget_summary_plt(month)
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side="right", fill="both", expand=True)

    def setup(self):
        form = GenerateMonthlySummaryForm(self)
        form.register_listener(self)


class Transactions(ABPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.transactions_frame = None
        self.tree = None
        # self.setup()

    def show_transactions(self):
        df = get_transactions_df()
        if self.transactions_frame:
            self.transactions_frame.destroy()
        # Create a Treeview widget to display the DataFrame
        self.transactions_frame = tk.Frame(self)
        self.transactions_frame.pack(fill="both", expand=True)
        cols = list(df.columns)
        tree = ttk.Treeview(
            self.transactions_frame, columns=cols + ["Edit", "Delete"], show="headings"
        )

        self.tree = tree
        # Add column headings
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        tree.heading("Edit", text="")
        tree.column("Edit", width=100)
        tree.heading("Delete", text="")
        tree.column("Delete", width=100)

        # Insert data into the Treeview
        # add edit and delete buttons to each row
        for _, row in df.iterrows():
            tree.insert("", "end", values=list(row) + ["Edit", "Delete"])

        # # Add buttons to each row
        # for item in tree.get_children():
        #     tree.insert(item, "end", values=["Edit", "Delete"])
        #     tree.item(item, values=row_values + [None, None], tags=(item,))

        tree.pack(side="left", fill="both", expand=True)
        tree.bind("<Double-Button-1>", self.edit_transaction)

    def edit_transaction(self, event):
        item = event.widget.selection()[0]
        row_vals = event.widget.item(item)["values"]
        clicked_col = event.widget.identify_column(event.x)
        cell_value = event.widget.item(item)["values"][
            int(clicked_col[1:]) - 1
        ]  # The value of the cell clicked
        # cell_value = self.tree.item(item, "values")[int(clicked_col) - 1]

        entry = tk.Entry(event.widget, width=10)
        # place entry on top of cell clicked
        entry.place(
            x=event.x,
            y=event.y,
            width=entry.winfo_reqwidth(),
            height=entry.winfo_reqheight(),
        )
        entry.focus_set()
        entry.bind("<Return>", lambda event: self.update_cell(event, item, clicked_col))
        entry.bind("<Escape>", lambda event: self.cancel_edit(event, item, clicked_col))

    def cancel_edit(self, event, item, clicked_col):
        self.tree.delete(self.tree.focus())

    def update_cell(self, event, item, clicked_col):
        new_value = event.widget.get()
        event.widget.set(item, column=clicked_col, value=new_value)
        event.widget.destroy()

    def setup(self):
        # create a bar with filters and refresh button
        filter_frame = tk.Frame(self)
        filter_frame.pack(pady=10)
        # create a button to refresh the transactions
        refresh_button = tk.Button(
            filter_frame, text="Refresh", command=self.show_transactions
        )
        refresh_button.pack(side="right")
        # dropdown to allow to filter by each column
        df = get_transactions_df()
        filter_options = list(df.columns)
        filter_var = tk.StringVar()
        filter_var.set(filter_options[0])
        filter_dropdown = tk.OptionMenu(filter_frame, filter_var, *filter_options)
        filter_dropdown.pack(side="left")
        # entry to allow to filter by a value

        self.show_transactions()
