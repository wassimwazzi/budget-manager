from datetime import datetime, timedelta
import calendar
import logging
import matplotlib.pyplot as plt
import pandas as pd
from src.db.dbmanager import DBManager
from src.constants import TKINTER_BACKGROUND_COLOR


db = DBManager()
logger = logging.getLogger("main").getChild(__name__)


def get_end_of_month(month: str):
    """
    start_of_month: str in the format YYYY-MM
    """
    month = datetime.strptime(month, "%Y-%m")
    _, last_day = calendar.monthrange(month.year, month.month)

    # Calculate the end of the month datetime
    end_of_month = month + timedelta(days=last_day - 1)
    return end_of_month.strftime("%Y-%m-%d")


def get_transactions_df(cols=None):
    transactions = db.select(
        """
        SELECT t.id, t.date, t.description, t.amount, t.category, t.code, t.inferred_category, f.filename
        FROM transactions t LEFT OUTER JOIN files f ON t.file_id = f.id
        ORDER BY t.date DESC
        """,
        [],
    )
    df = pd.DataFrame(
        transactions,
        columns=[
            "id",
            "date",
            "description",
            "amount",
            "category",
            "code",
            "inferred category",
            "filename",
        ],
    )
    # df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df["amount"] = df["amount"].apply(lambda x: round(float(x), 2))
    df["inferred category"] = df["inferred category"].apply(
        lambda x: "No" if x == 0 else "Yes"
    )
    df["filename"] = df["filename"].apply(
        lambda x: x.split("/")[-1].split("\\")[-1] if x else "No file"
    )
    if cols:
        df = df[cols]
    return df


def get_transactions_totals_df():
    totals = db.select(
        """
            SELECT SUM(AMOUNT) AS TOTAL, INCOME
            FROM TRANSACTIONS join CATEGORIES on TRANSACTIONS.CATEGORY = CATEGORIES.CATEGORY
            GROUP BY INCOME
        """,
        [],
    )
    df = pd.DataFrame(totals, columns=["total", "income"])
    # make sure there is a row for income = 0 and income = 1
    if len(df) == 0:
        df.loc[len(df.index)] = [0, 0]
        df.loc[len(df.index)] = [0, 1]
    elif len(df) == 1:
        if df.iloc[0]["income"] == 0:
            df.loc[len(df.index)] = [0, 1]
        else:
            df.loc[len(df.index)] = [0, 0]  # income = 0
    return df


def get_budget_summary_df(month, cols=None):
    """
    month: str in the format YYYY-MM
    """
    start_date = datetime.strptime(month, "%Y-%m").strftime("%Y-%m-01")
    end_date = get_end_of_month(month)
    df = db.select(
        f"""
            -- Give budget since date for each expense category
            WITH BUDGETSINCEDATE AS (
                SELECT c.CATEGORY, COALESCE(b.amount, 0) AS AMOUNT
                FROM CATEGORIES c
                LEFT OUTER JOIN Budgets b ON b.category = c.category
                WHERE c.INCOME = 0 AND (
                    b.start_date IS NULL
                    OR b.start_date = (
                        SELECT MAX(b2.start_date)
                        FROM Budgets b2
                        WHERE b2.start_date <= '{start_date}'
                        AND b2.category = c.category
                    )
                )
            ),

            TRANSACTIONSBUDGET AS (
                SELECT b.CATEGORY AS Category, b.AMOUNT AS Budget,
                    COALESCE(SUM(t.amount),0) AS Actual, b.AMOUNT - COALESCE(SUM(t.amount),0) AS Remaining
                FROM BUDGETSINCEDATE b
                LEFT OUTER JOIN TRANSACTIONS t ON (
                    t.category = b.category AND
                    t.date >= '{start_date}' AND
                    t.date <= '{end_date}'
                )
                GROUP BY b.CATEGORY
                ORDER BY Remaining ASC
            )

            SELECT Category, Budget, ROUND(Actual, 2) AS Actual, ROUND(Remaining, 2) AS Remaining
            FROM TRANSACTIONSBUDGET
            WHERE Actual > 0 OR budget > 0
            ;
        """,
        [],
    )
    df = pd.DataFrame(df, columns=cols or ["Category", "Budget", "Actual", "Remaining"])
    return df


