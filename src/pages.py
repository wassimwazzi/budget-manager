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
    get_budget_vs_spend_plt,
    get_spend_per_cateogire_pie_chart_plt,
    get_budget_minus_spend_bar_chart_plt
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
        fig = get_budget_vs_spend_plt(month)
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side="right", fill="both", expand=True)

        lower_frame = tk.Frame(self.frame)
        self.budget_frames.append(lower_frame)
        lower_frame.pack(fill="both", expand=True)
        # create pie chart
        fig = get_spend_per_cateogire_pie_chart_plt(month)
        canvas = FigureCanvasTkAgg(fig, master=lower_frame)
        canvas.get_tk_widget().configure(width=500, height=500)
        canvas.draw()
        canvas.get_tk_widget().pack(side="left", fill="both", expand=True)

        # create budget - spend bar chart
        fig = get_budget_minus_spend_bar_chart_plt(month)
        canvas = FigureCanvasTkAgg(fig, master=lower_frame)
        canvas.get_tk_widget().configure(width=500, height=500)
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
            columns=cols,
            show="headings",
        )

        # Add column headings
        for col in cols:
            tree.heading(col, text=col.title())
            tree.column(col, width=100)

        # Insert data into the Treeview
        # add edit and delete buttons to each row
        for _, row in self.transactions_df.iterrows():
            # make sure row values are in same order as columns
            row_values = [row[col] for col in cols]
            tree.insert("", "end", values=row_values)

        tree.pack(side="left", fill="both", expand=True)
        tree.bind("<Button-1>", self.edit_transaction)

    def show_filters(self):
        # create a bar with filters and refresh button
        filter_frame = tk.Frame(self.frame)
        filter_frame.pack(pady=10)
        # create a button to refresh the transactions
        refresh_button = tk.Button(filter_frame, text="Refresh", command=self.refresh)
        # put on right side
        refresh_button.grid(row=1, column=0)
        # dropdown to allow to sort by each column
        sort_label = tk.Label(filter_frame, text="Sort by:")
        sort_label.grid(row=0, column=1)
        sort_options = list(self.transactions_df.columns)
        sort_options.remove("id")
        sort_var = tk.StringVar()
        sort_var.set(sort_options[0])
        sort_dropdown = tk.OptionMenu(filter_frame, sort_var, *sort_options)
        sort_dropdown.grid(row=1, column=1)
        # asc or desc checkbox
        sort_asc_var = tk.BooleanVar()
        sort_asc_var.set(True)
        sort_asc_checkbox = tk.Checkbutton(
            filter_frame, text="Ascending", variable=sort_asc_var
        )
        sort_asc_checkbox.grid(row=1, column=2)
        # dropdown for search column
        search_menu_label = tk.Label(filter_frame, text="Search column:")
        search_menu_label.grid(row=0, column=3)
        search_menu_var = tk.StringVar()
        search_menu_var.set(sort_options[0])
        search_menu = tk.OptionMenu(filter_frame, search_menu_var, *sort_options)
        search_menu.grid(row=1, column=3)
        # search for a string in a column
        search_label = tk.Label(filter_frame, text="Search:")
        search_label.grid(row=0, column=4)
        search_var = tk.StringVar()
        search_entry = tk.Entry(filter_frame, textvariable=search_var)
        search_entry.grid(row=1, column=4)
        # submit button
        submit_button = tk.Button(
            filter_frame,
            text="Submit",
            command=lambda: self.filter_transactions(
                sort_var.get(),
                sort_asc_var.get(),
                search_menu_var.get(),
                search_var.get(),
            ),
        )
        submit_button.grid(row=1, column=5)

    def filter_transactions(self, sort_col, sort_asc, search_col, search_str):
        # get the transactions df
        if self.transactions_df is None:
            self.transactions_df = get_transactions_df()
        # filter by search string
        if search_str:
            match search_col:
                case "date":
                    self.transactions_df = self.transactions_df[
                        self.transactions_df[search_col].str.contains(search_str)
                    ]
                case "amount":
                    self.transactions_df = self.transactions_df[
                        self.transactions_df[search_col]
                        .astype(str)
                        .str.contains(search_str)
                    ]
                case _:
                    self.transactions_df = self.transactions_df[
                        self.transactions_df[search_col]
                        .str.lower()
                        .str.contains(search_str.lower())
                    ]
        # sort by column
        self.transactions_df = self.transactions_df.sort_values(
            by=sort_col, ascending=sort_asc
        ).reset_index(
            drop=True
        )  # reset index so that it matches the row number in the table when editing
        # refresh the transactions table
        self.show_transactions()

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
        self.transactions_df = get_transactions_df()
        self.transactions_form_frame = tk.Frame(self.frame)
        self.transactions_form_frame.pack(pady=10, side="top", fill="both", expand=True)
        # Create empty form
        self.transactions_form = EditTransactionForm(self.transactions_form_frame, None)
        self.show_filters()
        self.show_transactions()

    def notify_update(self):
        self.refresh()

    def refresh(self):
        # only refresh the transactions table
        self.transactions_df = None
        self.show_transactions()
