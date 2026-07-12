import sqlite3
import os

DB_PATH = 'test.db'
if os.path.exists(DB_PATH): os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
conn.execute('CREATE TABLE Test (id INTEGER, name TEXT)')
conn.execute('INSERT INTO Test VALUES (1, "test")')
conn.commit()
conn.close()

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
row = conn.execute('SELECT * FROM Test').fetchone()
conn.close()

try:
    print(f"Non-existent: {row['fake']}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

