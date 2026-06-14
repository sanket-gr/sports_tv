import sqlite3
import sys

def add_progress_column(db_path='sports_tv.db'):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Check if column exists
    cur.execute("PRAGMA table_info(streams)")
    cols = [row[1] for row in cur.fetchall()]
    if 'progress' in cols:
        print('progress column already exists')
        return
    try:
        cur.execute('ALTER TABLE streams ADD COLUMN progress INTEGER DEFAULT 0')
        conn.commit()
        print('progress column added')
    except Exception as e:
        print('error adding column:', e)
    finally:
        conn.close()

if __name__ == '__main__':
    add_progress_column()
