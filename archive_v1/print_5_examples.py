import os
import json
import sqlite3
import random
import sys

sys.stdout.reconfigure(encoding='utf-8')

ONTOLOGY_DIR = '.'
DB_PATH = 'quran_roots_dual_v2.sqlite'

with open('concept_ayah_mapping.json', 'r', encoding='utf-8') as f:
    mappings = json.load(f)

samples = random.sample(mappings, min(5, len(mappings)))

def get_concept_name(target_id):
    for filename in os.listdir(ONTOLOGY_DIR):
        if not filename.endswith('.json') or filename == 'concept_ayah_mapping.json':
            continue
        try:
            with open(os.path.join(ONTOLOGY_DIR, filename), 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                
            def search(obj):
                if isinstance(obj, dict):
                    if obj.get('lesson_concept_id') == target_id:
                        return obj.get('concept_name', 'اسم غير متوفر')
                    for v in obj.values():
                        res = search(v)
                        if res: return res
                elif isinstance(obj, list):
                    for item in obj:
                        res = search(item)
                        if res: return res
                return None
                
            result = search(data)
            if result:
                return result
        except:
            pass
    return "غير معروف"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("\n--- عينة من 5 مطابقات عشوائية ---\n")
for i, s in enumerate(samples, 1):
    lesson_id = s["lesson_concept_id"]
    global_ayah = s["global_ayah"]
    
    cursor.execute("SELECT surah_no, ayah_no, text_uthmani FROM ayah WHERE global_ayah = ?", (global_ayah,))
    row = cursor.fetchone()
    if row:
        s_no, a_no, text = row
        c_name = get_concept_name(lesson_id)
        
        print(f"[{i}] معرف المفهوم (ID): {lesson_id}")
        # print(f"[{i}] اسم المفهوم: {c_name}")
        print(f"    الآية [سورة {s_no} / الآية {a_no}]: ﴿{text}﴾")
        print("-" * 60)

conn.close()
