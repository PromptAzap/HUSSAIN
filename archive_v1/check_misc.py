import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('lectures_db.sqlite')
c = conn.cursor()
c.execute("SELECT l.lecture_id, l.title FROM lectures l JOIN series s ON l.series_id = s.series_id WHERE s.title = 'متفرقات'")
for r in c.fetchall():
    print(f"{r[0]} | {r[1]}")
conn.close()
