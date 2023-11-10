import sqlite3
import os
import logging
from sqlite3 import Error


def throws_db_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Error as e:
            logger.error(e)
            conn = args[0].conn
            if conn:
                args[0].conn.close()
                args[0].conn = None
            raise e

    return wrapper


logger = logging.getLogger("main").getChild(__name__)


# class to handle database
class DBManager:
    SCHEMA = "src/db/schema.sql"

    def __init__(self):
        self.db = os.getenv("DB_FILE")
        self.conn = None
        if not self.db:
            raise Exception("Database file not specified")

        if not os.path.exists(self.db):
            logger.info("Database %s does not exist. Creating...", self.db)
            self.setup()

    def _connect(self):
        try:
            return sqlite3.connect(self.db)
        except Error as e:
            logger.error("Error connecting to database: %s", e)
            return None

    def setup(self):
        self.conn = self._connect()
        with open(DBManager.SCHEMA, "r", encoding="utf-8") as f:
            schema = f.read()
            cur = self.conn.cursor()
            cur.executescript(schema)
            self.conn.commit()

    @throws_db_error
    def create_table(self, create_table_sql):
        self.conn = self._connect()
        c = self.conn.cursor()
        c.execute(create_table_sql)

    @throws_db_error
    def insert(self, sql, data):
        self.conn = self._connect()
        c = self.conn.cursor()
        c.execute(sql, data)
        self.conn.commit()
        return c.lastrowid

    @throws_db_error
    def insert_many(self, sql, data):
        self.conn = self._connect()
        c = self.conn.cursor()
        c.executemany(sql, data)
        self.conn.commit()
        return c.lastrowid

    @throws_db_error
    def select(self, sql, data):
        self.conn = self._connect()
        c = self.conn.cursor()
        c.execute(sql, data)
        return c.fetchall()

    @throws_db_error
    def update(self, sql, data):
        self.conn = self._connect()
        c = self.conn.cursor()
        c.execute(sql, data)
        self.conn.commit()

    @throws_db_error
    def delete(self, sql, data):
        self.conn = self._connect()
        c = self.conn.cursor()
        c.execute(sql, data)
        self.conn.commit()
