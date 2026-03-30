import os
import sys

# إضافة المسار الحالي للمسارات لضمان استيراد الوحدات المحلية
import os
import sys
sys.path.append(os.getcwd())

# محاولة حل مشكلة تحميل Torch DLLs في بيئة الـ Embedded
try:
    python_dir = os.path.dirname(sys.executable)
    torch_lib = os.path.join(python_dir, "Lib", "site-packages", "torch", "lib")
    if os.path.exists(torch_lib):
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(torch_lib)
        os.environ["PATH"] = torch_lib + os.pathsep + os.environ["PATH"]
except Exception:
    pass

from hybrid_search import HybridSearchEngine
import lectures_query

class HussainUnifiedEngine:
    def __init__(self):
        print("\n[START] جاري تشغيل المحرك الموحّد HUSSAIN...")
        
        # 1. تهيئة محرك البحث الدلالي (القرآن + الأنطولوجيا)
        # ملاحظة: HybridSearchEngine يقوم عند التحميل بتهيئة السيرفر والنماذج
        self.semantic_engine = HybridSearchEngine()
        
        # 2. التأكد من تحميل فهرس الدروس (FAISS/TF-IDF)
        print("   - تهيئة محرك بحث الدروس...")
        lectures_query.load_index()
        
        print("[DONE] المحرك الموحّد جاهز للعمل.\n")

    def search(self, query_text: str, top_k: int = 5, sources: list = None) -> dict:
        """
        إجراء بحث شامل في جميع المصادر ودمج النتائج.
        """
        if sources is None:
            sources = ["concepts", "quran", "lectures"]
            
        results = {
            "query": query_text,
            "ontology": None,
            "quran": [],
            "lectures": []
        }

        # نحن نستخدم Threading لتسريع البحث المتوازي في المصادر المختلفة
        # (اختياري، لكن مفيد للاستجابة السريعة)
        
        def search_lectures():
            if "lectures" in sources:
                results["lectures"] = lectures_query.search_paragraphs(query_text, top_k=top_k)

        def search_semantic():
            # البحث الدلالي في الأنطولوجيا
            query_embedding = self.semantic_engine.encoder.encode([query_text]).tolist()
            
            if "concepts" in sources:
                ont_res = self.semantic_engine.collection.query(
                    query_embeddings=query_embedding,
                    n_results=1
                )
                if ont_res['ids'] and len(ont_res['ids'][0]) > 0:
                    concept_id = ont_res['ids'][0][0]
                    results["ontology"] = {
                        "id": concept_id,
                        "name": ont_res['metadatas'][0][0]['name'],
                        "definition": ont_res['metadatas'][0][0]['definition'],
                        "distance": float(ont_res['distances'][0][0])
                    }
                    
                    # إذا وجدنا مفهوماً، نتحقق من الربط الثابت للقرآن
                    if "quran" in sources:
                        linked_ayahs = self.semantic_engine.mappings.get(concept_id, [])
                        for ga in linked_ayahs:
                            details = self.semantic_engine.get_ayah_details(ga)
                            if details:
                                details["match_type"] = "hard_link"
                                results["quran"].append(details)
            
            # إذا لم نجد آيات مرتبطة بالربط الثابت، أو أردنا المزيد من النتائج الدلالية للقرآن
            if "quran" in sources and not results["quran"]:
                # تفعيل Semantic Fallback للقرآن
                fallback_query = query_text
                if results["ontology"]:
                    fallback_query = f"{results['ontology']['name']} {results['ontology']['definition']}"
                
                fallback_embedding = self.semantic_engine.encoder.encode([fallback_query]).tolist()
                quran_res = self.semantic_engine.quran_collection.query(
                    query_embeddings=fallback_embedding,
                    n_results=top_k
                )
                
                if quran_res['ids'] and len(quran_res['ids'][0]) > 0:
                    for i in range(len(quran_res['ids'][0])):
                        ga = int(quran_res['ids'][0][i])
                        details = self.semantic_engine.get_ayah_details(ga)
                        if details:
                            details["match_type"] = "semantic_fallback"
                            details["distance"] = float(quran_res['distances'][0][i])
                            results["quran"].append(details)

        # تشغيل البحث في خيوط متوازية
        t1 = threading.Thread(target=search_lectures)
        t2 = threading.Thread(target=search_semantic)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        return results

    def get_paragraph_details(self, paragraph_id: str):
        """جلب تفاصيل فقرة مع سياقها"""
        details = lectures_query.get_paragraph_by_id(paragraph_id)
        if details:
            details["context"] = lectures_query.get_paragraph_context(paragraph_id, surrounding=2)
        return details

    def get_ayah_details(self, global_ayah: int):
        """جلب تفاصيل آية معينة"""
        return self.semantic_engine.get_ayah_details(global_ayah)

# --- تجربة المحرك ---
if __name__ == "__main__":
    engine = HussainUnifiedEngine()
    
    # تجربة البحث
    q = "الخسارة الحقيقية للإنسان"
    res = engine.search(q, top_k=2)
    
    print(f"\n[INFO] نتائج البحث عن: {q}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    if res["ontology"]:
        print(f"[INFO] المفهوم: {res['ontology']['name']}")
        
    print(f"\n[INFO] القرآن ({len(res['quran'])} نتائج):")
    for a in res["quran"]:
        print(f"  - ﴿{a['text'][:50]}...﴾ [{a['surah']}:{a['ayah_no']}] ({a['match_type']})")
        
    print(f"\n[INFO] الدروس ({len(res['lectures'])} نتائج):")
    for l in res["lectures"]:
        print(f"  - [{l['score']:.4f}] {l['series_title']} / {l['lecture_title']}")
        print(f"    {l['content'][:100]}...")
