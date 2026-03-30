import os
import sys
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# إضافة المجلد الرئيسي للمسارات لاستيراد المحرك الموحّد
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unified_engine import HussainUnifiedEngine
from core.rag_pipeline import HussainRAGPipeline

# تحميل الإعدادات من ملف .env
load_dotenv()

app = FastAPI(
    title="HUSSAIN Unified API",
    description="القاعدة الخلفية الموحدة لمنظومة HUSSAIN المعرفية",
    version="1.0.0"
)

# إعداد CORS للسماح للتطبيقات الأمامية بالوصول
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تهيئة المحرك لمرة واحدة عند بدء التشغيل
engine = HussainUnifiedEngine()
rag_pipeline = HussainRAGPipeline(engine)

# --- نماذج البيانات (Pydantic Models) ---

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    sources: Optional[List[str]] = ["concepts", "quran", "lectures"]

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []

# --- نقاط النهاية (Endpoints) ---

@app.get("/")
async def root():
    return {"message": "Welcome to HUSSAIN Unified API", "status": "online"}

@app.post("/api/v1/search")
async def search(request: SearchRequest):
    try:
        results = engine.search(request.query, top_k=request.top_k, sources=request.sources)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/quran/surah/{surah_no}")
async def get_surah(surah_no: int):
    # (سيتم ربطها بـ SQLite لاحقاً لجلب السورة كاملة)
    return {"message": "Endpoint pending implementation", "surah_no": surah_no}

@app.get("/api/v1/quran/ayah/{global_ayah}")
async def get_ayah(global_ayah: int):
    details = engine.get_ayah_details(global_ayah)
    if not details:
        raise HTTPException(status_code=404, detail="Ayah not found")
    return details

@app.get("/api/v1/lectures/paragraph/{paragraph_id}")
async def get_paragraph(paragraph_id: str):
    details = engine.get_paragraph_details(paragraph_id)
    if not details:
        raise HTTPException(status_code=404, detail="Paragraph not found")
    return details

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    try:
        response = rag_pipeline.generate_response(request.message, request.history)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- تشغيل السيرفر ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
