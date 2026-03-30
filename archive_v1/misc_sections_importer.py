import sqlite3
import json
import os
import uuid
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# ══════════════════════════════════════════════════════════
# الإعدادات
# ══════════════════════════════════════════════════════════
BASE_DIR       = Path(__file__).parent
MISC_DIR       = BASE_DIR / 'أقسام الدروس' / 'متفرقات'
DB_PATH        = BASE_DIR / 'lectures_db.sqlite'

# ══════════════════════════════════════════════════════════
# أداة مساعدة: استبعاد الدروس المستوردة مسبقاً
# ══════════════════════════════════════════════════════════
def get_imported_lecture_ids(conn):
    c = conn.cursor()
    c.execute('SELECT DISTINCT lecture_id FROM lecture_sections')
    return {row[0] for row in c.fetchall()}

def get_valid_lecture_ids(conn):
    c = conn.cursor()
    c.execute('SELECT lecture_id FROM lectures')
    return {row[0] for row in c.fetchall()}

# ══════════════════════════════════════════════════════════
# استيراد ملف JSON واحد
# ══════════════════════════════════════════════════════════
def import_json_file(conn, json_path, valid_ids, stats):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [WARN] خطأ في قراءة {json_path.name}: {e}")
        stats['errors'] += 1
        return

    lesson_meta = data.get('بيانات_الدرس', {})
    lecture_id  = lesson_meta.get('lecture_id', '').strip()

    if not lecture_id:
        print(f"  [WARN] لا يوجد lecture_id في: {json_path.name}")
        stats['errors'] += 1
        return

    if lecture_id not in valid_ids:
        print(f"  [WARN] lecture_id غير موجود في القاعدة: {lecture_id[:8]}... ({json_path.name})")
        stats['missing_lectures'] += 1
        return

    c = conn.cursor()

    # ── 1. lecture_extra_metadata (تحديث البيانات المفقودة) ──
    c.execute('''
        INSERT OR REPLACE INTO lecture_extra_metadata
            (lecture_id, ayah_range, date_gregorian, date_hijri, location)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        lecture_id,
        lesson_meta.get('نطاق_الآيات', ''),
        lesson_meta.get('التاريخ_الميلادي', ''),
        lesson_meta.get('التاريخ_الهجري', ''),
        lesson_meta.get('المكان', ''),
    ))

    # ── 2. الأقسام الموضوعية ──────────────────────────────
    sections = data.get('الأقسام_الموضوعية', [])
    for section in sections:
        section_id   = str(uuid.uuid4())
        par_range    = section.get('نطاق_الفقرات', {})
        tags         = section.get('concepts_tags', [])

        c.execute('''
            INSERT INTO lecture_sections (
                section_id, lecture_id, section_number,
                section_title, section_summary,
                start_sequence_index, end_sequence_index,
                start_paragraph_id, end_paragraph_id,
                concepts_tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            section_id,
            lecture_id,
            section.get('رقم_القسم', 0),
            section.get('اسم_القسم', ''),
            section.get('ملخص_القسم', ''),
            par_range.get('البداية_sequence_index'),
            par_range.get('النهاية_sequence_index'),
            par_range.get('البداية_paragraph_id', ''),
            par_range.get('النهاية_paragraph_id', ''),
            json.dumps(tags, ensure_ascii=False),
        ))
        stats['sections'] += 1

        # ── 3. إشارات الآيات لهذا القسم ──────────────────
        for ayah_ref in section.get('الآيات_المرتبطة', []):
            surah = ayah_ref.get('اسم_السورة', '').strip()
            ayah  = str(ayah_ref.get('رقم_الاية', '')).strip()
            if surah and ayah:
                c.execute('''
                    INSERT INTO section_ayah_refs
                        (ref_id, section_id, surah_name, ayah_number)
                    VALUES (?, ?, ?, ?)
                ''', (str(uuid.uuid4()), section_id, surah, ayah))
                stats['ayah_refs'] += 1

    stats['lectures_done'] += 1

# ══════════════════════════════════════════════════════════
# الدالة الرئيسية
# ══════════════════════════════════════════════════════════
def run_import():
    if not DB_PATH.exists():
        print(f"❌ لم يتم العثور على قاعدة البيانات: {DB_PATH}")
        return

    if not MISC_DIR.exists():
        print(f"❌ لم يتم العثور على مجلد المتفرقات: {MISC_DIR}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    valid_ids = get_valid_lecture_ids(conn)
    imported_ids = get_imported_lecture_ids(conn)
    
    print(f"[DB] الدروس المعرفة: {len(valid_ids)}")
    print(f"[DB] الدروس المستوردة مسبقاً: {len(imported_ids)}")

    stats = {
        'lectures_done':   0,
        'sections':        0,
        'ayah_refs':       0,
        'missing_lectures': 0,
        'errors':          0,
        'skipped':         0,
    }

    json_files = sorted(MISC_DIR.glob('*.json'))
    print(f"[DIR] ملفات المتفرقات الجديدة: {len(json_files)}\n")

    for jf in json_files:
        # التأكد من عدم التكرار
        with open(jf, 'r', encoding='utf-8') as f:
            data = json.load(f)
            lid = data.get('بيانات_الدرس', {}).get('lecture_id')
            if lid in imported_ids:
                print(f"  [-] تخطي {jf.name} (تم استيراده مسبقاً)")
                stats['skipped'] += 1
                continue
        
        print(f"  [+] استيراد {jf.name}...")
        import_json_file(conn, jf, valid_ids, stats)
        conn.commit()

    conn.close()

    # ══ التقرير النهائي ══
    print("\n" + "=" * 50)
    print("التقرير النهائي لنظام المتفرقات")
    print("=" * 50)
    print(f"  [OK] ملفات JSON مستوردة:              {stats['lectures_done']}")
    print(f"  [OK] اقسام موضوعية مضافة:             {stats['sections']}")
    print(f"  [OK] اشارات آيات مضافة:               {stats['ayah_refs']}")
    print(f"  [-] دروس تم تخطيها:                  {stats['skipped']}")
    if stats['missing_lectures']:
        print(f"  [WARN] دروس غير موجودة في القاعدة: {stats['missing_lectures']}")
    if stats['errors']:
        print(f"  [ERR] اخطاء في الملفات:             {stats['errors']}")
    print("=" * 50)

if __name__ == '__main__':
    run_import()
