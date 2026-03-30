import sqlite3
import os

def setup_database(db_path='lectures_db.sqlite'):
    """إنشاء جداول قاعدة البيانات والفهارس اللازمة للدروس"""
    
    # حذف القاعدة القديمة إذا وجدت لإعادة الإنشاء النظيف أثناء التطوير
    # if os.path.exists(db_path):
    #     os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. جدول السلاسل المعرفية
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS series (
        series_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        subtitle TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. جدول الدروس
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lectures (
        lecture_id TEXT PRIMARY KEY,
        series_id TEXT NOT NULL,
        lecture_number INTEGER NOT NULL,
        title TEXT,
        speaker TEXT,
        date TEXT,
        location TEXT,
        opening_ayah TEXT,
        metadata_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (series_id) REFERENCES series(series_id)
    )
    ''')
    
    # 3. جدول الفقرات (قلب المنظومة)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS paragraphs (
        paragraph_id TEXT PRIMARY KEY,
        lecture_id TEXT NOT NULL,
        sequence_index INTEGER NOT NULL,
        content TEXT NOT NULL,
        contains_ayat BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lecture_id) REFERENCES lectures(lecture_id)
    )
    ''')

    # 4. جدول ربط الفقرات بالآيات (مستقبلاً للربط التلقائي)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS paragraph_ayah_mapping (
        mapping_id TEXT PRIMARY KEY,
        paragraph_id TEXT NOT NULL,
        global_ayah_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (paragraph_id) REFERENCES paragraphs(paragraph_id)
    )
    ''')
    
    # 5. إنشاء الفهارس للبحث السريع (Indexes)
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_paragraphs_lecture ON paragraphs(lecture_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_paragraphs_sequence ON paragraphs(lecture_id, sequence_index);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_lectures_series ON lectures(series_id);')

    conn.commit()
    conn.close()
    print(f"تم تهيئة قاعدة البيانات {db_path} والجداول الأربعة وإنشاء الفهارس.")

if __name__ == "__main__":
    setup_database()
