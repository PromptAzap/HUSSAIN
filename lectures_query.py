"""
lectures_query.py  (v2 — FAISS Edition)
-----------------------------------------
واجهة استعلام الدروس:
  - search_paragraphs(query, top_k)           → أفضل الفقرات تطابقاً
  - get_paragraph_by_id(paragraph_id)         → فقرة مباشرة بمُعرّفها
  - get_paragraph_context(paragraph_id, ±N)   → الفقرة + الفقرات المحيطة

التحسينات في هذا الإصدار:
  - استخدام FAISS للبحث بدلاً من numpy matmul
  - ذاكرة ثابتة ~150MB بدلاً من 2.7GB
  - fallback تلقائي لـ .npy إذا لم يكن FAISS متاحاً
"""

# إضافة المسار الحالي للمسارات لضمان استيراد الوحدات المحلية
import os
import sys
sys.path.append(os.getcwd())

DB_PATH = "lectures_db.sqlite"

# ========== تطبيع النص (مطابق للـ Indexer) ==========

def normalize_arabic(text):
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tokenize(text):
    return [t for t in normalize_arabic(text).split() if len(t) > 2]


# ========== تحميل الفهرس ==========

_cache = {}   # cache في الذاكرة لمنع إعادة التحميل


def _load_faiss_backend(faiss_path):
    """تحميل فهرس FAISS"""
    try:
        from lectures_faiss_utils import load_faiss_index
        return load_faiss_index(faiss_path), "faiss"
    except Exception as e:
        print(f"  ⚠️  فشل تحميل FAISS من {faiss_path}: {e}")
        return None, None


def _load_numpy_backend(matrix_path):
    """تحميل مصفوفة numpy (fallback)"""
    if not matrix_path or not os.path.exists(matrix_path):
        return None, None
    print(f"  تحميل مصفوفة numpy من {matrix_path} ...")
    tfidf_matrix = np.load(matrix_path)
    print(f"  ✅ مصفوفة محمَّلة: {tfidf_matrix.shape}")
    return tfidf_matrix, "numpy"


def load_index(db_path=DB_PATH):
    """
    تحميل الفهرس من SQLite.
    يستخدم FAISS إن كان متوفراً، وينتقل لـ numpy كحل احتياطي.
    """
    global _cache
    if _cache:
        return _cache

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    def get(key):
        row = cursor.execute(
            "SELECT value FROM search_index WHERE key=?", (key,)
        ).fetchone()
        return row[0] if row else None

    vocab       = json.loads(get("vocab"))
    para_ids    = json.loads(get("para_ids"))
    faiss_path  = get("faiss_path")
    matrix_path = get("matrix_path")
    conn.close()

    vocab_size = len(vocab)
    backend    = None
    faiss_index = None
    tfidf_matrix = None

    # محاولة FAISS أولاً
    if faiss_path and os.path.exists(faiss_path):
        faiss_index, backend = _load_faiss_backend(faiss_path)

    # fallback لـ numpy
    if backend is None:
        tfidf_matrix, backend = _load_numpy_backend(matrix_path)

    if backend is None:
        raise RuntimeError(
            "لم يُعثر على أي فهرس. يُرجى تشغيل lectures_indexer.py أولاً."
        )

    print(f"  [INFO] محرك البحث: {backend.upper()} | الفقرات: {len(para_ids)}")

    _cache = {
        "vocab":        vocab,
        "para_ids":     para_ids,
        "vocab_size":   vocab_size,
        "faiss_index":  faiss_index,
        "tfidf_matrix": tfidf_matrix,
        "backend":      backend,
    }
    return _cache


def clear_cache():
    """مسح الـ cache لإعادة تحميل الفهرس"""
    global _cache
    _cache = {}


# ========== تحويل الاستعلام إلى متجه ==========

def query_to_vector(query_text: str, vocab: dict, vocab_size: int) -> np.ndarray:
    """
    تحويل نص الاستعلام إلى متجه TF مُطبَّع L2.
    """
    tokens = tokenize(query_text)
    q_vec = np.zeros(vocab_size, dtype=np.float32)
    for token in tokens:
        if token in vocab:
            q_vec[vocab[token]] += 1.0
    norm = np.linalg.norm(q_vec)
    if norm > 0:
        q_vec /= norm
    return q_vec


# ========== البحث في الفقرات ==========

