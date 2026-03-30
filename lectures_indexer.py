"""
lectures_indexer.py  (v2 — FAISS Edition)
------------------------------------------
بناء فهرس TF-IDF للفقرات من lectures_db.sqlite
مع دعم FAISS للبحث السريع في الذاكرة.

التحسينات في هذا الإصدار:
  - بناء فهرس FAISS بدلاً من حفظ مصفوفة numpy (~500 MB بدل 2.7 GB)
  - البحث في وقت التشغيل يستخدم الذاكرة بشكل أقل بنسبة 90%
  - fallback تلقائي لـ .npy إذا لم يكن faiss متاحاً

يعمل بدون PyTorch/ONNX — يستخدم numpy + faiss-cpu فقط.
"""

import os
import sys
import json
import math
import sqlite3
import re

import numpy as np

# إضافة المسار الحالي للمسارات لضمان استيراد الوحدات المحلية
sys.path.append(os.getcwd())

DB_PATH = "lectures_db.sqlite"

# ---- تطبيع النص العربي ----

def normalize_arabic(text):
    """تطبيع النصوص العربية لتحسين الفهرسة"""
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)   # إزالة التشكيل
    text = re.sub(r'[إأآا]', 'ا', text)                 # توحيد الهمزات
    text = re.sub(r'ة', 'ه', text)                      # توحيد التاء المربوطة
    text = re.sub(r'[^\w\s]', ' ', text)                # إزالة الرموز
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tokenize(text):
    """تقسيم النص إلى كلمات مفيدة (تجاوز الكلمات القصيرة جداً)"""
    return [t for t in normalize_arabic(text).split() if len(t) > 2]


# ---- حساب TF-IDF ----

