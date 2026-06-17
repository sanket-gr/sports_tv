import sqlite3

conn = sqlite3.connect('sports_tv.db')
try:
    conn.execute('ALTER TABLE streams ADD COLUMN cf_domain TEXT DEFAULT ""')
    conn.commit()
    print('cf_domain column added successfully')
except Exception as e:
    print(f'Note: {e}')
conn.close()
