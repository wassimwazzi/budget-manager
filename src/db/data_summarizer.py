from datetime import datetime, timedelta
import calendar
import matplotlib.pyplot as plt
import pandas as pd
from src.db.dbmanager import DBManager

db = DBManager()


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
        "SELECT id, date, description, amount, category, code, inferred_category FROM transactions",
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
        ],
    )
    # df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df["amount"] = df["amount"].apply(lambda x: round(float(x), 2))
    df["inferred category"] = df["inferred category"].apply(
        lambda x: "No" if x == 0 else "Yes"
    )
    if cols:
        df = df[cols]
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
                WHERE (
                    b.start_date IS NULL
                    OR b.start_date = (
                        SELECT MAX(b2.start_date)
                        FROM Budgets b2
                        WHERE b2.start_date <= '{start_date}'
                    )
                ) AND
                c.INCOME = 0
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

            SELECT * FROM TRANSACTIONSBUDGET
            WHERE Actual > 0 OR budget > 0
            ;
        """,
        [],
    )
    df = pd.DataFrame(df, columns=cols or ["Category", "Budget", "Actual", "Remaining"])
    return df


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


def get_budgets_df(cols=None):
    df = db.select(
        """
            SELECT b.category, b.amount, b.start_date
            FROM Budgets b JOIN Categories c ON b.category = c.category
        """,
        [],
    )
    df = pd.DataFrame(df, columns=cols or ["category", "amount", "start_date"])
    return df


def get_budget_vs_spend_plt(month):
    df = get_budget_summary_df(month)

    fig, ax = plt.subplots()  # Adjust the figure size as needed

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


def get_spend_per_cateogire_pie_chart_plt(month):
    # Pie chart of spend per category
    start_date = datetime.strptime(month, "%Y-%m").strftime("%Y-%m-01")
    end_date = get_end_of_month(month)
    transactions_for_month = db.select(
        f"""
            SELECT c.category, SUM(t.amount) AS total
            FROM Transactions t JOIN Categories c ON t.category = c.category
            WHERE t.date >= '{start_date}' AND t.date <= '{end_date}'
            GROUP BY c.category
        """,
        [],
    )
    df = pd.DataFrame(transactions_for_month, columns=["category", "total"])
    fig, ax = plt.subplots(figsize=(8, 8))  # You can adjust the size as needed

    ax.pie(df["total"], labels=df["category"], autopct="%1.1f%%")
    ax.axis("equal")
    ax.set_title("Spend per category")
    # set size of figure
    return fig


def get_budget_minus_spend_bar_chart_plt(month):
    df = get_budget_summary_df(month)
    fig, ax = plt.subplots()  # Adjust the figure size as needed

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
