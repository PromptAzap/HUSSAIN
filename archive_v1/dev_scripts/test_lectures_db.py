import sqlite3
import json

def generate_report(db_path='lectures_db.sqlite'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. عدد السلاسل والدروس والفقرات المخزنة
    cursor.execute("SELECT COUNT(*) FROM series")
    series_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM lectures")
    lectures_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM paragraphs")
    paragraphs_count = cursor.fetchone()[0]
    
    report = {
        "statistics": {
            "series": series_count,
            "lectures": lectures_count,
            "paragraphs": paragraphs_count
        },
        "sample": None
    }
    
    # 2. مثال على جلب فقرة محددة للتحقق من النص والمعرفات الفريدة
    cursor.execute('''
    SELECT 
        p.paragraph_id, 
        p.sequence_index,
        p.content, 
        p.contains_ayat, 
        l.title,
        s.title as series_title
    FROM paragraphs p
    JOIN lectures l ON p.lecture_id = l.lecture_id
    JOIN series s ON l.series_id = s.series_id
    WHERE l.title LIKE '%الدرس الأول%' AND p.sequence_index = 4
    LIMIT 1
    ''')
    
    sample_paragraph = cursor.fetchone()
    
    if sample_paragraph:
        p_id, seq_idx, content, has_ayat, l_title, s_title = sample_paragraph
        report["sample"] = {
            "series_title": s_title,
            "lecture_title": l_title,
            "sequence_index": seq_idx,
            "has_ayat": bool(has_ayat),
            "paragraph_id": p_id,
            "content": content
        }
        
    conn.close()
    
    with open("db_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    generate_report()
