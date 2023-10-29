from db.dbmanager import DBManager

if __name__ == "__main__":
    with DBManager() as db:
        print(db.select('SELECT * FROM transactions', ()))