def get_budget_history_df(cols=None, category=None):
    dates = db.select(
        """
        SELECT DISTINCT START_DATE AS Month
        FROM Budgets
        """,
        [],
    )

    budgets = db.select(
        """
        SELECT b.CATEGORY, b.AMOUNT, b.START_DATE
        FROM Budgets b
        """,
        [],
    )
    logger.debug("get_budget_history_df: dates: %s", dates)
    dates_df = pd.DataFrame(dates, columns=["month"])
    budgets_df = pd.DataFrame(budgets, columns=["category", "amount", "start_date"])
    # convert to datetime
    budgets_df["start_date"] = pd.to_datetime(budgets_df["start_date"], format="%Y-%m")
    # for each date, get the budget for each category
    # if there is no budget for that category, get the budget from the previous month where there is a budget for that category
    # if there is no budget for that category in the previous month, set the budget to 0
    for month in dates_df["month"]:
        # convert to datetime
        month = datetime.strptime(month, "%Y-%m")
        for category in budgets_df["category"].unique():
            budget = budgets_df[
                (budgets_df["category"] == category)
                & (budgets_df["start_date"] == month)
            ]
            if not budget.empty:
                logging.debug(
                    "get_budget_history_df: found existing budget for %s in %s: %s",
                    category,
                    month,
                    budget.iloc[0]["amount"],
                )
                continue

            logger.debug(
                "get_budget_history_df: no budget for %s in %s", category, month
            )
            # create a new row for this category and month
            # get the amount from a previous budget. If it exists, use that. Otherwise, use 0
            prev_budget = budgets_df[
                (budgets_df["category"] == category)
                & (budgets_df["start_date"] < month)
            ]
            # select the budget with the max start_date
            prev_budget = prev_budget[
                prev_budget["start_date"] == prev_budget["start_date"].max()
            ]
            if prev_budget.empty:
                logger.debug(
                    "get_budget_history_df: no previous budget for %s before %s. Setting it to 0",
                    category,
                    month,
                )
                budgets_df.loc[len(budgets_df.index)] = [
                    category,
                    0,  # amount
                    month,
                ]
            else:
                prev_budget = prev_budget.iloc[0]
                logger.debug(
                    "get_budget_history_df: previous budget for %s before %s: %s",
                    category,
                    month,
                    prev_budget["amount"],
                )
                budgets_df.loc[len(budgets_df.index)] = [
                    category,
                    prev_budget["amount"],
                    month,
                ]
    # sort by category and start_date
    budgets_df.sort_values(["category", "start_date"], inplace=True)
    # convert start_date back to string
    budgets_df["start_date"] = budgets_df["start_date"].apply(
        lambda x: x.strftime("%Y-%m")
    )
    logger.debug("get_budget_history_df: Result: ")
    logger.debug(budgets_df)

    # assert that number of rows is equal to number of dates * number of categories
    if not len(budgets_df.index) == len(dates_df.index) * len(
        budgets_df["category"].unique()
    ):
        logger.error(
            "get_budget_history_df: number of rows in budgets_df (%s) does not equal number of dates (%s) * number of categories (%s)",
            len(budgets_df.index),
            len(dates_df.index),
            len(budgets_df["category"].unique()),
        )
    return budgets_df


def get_monthly_income_df(cols=None):
    df = db.select(
        """
            SELECT strftime('%Y-%m', date) AS month, SUM(amount) AS total, c.category
            FROM Transactions t JOIN Categories c ON t.category = c.category
            WHERE c.income = 1
            GROUP BY month, c.category
            ORDER BY month
        """,
        [],
    )
    df = pd.DataFrame(df, columns=cols or ["month", "total", "category"])
    return df


def get_income_vs_expenses_df():
    df = db.select(
        """
            WITH DATES AS (
                SELECT DISTINCT strftime('%Y-%m', date) AS month
                FROM TRANSACTIONS
            ),
            INCOME AS (
                SELECT strftime('%Y-%m', date) AS month, SUM(amount) AS income
                FROM TRANSACTIONS t JOIN CATEGORIES c ON t.CATEGORY = c.CATEGORY
                WHERE c.INCOME = 1
                GROUP BY month
            ),
            EXPENSES AS (
                SELECT strftime('%Y-%m', date) AS month, SUM(amount) AS expenses
                FROM TRANSACTIONS t JOIN CATEGORIES c ON t.CATEGORY = c.CATEGORY
                WHERE c.INCOME = 0
                GROUP BY month
            )
            SELECT d.month, COALESCE(i.income, 0) AS income, COALESCE(e.expenses, 0) AS expenses
            FROM DATES d
            LEFT JOIN INCOME i ON d.month = i.month
            LEFT JOIN EXPENSES e ON d.month = e.month
            ORDER BY d.month ASC
            ;
        """,
        [],
    )
    df = pd.DataFrame(df, columns=["month", "income", "expenses"])
    return df


