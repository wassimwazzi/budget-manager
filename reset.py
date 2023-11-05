"""
    Setup database
"""

import dotenv
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
    # ask user to choose between dev and prod
    print("1. Development")
    print("2. Production")
    choice = input("Choose environment: ")
    if choice == "1":
        dotenv.load_dotenv(dotenv_path=".env.dev")
    elif choice == "2":
        dotenv.load_dotenv(dotenv_path=".env.prod")
    else:
        print("Invalid choice")
        exit(1)
    # drop all tables
    db = DBManager
    for table in TABLES:
        db.delete(f"DROP TABLE IF EXISTS {table}", ())

    # create tables
    db.setup()
