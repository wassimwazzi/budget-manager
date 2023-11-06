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
        self.edit_form.register_listener(self)
        self.filters_submit_button = None
        self.applied_search_filters = []
        self.filter_frame = None
        self.filters = []
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
        tree.pack(side="left", fill="both", expand=True)

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

        tree.bind("<Button-1>", self.on_row_click)

    def show_filters(self):
        # create a bar with filters and refresh button
        self.filters = []
        filter_frame = tk.Frame(self)
        filter_frame.pack(pady=10, side="top")
        self.filter_frame = filter_frame
        # create a button to refresh the transactions
        refresh_button = tk.Button(filter_frame, text="Refresh", command=self.refresh)
        # put on right side
        refresh_button.grid(row=1, column=0)
        self.filters.append((tk.Button, refresh_button))
        # dropdown to allow to sort by each column
        sort_label = tk.Label(filter_frame, text="Sort by:")
        sort_label.grid(row=0, column=1)
        sort_options = self.display_columns
        sort_var = tk.StringVar()
        sort_var.set(sort_options[0])
        self.filters.append((tk.OptionMenu, sort_var))
        sort_dropdown = tk.OptionMenu(filter_frame, sort_var, *sort_options)
        sort_dropdown.grid(row=1, column=1)
        # asc or desc checkbox
        sort_asc_var = tk.BooleanVar()
        sort_asc_var.set(False)
        sort_asc_checkbox = tk.Checkbutton(
            filter_frame, text="Ascending", variable=sort_asc_var
        )
        sort_asc_checkbox.grid(row=1, column=2)
        self.filters.append((tk.Checkbutton, sort_asc_var))
        # dropdown for search column
        search_menu_label = tk.Label(filter_frame, text="Search column:")
        search_menu_label.grid(row=0, column=3)
        search_menu_var = tk.StringVar()
        search_menu_var.set(sort_options[0])
        search_menu = tk.OptionMenu(filter_frame, search_menu_var, *sort_options)
        search_menu.grid(row=1, column=3)
        self.filters.append((tk.OptionMenu, search_menu_var))
        # search for a string in a column
        search_label = tk.Label(filter_frame, text="Search:")
        search_label.grid(row=0, column=4)
        search_var = tk.StringVar()
        search_entry = tk.Entry(filter_frame, textvariable=search_var)
        search_entry.grid(row=1, column=4)
        self.filters.append((tk.Entry, search_var))
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
        self.filters_submit_button = submit_button
        self.filters.append((tk.Button, submit_button))

    def show_applied_filters(self):
        # show applied search filters
        if self.applied_search_filters:
            applied_filters_label = tk.Label(
                self.filter_frame, text="Applied filters:", font=("Arial", 10)
            )
            applied_filters_label.grid(row=0, column=len(self.filters) + 1)
            filters = ", ".join(self.applied_search_filters)
            applied_filters = tk.Label(self.filter_frame, text=filters)
            applied_filters.grid(row=1, column=len(self.filters) + 1)
        else:
            # remove applied filters label
            for widget in self.filter_frame.winfo_children():
                if widget.grid_info()["column"] == len(self.filters) + 1:
                    widget.destroy()

    def clear_filters(self):
        self.applied_search_filters = []
        for filter_type, filter_value in self.filters:
            if filter_type == tk.Entry:
                filter_value.set("")
            elif filter_type == tk.OptionMenu:
                filter_value.set(self.display_columns[0])
            elif filter_type == tk.Checkbutton:
                filter_value.set(False)
        self.show_applied_filters()
        self.show_table()

    def filter_table(
        self, sort_col, sort_asc, search_col, search_str, update_filters=True
    ):
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
        if search_str and update_filters:
            self.applied_search_filters.append(search_col)
        self.show_applied_filters()
        self.show_table()

    def notify_update(self):
        self.data = None
        self.show_table()
        # keep applied filters, if any
        args = []
        for filter_type, filter_value in self.filters:
            if filter_type != tk.Button:
                args.append(filter_value.get())
        assert len(args) == 4
        self.filter_table(*args[:4], update_filters=False)

    def refresh(self):
        self.data = None
        self.applied_search_filters = []
        self.clear_filters()
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

        # Add totals row
        # sum all columns except the category column
        totals = df.sum(axis=0)
        totals["Category"] = "Total"
        tree.insert("", "end", values=list(totals), tags="totals_row")
        # choose a dark color since the font is white
        # #333333 is a dark grey
        tree.tag_configure("totals_row", background="darkgrey")

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
    def setup(self):
        table_frame = EditableTable(
            self.frame,
            get_files_df,
            TransactionsCsvForm,
        )
        table_frame.pack(fill="both", expand=True)
