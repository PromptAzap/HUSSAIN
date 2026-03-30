import sqlite3
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

def setup_sections_tables(db_path='lectures_db.sqlite'):
    """إنشاء جداول نظام الأقسام الموضوعية في قاعدة بيانات الدروس"""

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # ══════════════════════════════════════
    # جدول 1: الأقسام الموضوعية
    # ══════════════════════════════════════
    c.execute('''
    CREATE TABLE IF NOT EXISTS lecture_sections (
        section_id              TEXT PRIMARY KEY,
        lecture_id              TEXT NOT NULL,
        section_number          INTEGER NOT NULL,
        section_title           TEXT NOT NULL,
        section_summary         TEXT,
        start_sequence_index    INTEGER,
        end_sequence_index      INTEGER,
        start_paragraph_id      TEXT,
        end_paragraph_id        TEXT,
        concepts_tags           TEXT,           -- JSON Array مخزّن كنص
        created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lecture_id) REFERENCES lectures(lecture_id)
    )
    ''')

    # ══════════════════════════════════════
    # جدول 2: إشارات الآيات لكل قسم
    # ══════════════════════════════════════
    c.execute('''
    CREATE TABLE IF NOT EXISTS section_ayah_refs (
        ref_id          TEXT PRIMARY KEY,
        section_id      TEXT NOT NULL,
        surah_name      TEXT NOT NULL,
        ayah_number     TEXT NOT NULL,          -- نص لدعم النطاقات مثل "10-11"
        global_ayah_id  TEXT,                   -- للربط المستقبلي بـ quran_roots_dual_v2
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (section_id) REFERENCES lecture_sections(section_id)
    )
    ''')

    # ══════════════════════════════════════
    # جدول 3: بيانات وصفية إضافية للدروس
    # ══════════════════════════════════════
    c.execute('''
    CREATE TABLE IF NOT EXISTS lecture_extra_metadata (
        lecture_id          TEXT PRIMARY KEY,
        ayah_range          TEXT,               -- نطاق الآيات مثل "آل عمران: 100-103"
        date_gregorian      TEXT,               -- التاريخ الميلادي
        date_hijri          TEXT,               -- التاريخ الهجري
        location            TEXT,               -- المكان
        updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lecture_id) REFERENCES lectures(lecture_id)
    )
    ''')

    # ══════════════════════════════════════
    # الفهارس لتسريع الاستعلام
    # ══════════════════════════════════════
    c.execute('CREATE INDEX IF NOT EXISTS idx_sections_lecture    ON lecture_sections(lecture_id);')
    c.execute('CREATE INDEX IF NOT EXISTS idx_sections_number     ON lecture_sections(lecture_id, section_number);')
    c.execute('CREATE INDEX IF NOT EXISTS idx_sections_start_par  ON lecture_sections(start_paragraph_id);')
    c.execute('CREATE INDEX IF NOT EXISTS idx_ayah_refs_section   ON section_ayah_refs(section_id);')
    c.execute('CREATE INDEX IF NOT EXISTS idx_ayah_refs_surah     ON section_ayah_refs(surah_name);')
    c.execute('CREATE INDEX IF NOT EXISTS idx_extra_meta_lecture  ON lecture_extra_metadata(lecture_id);')

    conn.commit()
    conn.close()

    print(f"[OK] تم انشاء الجداول الثلاثة والفهارس في: {db_path}")
    print("   - lecture_sections")
    print("   - section_ayah_refs")
    print("   - lecture_extra_metadata")

if __name__ == '__main__':
    setup_sections_tables()
