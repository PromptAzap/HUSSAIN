import os
import codecs
import re
import uuid

class LectureParser:
    def __init__(self):
        # القائمة المدعومة من الترميزات للـ fallback
        self.encodings = ['utf-16le', 'utf-8', 'windows-1256', 'cp1256']
        
    def guess_encoding(self, file_path):
        """الكشف التلقائي عن الترميز الصحيح"""
        for enc in self.encodings:
            try:
                with codecs.open(file_path, 'r', encoding=enc) as f:
                    f.read()
                return enc
            except UnicodeDecodeError:
                continue
        return 'utf-8' # Default fallback
        
    def detect_ayahs_in_paragraph(self, text):
        """التحقق مما إذا كانت الفقرة تحتوي على آيات محاطة بأقواس قرآنية {...} أو ((...))"""
        # يمكن توسيعه لاحقاً للتعرف المتقدم
        if "{" in text and "}" in text:
            return True
        if "((" in text and "))" in text:
            return True
        return False

    def parse(self, file_path):
        """تحليل الملف واستخراج بياناته"""
        encoding = self.guess_encoding(file_path)
        
        with codecs.open(file_path, 'r', encoding=encoding) as f:
            text = f.read()

        lines = text.split('\n')
        
        metadata = {
            "title": None,
            "speaker": None,
            "date": None,
            "location": None,
            "series": None,
            "opening_ayah": None
        }
        
        paragraphs = []
        header_ended = False
        sequence_index = 1
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # استخراج الترويسة
            if not header_ended:
                if i == 0 and stripped_line:
                    metadata["series"] = stripped_line
                    continue
                if "الدرس الأول" in stripped_line or "الدرس الثاني" in stripped_line or stripped_line.startswith("الدرس"):
                    metadata["title"] = stripped_line
                    continue
                if stripped_line.startswith("{") and stripped_line.endswith("}") and not metadata["opening_ayah"] and i < 10:
                    metadata["opening_ayah"] = stripped_line
                    continue
                if "ألقاها السيد" in stripped_line:
                    metadata["speaker"] = stripped_line.replace("ألقاها السيد/", "").replace("ألقاها السيد", "").strip()
                    continue
                if "بتاريخ" in stripped_line:
                    metadata["date"] = stripped_line.replace("بتاريخ :", "").replace("بتاريخ", "").strip()
                    continue
                if "اليمن" in stripped_line or "صعدة" in stripped_line:
                    metadata["location"] = stripped_line.strip()
                    header_ended = True # نهاية الترويسة الرسمية
                    continue
                
                # إنذار أمان للخروج
                if i > 15 and stripped_line != "": 
                    header_ended = True
            
            # قسم الفقرات (الاحتفاظ بالنص الأصلي)
            if header_ended:
                if line.strip(): # تأكد أن السطر ليس فارغاً تماماً لتجنب تخزين الفراغات
                    content = line.rstrip('\r') # إزالة رمز العودة الخاص بويندوز فقط لمعالجة التنسيق العام
                    paragraphs.append({
                        "sequence_index": sequence_index,
                        "content": content,
                        "contains_ayat": self.detect_ayahs_in_paragraph(content)
                    })
                    sequence_index += 1

        return {
            "file_name": os.path.basename(file_path),
            "metadata": metadata,
            "paragraphs": paragraphs
        }
