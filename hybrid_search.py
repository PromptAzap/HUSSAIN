import os
import json
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

try:
    torch_lib = os.path.join(os.path.dirname(sys.executable), "Lib", "site-packages", "torch", "lib")
    if os.path.exists(torch_lib):
        os.add_dll_directory(torch_lib)
except Exception:
    pass

# ملاحظة: يتطلب تشغيل هذا السكربت تثبيت المكتبات التالية:
# pip install sentence-transformers chromadb tqdm
from sentence_transformers import SentenceTransformer
import chromadb

# =========================================================
# الإعدادات
# =========================================================
DB_PATH = 'quran_roots_dual_v2.sqlite'
MAPPING_JSON = 'concept_ayah_mapping.json'
ONTOLOGY_DIR = 'archive_v1'  # مسار ملفات الأنطولوجيا القديمة التي تم الفهرسة منها

class HybridSearchEngine:
    def __init__(self):
        print("1. جاري تهيئة محرك البحث (Semantic Engine)...")
        print("   - تحميل نموذج Sentence-Transformers للحوسبة الدلالية...")
        # استخدام نموذج يدعم اللغة العربية بكفاءة
        self.encoder = SentenceTransformer('asafaya/bert-base-arabic')
        
        print("   - تهيئة قاعدة بيانات ChromaDB المتجهة للمجموعات...")
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        # مجموعة المفاهيم (الأنطولوجيا)
        self.collection = self.chroma_client.get_or_create_collection(name="concepts_collection")
        # مجموعة آيات القرآن (Semantic Fallback)
        self.quran_collection = self.chroma_client.get_or_create_collection(name="quran_collection")
        
        print("   - تحميل خريطة الربط الثابت (Hard-Mapping)...")
        self.mappings = self._load_mappings()
        
    def _load_mappings(self):
        if not os.path.exists(MAPPING_JSON):
            return {}
        with open(MAPPING_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
        mapping_dict = {}
        for item in data:
            cid = item['lesson_concept_id']
            if cid not in mapping_dict:
                mapping_dict[cid] = []
            if item['global_ayah'] not in mapping_dict[cid]:
                mapping_dict[cid].append(item['global_ayah'])
        return mapping_dict

    def index_concepts(self):
        """قراءة المفاهيم وتضمينها كمتجهات (Vectors)"""
        print("\n2. جاري فهرسة مفاهيم الأنطولوجيا...")
        concepts_to_index = []
        for filename in os.listdir(ONTOLOGY_DIR):
            if filename.endswith('.json') and filename != MAPPING_JSON:
                try:
                    with open(os.path.join(ONTOLOGY_DIR, filename), 'r', encoding='utf-8-sig') as f:
                        data = json.load(f)
                        def extract(obj):
                            if isinstance(obj, dict):
                                if 'lesson_concept_id' in obj and 'concept_name' in obj:
                                    name = obj.get('concept_name', '')
                                    definition = obj.get('definition', '')
                                    text_to_embed = f"{name} - {definition}"
                                    concepts_to_index.append({
                                        'id': str(obj['lesson_concept_id']),
                                        'text': text_to_embed,
                                        'name': name,
                                        'definition': definition
                                    })
                                for k, v in obj.items(): extract(v)
                            elif isinstance(obj, list):
                                for item in obj: extract(item)
                        extract(data)
                except Exception:
                    pass

        if concepts_to_index:
            ids = [c['id'] for c in concepts_to_index]
            documents = [c['text'] for c in concepts_to_index]
            # تم إضافة الـ definition كـ Metadata لوقت الحاجة إليه في Fallback
            metadatas = [{"name": c['name'], "definition": c['definition']} for c in concepts_to_index]
            
            existing = self.collection.count()
            if existing < len(ids):
                print(f"   - توليد وتخزين متجهات لـ {len(ids)} مفهوم...")
                # المعالجة في دفعات لمنع استهلاك الذاكرة المفرط
                batch_size = 100
                for i in range(0, len(ids), batch_size):
                    end_idx = i + batch_size
                    b_ids = ids[i:end_idx]
                    b_docs = documents[i:end_idx]
                    b_meta = metadatas[i:end_idx]
                    b_embeds = self.encoder.encode(b_docs).tolist()
                    self.collection.add(ids=b_ids, documents=b_docs, embeddings=b_embeds, metadatas=b_meta)
                print("   ✅ اكتملت فهرسة المفاهيم.")
            else:
                print(f"   ✅ المفاهيم مفهرسة مسبقاً ({existing} مفهوم).")

    def index_quran(self):
        """قراءة آيات القرآن من SQLite وتضمينها كمتجهات (Vectors)"""
        print("\n3. جاري فهرسة آيات القرآن الكريم للـ Semantic Fallback...")
        
        # التحقق مما إذا كانت الفهرسة تمت مسبقاً (القرآن = 6236 آية)
        existing_ayahs = self.quran_collection.count()
        TOTAL_AYAHS = 6236
        if existing_ayahs >= TOTAL_AYAHS:
            print(f"   ✅ آيات القرآن مفهرسة مسبقاً الكامل ({existing_ayahs} آية).")
            return

        print("   - جلب وتضمين نحو 6236 آية... (قد تستغرق هذه العملية من 5 إلى 15 دقيقة)")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # نستخدم text_plain للحصول على أداء أفضل للبحث الدلالي
        cursor.execute("SELECT global_ayah, surah_no, ayah_no, text_plain FROM ayah ORDER BY global_ayah ASC")
        rows = cursor.fetchall()
        conn.close()

        ids = []
        documents = []
        metadatas = []
        
        for row in rows:
            global_ayah, surah_no, ayah_no, text_plain = row
            ids.append(str(global_ayah))
            documents.append(text_plain)
            metadatas.append({"surah_no": surah_no, "ayah_no": ayah_no})

        # ضخ الآيات على دفعات لمنع توقف الجهاز بسبب امتلاء الذاكرة
        batch_size = 300
        total_batches = (len(ids) // batch_size) + 1
        
        for i in range(0, len(ids), batch_size):
            end_idx = i + batch_size
            b_ids = ids[i:end_idx]
            b_docs = documents[i:end_idx]
            b_meta = metadatas[i:end_idx]
            
            print(f"     * معالجة الدفعة {(i//batch_size)+1} من {total_batches} ({len(b_ids)} آية)...")
            b_embeds = self.encoder.encode(b_docs).tolist()
            self.quran_collection.add(
                ids=b_ids,
                documents=b_docs,
                embeddings=b_embeds,
                metadatas=b_meta
            )
            
        print("   ✅ اكتملت فهرسة القرآن الكريم بالكامل.")

    def get_ayah_details(self, global_ayah):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT surah_no, ayah_no, text_uthmani FROM ayah WHERE global_ayah = ?", (global_ayah,))
        ayah_row = cursor.fetchone()
        
        if not ayah_row:
            conn.close()
            return None
            
        surah_no, ayah_no, text = ayah_row
        ayah_str_id = f"{surah_no}:{ayah_no}"
        cursor.execute("SELECT token, root FROM token WHERE ayah_id = ?", (ayah_str_id,))
        roots = cursor.fetchall()
        conn.close()
        
        return {
            "surah": surah_no, "ayah_no": ayah_no, "text": text,
            "roots": [{"token": t[0], "root": t[1]} for t in roots if t[1]]
        }

    def search(self, query_text, top_k=2):
        print(f"\n==================================================")
        print(f"🔍 نتيجة استعلام المستخدم: '{query_text}'")
        print(f"==================================================\n")
        
        # --- 1. البحث الدلالي في الأنطولوجيا (Concepts Collection) --- #
        query_embedding = self.encoder.encode([query_text]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=1 # نأخذ المفهوم الأقرب كمرجع أساسي
        )
        
        if not results['ids'] or len(results['ids'][0]) == 0:
            print("❌ لم يتم العثور على أي مفهوم مقارب في الأنطولوجيا.")
            return
            
        concept_id = results['ids'][0][0]
        concept_name = results['metadatas'][0][0]['name']
        concept_def = results['metadatas'][0][0]['definition']
        distance = results['distances'][0][0]
        
        print(f"🟢 (1) المفهوم المستخرج دلالياً من الأنطولوجيا:")
        print(f"   اسم المفهوم: [{concept_name}] (ID: {concept_id}) (مسافة: {distance:.4f})")
        
        # --- 2. التحقق من الربط الثابت بناءً على الاقتباس (Hard-Mapping) --- #
        linked_ayahs = self.mappings.get(concept_id, [])
        
        if linked_ayahs:
            print("\n📖 (2) الآيات القرآنية المرتبطة به مباشرة (Hard-link):")
            for ga in linked_ayahs:
                self._print_ayah_data(ga)
        else:
            # --- 3. تشغيل ميزة الرجوع الدلالي البديل (Semantic Fallback) --- #
            print("\n⚡ [Semantic Fallback المفهوم لا يملك ربطاً نصياً. جاري تفعيل]")
            print("   يبحث المحرك الدلالي في المصحف كاملاً باستخدام (اسم المفهم + تعريفه) لجلب المعنى المطابق...")
            
            # إنتاج سياق دلالي غني جداً من الأنطولوجيا للبحث به في القرآن
            fallback_query = f"{concept_name} {concept_def}"
            fallback_embedding = self.encoder.encode([fallback_query]).tolist()
            
            quran_results = self.quran_collection.query(
                query_embeddings=fallback_embedding,
                n_results=top_k # نجلب أقرب 2 آيات دلالياً
            )
            
            print(f"\n📖 (2) أقرب {top_k} آيات قرآنية للمعنى الفلسفي للمفهوم:")
            if quran_results['ids'] and len(quran_results['ids'][0]) > 0:
                for i in range(len(quran_results['ids'][0])):
                    global_ayah_fallback = int(quran_results['ids'][0][i])
                    q_dist = quran_results['distances'][0][i]
                    print(f"   📍 [النتيجة {i+1}] - نسبة التباعد الدلالي: {q_dist:.4f}")
                    self._print_ayah_data(global_ayah_fallback)
            else:
                print("   (لم يجد المحرك آيات مقاربة)")

    def _print_ayah_data(self, global_ayah):
        """helper function to cleanly print ayah and roots"""
        details = self.get_ayah_details(global_ayah)
        if details:
            print(f"   ﴿{details['text']}﴾ [سورة {details['surah']} / الآية {details['ayah_no']}]")
            roots_list = [f"{r['token']}({r['root']})" for r in details['roots'][:7]]
            if roots_list:
                print(f"   🌱 الجذور اللغوية: {' | '.join(roots_list)} ...\n")
            else:
                print(f"   🌱 الجذور اللغوية: (لم يعثر على جذور محددة)\n")

# =========================================================
# نقطة الإدخال
# =========================================================
if __name__ == "__main__":
    engine = HybridSearchEngine()
    engine.index_concepts()
    engine.index_quran() # إضافة فهرسة القرآن للمحرك الدلالي
    
    # نموذج لتجربة البحث (Fallbacks & Hard-links)
    queries = [
        "الخسارة الحقيقية للإنسان",
        "مواجهة أهل الكتاب"
    ]
    for q in queries:
        engine.search(q, top_k=2)
