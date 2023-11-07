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
    # df = db.select(
    #     f"""
    #         SELECT b.id, b.category, b.amount, b.start_date
    #         FROM Budgets b JOIN Categories c ON b.category = c.category
    #         {"WHERE b.category = " + category if category else ""}
    #         ORDER BY b.start_date ASC
    #     """,
    #     [],
    # )
    df = db.select(
        f"""
            WITH Budget_Dates AS (
                SELECT
                    DISTINCT START_DATE AS Month
                FROM
                    Budgets
            ),
            Budgets_With_Date AS (
                SELECT b.id, b.CATEGORY, b.AMOUNT, b.START_DATE, 0 AS AUTO
                FROM Budgets b
                JOIN Budget_Dates bd ON b.START_DATE = bd.Month
            ),
            Budgets_With_No_Date AS (
                SELECT
                    b.id,
                    b.CATEGORY,
                    b.AMOUNT,
                    bd.Month,
                    B.START_DATE,
                    1 AS AUTO
                FROM
                    Budgets b
                    JOIN Budget_Dates bd on bd.Month != b.START_DATE
                WHERE bd.Month NOT IN (SELECT START_DATE FROM BUDGETS WHERE CATEGORY = b.CATEGORY)
            ),
            MinMonthDiff AS (
                SELECT category, 
                    month,
                    MIN(ABS(START_DATE - month)) AS min_diff
                FROM Budgets_With_No_Date
                GROUP BY category, month
            ),
            Budget_History AS (
                SELECT t1.id, t1.CATEGORY, t1.AMOUNT, t1.START_DATE
                FROM Budgets_With_No_Date t1
                JOIN MinMonthDiff t2
                ON t1.category = t2.category
                AND t1.month = t2.month
                AND ABS(t1.START_DATE - t2.month) = t2.min_diff
                UNION ALL
                SELECT id, CATEGORY, AMOUNT, START_DATE
                FROM Budgets_With_Date
                ORDER BY CATEGORY, START_DATE
            )
            SELECT * FROM Budget_History
            {"WHERE CATEGORY = " + category if category else ""}
            ORDER BY CATEGORY, START_DATE ASC
            ;
        """,
        [],
    )
    df = pd.DataFrame(df, columns=cols or ["id", "category", "amount", "start_date"])
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
            SELECT b.id, b.category, b.amount, b.start_date
            FROM Budgets b JOIN Categories c ON b.category = c.category
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
            AND c.income = 0
            GROUP BY c.category
        """,
        [],
    )
    df = pd.DataFrame(transactions_for_month, columns=["category", "total"])
    fig, ax = plt.subplots()  # Adjust the size as needed

    # Calculate percentages and labels
    total_spend = df["total"].sum()
    percentages = df["total"] / total_spend * 100

    # Plot the pie chart
    wedges, texts, autotexts = ax.pie(
        df["total"], labels=df["category"], autopct="%1.0f%%"
    )
    ax.axis("equal")
    ax.set_title("Spend per category")
    percent_cuttoff = 5
    # only show texts and autotexts if the percentage is greater than percent_cuttoff
    for text, autotext, percent in zip(texts, autotexts, percentages):
        text.set_visible(percent > percent_cuttoff)
        autotext.set_visible(percent > percent_cuttoff)

    legend_labels = [
        f"{cat}: {percent:.1f}%" if percent < percent_cuttoff else cat
        for cat, percent in zip(df["category"], percentages)
    ]
    ax.legend(title="Categories", labels=legend_labels, loc="upper left")
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


def get_budget_history_plt(category=None):
    budget_history_df = get_budget_history_df()
    fig, ax = plt.subplots()  # Adjust the figure size as needed
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
    ax.legend()
    plt.tight_layout()  # Automatically adjust subplot parameters to prevent clipping
    return fig
