import sqlite3
from sqlite3 import Error


# class to handle database
class DBManager:
    DATABASE = 'db/db.sqlite3'
    def __init__(self):
        self.conn = None
        self.db = DBManager.DATABASE
        try:
            self.conn = sqlite3.connect(self.db)
        except Error as e:
            print(e)

    def setup(self):
        with open('db/schema.sql', 'r') as f:
            schema = f.read()
            cur = self.conn.cursor()
            cur.executescript(schema)
            self.conn.commit()

    def __del__(self):
        self.conn.close()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()

    def throws_db_error(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Error as e:
                print(e)
        return wrapper

    @throws_db_error
    def create_table(self, create_table_sql):
        c = self.conn.cursor()
        c.execute(create_table_sql)

    @throws_db_error
    def insert(self, sql, data):
        c = self.conn.cursor()
        c.execute(sql, data)
        self.conn.commit()
        return c.lastrowid

    @throws_db_error
    def select(self, sql, data):
        c = self.conn.cursor()
        c.execute(sql, data)
        return c.fetchall()

    @throws_db_error
    def update(self, sql, data):
        c = self.conn.cursor()
        c.execute(sql, data)
        self.conn.commit()

    @throws_db_error
    def delete(self, sql, data):
        c = self.conn.cursor()
        c.execute(sql, data)
        self.conn.commit()
