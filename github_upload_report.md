# 📊 تقرير تحليل المشروع وخطة رفعه على GitHub
**المشروع:** منظومة معرفية — محرك HUSSAIN للبحث الهجين  
**تاريخ التقرير:** 2026-03-30

---

## 🗂️ المرحلة الأولى: خريطة ملفات المشروع الكاملة

### 📐 توزيع المساحة الإجمالية (بدون python-embed)

| الملف/المجلد | الحجم | النوع |
|---|---|---|
| `lectures_tfidf.npy` | **2,685 MB** ⚠️ | مصفوفة TF-IDF مُوّلَّدة |
| `lectures_db.sqlite` | 17.57 MB | قاعدة بيانات الدروس |
| `quran_roots_dual_v2.sqlite` | 15.23 MB | قاعدة القرآن والجذور |
| `unified_ontology.ttl` | 3.24 MB | ملف الأنطولوجيا |
| `ماركداون/` | ~4.5 MB | ملفات المصدر الأصلية |
| `archive_v1/` (JSON files) | ~3.6 MB | بيانات المفاهيم الأرشيفية |
| `lectures_json_export/` | ~25 MB | تصدير JSON للدروس |
| `Lectures Module/` | ~صغير | ملفات .txt المصدر |
| **python-embed/** | **غيـر محدد (ضخم جداً)** | توزيعة Python محلية |

---

## ✅ المرحلة الثانية: تصنيف الملفات

### 🟢 الملفات الجوهرية — **يجب رفعها**

| الملف | الوظيفة | الحجم |
|---|---|---|
| `hybrid_search.py` | محرك البحث الهجين المركزي | 12 KB |
| `lectures_indexer.py` | **بانٍ** مصفوفة TF-IDF (يُولّد .npy) | 5.8 KB |
| `lectures_query.py` | واجهة البحث في الدروس | 7 KB |
| `lectures_manager.py` | مدير استيراد الدروس | 7.2 KB |
| `lecture_parser.py` | محلل ملفات الدروس | 4.1 KB |
| `export_lectures_to_json.py` | تصدير الدروس بصيغة JSON | 7 KB |
| `requirements.txt` | متطلبات المشروع | 0.2 KB |
| `README.md` | توثيق المشروع الرئيسي | 19.9 KB |
| `concept_ayah_mapping.json` | خريطة الربط المفاهيمي-القرآني | 3.1 KB |

### 🟡 الملفات الداعمة — **يُنصح برفعها**

| الملف | الوظيفة |
|---|---|
| `docs/BACKEND_OVERVIEW.md` | توثيق البنية التقنية |
| `docs/DATABASE_REFERENCE.md` | مرجع قواعد البيانات |
| `docs/DATA_PIPELINE.md` | توثيق خط معالجة البيانات |
| `docs/SEARCH_ENGINE.md` | توثيق محرك البحث |
| `unified_ontology.ttl` | الأنطولوجيا الدلالية (3.24 MB — مقبول) |
| `archive_v1/*.json` | بيانات المفاهيم — يمكن رفعها (إجمالي ~3.6 MB) |
| `Lectures Module/` | ملفات النصوص الأصلية للدروس |
| `ماركداون/` | ملفات Markdown المصدر |

### 🔴 الملفات التي **يجب استبعادها** من Git

| الملف/المجلد | السبب | الحجم |
|---|---|---|
| `lectures_tfidf.npy` ⚠️ | **مُوَلَّد تلقائياً** — يتجاوز حد GitHub 100MB | **2.62 GB** |
| `python-embed/` | توزيعة Python كاملة — لا مكانها في Git | ضخم جداً |
| `lectures_db.sqlite` | قاعدة بيانات ثنائية — يُنصح بإدارتها بشكل خاص | 17.6 MB |
| `quran_roots_dual_v2.sqlite` | قاعدة بيانات ثنائية — بيانات خام | 15.2 MB |
| `archive_v1/python-embed.zip` | ملف ضخم لا قيمة له في Git | 10.7 MB |
| `archive_v1/get-pip.py` | أداة تثبيت Python — غير ذات صلة | 2.1 MB |
| `lectures_json_export/` | **ناتج تصدير تلقائي** — يُعاد توليده | ~25 MB |
| `archive_v1/dev_logs/` | سجلات تطوير مؤقتة | صغير |

---

## 🚀 المرحلة الثالثة: الحلول الاحترافية للملف الضخم

### 🥇 الحل الأول (الأمثل): إعادة البناء عند الحاجة — **استراتيجية "Generated Artifact"**

**المبدأ:** ملف `lectures_tfidf.npy` ليس بيانات أصلية — هو **ناتج حسابي يُعاد توليده** من `lectures_db.sqlite` عبر تشغيل `lectures_indexer.py`.

**التطبيق:**

1. أضف الملف إلى `.gitignore` بشكل كامل
2. أضف في `README.md` قسم **"إعداد المشروع"** يشرح خطوة بناء الفهرس:
   ```bash
   # بعد استنساخ المشروع، قم ببناء فهرس TF-IDF
   python lectures_indexer.py
   ```
3. ضع قاعدة البيانات `lectures_db.sqlite` على **Google Drive / Hugging Face Datasets** وأضف رابطًا في README

**✅ المزايا:** مجاني تمامًا، لا تعقيد إضافي، النهج الصحيح هندسيًا  
**⚠️ العائق الوحيد:** المستخدم الجديد يحتاج وقتًا لإعادة بناء الفهرس (~10-30 دقيقة)

---

### 🥈 الحل الثاني: Git LFS (Large File Storage)

**المبدأ:** Git LFS يُخزّن الملفات الكبيرة خارج المستودع الأصلي ويضع مؤشرًا بدلًا منها.

**حدود GitHub:**
- GitHub Free: **1 GB** مساحة LFS + **1 GB/شهر** bandwidth  
- ملفنا حجمه **2.62 GB** → **يتجاوز الحد المجاني!**

**لو أردت استخدامه:**
```bash
# تثبيت Git LFS
git lfs install

# تتبع ملفات .npy
git lfs track "*.npy"
git lfs track "*.sqlite"

# إضافة .gitattributes
git add .gitattributes
git commit -m "Configure Git LFS"
```

**💰 التكلفة:** GitHub يطلب دفع $5/شهر لـ 50 GB إضافية  
**⚠️ التوصية:** غير مجدي لملف 2.62 GB بدون خطة مدفوعة

---

### 🥉 الحل الثالث: التخزين السحابي المتخصص

**خيارات مجانية احترافية:**

| المنصة | الحد المجاني | الاستخدام المثالي |
|---|---|---|
| **Hugging Face Datasets** | غير محدود (للبيانات) | ✅ الأفضل لمشاريع ML/NLP |
| **Zenodo** | 50 GB/مستودع | ✅ للأبحاث الأكاديمية |
| **Google Drive API** | 15 GB | ✅ مع رابط مباشر في README |
| **OneDrive** | 5 GB | خيار بديل |

**مثال التكامل مع Hugging Face:**
```python
# إضافة سكريبت تنزيل في setup.py أو scripts/download_data.py
from huggingface_hub import hf_hub_download

def download_tfidf_index():
    """تنزيل فهرس TF-IDF للدروس من Hugging Face"""
    hf_hub_download(
        repo_id="your-username/hussain-knowledge-db",
        repo_type="dataset",
        filename="lectures_tfidf.npy",
        local_dir="."
    )
```

---

## 📋 المرحلة الرابعة: ملف `.gitignore` المقترح

```gitignore
# ==========================================
# Generated Data Artifacts (do not commit)
# ==========================================

# مصفوفة TF-IDF الضخمة — تُعاد من lectures_indexer.py
lectures_tfidf.npy

# قواعد البيانات — كبيرة الحجم / ثنائية
*.sqlite
*.db

# تصدير JSON التلقائي — يُعاد من export_lectures_to_json.py
lectures_json_export/

# ==========================================
# Python Environment (never commit)
# ==========================================
python-embed/
__pycache__/
*.pyc
*.pyo
*.pyd
.venv/
venv/
env/

# ==========================================
# Development Artifacts
# ==========================================
archive_v1/dev_logs/
archive_v1/dev_data/
archive_v1/get-pip.py
archive_v1/python-embed.zip

# ==========================================
# ChromaDB Vector Store (regenerable)
# ==========================================
chroma_db/

# ==========================================
# OS & Editor Files
# ==========================================
.DS_Store
Thumbs.db
*.tmp
.idea/
.vscode/
```

---

## 📦 المرحلة الخامسة: هيكل المستودع المقترح على GitHub

```
hussain-knowledge-engine/
├── 📄 README.md                    ← يشمل: رابط تنزيل البيانات + تعليمات الإعداد
├── 📄 requirements.txt
├── 📄 .gitignore
│
├── 🔬 Core Engine/
│   ├── hybrid_search.py            ← محرك البحث الهجين
│   ├── lectures_query.py           ← واجهة الاستعلام
│   ├── lectures_indexer.py         ← باني الفهرس (يُولّد .npy)
│   ├── lectures_manager.py         ← مدير الدروس
│   ├── lecture_parser.py           ← محلل الملفات
│   └── export_lectures_to_json.py  ← أداة التصدير
│
├── 📊 Data/
│   ├── concept_ayah_mapping.json   ← خريطة الربط (3 KB فقط)
│   └── unified_ontology.ttl        ← الأنطولوجيا (3.2 MB — مقبول)
│
├── 📁 archive_v1/                  ← بيانات المفاهيم JSON
│   └── *.json                      (فقط ملفات data، لا dev_logs/dev_data)
│
├── 📖 docs/
│   ├── BACKEND_OVERVIEW.md
│   ├── DATABASE_REFERENCE.md
│   ├── DATA_PIPELINE.md
│   └── SEARCH_ENGINE.md
│
└── 📁 Lectures Module/             ← النصوص الأصلية للدروس
    └── (مجلدات السلاسل/*.txt)

# ❌ مستبعد من Git:
# - lectures_tfidf.npy (2.62 GB) → تُولَّد محلياً
# - lectures_db.sqlite (17.6 MB) → رابط تنزيل في README
# - quran_roots_dual_v2.sqlite (15.2 MB) → رابط تنزيل في README
# - python-embed/ → يستخدم المطور Python المثبت عليه
```

---

## ⚡ خطة التنفيذ خطوة بخطوة

### الخطوة 1: إنشاء `.gitignore`
```bash
# في مجلد المشروع:
git init
# (انسخ محتوى .gitignore المقترح أعلاه)
```

### الخطوة 2: رفع قاعدتَي البيانات للتخزين السحابي
- ارفع `lectures_db.sqlite` و `quran_roots_dual_v2.sqlite` على **Google Drive** أو **Hugging Face**
- انسخ رابط التنزيل المباشر

### الخطوة 3: أضف سكريبت الإعداد `setup.py`
```python
"""
setup.py — سكريبت الإعداد الأولي للمشروع
يتحقق من وجود الملفات الضرورية ويرشد المستخدم لتنزيلها
"""
import os

REQUIRED_FILES = {
    "lectures_db.sqlite": "https://YOUR_DRIVE_LINK",
    "quran_roots_dual_v2.sqlite": "https://YOUR_DRIVE_LINK"
}

for fname, url in REQUIRED_FILES.items():
    if not os.path.exists(fname):
        print(f"⚠️  الملف المطلوب غير موجود: {fname}")
        print(f"   📥 حمّله من: {url}")
    else:
        print(f"✅ {fname} — موجود")

if not os.path.exists("lectures_tfidf.npy"):
    print("\n📋 الفهرس غير موجود. لبنائه:")
    print("   python lectures_indexer.py")
```

### الخطوة 4: الرفع على GitHub
```bash
git add .
git commit -m "Initial commit: HUSSAIN Knowledge Search Engine"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/hussain-knowledge.git
git push -u origin main
```

---

## 📊 ملخص قرار الاستبعاد

| الملف | القرار | الحجم المُوفَّر |
|---|---|---|
| `lectures_tfidf.npy` | ❌ استبعاد + إعادة بناء | **2,685 MB** |
| `python-embed/` | ❌ استبعاد (بيئة محلية) | ~ضخم جداً |
| `lectures_json_export/` | ❌ استبعاد (ناتج تلقائي) | ~25 MB |
| `lectures_db.sqlite` | 🌐 تخزين خارجي + رابط | 17.6 MB |
| `quran_roots_dual_v2.sqlite` | 🌐 تخزين خارجي + رابط | 15.2 MB |
| `archive_v1/get-pip.py` | ❌ استبعاد | 2.1 MB |
| **الكود + التوثيق** | ✅ رفع كامل | ~5 MB فقط! |

> **النتيجة:** المستودع على GitHub سيكون أقل من **10 MB** بدلاً من **2.8 GB**، مع الاحتفاظ بكل المعرفة الجوهرية للمشروع.
