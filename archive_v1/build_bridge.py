import os
import json
import sqlite3
import sys
import re

# =========================================================
# الإعدادات
# =========================================================
DB_PATH = 'quran_roots_dual_v2.sqlite'
ONTOLOGY_DIR = '.'  # المجلد الحالي حيث توجد ملفات JSON
OUTPUT_JSON = 'concept_ayah_mapping.json'

def normalize_text(text):
    """
    تطبيع النص العربي لزيادة دقة المطابقة:
    - إزالة التشكيل.
    - توحيد أشكال الألف، التاء المربوطة والمفتوحة، والياء.
    - إزالة علامات الترقيم الزائدة لتجنب تعارض الفواصل والأقواس.
    """
    if not isinstance(text, str):
        return ""
    
    # تفريغ النص من التشكيل
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
    # توحيد الألفات
    text = re.sub(r'[أإآ]', 'ا', text)
    # توحيد التاء والهاء
    text = re.sub(r'ة', 'ه', text)
    # توحيد الياء والألف المقصورة
    text = re.sub(r'[يى]$', 'ى', text)
    # إزالة الأقواس الهلالية والقرآنية ومختلف الرموز غير الحرفية
    text = re.sub(r'[^\w\s]', '', text)
    # إزالة المسافات المتعددة وتحويلها لمسافة واحدة
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def extract_concepts_from_json(file_path):
    """
    بحث عودي (Recursive) داخل ملف JSON لاستخراج أي مفهوم 
    يحتوي على مفاتيحه الأساسية: lesson_concept_id و foundational_quote.
    هذه الطريقة تضمن عمل السكربت بغض النظر عن بنية الـ JSON الدقيقة المعتمدة لديك.
    """
    concepts = []
    
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️ تجاهل ملف {file_path} بسبب خطأ في القراءة: {e}")
        return concepts

    def recursive_search(obj):
        if isinstance(obj, dict):
            # إذا وجدنا قاموساً (Dict) يحتوي على المفتاحين معاً
            if 'lesson_concept_id' in obj and 'foundational_quote' in obj:
                quote = obj.get('foundational_quote')
                if quote and str(quote).strip():
                    concepts.append({
                        'lesson_concept_id': obj['lesson_concept_id'],
                        'foundational_quote': quote
                    })
            # متابعة البحث في باقي القيم
            for key, value in obj.items():
                recursive_search(value)
        elif isinstance(obj, list):
            for item in obj:
                recursive_search(item)

    recursive_search(data)
    return concepts

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print(f"==== بدء تشغيل أداة الربط (The Bridge) ====\n")
    
    # 1. استخراج جميع المفاهيم من ملفات الأنطولوجيا (JSON) الموجودة
    all_concepts = []
    for filename in os.listdir(ONTOLOGY_DIR):
        if filename.endswith('.json') and filename != OUTPUT_JSON:
            file_path = os.path.join(ONTOLOGY_DIR, filename)
            concepts = extract_concepts_from_json(file_path)
            if concepts:
                all_concepts.extend(concepts)
                print(f"✅ تم دمج {len(concepts)} مفهوم من ملف: {filename}")

    if not all_concepts:
        print("\n❌ لم يتم العثور على أي مفاهيم تحتوي على lesson_concept_id و foundational_quote.")
        return

    print(f"\nإجمالي المفاهيم التي تم العثور عليها للاستكشاف: {len(all_concepts)}")

    # 2. الاتصال بقاعدة البيانات وقراءة الآيات
    if not os.path.exists(DB_PATH):
        print(f"\n❌ ملف قاعدة البيانات غير موجود في المسار: {DB_PATH}")
        return

    print("\nجارٍ الاتصال بقاعدة البيانات وتحميل الجدول [ayah]...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT global_ayah, surah_no, ayah_no, text_plain, text_plain_norm FROM ayah")
        ayahs = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"❌ حدث خطأ أثناء قراءة الجدول: {e}")
        conn.close()
        return
        
    print(f"تم بنجاح تحميل {len(ayahs)} آية قرآنية للبحث والتطابق.\n")

    # 3. محرك المطابقة (Matching Mechanism)
    mappings = []
    matched_concepts_count = 0

    print("جارٍ تحضير النصوص وتسريعها (Optimization)...")
    preprocessed_ayahs = []
    for ayah in ayahs:
        preprocessed_ayahs.append({
            "global_ayah": ayah[0],
            "ayah_norm": normalize_text(str(ayah[4]))
        })

    print("جارٍ مقارنة ومطابقة الاقتباسات التأسيسية مع قاعدة البيانات...")
    
    for concept in all_concepts:
        concept_id = concept['lesson_concept_id']
        quote_original = str(concept['foundational_quote'])
        
        # تطبيع الاقتباس
        quote_norm = normalize_text(quote_original)
        
        # التأكد من أن الاقتباس التأسيسي يحتوي على 4 كلمات على الأقل لضمان الدقة
        if len(quote_norm.split()) < 4:
            continue

        matched_for_this_concept = False
        
        for pre_ayah in preprocessed_ayahs:
            global_ayah = pre_ayah["global_ayah"]
            ayah_norm = pre_ayah["ayah_norm"]
            
            # -- آليات المطابقة المرنة (Flexible Matching) --
            # أ - الاقتباس مطابق كلياً أو موجود داخل الآية كأساس
            if quote_norm in ayah_norm:
                mappings.append({"lesson_concept_id": concept_id, "global_ayah": global_ayah})
                matched_for_this_concept = True
            
            # ب - الآية موجودة بالكامل داخل الاقتباس (في حال كان الاقتباس يحتوي عدة آيات أو شرح مرافق)
            elif ayah_norm in quote_norm:
                # لتجنب تطابق كلمات قصيرة جدا تُحسب كـ"آية"، نقوم بالتحقق من طول الآية المكتشفة
                if len(ayah_norm) > 15:  
                    mappings.append({"lesson_concept_id": concept_id, "global_ayah": global_ayah})
                    matched_for_this_concept = True

        if matched_for_this_concept:
            matched_concepts_count += 1
            
    conn.close()

    # إزالة التكرار (في حال تقاطعت الآليات)
    unique_mappings = []
    seen = set()
    for m in mappings:
        t = (m['lesson_concept_id'], m['global_ayah'])
        if t not in seen:
            seen.add(t)
            unique_mappings.append(m)

    # 4. إصدار ملف المخرجات
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(unique_mappings, f, ensure_ascii=False, indent=4)

    print(f"\n==== اكتملت العملية ====")
    print(f"📊 النتائج:")
    print(f"- إجمالي المفاهيم ذات التطابق الناجح: {matched_concepts_count} من {len(all_concepts)}")
    print(f"- إجمالي العلاقات (المفهوم <-> الآية) المستخرجة والمفرزة: {len(unique_mappings)}")
    print(f"- تم حفظ مصفوفة الروابط في الملف الجديد بمسار: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
