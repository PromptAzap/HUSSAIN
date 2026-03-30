import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('quran_roots_dual_v2.sqlite')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print(f"Tables: {tables}")
for t in tables:
    c.execute(f"PRAGMA table_info({t})")
    print(f"Schema for {t}: {[r[1] for r in c.fetchall()]}")
conn.close()
