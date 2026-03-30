import sqlite3
conn = sqlite3.connect('lectures_db.sqlite')
c = conn.cursor()
c.execute("SELECT title, lecture_id FROM lectures WHERE speaker IS NULL OR speaker = ''")
print(f"Missing Speaker: {c.fetchall()}")
conn.close()
