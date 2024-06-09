import sqlite3


NAME_OF_DB = 'database.db'


class DB:
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def connect(self):
        try:
            self.conn = sqlite3.connect(NAME_OF_DB, check_same_thread=False)
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as error:
            return False
