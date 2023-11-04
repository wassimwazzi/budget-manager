import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from src.form.form import (
    AddTransactionForm,
    TransactionsCsvForm,
    GenerateMonthlySummaryForm,
    EditTransactionForm,
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
        # Create a frame for the page that will be used, and can be destroyed and recreated
        self.frame = tk.Frame(self)
        self.frame.pack(fill="both", expand=True)
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

    def clear(self):
        # remove all widgets from the frame
        for widget in self.frame.winfo_children():
            widget.destroy()

    def refresh(self):
        self.clear()
        self.setup()


class DataEntry(ABPage):
    def setup(self):
        AddTransactionForm(self)
        TransactionsCsvForm(self)


class Home(ABPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.budget_frames = []
        # self.setup()

    def notify(self, month):
        self.budget_summary(month)

    def budget_summary(self, month):
        df = get_budget_summary_df(month)
        if self.budget_frames:
            for frame in self.budget_frames:
                frame.destroy()
        upper_frame = tk.Frame(self.frame)
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
        form = GenerateMonthlySummaryForm(self.frame)
        form.register_listener(self)


class Transactions(ABPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.transactions_form_frame = None
        self.transactions_table_frame = None
        self.transactions_form = None
        self.transactions_df = None

    def show_transactions(self):
        if self.transactions_df is None:
            self.transactions_df = get_transactions_df()
        # Create a Treeview widget to display the DataFrame
        if self.transactions_table_frame:
            self.transactions_table_frame.destroy()
        self.transactions_table_frame = tk.Frame(self.frame)
        self.transactions_table_frame.pack(fill="both", expand=True)
        cols = [
            "date",
            "description",
            "amount",
            "category",
            "code",
            "inferred category",
        ]
        tree = ttk.Treeview(
            self.transactions_table_frame,
            columns=cols + ["Edit", "Delete"],
            show="headings",
        )

        # Add column headings
        for col in cols:
            tree.heading(col, text=col.title())
            tree.column(col, width=100)
        tree.heading("Edit", text="")
        tree.column("Edit", width=100)
        tree.heading("Delete", text="")
        tree.column("Delete", width=100)

        # Insert data into the Treeview
        # add edit and delete buttons to each row
        for _, row in self.transactions_df.iterrows():
            # make sure row values are in same order as columns
            row_values = [row[col] for col in cols]
            tree.insert("", "end", values=row_values + ["Edit", "Delete"])

        # # Add buttons to each row
        # for item in tree.get_children():
        #     tree.insert(item, "end", values=["Edit", "Delete"])
        #     tree.item(item, values=row_values + [None, None], tags=(item,))

        tree.pack(side="left", fill="both", expand=True)
        tree.bind("<Button-1>", self.edit_transaction)

    def edit_transaction(self, event):
        selected_row = event.widget.selection()
        if not selected_row:
            # q: why is this sometimes empty?
            return
        selected_row = selected_row[0]
        # clear the form frame
        for widget in self.transactions_form_frame.winfo_children():
            widget.destroy()

        row_id = event.widget.index(selected_row)
        transaction_id = self.transactions_df.loc[int(row_id)]["id"]
        self.transactions_form = EditTransactionForm(
            self.transactions_form_frame, transaction_id
        )
        self.transactions_form.register_listener(self)
        fields = self.transactions_form.get_form_fields()
        for field in fields:
            field.set_value(self.transactions_df.loc[int(row_id)][field.get_name()])

    def setup(self):
        self.transactions_form_frame = tk.Frame(self.frame)
        self.transactions_form_frame.pack(pady=10, side="top", fill="both", expand=True)
        # Create empty form
        self.transactions_form = EditTransactionForm(self.transactions_form_frame, None)
        # create a bar with filters and refresh button
        filter_frame = tk.Frame(self.frame)
        filter_frame.pack(pady=10)
        # create a button to refresh the transactions
        refresh_button = tk.Button(filter_frame, text="Refresh", command=self.refresh)
        refresh_button.pack(side="right")
        # dropdown to allow to filter by each column
        self.transactions_df = get_transactions_df()
        filter_options = list(self.transactions_df.columns)
        filter_var = tk.StringVar()
        filter_var.set(filter_options[0])
        filter_dropdown = tk.OptionMenu(filter_frame, filter_var, *filter_options)
        filter_dropdown.pack(side="left")
        # entry to allow to filter by a value

        self.show_transactions()

    def notify_update(self):
        self.refresh()

    def refresh(self):
        # only refresh the transactions table
        self.transactions_df = None
        self.show_transactions()