def get_budgets_df(cols=None):
    df = db.select(
        """
            SELECT b.id, b.category, b.amount, b.start_date
            FROM Budgets b JOIN Categories c ON b.category = c.category
            ORDER BY b.start_date DESC
        """,
        [],
    )
    df = pd.DataFrame(df, columns=cols or ["id", "category", "amount", "start_date"])
    return df


def get_files_df(cols=None):
    df = db.select(
        """
            SELECT f.id, f.filename, f.message, f.status, f.date
            FROM Files f
            ORDER BY f.date DESC
        """,
        [],
    )
    df = pd.DataFrame(
        df, columns=cols or ["id", "filename", "message", "status", "date"]
    )
    return df


def get_categories_df(cols=None):
    df = db.select(
        """
            SELECT c.category, c.income, c.description
            FROM Categories c
        """,
        [],
    )
    df = pd.DataFrame(df, columns=cols or ["category", "income", "description"])
    df["income"] = df["income"].apply(lambda x: "Yes" if x else "No")
    return df


def get_budget_vs_spend_plt(month):
    df = get_budget_summary_df(month)

    fig, ax = plt.subplots()  # Adjust the figure size as needed
    fig.patch.set_facecolor(TKINTER_BACKGROUND_COLOR)
    ax.set_facecolor(TKINTER_BACKGROUND_COLOR)
    # Create a bar chart of the budget vs. actual for each category
    width = 0.4
    x = range(len(df["Category"]))
    ax.bar(x, df["Budget"], width=width, label="Budget")
    ax.bar([i + width for i in x], df["Actual"], width=width, label="Actual")

    # Set x-axis labels, rotate them, and adjust spacing
    ax.set_xticks([i + width / 2 for i in x])  # Adjust spacing
    ax.set_xticklabels(
        df["Category"], rotation=45, ha="right"
    )  # Rotate labels for readability

    # Set labels and legend
    ax.set_xlabel("Category")
    ax.set_ylabel("Amount")
    ax.set_title("Budget vs. Actual")
    ax.legend()

    plt.tight_layout()  # Automatically adjust subplot parameters to prevent clipping

    return fig


def get_spend_per_category_pie_chart_plt(month=None):
    if month:
        # Pie chart of spend per category
        start_date = datetime.strptime(month, "%Y-%m").strftime("%Y-%m-01")
        end_date = get_end_of_month(month)
        transactions_for_month = db.select(
            f"""
                SELECT c.category, SUM(t.amount) AS total
                FROM Transactions t JOIN Categories c ON t.category = c.category
                WHERE t.date >= '{start_date}' AND t.date <= '{end_date}'
                AND c.income = 0
                GROUP BY c.category
            """,
            [],
        )
    else:
        transactions_for_month = db.select(
            """
                SELECT c.category, SUM(t.amount) AS total
                FROM Transactions t JOIN Categories c ON t.category = c.category
                WHERE c.income = 0
                GROUP BY c.category
            """,
            [],
        )
    df = pd.DataFrame(transactions_for_month, columns=["category", "total"])
    fig, ax = plt.subplots()  # Adjust the size as needed
    fig.patch.set_facecolor(TKINTER_BACKGROUND_COLOR)
    ax.set_facecolor(TKINTER_BACKGROUND_COLOR)

    # Calculate percentages and labels
    total_spend = df["total"].sum()
    percentages = df["total"] / total_spend * 100

    # Plot the pie chart
    wedges, texts, autotexts = ax.pie(
        df["total"], labels=df["category"], autopct="%1.0f%%"
    )
    ax.axis("equal")
    title = (
        f"Spend Per Category for {month}" if month else "Historical Spend Per Category"
    )
    ax.set_title(title)
    percent_cuttoff = 3
    # only show texts and autotexts if the percentage is greater than percent_cuttoff
    for text, autotext, percent in zip(texts, autotexts, percentages):
        text.set_visible(percent > percent_cuttoff)
        autotext.set_visible(percent > percent_cuttoff)

    # legend_labels = [
    #     f"{cat}: {percent:.1f}%" if percent < percent_cuttoff else cat
    #     for cat, percent in zip(df["category"], percentages)
    # ]
    # ax.legend(title="Categories", labels=legend_labels, loc="lower left")
    return fig


