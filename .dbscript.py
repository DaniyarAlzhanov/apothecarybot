import sqlite3


conn = sqlite3.connect('database.db')
cur = conn.cursor()

with open('.create_db.sql', 'r') as f:
    sql = f.read()


conn.executescript(sql)

conn.commit()
conn.close()