def build_tfidf_index(paragraphs):
    """
    يقبل قائمة من (paragraph_id, content) ويعيد:
      - vocab        : قاموس الكلمات → فهرس
      - tfidf_matrix : مصفوفة numpy (n_docs × vocab_size) — مُطبَّعة L2
      - para_ids     : الترتيب نفسه لـ paragraph_id
    """
    corpus = [tokenize(content) for _, content in paragraphs]
    para_ids = [pid for pid, _ in paragraphs]
    n_docs = len(corpus)

    # TF (Term Frequency)
    print(f"  [TF-IDF] بناء مصفوفة TF-IDF لـ {n_docs} فقرة...")
    vocab_set = set()
    for tokens in corpus:
        vocab_set.update(tokens)
    vocab = {word: idx for idx, word in enumerate(sorted(vocab_set))}
    vocab_size = len(vocab)
    print(f"  حجم القاموس: {vocab_size} كلمة فريدة")

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

    # Normalize rows (L2) — ضروري لـ Cosine Similarity وفهرس FAISS
    norms = np.linalg.norm(tfidf_matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    tfidf_matrix = tfidf_matrix / norms

    return vocab, tfidf_matrix, para_ids


# ---- حفظ الفهرس ----

def save_index_to_db(vocab, para_ids, matrix_shape, db_path, faiss_path=None, npy_path=None):
    """
    حفظ بيانات الفهرس في SQLite:
      - vocab      → JSON
      - para_ids   → JSON
      - matrix_shape → JSON
      - faiss_path → مسار فهرس FAISS (إن وُجد)
      - matrix_path → مسار .npy (للتوافق مع القديم، إن وُجد)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS search_index (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')

    entries = {
        "vocab": json.dumps(vocab, ensure_ascii=False),
        "para_ids": json.dumps(para_ids),
        "matrix_shape": json.dumps(list(matrix_shape)),
    }
    if faiss_path:
        entries["faiss_path"] = faiss_path
    if npy_path:
        entries["matrix_path"] = npy_path

    for key, value in entries.items():
        cursor.execute(
            "INSERT OR REPLACE INTO search_index (key, value) VALUES (?, ?)",
            (key, value)
        )

    conn.commit()
    conn.close()
    print("  تم حفظ بيانات الفهرس في SQLite")


def _try_build_faiss(tfidf_matrix, db_path):
    """
    محاولة بناء وحفظ فهرس FAISS.
    يعيد مسار الفهرس إن نجح، أو None إن فشل.
    """
    try:
        from lectures_faiss_utils import build_faiss_index, save_faiss_index
        index_dir = os.path.dirname(os.path.abspath(db_path))
        faiss_path = os.path.join(index_dir, "lectures_faiss.index")

        print(f"\n[3] بناء فهرس FAISS...")
        faiss_index = build_faiss_index(tfidf_matrix, batch_size=500)
        save_faiss_index(faiss_index, faiss_path)
        return faiss_path

    except ImportError:
        print("\n  [INFO] faiss غير متوفر — سيتم الاكتفاء بالفهرس العادي (.npy)")
        return None
    except Exception as e:
        print(f"\n  [WARN] فشل بناء FAISS: {e}")
        return None


def _save_npy_fallback(tfidf_matrix, db_path):
    """
    حفظ المصفوفة كـ .npy كحل احتياطي.
    """
    index_dir = os.path.dirname(os.path.abspath(db_path))
    npy_path = os.path.join(index_dir, "lectures_tfidf.npy")
    print(f"  [DISK] {npy_path}")
    return npy_path


# ---- نقطة التشغيل الرئيسية ----

def run_indexing(db_path=DB_PATH):
    """نقطة التشغيل الرئيسية"""
    print(f"[1] جلب الفقرات من {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # التحقق من وجود فهرس سابق مكتمل
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='search_index'")
    if cursor.fetchone():
        cursor.execute("SELECT value FROM search_index WHERE key='para_ids'")
        row = cursor.fetchone()
        if row:
            existing = json.loads(row[0])
            cursor.execute("SELECT COUNT(*) FROM paragraphs")
            total = cursor.fetchone()[0]
            if len(existing) >= total:
                # تحقق من وجود فهرس FAISS
                cursor.execute("SELECT value FROM search_index WHERE key='faiss_path'")
                faiss_row = cursor.fetchone()
                if faiss_row and os.path.exists(faiss_row[0]):
                    print(f"  الفهرس موجود مسبقاً ({len(existing)} فقرة) مع FAISS index.")
                    conn.close()
                    return
                else:
                    print(f"  الفهرس النصي موجود لكن FAISS غير موجود — سيتم بناؤه.")
                    conn.close()
                    # نقرأ المصفوفة القديمة ونبني منها FAISS
                    _upgrade_to_faiss(db_path)
                    return

    cursor.execute("SELECT paragraph_id, content FROM paragraphs ORDER BY rowid ASC")
    paragraphs = cursor.fetchall()
    conn.close()
    print(f"  تم جلب {len(paragraphs)} فقرة.")

    print("\n[2] بناء مصفوفة TF-IDF...")
    vocab, tfidf_matrix, para_ids = build_tfidf_index(paragraphs)

    # محاولة بناء FAISS
    faiss_path = _try_build_faiss(tfidf_matrix, db_path)

    # إذا فشل FAISS نحفظ .npy كاحتياط
    npy_path = None
    if faiss_path is None:
        npy_path = _save_npy_fallback(tfidf_matrix, db_path)

    print("\n[4] حفظ بيانات الفهرس في SQLite...")
    save_index_to_db(
        vocab=vocab,
        para_ids=para_ids,
        matrix_shape=tfidf_matrix.shape,
        db_path=db_path,
        faiss_path=faiss_path,
        npy_path=npy_path,
    )

    method = "FAISS" if faiss_path else "numpy .npy"
    print(f"\n[DONE] فهرسة {len(para_ids)} فقرة | الطريقة: {method} | الأبعاد: {tfidf_matrix.shape}")


def _upgrade_to_faiss(db_path):
    """
    ترقية: إذا كان الفهرس النصي موجوداً (.npy) لكن FAISS غير موجود،
    يُحمَّل الـ .npy ويُبنى منه فهرس FAISS.
    """
    print("  جاري الترقية إلى FAISS من الفهرس الموجود...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM search_index WHERE key='matrix_path'")
    row = cursor.fetchone()
    conn.close()

    if not row or not os.path.exists(row[0]):
        print("  ⚠️  لم يُعثر على ملف .npy. يُرجى إعادة الفهرسة الكاملة.")
        return

    print(f"  تحميل {row[0]}...")
    tfidf_matrix = np.load(row[0])

    faiss_path = _try_build_faiss(tfidf_matrix, db_path)
    if faiss_path:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO search_index (key, value) VALUES (?, ?)",
            ("faiss_path", faiss_path)
        )
        conn.commit()
        conn.close()
        print("  ✅ تم ترقية الفهرس إلى FAISS بنجاح.")


if __name__ == "__main__":
    run_indexing()
