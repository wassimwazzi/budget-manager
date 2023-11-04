"""
    Setup database
"""

from src.db.dbmanager import DBManager

TABLES = [
    "transactions",
    "categories",
    "codes",
    "currencies",
    "budgets",
    "files",
]

if __name__ == "__main__":
    # drop all tables
    db = DBManager()
    for table in TABLES:
        db.delete(f"DROP TABLE IF EXISTS {table}", ())

    # create tables
    db.setup()
