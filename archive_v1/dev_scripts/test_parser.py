import json
import codecs
import re
import os

def parse_lecture(file_path):
    text = ""
    try:
        with codecs.open(file_path, 'r', encoding='utf-16le') as f:
            text = f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

    # الاعتماد على السطر الجديد \n كمعيار وحيد لتقسيم الفقرات
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
                header_ended = True # المكان عادةً هو نهاية الترويسة
                continue
            
            # إنذار أمان للخروج من الترويسة في حال لم نجد المكان
            if i > 15 and stripped_line != "": 
                header_ended = True
        
        # حفظ النص الأصلي مع تفادي إدخال الأسطر الفارغة تمامًا كفقرات، مع الاحتفاظ بمسافات التنسيق داخل الفقرة
        if header_ended:
            if line.strip(): # عدم تسجيل الأسطر الفارغة، ولكن النص نفسه لا يتم تنظيفه (يحفظ كما هو)
                paragraphs.append({
                    "sequence_index": sequence_index,
                    "content": line.rstrip('\r') # إزالة رمز العودة الخاص بويندوز فقط إن وجد
                })
                sequence_index += 1

    result = {
        "file_name": os.path.basename(file_path),
        "metadata": metadata,
        "paragraphs": paragraphs
    }
    
    return result

file_path = r"c:\Users\Az\Downloads\مفاهيم السيد حسين\منظومة معرفية\Lectures Module\دروس آيات من آل عمران\سورة آل عمران ـ الدرس الأول.txt"
parsed_data = parse_lecture(file_path)

output_data = {
    "file_extracted": parsed_data["file_name"],
    "metadata": parsed_data["metadata"],
    "total_paragraphs": len(parsed_data["paragraphs"]),
    "paragraphs_sample": parsed_data["paragraphs"][:8] # أول 8 فقرات للعرض على المستخدم
}

# حفظ العينة
with open('sample_parsed_lecture.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)

print("✅ تم الاستخراج بنجاح -> sample_parsed_lecture.json")
