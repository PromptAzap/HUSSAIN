# 📋 خطة تنفيذية: وحدة تخزين وفهرسة الدروس (Lectures Module)
## مشروع HUSSAIN الهجين للملاحة الإسلامية الدلالية

---

### 1️⃣ ملخص القرارات التقنية (Technical Decisions Summary)

بناءً على المتطلبات المحددة، تم اعتماد المعايير التالية للتنفيذ:

| الجانب | القرار المعتمد | المبرر |
|--------|----------------|---------|
| **تخزين الفقرات** | كل فقرة كصف مستقل (`paragraphs` table) | يسهل الربط الدقيق مع الأنطولوجيا والآيات |
| **تنظيف النص** | بدون تغيير (Preserve Original) | الحفاظ على التنسيق الأصلي للعرض |
| **تحديد الفقرات** | السطر الجديد = فقرة جديدة (`\n`) | بساطة التقسيم ووضوح الحدود |
| **مرحلة الربط** | متأخرة (بعد اكتمال قاعدة الدروس) | فصل المسؤوليات وضمان استقرار البنية أولاً |

---

### 2️⃣ الهيكلية المقترحة لقاعدة البيانات (Database Schema)

سيتم إنشاء قاعدة بيانات جديدة `lectures_db.sqlite` تحتوي على الجداول التالية:

```sql
-- جدول السلاسل المعرفية
CREATE TABLE series (
    series_id TEXT PRIMARY KEY,           -- UUID فريد
    title TEXT NOT NULL,                   -- اسم السلسلة (مثال: سورة آل عمران)
    subtitle TEXT,                         -- العنوان الفرعي (مثال: دروس من هدي القرآن الكريم)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول الدروس
CREATE TABLE lectures (
    lecture_id TEXT PRIMARY KEY,          -- UUID فريد
    series_id TEXT NOT NULL,              -- مفتاح أجنبي للسلسلة
    lecture_number INTEGER NOT NULL,      -- رقم الدرس التسلسلي
    title TEXT,                           -- عنوان الدرس
    speaker TEXT,                         -- اسم المتحدث
    date TEXT,                            -- تاريخ الإلقاء
    location TEXT,                        -- مكان الإلقاء
    opening_ayah TEXT,                    -- الآية الافتتاحية
    metadata_json TEXT,                   -- بيانات وصفية إضافية بصيغة JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (series_id) REFERENCES series(series_id)
);

-- جدول الفقرات (النواة الأساسية)
CREATE TABLE paragraphs (
    paragraph_id TEXT PRIMARY KEY,        -- UUID فريد عالمي
    lecture_id TEXT NOT NULL,             -- مفتاح أجنبي للدرس
    sequence_index INTEGER NOT NULL,      -- ترتيب الفقرة داخل الدرس (1, 2, 3...)
    content TEXT NOT NULL,                -- نص الفقرة (كما هو بدون تعديل)
    contains_ayat BOOLEAN DEFAULT 0,      -- هل تحتوي على آيات قرآنية؟
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lecture_id) REFERENCES lectures(lecture_id)
);

-- جدول ربط الفقرات بالآيات (للمرحلة المستقبلية)
CREATE TABLE paragraph_ayah_mapping (
    mapping_id TEXT PRIMARY KEY,
    paragraph_id TEXT NOT NULL,
    global_ayah_id TEXT NOT NULL,         -- معرف الآية من quran_roots_dual_v2.sqlite
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paragraph_id) REFERENCES paragraphs(paragraph_id)
);

-- فهارس للبحث السريع
CREATE INDEX idx_paragraphs_lecture ON paragraphs(lecture_id);
CREATE INDEX idx_paragraphs_sequence ON paragraphs(lecture_id, sequence_index);
CREATE INDEX idx_lectures_series ON lectures(series_id);
```

---

### 3️⃣ مراحل التنفيذ (Implementation Phases)

#### **المرحلة الأولى: بناء المحرر والنماذج (Parser & Models)**
| المهمة | الوصف | المخرج |
|--------|-------|--------|
| 1.1 | إنشاء كلاس `LectureParser` لقراءة ملفات `.txt` | وحدة تحليل نصوص |
| 1.2 | تطوير خوارزمية استخراج الـ Header (العنوان، التاريخ، المكان) | بيانات وصفية منظمة |
| 1.3 | تطوير خوارزمية تقسيم الفقرات بناءً على `\n` | قائمة فقرات مرتبة |
| 1.4 | إنشاء كلاس `LectureDatabase` لإدارة الاتصال بـ SQLite | واجهة قاعدة البيانات |

