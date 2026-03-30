"""
lectures_indexer.py
-------------------
بناء فهرس TF-IDF للفقرات من lectures_db.sqlite  
يعمل بدون PyTorch/ONNX باستخدام numpy فقط.
يُخزّن الفهرس داخل جدول search_index في نفس قاعدة البيانات.
"""
import os
import sys
import json
import math
import sqlite3
import re

import numpy as np

DB_PATH = "lectures_db.sqlite"

# ---- نظافة النص العربي ----
def normalize_arabic(text):
    """تطبيع النصوص العربية لتحسين الفهرسة"""
    # إزالة التشكيل
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
    # توحيد الهمزات
    text = re.sub(r'[إأآا]', 'ا', text)
    # توحيد التاء المربوطة
    text = re.sub(r'ة', 'ه', text)
    # إزالة الرموز غير الحروف
    text = re.sub(r'[^\w\s]', ' ', text)
    # تنظيف المسافات
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def tokenize(text):
    """تقسيم النص إلى كلمات مفيدة (تجاوز الكلمات القصيرة جداً)"""
    normalized = normalize_arabic(text)
    tokens = normalized.split()
    return [t for t in tokens if len(t) > 2]

# ---- حساب TF-IDF ----
def build_tfidf_index(paragraphs):
    """
    يقبل قائمة من (paragraph_id, content) ويعيد:
    - vocab : قاموس الكلمات → فهرس
    - tfidf_matrix : مصفوفة numpy (n_docs x vocab_size)
    - para_ids : الترتيب نفسه لـ paragraph_id
    """
    corpus = [tokenize(content) for _, content in paragraphs]
    para_ids = [pid for pid, _ in paragraphs]
    n_docs = len(corpus)

    print(f"  بناء القاموس من {n_docs} فقرة...")
    # بناء المفردات
    vocab_set = set()
    for tokens in corpus:
        vocab_set.update(tokens)
    vocab = {word: idx for idx, word in enumerate(sorted(vocab_set))}
    vocab_size = len(vocab)
    print(f"  حجم القاموس: {vocab_size} كلمة فريدة")

    # TF (Term Frequency)
    tf_matrix = np.zeros((n_docs, vocab_size), dtype=np.float32)
    for i, tokens in enumerate(corpus):
        if not tokens:
            continue
        for token in tokens:
            if token in vocab:
                tf_matrix[i, vocab[token]] += 1
        tf_matrix[i] /= len(tokens) + 1e-9

    # IDF (Inverse Document Frequency)
    df = np.sum(tf_matrix > 0, axis=0).astype(np.float32)
    idf = np.log((n_docs + 1) / (df + 1)) + 1.0

    tfidf_matrix = tf_matrix * idf

    # Normalize rows (L2)
    norms = np.linalg.norm(tfidf_matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    tfidf_matrix = tfidf_matrix / norms

    return vocab, tfidf_matrix, para_ids

def save_index_to_db(vocab, tfidf_matrix, para_ids, db_path):
    """
    حفظ الفهرس:
    - القاموس + para_ids → داخل SQLite (search_index)
    - مصفوفة TF-IDF    → ملف .npy بجوار قاعدة البيانات (أسرع وأكثر أماناً)
    """
    index_dir = os.path.dirname(os.path.abspath(db_path))
    matrix_path = os.path.join(index_dir, "lectures_tfidf.npy")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS search_index (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')

    print("  حفظ القاموس...")
    cursor.execute("INSERT OR REPLACE INTO search_index (key, value) VALUES (?, ?)",
                   ("vocab", json.dumps(vocab, ensure_ascii=False)))

    print("  حفظ ترتيب paragraph_ids...")
    cursor.execute("INSERT OR REPLACE INTO search_index (key, value) VALUES (?, ?)",
                   ("para_ids", json.dumps(para_ids)))

    shape_info = json.dumps(list(tfidf_matrix.shape))
    cursor.execute("INSERT OR REPLACE INTO search_index (key, value) VALUES (?, ?)",
                   ("matrix_shape", shape_info))

    # مسار ملف المصفوفة
    cursor.execute("INSERT OR REPLACE INTO search_index (key, value) VALUES (?, ?)",
                   ("matrix_path", matrix_path))

    conn.commit()
    conn.close()

    print(f"  حفظ مصفوفة TF-IDF في {matrix_path} ...")
    np.save(matrix_path, tfidf_matrix)

    print("  تم حفظ الفهرس بنجاح.")


def run_indexing(db_path=DB_PATH):
    """نقطة التشغيل الرئيسية"""
    print(f"[1] جلب الفقرات من {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # التحقق من عدم وجود فهرس سابق لتجنب إعادة العمل
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='search_index'")
    if cursor.fetchone():
        cursor.execute("SELECT value FROM search_index WHERE key='para_ids'")
        row = cursor.fetchone()
        if row:
            existing = json.loads(row[0])
            cursor.execute("SELECT COUNT(*) FROM paragraphs")
            total = cursor.fetchone()[0]
            if len(existing) >= total:
                print(f"  الفهرس موجود مسبقاً ({len(existing)} فقرة). لا حاجة لإعادة البناء.")
                conn.close()
                return

    cursor.execute("SELECT paragraph_id, content FROM paragraphs ORDER BY rowid ASC")
    paragraphs = cursor.fetchall()
    conn.close()
    print(f"  تم جلب {len(paragraphs)} فقرة.")

    print("[2] بناء مصفوفة TF-IDF...")
    vocab, tfidf_matrix, para_ids = build_tfidf_index(paragraphs)

    print("[3] حفظ الفهرس في قاعدة البيانات...")
    save_index_to_db(vocab, tfidf_matrix, para_ids, db_path)

    print(f"\n[تم] فهرسة {len(para_ids)} فقرة بمصفوفة حجمها {tfidf_matrix.shape}")

if __name__ == "__main__":
    run_indexing()
