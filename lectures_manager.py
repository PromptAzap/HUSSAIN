import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sqlite3
import json
import uuid
from lecture_parser import LectureParser
from lectures_db_setup import setup_database

class LecturesManager:
    def __init__(self, db_path='lectures_db.sqlite'):
        self.db_path = db_path
        self.parser = LectureParser()
        
        # التأكد من وجود/تهيئة القاعدة قبل بدء الإدارة
        setup_database(db_path)

    def _get_or_create_series(self, title, subtitle=None):
        """إنشاء أو جلب معرف السلسلة من قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT series_id FROM series WHERE title = ?", (title,))
        result = cursor.fetchone()
        
        if result:
            conn.close()
            return result[0]
            
        series_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO series (series_id, title, subtitle) VALUES (?, ?, ?)",
                       (series_id, title, subtitle))
        conn.commit()
        conn.close()
        return series_id

    def process_lecture_file(self, file_path):
        """تحليل ومعالجة ملف درس وحفظه في قاعدة البيانات"""
        print(f"قيد المعالجة: {os.path.basename(file_path)}")
        parsed_data = self.parser.parse(file_path)
        metadata = parsed_data['metadata']
        paragraphs = parsed_data['paragraphs']
        
        # استخراج/الاعتماد على اسم مجلد مسار الملف إذا كان title السلسلة فارغاً من النظرة الأولى
        series_title = metadata.get('series')
        if not series_title:
            series_title = os.path.basename(os.path.dirname(file_path))
            
        series_id = self._get_or_create_series(series_title)
        
        # استخراج رقم الدرس من العنوان إن أمكن أو تعيينه لـ 1 كقيمة افتراضية
        lecture_number = 1
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # التأكد مسبقاً من عدم وجود الدرس لتجنب الازدواجية
        cursor.execute("SELECT lecture_id FROM lectures WHERE title = ? AND series_id = ?", 
                       (metadata.get('title'), series_id))
        if cursor.fetchone():
            print(f"الدرس [{metadata.get('title')}] موجود مسبقاً، جاري التخطي.")
            conn.close()
            return
            
        lecture_id = str(uuid.uuid4())
        
        # إضافة الدرس
        cursor.execute('''
        INSERT INTO lectures (lecture_id, series_id, lecture_number, title, speaker, date, location, opening_ayah, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lecture_id,
            series_id,
            lecture_number,
            metadata.get('title'),
            metadata.get('speaker'),
            metadata.get('date'),
            metadata.get('location'),
            metadata.get('opening_ayah'),
            json.dumps({"original_file": parsed_data['file_name']}, ensure_ascii=False)
        ))
        
        # إضافة الفقرات كصفوف مستقلة مع المحافظة على النص الأصلي
        for p in paragraphs:
            paragraph_id = str(uuid.uuid4())
            cursor.execute('''
            INSERT INTO paragraphs (paragraph_id, lecture_id, sequence_index, content, contains_ayat)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                paragraph_id,
                lecture_id,
                p['sequence_index'],
                p['content'],
                1 if p['contains_ayat'] else 0
            ))
            
        conn.commit()
        conn.close()
        print(f"  --> فقرات مخزنة: {len(paragraphs)}")

    def process_all_lectures(self, lectures_root_dir):
        """
        Batch Processing: المرور على جميع المجلدات داخل مجلد الدروس الرئيسي،
        واعتبار كل مجلد سلسلة مستقلة، ومعالجة كل ملف .txt بداخله كدرس.
        """
        total_files = 0
        total_paragraphs = 0
        skipped = 0
        errors = 0
        manifest = []

        # كل مجلد داخل Lectures Module = سلسلة
        for folder_name in os.listdir(lectures_root_dir):
            folder_path = os.path.join(lectures_root_dir, folder_name)
            if not os.path.isdir(folder_path):
                continue

            series_label = folder_name
            txt_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]

            if not txt_files:
                continue

            print(f"\n[سلسلة] {series_label} ({len(txt_files)} درس)")

            for txt_file in sorted(txt_files):
                file_path = os.path.join(folder_path, txt_file)
                try:
                    before_count = self._paragraph_count()
                    self.process_lecture_file(file_path)
                    after_count = self._paragraph_count()
                    added = after_count - before_count
                    if added > 0:
                        total_paragraphs += added
                        total_files += 1
                        manifest.append({
                            "series": series_label,
                            "file": txt_file,
                            "paragraphs_added": added
                        })
                    else:
                        skipped += 1
                except Exception as e:
                    errors += 1
                    print(f"  [خطأ] {txt_file}: {e}")

        # حفظ سجل الجرد (Manifest)
        manifest_path = os.path.join(os.path.dirname(self.db_path), "lectures_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({
                "total_files_processed": total_files,
                "total_paragraphs_stored": total_paragraphs,
                "skipped_duplicates": skipped,
                "errors": errors,
                "entries": manifest
            }, f, ensure_ascii=False, indent=4)

        print(f"\n==== الإجمالي ====")
        print(f"ملفات تمت معالجتها: {total_files}")
        print(f"فقرات مخزنة: {total_paragraphs}")
        print(f"مكررة (تم تخطيها): {skipped}")
        print(f"أخطاء: {errors}")
        print(f"سجل الجرد محفوظ: {manifest_path}")

    def _paragraph_count(self):
        """جلب العدد الحالي للفقرات في القاعدة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM paragraphs")
        count = cursor.fetchone()[0]
        conn.close()
        return count


if __name__ == "__main__":
    LECTURES_ROOT = r"c:\Users\Az\Downloads\مفاهيم السيد حسين\منظومة معرفية\Lectures Module"
    manager = LecturesManager()
    manager.process_all_lectures(LECTURES_ROOT)
