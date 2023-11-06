import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from src.form.form import (
    AddTransactionForm,
    TransactionsCsvForm,
    GenerateMonthlySummaryForm,
    EditTransactionForm,
    EditBudgetForm,
    AddBudgetForm,
)
from src.db.data_summarizer import (
    get_transactions_df,
    get_budget_summary_df,
    get_monthly_income_df,
    get_budgets_df,
    get_files_df,
    get_budget_vs_spend_plt,
    get_spend_per_cateogire_pie_chart_plt,
    get_budget_minus_spend_bar_chart_plt,
)


class EditableTable(tk.Frame):
    def __init__(self, parent, get_data_func, edit_form_cls, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.get_data_func = get_data_func
        self.data = get_data_func()
        self.columns = list(self.data.columns)
        self.display_columns = self.columns.copy()
        self.display_columns.remove("id")
        self.table_frame = tk.Frame(self)
        self.table_frame.pack(side="bottom", fill="both", expand=True)
        self.edit_form_cls = edit_form_cls
        self.edit_form_frame = tk.Frame(self)
        self.edit_form_frame.pack(side="top", fill="both", expand=True)
        self.edit_form = edit_form_cls(self.edit_form_frame, None)
        self.show_filters()
        self.show_table()

    def on_row_click(self, event):
        selected_row = event.widget.selection()
        if not selected_row:
            # q: why is this sometimes empty?
            return
        selected_row = selected_row[0]
        # clear the form frame
        for widget in self.edit_form_frame.winfo_children():
            widget.destroy()

        row_id = event.widget.index(selected_row)
        transaction_id = self.data.loc[int(row_id)]["id"]
        self.edit_form = self.edit_form_cls(self.edit_form_frame, transaction_id)
        self.edit_form.register_listener(self)
        fields = self.edit_form.get_form_fields()
        for field in fields:
            field.set_value(self.data.loc[int(row_id)][field.get_name()])

    def show_table(self):
        if self.data is None:
            self.data = self.get_data_func()
        # Create a Treeview widget to display the DataFrame
        if self.table_frame:
            self.table_frame.destroy()
        self.table_frame = tk.Frame(self)
        self.table_frame.pack(fill="both", expand=True)
        cols = self.display_columns
        tree = ttk.Treeview(
            self.table_frame,
            columns=cols,
            show="headings",
        )

        # Add column headings
        for col in cols:
            tree.heading(col, text=col.title())
            tree.column(col, width=100)

        # Insert data into the Treeview
        # add edit and delete buttons to each row
        for _, row in self.data.iterrows():
            # make sure row values are in same order as columns
            row_values = [row[col] for col in cols]
            tree.insert("", "end", values=row_values)

        tree.pack(side="left", fill="both", expand=True)
        tree.bind("<Button-1>", self.on_row_click)

    def show_filters(self):
        # create a bar with filters and refresh button
        filter_frame = tk.Frame(self)
        filter_frame.pack(pady=10)
        # create a button to refresh the transactions
        refresh_button = tk.Button(filter_frame, text="Refresh", command=self.refresh)
        # put on right side
        refresh_button.grid(row=1, column=0)
        # dropdown to allow to sort by each column
        sort_label = tk.Label(filter_frame, text="Sort by:")
        sort_label.grid(row=0, column=1)
        sort_options = self.display_columns
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
            command=lambda: self.filter_table(
                sort_var.get(),
                sort_asc_var.get(),
                search_menu_var.get(),
                search_var.get(),
            ),
        )
        submit_button.grid(row=1, column=5)

    def filter_table(self, sort_col, sort_asc, search_col, search_str):
        # get the transactions df
        if self.data is None:
            self.data = self.get_data_func()
        # filter by search string
        self.data = self.data[
            self.data[search_col]
            .astype(str)
            .str.lower()
            .str.contains(search_str.lower())
        ]
        # sort by column
        self.data = self.data.sort_values(by=sort_col, ascending=sort_asc).reset_index(
            drop=True
        )  # reset index so that it matches the row number in the table when editing
        # refresh the transactions table
        self.show_table()

    def notify_update(self):
        self.refresh()

    def refresh(self):
        self.data = None
        self.show_table()


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
        AddBudgetForm(self)


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
    def setup(self):
        table_frame = EditableTable(
            self.frame,
            get_transactions_df,
            EditTransactionForm,
        )
        table_frame.pack(fill="both", expand=True)


class Budget(ABPage):
    def setup(self):
        table_frame = EditableTable(
            self.frame,
            get_budgets_df,
            EditBudgetForm,
        )
        table_frame.pack(fill="both", expand=True)


class Files(ABPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.table_frame = None

    def show_table(self):
        if self.table_frame:
            self.table_frame.destroy()
        self.table_frame = tk.Frame(self.frame)
        self.table_frame.pack(fill="both", expand=True)
        df = get_files_df()
        # Create a Treeview widget to display the DataFrame
        cols = list(df.columns)
        cols.remove("id")
        tree = ttk.Treeview(self.table_frame, columns=cols, show="headings")
        # Add column headings
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        # Insert data into the Treeview
        for _, row in df.iterrows():
            row_values = [row[col] for col in cols]
            tree.insert("", "end", values=row_values)

        tree.pack(side="left", fill="both", expand=True)

    def show_filter(self):
        # Only refresh button
        refresh_button = tk.Button(self.frame, text="Refresh", command=self.show_table)
        refresh_button.pack()

    def setup(self):
        self.show_filter()
        self.show_table()
