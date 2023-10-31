from datetime import datetime, timedelta
import calendar
import matplotlib.pyplot as plt
import pandas as pd
from src.db.dbmanager import DBManager

db = DBManager()


def get_end_of_month(start_of_month: str):
    start_of_month = start_of_month[:7]
    start_of_month += "-01"
    start_of_month = datetime.strptime(start_of_month, "%Y-%m-%d")
    _, last_day = calendar.monthrange(start_of_month.year, start_of_month.month)

    # Calculate the end of the month datetime
    end_of_month = start_of_month + timedelta(days=last_day - 1)
    return end_of_month.strftime("%Y-%m-%d")


def get_transactions_df():
    transactions = db.select(
        "SELECT date, description, amount, category, code FROM transactions", []
    )
    print(transactions)
    df = pd.DataFrame(
        transactions,
        columns=["date", "description", "amount", "category", "code"],
    )
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = df["amount"].apply(lambda x: round(float(x), 2))
    return df


def get_budget_summary_df(month):
    start_date = month[:7] + "-01"
    end_date = get_end_of_month(start_date)
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
                    COALESCE(SUM(t.amount),0) AS Actual, b.AMOUNT - COALESCE(SUM(t.amount),0) AS Difference
                FROM BUDGETSINCEDATE b
                LEFT OUTER JOIN TRANSACTIONS t ON (
                    t.category = b.category AND
                    t.date >= '{start_date}' AND
                    t.date <= '{end_date}'
                )
                GROUP BY b.CATEGORY
                ORDER BY Difference ASC
            )

            SELECT * FROM TRANSACTIONSBUDGET
            WHERE Actual > 0 OR budget > 0
            ;
        """,
        [],
    )
    df = pd.DataFrame(df, columns=["Category", "Budget", "Actual", "Difference"])
    return df


def get_monthly_income_df():
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
    df = pd.DataFrame(df, columns=["month", "total", "category"])
    print(df)
    return df


def get_budget_summary_plt(month):
    df = get_budget_summary_df(month)

    fig, ax = plt.subplots()

    # Create a bar chart of the budget vs. actual vs difference for each category
    ax.bar(df["Category"], df["Budget"], label="Budget")
    ax.bar(df["Category"], df["Actual"], label="Actual")
    ax.bar(df["Category"], df["Difference"], label="Difference")

    # Set labels and legend
    ax.set_xlabel("Category")
    ax.set_ylabel("Amount")
    ax.set_title("Budget vs. Actual")

    return fig
