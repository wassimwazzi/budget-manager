import sqlite3
from sqlite3 import Error
import os


# class to handle database
class DBManager:
    DATABASE = 'db/db.sqlite3'
    def __init__(self):
        self.conn = None
        self.db = DBManager.DATABASE
        try:
            doSetup = not os.path.exists(self.db)
            self.conn = sqlite3.connect(self.db)
            if doSetup:
                print('Creating database...')
                self.__setup()
        except Error as e:
            print(e)

    def __setup(self):
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

    def create_table(self, create_table_sql):
        try:
            c = self.conn.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print(e)

    def insert(self, sql, data):
        try:
            c = self.conn.cursor()
            c.execute(sql, data)
            self.conn.commit()
            return c.lastrowid
        except Error as e:
            print(e)

    def select(self, sql, data):
        try:
            c = self.conn.cursor()
            c.execute(sql, data)
            return c.fetchall()
        except Error as e:
            print(e)

    def update(self, sql, data):
        try:
            c = self.conn.cursor()
            c.execute(sql, data)
            self.conn.commit()
        except Error as e:
            print(e)

    def delete(self, sql, data):
        try:
            c = self.conn.cursor()
            c.execute(sql, data)
            self.conn.commit()
        except Error as e:
            print(e)

# Path: models.py
