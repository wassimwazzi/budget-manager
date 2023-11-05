import sqlite3
import os
from sqlite3 import Error


def throws_db_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Error as e:
            print(e)

    return wrapper


# class to handle database
class DBManager:
    SCHEMA = "src/db/schema.sql"

    def __init__(self):
        self.db = os.getenv("DB_FILE")
        if not self.db:
            raise Exception("Database file not specified")

        if not os.path.exists(self.db):
            print("Database does not exist. Creating...")
            self.setup()

    def _connect(self):
        try:
            return sqlite3.connect(self.db)
        except Error as e:
            print(e)
            return None

    def setup(self):
        conn = self._connect()
        with open(DBManager.SCHEMA, "r", encoding="utf-8") as f:
            schema = f.read()
            cur = conn.cursor()
            cur.executescript(schema)
            conn.commit()

    # def __del__(self):
    #     self.conn.close()

    # def __enter__(self):
    #     return self

    # def __exit__(self, exc_type, exc_value, traceback):
    #     self.conn.close()

    # @throws_db_error
    def create_table(self, create_table_sql):
        conn = self._connect()
        c = conn.cursor()
        c.execute(create_table_sql)

    # @throws_db_error
    def insert(self, sql, data):
        conn = self._connect()
        c = conn.cursor()
        c.execute(sql, data)
        conn.commit()
        return c.lastrowid

    def insert_many(self, sql, data):
        conn = self._connect()
        c = conn.cursor()
        c.executemany(sql, data)
        conn.commit()
        return c.lastrowid

    # @throws_db_error
    def select(self, sql, data):
        conn = self._connect()
        c = conn.cursor()
        c.execute(sql, data)
        return c.fetchall()

    # @throws_db_error
    def update(self, sql, data):
        conn = self._connect()
        c = conn.cursor()
        c.execute(sql, data)
        conn.commit()

    # @throws_db_error
    def delete(self, sql, data):
        conn = self._connect()
        c = conn.cursor()
        c.execute(sql, data)
        conn.commit()
