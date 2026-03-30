"""
lectures_query.py
-----------------
واجهة استعلام الدروس:
  - search_paragraphs(query, top_k) → أفضل الفقرات تطابقاً
  - get_paragraph_by_id(paragraph_id) → فقرة مباشرة بمُعرّفها
  - get_paragraph_context(paragraph_id, surrounding=2) → الفقرة + الفقرات المحيطة بها
"""
import os
import sys
import json
import sqlite3
import re

import numpy as np

DB_PATH = "lectures_db.sqlite"

# ========== نظافة النص (مطابق للـ Indexer) ==========
def normalize_arabic(text):
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def tokenize(text):
    normalized = normalize_arabic(text)
    tokens = normalized.split()
    return [t for t in tokens if len(t) > 2]


# ========== تحميل الفهرس من القاعدة ==========
_cache = {}  # cache لمنع إعادة التحميل في كل استعلام

def load_index(db_path=DB_PATH):
    global _cache
    if _cache:
        return _cache

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT value FROM search_index WHERE key='vocab'")
    vocab = json.loads(cursor.fetchone()[0])

    cursor.execute("SELECT value FROM search_index WHERE key='para_ids'")
    para_ids = json.loads(cursor.fetchone()[0])

    cursor.execute("SELECT value FROM search_index WHERE key='matrix_path'")
    matrix_path = cursor.fetchone()[0]

    conn.close()

    tfidf_matrix = np.load(matrix_path)

    _cache = {"vocab": vocab, "para_ids": para_ids, "tfidf_matrix": tfidf_matrix}
    return _cache



# ========== تحويل الاستعلام إلى متجه ==========
def query_to_vector(query_text, vocab, matrix_shape):
    tokens = tokenize(query_text)
    vocab_size = matrix_shape[1]
    q_vec = np.zeros(vocab_size, dtype=np.float32)
    for token in tokens:
        if token in vocab:
            q_vec[vocab[token]] += 1.0
    norm = np.linalg.norm(q_vec)
    if norm > 0:
        q_vec /= norm
    return q_vec


# ========== واجهات الاستعلام العامة ==========

def search_paragraphs(query_text, top_k=5, db_path=DB_PATH):
    """
    البحث الدلالي في فقرات الدروس.
    يُعيد قائمة من القواميس (paragraph_id, score, content, lecture_title, series_title)
    """
    index = load_index(db_path)
    vocab = index["vocab"]
    para_ids = index["para_ids"]
    tfidf_matrix = index["tfidf_matrix"]

    q_vec = query_to_vector(query_text, vocab, tfidf_matrix.shape)

    # Cosine Similarity = dot product (المصفوفة مُطبَّعة مسبقاً)
    scores = tfidf_matrix @ q_vec

    top_indices = np.argsort(scores)[::-1][:top_k]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    results = []
    for idx in top_indices:
        pid = para_ids[idx]
        score = float(scores[idx])
        if score < 0.01:
            continue
        cursor.execute('''
        SELECT p.content, l.title, s.title, p.sequence_index, p.contains_ayat
        FROM paragraphs p
        JOIN lectures l ON p.lecture_id = l.lecture_id
        JOIN series s ON l.series_id = s.series_id
        WHERE p.paragraph_id = ?
        ''', (pid,))
        row = cursor.fetchone()
        if row:
            results.append({
                "paragraph_id": pid,
                "score": round(score, 4),
                "content": row[0],
                "lecture_title": row[1],
                "series_title": row[2],
                "sequence_index": row[3],
                "contains_ayat": bool(row[4])
            })
    conn.close()
    return results


def get_paragraph_by_id(paragraph_id, db_path=DB_PATH):
    """جلب فقرة مباشرة بـ paragraph_id"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT p.content, p.sequence_index, p.contains_ayat,
           l.title as lecture_title, l.speaker, l.date, l.location,
           s.title as series_title
    FROM paragraphs p
    JOIN lectures l ON p.lecture_id = l.lecture_id
    JOIN series s ON l.series_id = s.series_id
    WHERE p.paragraph_id = ?
    ''', (paragraph_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "paragraph_id": paragraph_id,
        "content": row[0],
        "sequence_index": row[1],
        "contains_ayat": bool(row[2]),
        "lecture": {
            "title": row[3],
            "speaker": row[4],
            "date": row[5],
            "location": row[6]
        },
        "series": row[7]
    }


def get_paragraph_context(paragraph_id, surrounding=2, db_path=DB_PATH):
    """
    جلب الفقرة المحددة مع الفقرات المحيطة بها (السابقة واللاحقة).
    surrounding=2 يعني فقرتين قبل وفقرتين بعد.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # أولاً: جلب lecture_id و sequence_index للفقرة المستهدفة
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

    context_rows = cursor.fetchall()
    conn.close()

    context = []
    for r in context_rows:
        context.append({
            "paragraph_id": r[0],
            "sequence_index": r[1],
            "content": r[2],
            "contains_ayat": bool(r[3]),
            "is_target": r[0] == paragraph_id
        })
    return context


# ========== اختبار مباشر ==========
if __name__ == "__main__":
    import json as _json
    results = search_paragraphs("طاعة أهل الكتاب وخطر الكفر", top_k=3)
    output = {
        "query": "طاعة أهل الكتاب وخطر الكفر",
        "results": results
    }
    with open("query_test_result.json", "w", encoding="utf-8") as f:
        _json.dump(output, f, ensure_ascii=False, indent=4)
    print(f"تم: {len(results)} نتيجة -> query_test_result.json")

    # اختبار جلب السياق
    if results:
        pid = results[0]["paragraph_id"]
        context = get_paragraph_context(pid, surrounding=2)
        with open("context_test_result.json", "w", encoding="utf-8") as f:
            _json.dump(context, f, ensure_ascii=False, indent=4)
        print(f"سياق الفقرة الاولى -> context_test_result.json")
