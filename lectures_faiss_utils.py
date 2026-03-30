"""
lectures_faiss_utils.py
-----------------------
وحدة مساعدة لبناء وإدارة فهرس FAISS للبحث السريع في فقرات الدروس.

يوفر:
  - build_faiss_index()  : بناء الفهرس من مصفوفة TF-IDF على دفعات
  - save_faiss_index()   : حفظ الفهرس على القرص
  - load_faiss_index()   : تحميل الفهرس
  - search_faiss()       : البحث بمتجه الاستعلام

المتطلبات:
  pip install faiss-cpu
"""

import os
import numpy as np

# --- التحقق من توفر FAISS ---
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


def check_faiss():
    """يتحقق من تثبيت faiss ويرمي استثناء واضحاً إن لم يكن متوفراً"""
    if not FAISS_AVAILABLE:
        raise ImportError(
            "مكتبة faiss غير مثبتة.\n"
            "للتثبيت: pip install faiss-cpu"
        )


def build_faiss_index(tfidf_matrix: np.ndarray, batch_size: int = 500):
    """
    بناء فهرس FAISS IndexFlatIP من مصفوفة TF-IDF مُطبَّعة (L2).

    المعاملات:
        tfidf_matrix : مصفوفة numpy شكلها (n_docs, vocab_size)
                       يجب أن تكون مُطبَّعة L2 مسبقاً.
        batch_size   : حجم الدفعة عند إضافة الوثائق.

    يعيد:
        faiss.Index  : فهرس FAISS جاهز للبحث.
    """
    check_faiss()

    n_docs, vocab_size = tfidf_matrix.shape
    print(f"  بناء FAISS IndexFlatIP | الأبعاد: {vocab_size} | الوثائق: {n_docs}")

    index = faiss.IndexFlatIP(vocab_size)

    for i in range(0, n_docs, batch_size):
        end = min(i + batch_size, n_docs)
        batch = tfidf_matrix[i:end].astype(np.float32).copy()
        index.add(batch)

        if (i // batch_size) % 10 == 0 or end == n_docs:
            print(f"    └─ {end}/{n_docs} وثيقة مُضافة...")

    print(f"  ✅ FAISS index مكتمل ({index.ntotal} وثيقة)")
    return index


def save_faiss_index(index, path: str) -> None:
    """
    حفظ فهرس FAISS على القرص.

    المعاملات:
        index : faiss.Index
        path  : مسار الملف (يُنصح بامتداد .faiss)
    """
    check_faiss()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    faiss.write_index(index, path)
    size_mb = round(os.path.getsize(path) / (1024 ** 2), 1)
    print(f"  💾 FAISS index محفوظ: {path} ({size_mb} MB)")


def load_faiss_index(path: str):
    """
    تحميل فهرس FAISS من القرص.

    يعيد:
        faiss.Index
    """
    check_faiss()

    if not os.path.exists(path):
        raise FileNotFoundError(f"ملف FAISS غير موجود: {path}")

    index = faiss.read_index(path)
    print(f"  ✅ FAISS index محمَّل: {index.ntotal} وثيقة")
    return index


def search_faiss(index, query_vec: np.ndarray, top_k: int = 5):
    """
    البحث في فهرس FAISS بمتجه استعلام.

    المعاملات:
        index     : faiss.Index (مُحمَّل)
        query_vec : متجه numpy شكله (vocab_size,) — مُطبَّع L2
        top_k     : عدد النتائج المطلوبة

    يعيد:
        (scores, indices):
          scores  : مصفوفة float32 بدرجات التشابه (تنازلي)
          indices : مصفوفة int64 بمؤشرات الوثائق (-1 = غير موجود)
    """
    check_faiss()

    q = query_vec.astype(np.float32).reshape(1, -1)
    D, I = index.search(q, top_k)
    return D[0], I[0]


def get_index_info(index) -> dict:
    """معلومات مختصرة عن فهرس FAISS"""
    check_faiss()
    return {
        "total_vectors": index.ntotal,
        "dimension": index.d,
        "is_trained": index.is_trained,
    }
