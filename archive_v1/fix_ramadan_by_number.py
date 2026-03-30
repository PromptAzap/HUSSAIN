"""
fix_ramadan_by_number.py
--------------------------
دروس رمضان لها UUIDs مزيفة في JSON.
نربطها بـ lecture_number عبر اسم الملف (7.json = رقم 7).
"""
import sqlite3, json, uuid, sys, re
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR     = Path(__file__).parent
SECTIONS_DIR = BASE_DIR / 'أقسام الدروس' / 'سلسلة_دروس_رمضان'
DB_PATH      = BASE_DIR / 'lectures_db.sqlite'

conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()

# جلب دروس رمضان من القاعدة مرتبة بعنوانها الأصلي
c.execute("""
    SELECT l.lecture_id, l.title
    FROM lectures l
    JOIN series s ON l.series_id = s.series_id
    WHERE s.title LIKE '%رمضان%'
""")
ramadan_in_db = c.fetchall()

# بناء mapping: رقم الدرس -> lecture_id
# العنوان في القاعدة مثل: "7_الدرس السابع"
num_to_id = {}
for lid, title in ramadan_in_db:
    # استخراج الرقم من أول العنوان (10-2 أو 7 إلخ)
    m = re.match(r'^(\d+(?:-\d+)?)', title.strip())
    if m:
        num_to_id[m.group(1)] = lid

print(f'[DB] دروس رمضان في القاعدة: {len(ramadan_in_db)}')
print(f'[MAP] أرقام مُعرَّفة: {sorted(num_to_id.keys())}')

# المرور على ملفات رمضان بالرقم
json_files = sorted(SECTIONS_DIR.glob('*.json'))
print(f'\n[JSON] ملفات رمضان: {len(json_files)}')

imported  = 0
skipped   = 0
sec_count = 0
aya_count = 0

for jf in json_files:
    # استخراج الرقم من اسم الملف (10-2.json -> "10-2")
    file_num = jf.stem  # بدون .json
    correct_lid = num_to_id.get(file_num)

    if not correct_lid:
        print(f'  [SKIP] {jf.name} — رقم "{file_num}" غير مطابق')
        skipped += 1
        continue

    with open(jf, 'r', encoding='utf-8') as f:
        data = json.load(f)

    meta = data.get('بيانات_الدرس', {})

    # lecture_extra_metadata
    c.execute("""
        INSERT OR REPLACE INTO lecture_extra_metadata
            (lecture_id, ayah_range, date_gregorian, date_hijri, location)
        VALUES (?, ?, ?, ?, ?)
    """, (
        correct_lid,
        meta.get('نطاق_الآيات', ''),
        meta.get('التاريخ_الميلادي', ''),
        meta.get('التاريخ_الهجري', ''),
        meta.get('المكان', ''),
    ))

    # الأقسام
    for section in data.get('الأقسام_الموضوعية', []):
        section_id = str(uuid.uuid4())
        par_range  = section.get('نطاق_الفقرات', {})
        tags       = section.get('concepts_tags', [])

        c.execute("""
            INSERT INTO lecture_sections (
                section_id, lecture_id, section_number,
                section_title, section_summary,
                start_sequence_index, end_sequence_index,
                start_paragraph_id, end_paragraph_id, concepts_tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            section_id, correct_lid,
            section.get('رقم_القسم', 0),
            section.get('اسم_القسم', ''),
            section.get('ملخص_القسم', ''),
            par_range.get('البداية_sequence_index'),
            par_range.get('النهاية_sequence_index'),
            par_range.get('البداية_paragraph_id', ''),
            par_range.get('النهاية_paragraph_id', ''),
            json.dumps(tags, ensure_ascii=False),
        ))
        sec_count += 1

        for ayah_ref in section.get('الآيات_المرتبطة', []):
            surah = ayah_ref.get('اسم_السورة', '').strip()
            ayah  = str(ayah_ref.get('رقم_الاية', '')).strip()
            if surah and ayah:
                c.execute("""
                    INSERT INTO section_ayah_refs (ref_id, section_id, surah_name, ayah_number)
                    VALUES (?, ?, ?, ?)
                """, (str(uuid.uuid4()), section_id, surah, ayah))
                aya_count += 1

    imported += 1
    print(f'  [OK] {jf.name} -> {correct_lid[:8]}...')

conn.commit()
conn.close()

print(f'\n[DONE]')
print(f'  مستورد:         {imported}')
print(f'  متخطى:          {skipped}')
print(f'  أقسام مضافة:   {sec_count}')
print(f'  آيات مضافة:    {aya_count}')
