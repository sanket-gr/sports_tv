import sqlite3
conn = sqlite3.connect('sports_tv.db')
conn.execute("UPDATE streams SET title='[ERROR] Stream expired – game has ended', updated_at=CURRENT_TIMESTAMP WHERE hls_url=''")
conn.commit()
print("Updated", conn.total_changes, "rows")
conn.close()
