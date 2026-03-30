import sqlite3
import sys
import os
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'lectures_db.sqlite'
QURAN_DB = 'quran_roots_dual_v2.sqlite'

# قائمة مطابقة السور (رقم -> اسم)
# تم تزويدها برمجياً لضمان الفحص
surah_map = {
    1: "الفاتحة", 2: "البقرة", 3: "آل عمران", 4: "النساء", 5: "المائدة",
    6: "الأنعام", 7: "الأعراف", 8: "الأنفال", 9: "التوبة", 10: "يونس",
    11: "هود", 12: "يوسف", 13: "الرعد", 14: "إبراهيم", 15: "الحجر",
    16: "النحل", 17: "الإسراء", 18: "الكهف", 19: "مريم", 20: "طه",
    21: "الأنبياء", 22: "الحج", 23: "المؤمنون", 24: "النور", 25: "الفرقان",
    26: "الشعراء", 27: "النمل", 28: "القصص", 29: "العنكبوت", 30: "الروم",
    31: "لقمان", 32: "السجدة", 33: "الأحزاب", 34: "سبأ", 35: "فاطر",
    36: "يس", 37: "الصافات", 38: "ص", 39: "الزمر", 40: "غافر",
    41: "فصلت", 42: "الشورى", 43: "الزخرف", 44: "الدخان", 45: "الجاثية",
    46: "الأحقاف", 47: "محمد", 48: "الفتح", 49: "الحجرات", 50: "ق",
    51: "الذاريات", 52: "الطور", 53: "النجم", 54: "القمر", 55: "الرحمن",
    56: "الواقعة", 57: "الحديد", 58: "المجادلة", 59: "الحشر", 60: "الممتحنة",
    61: "الصف", 62: "الجمعة", 63: "المنافقون", 64: "التغابن", 65: "الطلاق",
    66: "التحريم", 67: "الملك", 68: "القلم", 69: "الحاقة", 70: "المعارج",
    71: "نوح", 72: "الجن", 73: "المزمل", 74: "المدثر", 75: "القيامة",
    76: "الإنسان", 77: "المرسلات", 78: "النبأ", 79: "النازعات", 80: "عبس",
    81: "التكوير", 82: "الانفطار", 83: "المطففين", 84: "الانشقاق", 85: "البروج",
    86: "الطارق", 87: "الأعلى", 88: "الغاشية", 89: "الفجر", 90: "البلد",
    91: "الشمس", 92: "الليل", 93: "الضحى", 94: "الشرح", 95: "التين",
    96: "العلق", 97: "القدر", 98: "البينة", 99: "الزلزلة", 100: "العاديات",
    101: "القارعة", 102: "التكاثر", 103: "العصر", 104: "الهمزة", 105: "الفيل",
    106: "قريش", 107: "الماعون", 108: "الكوثر", 109: "الكافرون", 110: "النصر",
    111: "المسد", 112: "الإخلاص", 113: "الفلق", 114: "الناس"
}
name_to_num = {v: k for k, v in surah_map.items()}

def audit():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    results = {}

    # 1. General Stats
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in c.fetchall()]
    table_counts = {}
    for t in sorted(tables):
        c.execute(f"SELECT COUNT(*) FROM {t}")
        table_counts[t] = c.fetchone()[0]
    results['table_counts'] = table_counts

    # 2. Integrity
    c.execute("PRAGMA foreign_key_check")
    results['fk_violations'] = c.fetchall()
    
    c.execute("SELECT COUNT(*) FROM paragraphs WHERE lecture_id NOT IN (SELECT lecture_id FROM lectures)")
    results['orphaned_paragraphs'] = c.fetchone()[0]
    
    c.execute("SELECT lecture_id, COUNT(*), MAX(sequence_index) FROM paragraphs GROUP BY lecture_id")
    results['seq_gaps'] = [r for r in c.fetchall() if r[1] != r[2]]

    # 3. Quality & Metadata
    c.execute("SELECT COUNT(*) FROM lectures WHERE speaker IS NULL OR speaker = ''")
    results['missing_speaker'] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM lectures l LEFT JOIN lecture_extra_metadata e ON l.lecture_id = e.lecture_id WHERE e.lecture_id IS NULL")
    results['missing_extra_meta'] = c.fetchone()[0]

    # Tags Analysis
    c.execute("SELECT concepts_tags FROM lecture_sections WHERE concepts_tags IS NOT NULL")
    tags_data = c.fetchall()
    tag_list = []
    for row in tags_data:
        try:
            tag_list.extend(json.loads(row[0]))
        except: pass
    results['total_tags'] = len(tag_list)
    results['unique_tags'] = len(set(tag_list))

    # 4. Quran Integration Readiness
    c.execute("SELECT DISTINCT surah_name FROM section_ayah_refs")
    referenced_surahs = [s[0] for s in c.fetchall()]
    unmapped = [s for s in referenced_surahs if s not in name_to_num]
    results['unmapped_surahs'] = unmapped

    # 5. Performance
    results['db_size_mb'] = os.path.getsize(DB_PATH) / (1024*1024)

    # Output Report (Private JSON for script)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    conn.close()

if __name__ == "__main__":
    audit()
