"""
export_lectures_to_json.py
---------------------------
تصدير جميع الدروس من lectures_db.sqlite إلى ملفات JSON منفصلة.
كل ملف يحمل بيانات الدرس الكاملة + فقراته مرتبة حسب sequence_index.
"""
import os
import sys
import re
import json
import sqlite3
import time

DB_PATH = "lectures_db.sqlite"
EXPORT_DIR = "lectures_json_export"

# ---- أدوات مساعدة ----

def sanitize_filename(name, max_len=60):
    """تنظيف اسم الملف من الرموز غير المسموح بها في Windows"""
    if not name:
        return "unnamed"
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    name = re.sub(r'\s+', '_', name.strip())
    return name[:max_len]

def progress(current, total, prefix=""):
    percent = int((current / total) * 100)
    filled = int(percent / 5)
    bar = "#" * filled + "-" * (20 - filled)
    print(f"\r{prefix} [{bar}] {percent}% ({current}/{total})", end="", flush=True)


# ---- منطق التصدير ----

def fetch_all_lectures(conn):
    """جلب كل الدروس مع بيانات سلسلتها"""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            l.lecture_id,
            l.lecture_number,
            l.title,
            l.speaker,
            l.date,
            l.location,
            l.opening_ayah,
            l.metadata_json,
            l.created_at,
            s.series_id,
            s.title  AS series_title,
            s.subtitle AS series_subtitle
        FROM lectures l
        JOIN series s ON l.series_id = s.series_id
        ORDER BY s.title ASC, l.lecture_number ASC
    ''')
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def fetch_paragraphs(conn, lecture_id):
    """جلب فقرات درس واحد مرتبة حسب sequence_index"""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT paragraph_id, sequence_index, content, contains_ayat
        FROM paragraphs
        WHERE lecture_id = ?
        ORDER BY sequence_index ASC
    ''', (lecture_id,))
    paragraphs = []
    for row in cursor.fetchall():
        paragraphs.append({
            "paragraph_id": row[0],
            "sequence_index": row[1],
            "content": row[2],
            "contains_ayat": bool(row[3])
        })
    return paragraphs


def export_lecture(lecture, paragraphs, export_dir):
    """تجميع بيانات الدرس وكتابتها كملف JSON"""
    metadata_extra = {}
    if lecture.get("metadata_json"):
        try:
            metadata_extra = json.loads(lecture["metadata_json"])
        except Exception:
            pass

    doc = {
        "lecture_id": lecture["lecture_id"],
        "metadata": {
            "lecture_number": lecture["lecture_number"],
            "title": lecture["title"],
            "speaker": lecture["speaker"],
            "date": lecture["date"],
            "location": lecture["location"],
            "opening_ayah": lecture["opening_ayah"],
            "created_at": lecture["created_at"],
            "extra": metadata_extra,
            "series": {
                "series_id": lecture["series_id"],
                "title": lecture["series_title"],
                "subtitle": lecture["series_subtitle"]
            }
        },
        "statistics": {
            "total_paragraphs": len(paragraphs),
            "paragraphs_with_ayat": sum(1 for p in paragraphs if p["contains_ayat"])
        },
        "paragraphs": paragraphs
    }

    # بناء اسم الملف: {lecture_id_prefix}_{title}.json
    lid_short = lecture["lecture_id"][:8]
    title_clean = sanitize_filename(lecture["title"] or "بدون_عنوان")
    series_clean = sanitize_filename(lecture["series_title"] or "")

    # تنظيم بالمجلدات الفرعية حسب السلسلة
    series_dir = os.path.join(export_dir, series_clean)
    os.makedirs(series_dir, exist_ok=True)

    filename = f"{lid_short}_{title_clean}.json"
    filepath = os.path.join(series_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)

    return filepath, len(paragraphs)


# ---- نقطة الدخول ----

def run_export(single_lecture_id=None, db_path=DB_PATH, export_dir=EXPORT_DIR):
    os.makedirs(export_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    lectures = fetch_all_lectures(conn)

    if single_lecture_id:
        lectures = [l for l in lectures if l["lecture_id"] == single_lecture_id]
        if not lectures:
            print(f"[خطأ] لم يُعثر على الدرس بالمعرف: {single_lecture_id}")
            conn.close()
            return

    total = len(lectures)
    print(f"بدء التصدير: {total} درس -> {export_dir}/")

    manifest_entries = []
    errors = []
    total_paragraphs = 0

    start_time = time.time()

    for i, lecture in enumerate(lectures, 1):
        progress(i, total, prefix="تصدير")
        try:
            paragraphs = fetch_paragraphs(conn, lecture["lecture_id"])
            filepath, para_count = export_lecture(lecture, paragraphs, export_dir)
            total_paragraphs += para_count
            manifest_entries.append({
                "lecture_id": lecture["lecture_id"],
                "series": lecture["series_title"],
                "title": lecture["title"],
                "paragraphs": para_count,
                "file": os.path.relpath(filepath, export_dir)
            })
        except Exception as e:
            errors.append({"lecture_id": lecture["lecture_id"], "error": str(e)})

    conn.close()
    elapsed = round(time.time() - start_time, 2)
    print()  # سطر جديد بعد Progress Bar

    # كتابة ملف الجرد
    manifest = {
        "export_summary": {
            "total_lectures": len(manifest_entries),
            "total_paragraphs": total_paragraphs,
            "errors": len(errors),
            "elapsed_seconds": elapsed,
            "db_source": db_path,
            "export_dir": export_dir
        },
        "error_log": errors,
        "entries": manifest_entries
    }

    manifest_path = os.path.join(export_dir, "export_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"تم: {len(manifest_entries)} درس | {total_paragraphs} فقرة | {len(errors)} خطأ | {elapsed}s")
    print(f"سجل الجرد: {manifest_path}")


if __name__ == "__main__":
    # --- اختبار درس واحد أولاً ---
    conn_test = sqlite3.connect(DB_PATH)
    cursor_test = conn_test.cursor()
    cursor_test.execute("SELECT lecture_id FROM lectures LIMIT 1")
    first_id = cursor_test.fetchone()[0]
    conn_test.close()

    print("--- اختبار درس واحد ---")
    run_export(single_lecture_id=first_id)

    print("\n--- تصدير جميع الـ 82 درس ---")
    run_export()
