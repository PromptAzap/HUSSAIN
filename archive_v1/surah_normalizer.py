import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'lectures_db.sqlite'

std_114 = [
    "الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة", "الأنعام", "الأعراف", "الأنفال", "التوبة", "يونس",
    "هود", "يوسف", "الرعد", "إبراهيم", "الحجر", "النحل", "الإسراء", "الكهف", "مريم", "طه",
    "الأنبياء", "الحج", "المؤمنون", "النور", "الفرقان", "الشعراء", "النمل", "القصص", "العنكبوت", "الروم",
    "لقمان", "السجدة", "الأحزاب", "سبأ", "فاطر", "يس", "الصافات", "ص", "الزمر", "غافر",
    "فصلت", "الشورى", "الزخرف", "الدخان", "الجاثية", "الأحقاف", "محمد", "الفتح", "الحجرات", "ق",
    "الذاريات", "الطور", "النجم", "القمر", "الرحمن", "الواقعة", "الحديد", "المجادلة", "الحشر", "الممتحنة",
    "الصف", "الجمعة", "المنافقون", "التغابن", "الطلاق", "التحريم", "الملك", "القلم", "الحاقة", "المعارج",
    "نوح", "الجن", "المزمل", "المدثر", "القيامة", "الإنسان", "المرسلات", "النبأ", "النازعات", "عبس",
    "التكوير", "الانفطار", "المطففين", "الانشقاق", "البروج", "الطارق", "الأعلى", "الغاشية", "الفجر", "البلد",
    "الشمس", "الليل", "الضحى", "الشرح", "التين", "العلق", "القدر", "البينة", "الزلزلة", "العاديات",
    "القارعة", "التكاثر", "العصر", "الهمزة", "الفيل", "قريش", "الماعون", "الكوثر", "الكافرون", "النصر",
    "المسد", "الإخلاص", "الفلق", "الناس"
]

def normalize_text(text):
    if not text: return ""
    text = text.replace("ـ", "")
    text = re.sub(r'[\u064B-\u065F]', '', text)
    # إزالة التعريف للمطابقة ولكن الحفاظ عليه في الإرجاع للمعياري
    norm = re.sub(r'[أإآ]', 'ا', text)
    # norm = norm.replace("ال", "") # حذر جداً
    return norm.strip()

def get_best_match(name, standard_list):
    norm_name = normalize_text(name)
    
    # 1. مطابقة تامة
    for std in standard_list:
        if norm_name == normalize_text(std):
            return std
            
    # 2. مطابقة بدون "ال" التعريف (للحالات التي فقدت ال)
    if not norm_name.startswith("ال"):
        for std in standard_list:
            if norm_name == normalize_text(std).replace("ال", "", 1): # استبدال أول ال
                return std

    # 3. معالجة النطاقات
    if " - " in name or "-" in name or " إلى " in name:
        parts = re.split(r' - |-| إلى ', name)
        matches = []
        for p in parts:
            m = get_best_match(p.strip(), standard_list)
            if m: matches.append(m)
        if matches:
            return " - ".join(matches)
            
    return name

def run_normalization():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT DISTINCT surah_name FROM section_ayah_refs")
    unique_names = [r[0] for r in c.fetchall()]
    
    print(f"--- تنفيذ التصحيح النهائي لـ {len(unique_names)} اسماً ---")
    
    for name in unique_names:
        standardized = get_best_match(name, std_114)
        if standardized != name:
            print(f"  [FIXED] '{name}' -> '{standardized}'")
            c.execute("UPDATE section_ayah_refs SET surah_name = ? WHERE surah_name = ?", (standardized, name))
            
    conn.commit()
    
    # تأكيد بقرة - زمر
    c.execute("UPDATE section_ayah_refs SET surah_name = 'البقرة - الزمر' WHERE surah_name = 'بقرة - زمر'")
    if c.rowcount > 0:
        print("  [FIXED] 'بقرة - زمر' -> 'البقرة - الزمر'")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    run_normalization()
