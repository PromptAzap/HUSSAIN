# 📋 وثيقة المتطلبات الفنية الشاملة
## منظومة HUSSAIN — التطبيقات المقترحة

**الإصدار:** 1.0 | **التاريخ:** 2026-03-30  
**المؤلف:** فريق منظومة HUSSAIN

---

## فهرس الوثائق

| التطبيق | الاختصار | الأولوية | الصفحة |
|---|---|---|---|
| [HUSSAIN Scholar](#app-1) | HS | 🔴 P0 | §1 |
| [رفيق الدرس](#app-3) | RD | 🔴 P0 | §2 |
| [المرشد الفكري](#app-4) | MF | 🟡 P1 | §3 |
| [المخيلة المعرفية](#app-2) | MM | 🟡 P1 | §4 |
| [المصحف الذكي](#app-6) | MZ | 🟢 P2 | §5 |
| [لوحة الاستكشاف](#app-5) | LA | 🟢 P2 | §6 |

---

---

# <a id="app-1"></a>§1 — HUSSAIN Scholar

## 1.1 نظرة عامة

| الخاصية | القيمة |
|---|---|
| **النوع** | Web App (PWA) |
| **الجمهور المستهدف** | باحثون، طلاب دراسات إسلامية، مثقفون |
| **الوصف** | محرك بحث دلالي هجين يُجيب على استعلامات اللغة الطبيعية بنتائج من الأنطولوجيا والدروس والقرآن |
| **الأولوية** | 🔴 P0 — الأساس الذي تنبني عليه باقي التطبيقات |

---

## 1.2 حالات الاستخدام (Use Cases)

```mermaid
graph LR
    U([المستخدم])
    A([الباحث المتخصص])
    
    U --> UC1[بحث بكلمة مفتاحية]
    U --> UC2[بحث بجملة كاملة]
    U --> UC3[استكشاف مفهوم]
    U --> UC4[عرض سياق الفقرة]
    U --> UC5[مشاركة نتيجة]
    U --> UC6[حفظ نتيجة]
    
    A --> UC7[تصفية حسب السلسلة]
    A --> UC8[تصفية حسب التاريخ]
    A --> UC9[تصدير النتائج JSON]
    A --> UC10[ضبط معاملات البحث]
```

### حالات الاستخدام التفصيلية

| UC# | العنوان | المحفز | التدفق الرئيسي | نتيجة البحث |
|---|---|---|---|---|
| UC-01 | بحث دلالي | المستخدم يكتب نصاً | إدخال → معالجة → نتائج ثلاثية | نتائج من 3 مصادر |
| UC-02 | استكشاف مفهوم | نقر على مفهوم في النتيجة | فتح صفحة المفهوم | شبكة روابط المفهوم |
| UC-03 | قراءة سياق | نقر "السياق الكامل" | عرض الفقرات المحيطة | ٥ فقرات حول النتيجة |
| UC-04 | مشاركة | نقر "مشاركة" | توليد رابط أو صورة | رابط مباشر / صورة PNG |
| UC-05 | تصفية | نقر Filters | اختيار السلسلة/النوع | نتائج مُصفَّاة |

---

## 1.3 المتطلبات الوظيفية (Functional Requirements)

### FR-01: واجهة البحث
- [ ] **FR-01-1:** قبول نص عربي بحد أقصى 500 حرف
- [ ] **FR-01-2:** اقتراحات فورية بعد 2 ثانية من التوقف عن الكتابة
- [ ] **FR-01-3:** حفظ آخر 20 استعلام في LocalStorage
- [ ] **FR-01-4:** دعم البحث بـ Enter أو زر البحث

### FR-02: نظام النتائج الثلاثية
- [ ] **FR-02-1:** عرض نتيجة دلالية من الأنطولوجيا (ChromaDB)
- [ ] **FR-02-2:** عرض آية/آيات مرتبطة (Hard-link أو Semantic Fallback)
- [ ] **FR-02-3:** عرض أفضل 5 فقرات من الدروس (TF-IDF)
- [ ] **FR-02-4:** عرض نسبة التطابق لكل نتيجة (%)
- [ ] **FR-02-5:** ترتيب النتائج حسب درجة الملاءمة

### FR-03: التصفية والفرز
- [ ] **FR-03-1:** تصفية حسب السلسلة (7 سلاسل)
- [ ] **FR-03-2:** تصفية حسب نوع النتيجة (أنطولوجيا / درس / قرآن)
- [ ] **FR-03-3:** فرز حسب: الأعلى تطابقاً / الأحدث
- [ ] **FR-03-4:** خيار تضييق/توسيع عدد النتائج (3 / 5 / 10)

### FR-04: صفحة النتيجة التفصيلية
- [ ] **FR-04-1:** عرض النص الكامل للفقرة مع تمييز مصطلح البحث
- [ ] **FR-04-2:** عرض الفقرات المحيطة (±2 فقرة)
- [ ] **FR-04-3:** بيانات الدرس: الاسم، السلسلة، رقم الدرس
- [ ] **FR-04-4:** روابط للمفاهيم المرتبطة من الأنطولوجيا

---

## 1.4 المتطلبات غير الوظيفية (Non-Functional Requirements)

| المتطلب | المعيار |
|---|---|
| **الأداء** | نتائج خلال ≤ 2 ثانية لـ 95% من الاستعلامات |
| **التوافر** | 99.5% uptime |
| **التزامن** | دعم 100 مستخدم في نفس الوقت |
| **الاستجابة** | يعمل على: desktop, tablet, mobile |
| **RTL** | 100% دعم اليمين لليسار |
| **الأمان** | HTTPS إجباري، rate limiting (60 req/min/IP) |
| **SEO** | SSR من خلال Next.js |

---

## 1.5 المعمارية التقنية

```mermaid
graph TB
    subgraph "Client Layer"
        UI[Next.js 14 App]
        SW[Service Worker PWA]
        LS[LocalStorage Cache]
    end

    subgraph "API Gateway"
        GW[FastAPI Gateway]
        RL[Rate Limiter]
        Cache[Redis Cache]
    end

    subgraph "Search Engine Core"
        HS_Engine[HUSSAIN Hybrid Engine]
        
        subgraph "Semantic Layer"
            BERT[BERT Encoder\nasafaya/bert-base-arabic]
            ChromaC[ChromaDB\nconcepts_collection]
            ChromaQ[ChromaDB\nquran_collection]
        end
        
        subgraph "Lexical Layer"
            TFIDF[TF-IDF Index\nlectures_tfidf.npy]
        end
    end

    subgraph "Data Layer"
        LDB[(lectures_db.sqlite)]
        QDB[(quran_roots_dual_v2.sqlite)]
        MAP[concept_ayah_mapping.json]
    end

    UI --> GW
    GW --> RL --> Cache
    Cache -->|miss| HS_Engine
    HS_Engine --> BERT --> ChromaC
    HS_Engine --> BERT --> ChromaQ
    HS_Engine --> TFIDF
    ChromaC --> MAP --> QDB
    ChromaQ --> QDB
    TFIDF --> LDB
```

---

## 1.6 تدفق البيانات (Data Flow)

```mermaid
sequenceDiagram
    actor User
    participant UI as Next.js UI
    participant API as FastAPI
    participant Cache as Redis
    participant Engine as HUSSAIN Engine
    participant DBs as Databases

    User->>UI: يكتب استعلاماً
    UI->>UI: Debounce 500ms
    UI->>API: POST /api/search {query, filters}
    
    API->>Cache: GET cache_key
    alt مخزن مؤقتاً
        Cache-->>API: cached_result
        API-->>UI: 200 {results}
    else غير مخزن
        API->>Engine: search(query, filters)
        
        par بحث متوازٍ
            Engine->>DBs: Semantic search (ChromaDB)
        and
            Engine->>DBs: Lexical search (TF-IDF + SQLite)
        end
        
        Engine->>Engine: دمج + ترتيب النتائج
        Engine-->>API: merged_results
        API->>Cache: SET cache_key (TTL: 5min)
        API-->>UI: 200 {results}
    end
    
    UI->>UI: عرض النتائج الثلاثية
    User->>UI: نقر على نتيجة
    UI->>API: GET /api/paragraph/{id}/context
    API->>DBs: جلب السياق ±2 فقرة
    DBs-->>UI: context_paragraphs
    UI->>User: عرض النافذة المنبثقة
```

---

## 1.7 مواصفات API

### `POST /api/v1/search`

**Request:**
```json
{
  "query": "الخسارة الحقيقية للإنسان",
  "top_k": 5,
  "filters": {
    "sources": ["ontology", "lectures", "quran"],
    "series": ["سلسلة دروس رمضان"],
    "min_score": 0.3
  }
}
```

**Response:**
```json
{
  "query": "الخسارة الحقيقية للإنسان",
  "processing_time_ms": 847,
  "results": {
    "ontology": {
      "concept_id": "uuid",
      "concept_name": "الخسارة الحقيقية",
      "definition": "...",
      "score": 0.89,
      "linked_ayahs": [103]
    },
    "quran": [
      {
        "global_ayah": 103,
        "surah_no": 103,
        "ayah_no": 1,
        "text": "﴿وَالْعَصْرِ﴾",
        "roots": [{"token": "العصر", "root": "ع-ص-ر"}],
        "match_type": "hard_link",
        "score": 1.0
      }
    ],
    "lectures": [
      {
        "paragraph_id": "uuid",
        "content": "...",
        "lecture_title": "الدرس الثالث",
        "series_title": "سلسلة دروس رمضان",
        "score": 0.74,
        "contains_ayat": true
      }
    ]
  }
}
```

### `GET /api/v1/paragraph/{id}/context`

**Response:**
```json
{
  "target_paragraph_id": "uuid",
  "context": [
    {"sequence_index": 14, "content": "...", "is_target": false},
    {"sequence_index": 15, "content": "...", "is_target": true},
    {"sequence_index": 16, "content": "...", "is_target": false}
  ],
  "lecture": {"title": "...", "series": "...", "speaker": "..."}
}
```

---

---

# <a id="app-3"></a>§2 — رفيق الدرس (Lecture Companion)

## 2.1 نظرة عامة

| الخاصية | القيمة |
|---|---|
| **النوع** | PWA + Mobile-First |
| **الجمهور المستهدف** | المتعلم اليومي، من يريد قراءة منتظمة |
| **الوصف** | تطبيق قراءة مركّزة للدروس مع ربط الآيات تلقائياً وإمكانية التعليق والحفظ |
| **الأولوية** | 🔴 P0 |

---

## 2.2 حالات الاستخدام

```mermaid
graph LR
    U([المستخدم])
    
    U --> UC1[تصفح السلاسل والدروس]
    U --> UC2[قراءة درس كامل]
    U --> UC3[عرض الآية المرتبطة]
    U --> UC4[تعليم فقرة]
    U --> UC5[كتابة ملاحظة شخصية]
    U --> UC6[متابعة التقدم]
    U --> UC7[وضع القراءة المركّزة]
    U --> UC8[تغيير حجم الخط والثيم]
    U --> UC9[مشاركة فقرة]
    U --> UC10[البحث داخل درس]
```

---

## 2.3 المتطلبات الوظيفية

### FR-01: مكتبة الدروس
- [ ] عرض 7 سلاسل كـ بطاقات مميزة
- [ ] عرض الدروس ضمن كل سلسلة مع شريط التقدم
- [ ] الدرس مكتمل / قيد القراءة / لم يُبدأ

### FR-02: قارئ الدروس
- [ ] عرض الفقرات تسلسلياً مع ترقيم
- [ ] **الإضاءة الذهبية:** كل فقرة تحتوي `contains_ayat=true` تُحاط بهالة ذهبية
- [ ] نقر الهالة → نافذة منبثقة بالآية الكاملة + جذورها
- [ ] تمييز آخر موضع قراءة تلقائياً (Bookmark التلقائي)

### FR-03: الميزة الاجتماعية / الشخصية
- [ ] تمييز فقرة باللون (أصفر / أخضر / أحمر)
- [ ] كتابة ملاحظة على فقرة محددة
- [ ] حفظ المفضلة عبر IndexedDB (بدون حساب)

### FR-04: تخصيص القراءة
- [ ] 3 أحجام خط: صغير / متوسط / كبير
- [ ] 3 ثيمات: ليلي / نهاري / بني كلاسيكي
- [ ] عرض/إخفاء أرقام الفقرات

---

## 2.4 المعمارية التقنية

```mermaid
graph TB
    subgraph "Frontend (PWA)"
        App[Next.js App]
        SW[Service Worker]
        IDB[IndexedDB\nملاحظات + تقدم + مفضلة]
        Cache_F[Cache API\nدروس مُحمَّلة]
    end

    subgraph "Backend API"
        API[FastAPI]
        LDB[(lectures_db.sqlite)]
        QDB[(quran_roots_dual_v2.sqlite)]
    end

    App -->|"GET /series"| API
    App -->|"GET /lectures/{series_id}"| API
    App -->|"GET /lecture/{id}/paragraphs"| API
    App -->|"GET /paragraph/{id}/ayah"| API
    
    API --> LDB
    API --> QDB
    
    App <-->|sync| IDB
    SW -->|cache| Cache_F
```

---

## 2.5 تدفق القراءة

```mermaid
stateDiagram-v2
    [*] --> الرئيسية

    الرئيسية --> اختيار_سلسلة: tap سلسلة
    اختيار_سلسلة --> اختيار_درس: tap درس
    
    اختيار_درس --> القارئ: tap اقرأ
    
    state القارئ {
        [*] --> تحميل_الفقرات
        تحميل_الفقرات --> عرض_الفقرات
        
        state عرض_الفقرات {
            فقرة_عادية --> فقرة_عادية: scroll
            فقرة_عادية --> فقرة_قرآنية: push contains_ayat
            فقرة_قرآنية --> نافذة_الآية: tap هالة ذهبية
            نافذة_الآية --> فقرة_قرآنية: dismiss
        }
        
        عرض_الفقرات --> تعليم_فقرة: long press
        تعليم_فقرة --> عرض_الفقرات: اختيار لون
        عرض_الفقرات --> كتابة_ملاحظة: tap أيقونة قلم
    }
    
    القارئ --> المفضلة: tap ♥
    القارئ --> مشاركة: tap share
```

---

## 2.6 نموذج البيانات المحلية (IndexedDB)

```typescript
// schema: IndexedDB stores
interface ReadingProgress {
  lectureId: string;
  lastParagraphIndex: number;
  completedAt?: Date;
  percentage: number;
}

interface Annotation {
  id: string;
  paragraphId: string;
  lectureId: string;
  color: 'yellow' | 'green' | 'red';
  note?: string;
  createdAt: Date;
}

interface Bookmark {
  id: string;
  paragraphId: string;
  lectureId: string;
  seriesTitle: string;
  excerpt: string;
  createdAt: Date;
}
```

---

---

# <a id="app-4"></a>§3 — المرشد الفكري (AI Scholarly Assistant)

## 3.1 نظرة عامة

| الخاصية | القيمة |
|---|---|
| **النوع** | Chat Interface + RAG Pipeline |
| **الجمهور المستهدف** | المستخدم العام — يريد فهماً عميقاً |
| **الوصف** | واجهة محادثة تعتمد على LLM مع HUSSAIN كمصدر RAG للإجابة الموثّقة |
| **الأولوية** | 🟡 P1 |

---

## 3.2 حالات الاستخدام

```mermaid
graph LR
    U([المستخدم])
    
    U --> UC1[طرح سؤال فكري]
    U --> UC2[طلب تفسير آية]
    U --> UC3[طلب شرح مفهوم]
    U --> UC4[مناقشة فكرة]
    U --> UC5[عرض المصادر كاملةً]
    U --> UC6[نسخ الإجابة]
    U --> UC7[تقييم الإجابة]
    U --> UC8[بدء محادثة جديدة]
    U --> UC9[استعادة محادثة سابقة]
```

---

## 3.3 معمارية RAG Pipeline

```mermaid
graph TB
    subgraph "User Interface"
        Chat[واجهة المحادثة]
    end

    subgraph "RAG Orchestrator"
        Query_Proc[معالج الاستعلام]
        Retriever[مسترجع السياق]
        Prompt_Builder[باني الـ Prompt]
        LLM_Call[استدعاء LLM]
        Citation_Builder[باني الاستشهادات]
    end

    subgraph "Knowledge Base - HUSSAIN"
        direction TB
        ChromaDB[ChromaDB\nالأنطولوجيا + القرآن]
        TFIDF_S[TF-IDF Search\nالدروس]
        MAP_F[concept_ayah_mapping]
    end

    subgraph "External LLM"
        Gemini[Gemini API\nGemini-1.5-Pro]
    end

    Chat -->|user_message| Query_Proc
    Query_Proc --> Retriever
    
    Retriever --> ChromaDB
    Retriever --> TFIDF_S
    Retriever --> MAP_F
    
    Retriever -->|top_k contexts| Prompt_Builder
    Prompt_Builder -->|structured prompt| LLM_Call
    LLM_Call --> Gemini
    Gemini -->|raw_response| Citation_Builder
    Citation_Builder -->|answer + sources| Chat
```

---

## 3.4 هيكل الـ Prompt

```
SYSTEM PROMPT:
═══════════════════════════════════════
أنت مرشد فكري متخصص في فكر السيد حسين بدر الدين الحوثي
والدراسات القرآنية. أجب فقط بناءً على السياق المُقدَّم.
اذكر المصدر بدقة. إذا لم يكن في السياق، قل "لم أجد في المصادر المتاحة".
لا تُبدع ولا تُكمل من خيالك.
═══════════════════════════════════════

CONTEXT (مُسترجَع من HUSSAIN):
─────────────────────────
[CONCEPT]: {concept_name} — {definition}
[AYAH]: ﴿{ayah_text}﴾ [{surah}:{ayah_no}]
[LECTURE_EXCERPT_1]: "{paragraph_content}" 
  ← المصدر: {series_title} / {lecture_title}
[LECTURE_EXCERPT_2]: "{paragraph_content}"
  ← المصدر: {series_title} / {lecture_title}
─────────────────────────

USER QUESTION: {user_message}

FORMAT:
- ابدأ بالإجابة المباشرة
- استشهد بالنص الحرفي بين علامتَي اقتباس
- اذكر المصادر في نهاية الإجابة بصيغة: [⟵ المصدر: ...]
```

---

## 3.5 تدفق المحادثة

```mermaid
sequenceDiagram
    actor User
    participant UI as Chat UI
    participant API as FastAPI RAG
    participant HUSSAIN as HUSSAIN Engine
    participant LLM as Gemini API

    User->>UI: "ما معنى الولاية في فكر السيد؟"
    UI->>API: POST /api/chat {message, conversation_id, history}
    
    API->>HUSSAIN: retrieve(query, top_k=5)
    HUSSAIN->>HUSSAIN: semantic search (ChromaDB)
    HUSSAIN->>HUSSAIN: lexical search (TF-IDF)
    HUSSAIN-->>API: [{context_items}]
    
    API->>API: build_prompt(context, history, message)
    API->>LLM: generate(prompt, max_tokens=800)
    LLM-->>API: raw_text_response
    
    API->>API: extract_citations(response)
    API-->>UI: {answer, sources, conversation_id}
    
    UI->>UI: عرض الإجابة مع Streaming
    UI->>UI: عرض بطاقات المصادر قابلة للنقر
    User->>UI: نقر مصدر
    UI->>API: GET /api/paragraph/{id}/context
    API-->>UI: فتح الدرس في نافذة جانبية
```

---

## 3.6 مواصفات API

### `POST /api/v1/chat`

**Request:**
```json
{
  "message": "ما معنى الولاية في فكر السيد؟",
  "conversation_id": "uuid-or-null",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "options": {
    "max_sources": 3,
    "include_quran": true,
    "stream": true
  }
}
```

**Response (Stream):**
```json
// SSE stream chunks:
data: {"chunk": "الولاية في فكر السيد", "type": "text"}
data: {"chunk": " تُمثّل...", "type": "text"}
data: {"type": "sources", "sources": [
  {"type": "lecture", "paragraph_id": "uuid", "excerpt": "...", "series": "...", "score": 0.87},
  {"type": "quran", "global_ayah": 60, "text": "﴿...﴾", "surah": 5}
]}
data: {"type": "done"}
```

---

## 3.7 حدود ومحاذير النظام

> [!CAUTION]
> **التحذيرات الأخلاقية والتقنية**
> - النظام يُجيب فقط من مصادر HUSSAIN — لا اجتهاد خارجها
> - تحذير واضح للمستخدم: "الإجابات مبنية على مصادر المشروع وليست فتوى أو رأياً دينياً رسمياً"
> - حد معدل الاستخدام: 20 رسالة / 10 دقائق / مستخدم

---

---

# <a id="app-2"></a>§4 — المخيلة المعرفية (Knowledge Graph Explorer)

## 4.1 نظرة عامة

| الخاصية | القيمة |
|---|---|
| **النوع** | Interactive Web Visualization |
| **الجمهور المستهدف** | الباحث الأكاديمي، المفكر |
| **الوصف** | خريطة مرئية تفاعلية للأنطولوجيا — كل مفهوم عقدة، والعلاقات بينها خطوط مضيئة |
| **الأولوية** | 🟡 P1 |

---

## 4.2 حالات الاستخدام

```mermaid
graph LR
    U([المستخدم])
    A([الباحث])
    
    U --> UC1[استكشاف الخريطة بحرية]
    U --> UC2[بحث عن مفهوم]
    U --> UC3[عرض تفاصيل مفهوم]
    U --> UC4[رؤية روابط مفهوم]
    U --> UC5[تتبع مسار بين مفهومَين]
    
    A --> UC6[تصفية حسب الفئة]
    A --> UC7[تحديد عمق الروابط]
    A --> UC8[تصدير الرسم البياني]
    A --> UC9[عرض إحصائيات العقدة]
```

---

## 4.3 معمارية المكونات

```mermaid
graph TB
    subgraph "Frontend"
        React_App[React App]
        
        subgraph "Graph Engine"
            Sigma[Sigma.js / D3.js]
            Layout[Force-Atlas2 Layout]
            Renderer[WebGL Renderer]
        end
        
        subgraph "UI Components"
            SearchBar[بحث المفاهيم]
            NodePanel[لوحة تفاصيل العقدة]
            FilterPanel[لوحة التصفية]
            MiniMap[الخريطة المصغّرة]
        end
    end

    subgraph "Backend"
        API[FastAPI]
        GraphDB[Graph Builder\nfrom ontology.ttl]
        TTL[(unified_ontology.ttl)]
    end

    React_App --> Sigma
    React_App --> SearchBar
    React_App --> NodePanel
    
    API -->|"GET /api/graph"| React_App
    GraphDB --> TTL
    API --> GraphDB
```

---

## 4.4 هيكل بيانات الجراف

```typescript
interface GraphData {
  nodes: Node[];
  edges: Edge[];
  metadata: {
    total_concepts: number;
    total_relations: number;
    categories: string[];
  };
}

interface Node {
  id: string;           // concept_id
  label: string;        // concept_name
  category: string;     // الفئة الكبرى
  definition: string;
  size: number;         // عدد الروابط → حجم العقدة
  color: string;        // لون الفئة
  linked_ayahs: number[];
  lecture_count: number;
}

interface Edge {
  id: string;
  source: string;       // concept_id
  target: string;       // concept_id
  relation_type: string; // "يشمل" / "مرتبط بـ" / "ضد"
  weight: number;       // قوة العلاقة
}
```

---

## 4.5 تدفق "المسار الفكري" (Path Finding)

```mermaid
sequenceDiagram
    actor User
    participant UI as Graph UI
    participant API as FastAPI
    participant Graph as Graph Analyzer

    User->>UI: اختيار مفهوم A (الخوف)
    UI->>UI: تمييز المفهوم
    User->>UI: اختيار مفهوم B (التحرر)
    UI->>API: POST /api/graph/path {from: "uuid_A", to: "uuid_B"}
    
    API->>Graph: BFS/Dijkstra shortest path
    Graph->>Graph: تحليل الأنطولوجيا
    Graph-->>API: [concept_A, concept_C, concept_D, concept_B]
    
    API-->>UI: {path: [...], steps: 3}
    UI->>UI: رسم خط نابض يمر عبر المسار
    UI->>UI: عرض شريط المسار في الأسفل
    
    Note over UI: الخوف → المراقبة → التقوى → التحرر
```

---

## 4.6 API الجراف

### `GET /api/v1/graph`
```json
// Response
{
  "nodes": [...],
  "edges": [...],
  "generated_at": "2026-03-30T..."
}
```

### `GET /api/v1/graph/node/{concept_id}`
```json
{
  "concept": {"id": "...", "name": "...", "definition": "..."},
  "relations": [
    {"target": "...", "type": "يشمل", "weight": 0.8}
  ],
  "linked_ayahs": [...],
  "lecture_excerpts": [...]
}
```

### `POST /api/v1/graph/path`
```json
// Request
{"from": "concept_uuid_a", "to": "concept_uuid_b"}

// Response
{
  "path": ["uuid_a", "uuid_c", "uuid_d", "uuid_b"],
  "labels": ["الخوف", "المراقبة", "التقوى", "التحرر"],
  "steps": 3,
  "found": true
}
```

---

---

# <a id="app-6"></a>§5 — المصحف الذكي (Smart Quran Interface)

## 5.1 نظرة عامة

| الخاصية | القيمة |
|---|---|
| **النوع** | Standalone Web App |
| **الجمهور المستهدف** | قارئ القرآن + الباحث |
| **الوصف** | عرض القرآن مع طبقة HUSSAIN — كل آية تحمل إمكانية الاطلاع على ما قاله السيد عنها |
| **الأولوية** | 🟢 P2 |

---

## 5.2 حالات الاستخدام

```mermaid
graph LR
    U([المستخدم])
    
    U --> UC1[تصفح سورة]
    U --> UC2[الانتقال لآية مباشرة]
    U --> UC3[عرض الجذور اللغوية]
    U --> UC4[اكتشاف ماذا قال السيد عن الآية]
    U --> UC5[قراءة السياق من الدروس]
    U --> UC6[البحث بكلمة قرآنية]
    U --> UC7[عرض إحصائيات الآية]
    U --> UC8[وضع القراءة بلا تشتيت]
```

---

## 5.3 المعمارية التقنية

```mermaid
graph TB
    subgraph "Frontend"
        Reader[Quran Reader\nNext.js]
        
        subgraph "الطبقات المرئية"
            Layer0[الطبقة ٠: النص القرآني]
            Layer1[الطبقة ١: الجذور اللغوية]
            Layer2[الطبقة ٢: روابط HUSSAIN]
        end
    end

    subgraph "Backend"
        API[FastAPI]
        QDB[(quran_roots_dual_v2.sqlite)]
        LDB[(lectures_db.sqlite)]
        ChromaQ[ChromaDB quran_collection]
    end

    Reader --> Layer0
    Reader --> Layer1
    Reader --> Layer2
    
    Layer0 -->|"GET /api/surah/{no}"| API
    Layer1 -->|"GET /api/ayah/{id}/roots"| API
    Layer2 -->|"GET /api/ayah/{id}/hussain_context"| API
    
    API --> QDB
    API --> LDB
    API --> ChromaQ
```

---

## 5.4 تدفق اكتشاف سياق HUSSAIN للآية

```mermaid
flowchart TD
    A[المستخدم ينقر آية] --> B{هل الآية في Hard-Link Map؟}
    
    B -->|نعم| C[جلب المفاهيم المرتبطة مباشرة]
    B -->|لا| D[Semantic Search في ChromaDB]
    
    C --> E[جلب فقرات الدروس التي تذكر الآية]
    D --> F[جلب أقرب 3 فقرات دلالياً]
    
    E --> G[دمج النتائج]
    F --> G
    
    G --> H[عرض Panel جانبي\nبالفقرات + المفاهيم]
    H --> I{المستخدم ينقر فقرة؟}
    I -->|نعم| J[فتح الدرس كاملاً في رفيق الدرس]
    I -->|لا| K[إغلاق Panel]
```

---

## 5.5 مواصفات API

### `GET /api/v1/surah/{surah_no}`
```json
{
  "surah_no": 5,
  "name_arabic": "المائدة",
  "total_ayahs": 120,
  "ayahs": [
    {
      "global_ayah": 580,
      "ayah_no": 1,
      "text_uthmani": "﴿يَا أَيُّهَا الَّذِينَ آمَنُوا...﴾",
      "has_hussain_context": true,
      "hussain_context_count": 3
    }
  ]
}
```

### `GET /api/v1/ayah/{global_ayah}/hussain_context`
```json
{
  "ayah": {"text": "...", "surah_no": 5, "ayah_no": 51},
  "roots": [{"token": "أَوْلِيَاءَ", "root": "و-ل-ي"}],
  "hussain_context": {
    "linked_concepts": [
      {"name": "الولاية", "definition": "...", "match": "hard_link"}
    ],
    "lecture_excerpts": [
      {
        "paragraph_id": "uuid",
        "content": "...",
        "lecture_title": "...",
        "series_title": "...",
        "relevance_score": 0.91
      }
    ]
  }
}
```

---

---

# <a id="app-5"></a>§6 — لوحة الاستكشاف (Analytics Dashboard)

## 6.1 نظرة عامة

| الخاصية | القيمة |
|---|---|
| **النوع** | Data Visualization Dashboard |
| **الجمهور المستهدف** | الباحث الأكاديمي / مطور المشروع |
| **الوصف** | لوحة بيانات تحليلية تستعرض إحصائيات المشروع، شبكات المفاهيم، وأنماط الارتباط |
| **الأولوية** | 🟢 P2 |

---

## 6.2 مخطط مكونات اللوحة

```mermaid
graph TB
    subgraph "Dashboard Layout"
        Header[رأس اللوحة: إجماليات سريعة]
        
        subgraph "الصف الأول"
            W1[عداد: الدروس]
            W2[عداد: الفقرات]
            W3[عداد: المفاهيم]
            W4[عداد: الآيات المرتبطة]
        end
        
        subgraph "الصف الثاني"
            W5[خريطة حرارية: كثافة المفاهيم]
            W6[Chord Diagram: تداخل السلاسل]
        end
        
        subgraph "الصف الثالث"
            W7[Bar Chart: توزيع الفقرات بالسلسلة]
            W8[Treemap: كثافة الجذور اللغوية]
        end
        
        subgraph "الصف الرابع"
            W9[Timeline: الدروس عبر الزمن]
            W10[Scatter: تطابق المفاهيم مع الآيات]
        end
    end
```

---

## 6.3 حالات الاستخدام

```mermaid
graph LR
    R([الباحث])
    D([المطور])
    
    R --> UC1[عرض إحصائيات عامة]
    R --> UC2[تحليل توزيع المفاهيم]
    R --> UC3[رؤية أكثر الآيات ارتباطاً]
    R --> UC4[مقارنة السلاسل]
    R --> UC5[تصدير البيانات CSV]
    
    D --> UC6[مراقبة حالة القاعدة]
    D --> UC7[كشف فجوات الفهرسة]
    D --> UC8[تقرير الجودة]
```

---

## 6.4 API التحليلات

### `GET /api/v1/analytics/overview`
```json
{
  "totals": {
    "series": 7,
    "lectures": 86,
    "paragraphs": 11883,
    "concepts": 1247,
    "quran_ayahs_linked": 423,
    "unique_roots": 3812
  },
  "last_updated": "2026-03-30T..."
}
```

### `GET /api/v1/analytics/concepts/top`
```json
{
  "top_concepts": [
    {
      "name": "الإيمان",
      "ayah_links": 234,
      "lecture_mentions": 456,
      "series_distribution": {
        "معرفة الله": 180,
        "مديح القرآن": 90
      }
    }
  ]
}
```

### `GET /api/v1/analytics/series/comparison`
```json
{
  "series": [
    {
      "title": "سلسلة دروس رمضان",
      "lectures": 26,
      "paragraphs": 4230,
      "avg_paragraphs_per_lecture": 162.7,
      "concepts_mentioned": 340,
      "ayahs_linked": 87
    }
  ]
}
```

---

---

# القسم المشترك: الـ API الموحّد

## الـ Backend الموحّد وتوزيع الـ Endpoints

```mermaid
graph LR
    subgraph "Applications"
        HS[HUSSAIN Scholar]
        RD[رفيق الدرس]
        MF[المرشد الفكري]
        MM[المخيلة المعرفية]
        MZ[المصحف الذكي]
        LA[لوحة الاستكشاف]
    end

    subgraph "FastAPI — Unified Backend"
        direction TB
        
        SR[/api/v1/search]
        CH[/api/v1/chat]
        LC[/api/v1/lectures]
        PR[/api/v1/paragraphs]
        QR[/api/v1/quran]
        GR[/api/v1/graph]
        AN[/api/v1/analytics]
    end

    HS --> SR
    HS --> PR
    
    RD --> LC
    RD --> PR
    RD --> QR
    
    MF --> CH
    MF --> SR
    
    MM --> GR
    
    MZ --> QR
    MZ --> PR
    
    LA --> AN
    LA --> GR
```

---

## بنية المشروع الكاملة المقترحة

```
hussain-platform/
│
├── backend/                    ← FastAPI Unified API
│   ├── api/
│   │   ├── routes/
│   │   │   ├── search.py       ← /api/v1/search
│   │   │   ├── chat.py         ← /api/v1/chat (RAG)
│   │   │   ├── lectures.py     ← /api/v1/lectures
│   │   │   ├── paragraphs.py   ← /api/v1/paragraphs
│   │   │   ├── quran.py        ← /api/v1/quran
│   │   │   ├── graph.py        ← /api/v1/graph
│   │   │   └── analytics.py    ← /api/v1/analytics
│   │   └── middleware/
│   │       ├── rate_limiter.py
│   │       └── cache.py
│   ├── core/
│   │   ├── hussain_engine.py   ← محرك HUSSAIN الحالي
│   │   ├── rag_pipeline.py     ← RAG للمرشد الفكري
│   │   └── graph_builder.py    ← بناء الجراف من TTL
│   ├── data/                   ← قواعد البيانات
│   └── main.py
│
├── apps/
│   ├── scholar/                ← HUSSAIN Scholar (Next.js)
│   ├── companion/              ← رفيق الدرس (Next.js PWA)
│   ├── guide/                  ← المرشد الفكري (Next.js)
│   ├── explorer/               ← المخيلة المعرفية (React + D3)
│   ├── quran/                  ← المصحف الذكي (Next.js)
│   └── dashboard/              ← لوحة الاستكشاف (React)
│
└── packages/
    ├── ui/                     ← مكتبة مكونات مشتركة
    ├── api-client/             ← TypeScript API Client
    └── design-tokens/          ← ألوان + خطوط مشتركة
```

---

## معايير القبول العامة (Definition of Done)

```
لكل تطبيق، لا يُعتبر مكتملاً إلا عند:

✅ يعمل على Chrome + Firefox + Safari
✅ متجاوب بالكامل (320px → 1920px)
✅ RTL صحيح 100% بدون كسر تخطيط
✅ نسبة تباين Accessibility ≥ AA (WCAG 2.1)
✅ اختبارات API: 100% coverage للـ routes الأساسية
✅ وقت التحميل الأولي ≤ 3 ثوانٍ (LCP)
✅ يعمل بدون JavaScript (SSR للمحتوى الأساسي)
✅ موثّق في README بمثال استخدام واحد على الأقل
```

---

*وثيقة المتطلبات الفنية — منظومة HUSSAIN | v1.0 | 2026-03-30*