def get_budget_minus_spend_bar_chart_plt(month):
    df = get_budget_summary_df(month)
    fig, ax = plt.subplots()  # Adjust the figure size as needed
    fig.patch.set_facecolor(TKINTER_BACKGROUND_COLOR)
    ax.set_facecolor(TKINTER_BACKGROUND_COLOR)

    # Create a bar chart of the budget vs. actual for each category
    width = 0.4
    x = range(len(df["Category"]))
    ax.bar(x, df["Remaining"], width=width, label="Remaining")

    # Set x-axis labels, rotate them, and adjust spacing
    ax.set_xticks([i + width / 2 for i in x])  # Adjust spacing
    ax.set_xticklabels(
        df["Category"], rotation=45, ha="right"
    )  # Rotate labels for readability

    # Set labels and legend
    ax.set_xlabel("Category")
    ax.set_ylabel("Amount")
    ax.set_title("Remaining amount from budget")
    ax.legend()

    plt.tight_layout()  # Automatically adjust subplot parameters to prevent clipping

    return fig


def get_budget_history_plt(category=None):
    # DF SHOULD BE SORTED BY CATEGORY AND START_DATE!!
    budget_history_df = get_budget_history_df()
    fig, ax = plt.subplots()  # Adjust the figure size as needed
    fig.patch.set_facecolor(TKINTER_BACKGROUND_COLOR)
    ax.set_facecolor(TKINTER_BACKGROUND_COLOR)

    dates = budget_history_df["start_date"].unique()
    # convert the dates to datetime objects
    dates = [datetime.strptime(date, "%Y-%m") for date in dates]
    # sort the dates from earliest to latest
    dates.sort()

    # plot the amount over time for each category
    # label each line with its category
    # show points on the line
    # extend each line on both sides to the edge of the plot. Stay constant after the last date
    for category in budget_history_df["category"].unique():
        category_df = budget_history_df[budget_history_df["category"] == category]
        ax.plot(
            dates,
            category_df["amount"],
            label=category,
            marker="o",
        )
    ax.set_xlabel("Date")
    ax.set_ylabel("Amount")
    ax.set_title("Budget history")
    # show legend outside of the plot
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()  # Automatically adjust subplot parameters to prevent clipping
    return fig


def get_income_vs_expenses_plt():
    # plot a line for income and a line for expenses
    # show points on the line
    # show dates on the x-axis
    df = get_income_vs_expenses_df()
    fig, ax = plt.subplots()  # Adjust the figure size as needed
    fig.patch.set_facecolor(TKINTER_BACKGROUND_COLOR)
    ax.set_facecolor(TKINTER_BACKGROUND_COLOR)

    dates = df["month"].unique()
    # convert the dates to datetime objects
    dates = [datetime.strptime(date, "%Y-%m") for date in dates]
    # sort the dates from earliest to latest
    dates.sort()
    df.sort_values("month", inplace=True, ascending=True)
    # plot the line for income
    ax.plot(
        dates,
        df["income"],
        label="Income",
        marker="o",
    )
    # plot the line for expenses
    ax.plot(
        dates,
        df["expenses"],
        label="Expenses",
        marker="o",
    )

    # add lines for the average income and average expenses
    avg_income = df["income"].mean()
    avg_expenses = df["expenses"].mean()

    ax.axhline(
        avg_income,
        color="green",
        linestyle="--",
        label="Average income",
    )

    ax.axhline(
        avg_expenses,
        color="red",
        linestyle="--",
        label="Average expenses",
    )

    ax.set_xlabel("Date")
    ax.set_ylabel("Amount")
    ax.set_title("Income vs. Expenses")
    # show legend outside of the plot
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()  # Automatically adjust subplot parameters to prevent clipping
    return fig
