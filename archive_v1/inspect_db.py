import sqlite3

def inspect_database(db_path):
    # مسار قاعدة البيانات
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"--- استكشاف قاعدة البيانات: {db_path} ---\n")

    # استخراج أسماء الجداول
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    if not tables:
        print("قاعدة البيانات فارغة أو لا توجد جداول.")
        return

    for table in tables:
        table_name = table[0]
        print(f"📌 الجدول: {table_name}")
        
        # استخراج معلومات أعمدة الجدول (Schema)
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        print("   الأعمدة:")
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, pk = col
            pk_str = " (Primary Key)" if pk else ""
            print(f"     - {col_name} [{col_type}]{pk_str}")
        
        # عرض أول 3 صفوف من كل جدول لأخذ فكرة عن البيانات
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
        sample_rows = cursor.fetchall()
        print("   عينة بيانات (3 صفوف):")
        for row in sample_rows:
            print(f"     {row}")
        
        print("-" * 50)

    conn.close()

if __name__ == "__main__":
    db_file = "quran_roots_dual_v2.sqlite"
    inspect_database(db_file)