def search_paragraphs(query_text: str, top_k: int = 5, db_path: str = DB_PATH) -> list:
    """
    البحث في فقرات الدروس.
    يعيد قائمة من القواميس مرتبة تنازلياً بالتطابق.
    """
    index    = load_index(db_path)
    vocab    = index["vocab"]
    para_ids = index["para_ids"]
    vocab_size = index["vocab_size"]

    q_vec = query_to_vector(query_text, vocab, vocab_size)

    # --- FAISS Backend ---
    if index["backend"] == "faiss":
        from lectures_faiss_utils import search_faiss
        scores_arr, indices_arr = search_faiss(index["faiss_index"], q_vec, top_k)
        top_pairs = [
            (float(scores_arr[i]), int(indices_arr[i]))
            for i in range(len(indices_arr))
            if indices_arr[i] >= 0 and scores_arr[i] >= 0.01
        ]

    # --- NumPy Fallback ---
    else:
        scores_all = index["tfidf_matrix"] @ q_vec
        top_indices = np.argsort(scores_all)[::-1][:top_k]
        top_pairs = [
            (float(scores_all[idx]), idx)
            for idx in top_indices
            if scores_all[idx] >= 0.01
        ]

    if not top_pairs:
        return []

    # جلب بيانات الفقرات من SQLite
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()
    results = []

    for score, idx in top_pairs:
        pid = para_ids[idx]
        cursor.execute('''
            SELECT p.content, l.title, s.title, p.sequence_index, p.contains_ayat
            FROM paragraphs p
            JOIN lectures  l ON p.lecture_id = l.lecture_id
            JOIN series    s ON l.series_id  = s.series_id
            WHERE p.paragraph_id = ?
        ''', (pid,))
        row = cursor.fetchone()
        if row:
            results.append({
                "paragraph_id":  pid,
                "score":         round(score, 4),
                "content":       row[0],
                "lecture_title": row[1],
                "series_title":  row[2],
                "sequence_index":row[3],
                "contains_ayat": bool(row[4]),
            })

    conn.close()
    return results


# ========== جلب فقرة بمعرّفها ==========

def get_paragraph_by_id(paragraph_id: str, db_path: str = DB_PATH) -> dict | None:
    """جلب فقرة كاملة مع بيانات درسها"""
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.content, p.sequence_index, p.contains_ayat,
               l.title, l.speaker, l.date, l.location,
               s.title
        FROM paragraphs p
        JOIN lectures l ON p.lecture_id = l.lecture_id
        JOIN series   s ON l.series_id  = s.series_id
        WHERE p.paragraph_id = ?
    ''', (paragraph_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "paragraph_id":  paragraph_id,
        "content":       row[0],
        "sequence_index":row[1],
        "contains_ayat": bool(row[2]),
        "lecture": {
            "title":    row[3],
            "speaker":  row[4],
            "date":     row[5],
            "location": row[6],
        },
        "series": row[7],
    }


# ========== السياق المحيط بفقرة ==========

def get_paragraph_context(
    paragraph_id: str,
    surrounding: int = 2,
    db_path: str = DB_PATH,
) -> list | None:
    """
    جلب الفقرة مع الفقرات المجاورة (surrounding قبل + surrounding بعد).
    """
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT lecture_id, sequence_index FROM paragraphs WHERE paragraph_id = ?",
        (paragraph_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    lecture_id, seq_idx = row
    min_seq = max(1, seq_idx - surrounding)
    max_seq = seq_idx + surrounding

    cursor.execute('''
        SELECT paragraph_id, sequence_index, content, contains_ayat
        FROM paragraphs
        WHERE lecture_id = ? AND sequence_index BETWEEN ? AND ?
        ORDER BY sequence_index ASC
    ''', (lecture_id, min_seq, max_seq))

    context = [
        {
            "paragraph_id":  r[0],
            "sequence_index":r[1],
            "content":       r[2],
            "contains_ayat": bool(r[3]),
            "is_target":     r[0] == paragraph_id,
        }
        for r in cursor.fetchall()
    ]
    conn.close()
    return context


# ========== اختبار مباشر ==========

if __name__ == "__main__":
    import json as _json
    query = "طاعة أهل الكتاب وخطر الكفر"
    print(f"\n[INFO] الاستعلام: {query}\n")
    results = search_paragraphs(query, top_k=3)
    print(f"النتائج ({len(results)}):")
    for r in results:
        print(f"  [{r['score']:.4f}] {r['series_title']} / {r['lecture_title']}")
        print(f"  {r['content'][:120]}...")
        print()