#### **المرحلة الثانية: الفهرسة والتخزين (Indexing & Storage)**
| المهمة | الوصف | المخرج |
|--------|-------|--------|
| 2.1 | معالجة ملف `سورة آل عمران ـ الدرس الأول.txt` كنموذج أولي | درس مفهرس كامل |
| 2.2 | توليد UUIDs فريدة لكل (سلسلة، درس، فقرة) | معرفات مرجعية |
| 2.3 | تخزين النصوص دون تعديل مع حفظ التسلسل | قاعدة `lectures_db.sqlite` |
| 2.4 | إنشاء ملف `lectures_manifest.json` كسجل مركي للملفات المعالجة | قائمة الجرد |

#### **المرحلة الثالثة: التكامل مع ChromaDB (Vector Indexing)**
| المهمة | الوصف | المخرج |
|--------|-------|--------|
| 3.1 | إنشاء مجموعة جديدة `lectures_collection` في ChromaDB | مجموعة متجهات |
| 3.2 | توليد Embeddings لكل فقرة باستخدام `asafaya/bert-base-arabic` | متجهات دلالية |
| 3.3 | ربط كل متجه بـ `paragraph_id` للرجوع السريع | ربط معكوس |

#### **المرحلة الرابعة: واجهة الاستعلام (Query Interface)**
| المهمة | الوصف | المخرج |
|--------|-------|--------|
| 4.1 | إضافة دوال `get_lecture_by_id()`, `get_paragraph_by_id()` | استرجاع مباشر |
| 4.2 | إضافة دالة `search_paragraphs(query_text, top_k)` | بحث دلالي |
| 4.3 | إضافة دالة `get_paragraph_context(paragraph_id, surrounding=2)` | سياق القراءة |

---

### 4️⃣ هيكلية الملفات الجديدة (New File Structure)

```
📁 منظومة معرفية (Root Directory)
├── 📄 hybrid_search.py              # المحرك الحالي (يُحدَّث ليدعم الدروس)
├── 📄 lectures_manager.py           # ⭐ ملف جديد: إدارة الدروس والفقرات
├── 📄 lecture_parser.py             # ⭐ ملف جديد: تحليل نصوص الدروس
├── 📄 lectures_db.sqlite            # ⭐ قاعدة بيانات جديدة
├── 📄 chroma_db/                    # يُضاف لها lectures_collection
│   └── ...
├── 📁 ماركداون/
│   └── ...                          # مصدر ملفات الدروس الخام
└── 📁 archive_v1/
    └── ...
```

---

### 5️⃣ معايير القبول (Acceptance Criteria)

قبل الانتقال لمرحلة الربط مع الأنطولوجيا، يجب تحقيق التالي:

- [ ] **قاعدة البيانات:** إنشاء `lectures_db.sqlite` بنجاح مع الجداول الأربعة.
- [ ] **النموذج الأولي:** فهرسة درس واحد كامل (آل عمران - الدرس الأول) بجميع فقراته.
- [ ] **المعرفات:** كل فقرة لها `paragraph_id` فريد يمكن الرجوع إليه.
- [ ] **التسلسل:** الفقرات مرتبة correctly حسب `sequence_index`.
- [ ] **الأصل:** النص مخزن كما هو بدون أي تعديل أو تنظيف.
- [ ] **ChromaDB:** مجموعة `lectures_collection` جاهزة للبحث الدلالي.
- [ ] **الاسترجاع:** يمكن جلب أي فقرة عبر `paragraph_id` خلال <100ms.

---

### 6️⃣ الجدول الزمني المقترح (Timeline)

| المرحلة | المدة التقديرية | الأولوية |
|--------|-----------------|----------|
| بناء قاعدة البيانات والنماذج | يوم واحد | 🔴 عالية |
| معالجة الدرس النموذجي | نصف يوم | 🔴 عالية |
| التكامل مع ChromaDB | يوم واحد | 🟡 متوسطة |
| واجهة الاستعلام والاختبار | يوم واحد | 🟡 متوسطة |
| **المرحلة التالية (الربط)** | لاحقاً | ⚪ مؤجلة |

---

### 7️⃣ المخاطر والتخفيف منها (Risks & Mitigation)

| الخطر | التأثير | التخفيف |
|-------|---------|---------|
| تغير هيكلية ملفات الدروس | فشل المحرر | جعل المحرر قابل للتكوين (Configurable) |
| حجم قاعدة البيانات | بطء الأداء | استخدام فهارس (Indexes) على الحقول الرئيسية |
| تكرار الفقرات | تضخم البيانات | إضافة تحقق من التكرار قبل الإدراج |
| فقدان التنسيق | عرض خاطئ | تخزين النص الخام كما هو بدون معالجة |

---

