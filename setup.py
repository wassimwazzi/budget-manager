"""
    Setup database
"""

from db.dbmanager import DBManager

TABLES = [
    "transactions",
    "categories",
    "codes",
    "currencies",
]

if __name__ == "__main__":
    # drop all tables
    db = DBManager()
    for table in TABLES:
        db.delete("DROP TABLE IF EXISTS {}".format(table), [])

    # create tables
    db.setup()
