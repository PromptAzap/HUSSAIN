import os
from openai import OpenAI
from typing import List, Dict
from dotenv import load_dotenv

# استيراد المحرك الموحّد لجلب السياق
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from unified_engine import HussainUnifiedEngine

# تحميل الإعدادات
load_dotenv()

class HussainRAGPipeline:
    def __init__(self, engine: HussainUnifiedEngine):
        self.engine = engine
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"  # أو gpt-3.5-turbo للأداء الأسرع

    def generate_response(self, user_query: str, history: List[Dict] = []) -> Dict:
        """
        توليد إجابة ذكية بناءً على السياق المسترجع من منظومة HUSSAIN.
        """
        # 1. استرجاع السياق الموحّد (القرآن، الدروس، الأنطولوجيا)
        context_data = self.engine.search(user_query, top_k=3)
        
        # 2. بناء الـ System Prompt بالسياق
        system_prompt = self._build_system_prompt(context_data)
        
        # 3. استدعاء OpenAI
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-5:]:  # نأخذ آخر 5 رسائل فقط للحفاظ على الـ Focus
            messages.append(msg)
        messages.append({"role": "user", "content": user_query})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=800
            )
            
            ai_answer = response.choices[0].message.content
            
            return {
                "answer": ai_answer,
                "sources": {
                    "ontology": context_data["ontology"],
                    "quran": context_data["quran"],
                    "lectures": context_data["lectures"]
                }
            }
            
        except Exception as e:
            return {"error": f"Error calling AI: {str(e)}"}

    def _build_system_prompt(self, context: Dict) -> str:
        """
        تنسيق السياق المسترجع في Prompt موجه للـ LLM.
        """
        prompt = (
            "أنت المساعد الذكي المختص في منظومة HUSSAIN المعرفية. "
            "مهمتك هي الإجابة عن أسئلة المستخدمين بدقة وأمانة علمية بناءً على 'السياق المتاح' فقط. "
            "إذا لم تجد الإجابة في السياق، قل بوضوح: 'بناءً على المصادر المتاحة حالياً، لا تتوفر تفاصيل محددة عن هذا الموضوع'.\n\n"
            "--- السياق المسترجع ---\n"
        )
        
        if context["ontology"]:
            prompt += f"[مفهوم من الأنطولوجيا]: {context['ontology']['name']} - {context['ontology']['definition']}\n"
            
        if context["quran"]:
            prompt += "[آيات قرآنية مرتبطة]:\n"
            for a in context["quran"]:
                prompt += f"  - ﴿{a['text']}﴾ [{a['surah']}:{a['ayah_no']}]\n"
                
        if context["lectures"]:
            prompt += "[اقتباسات من دروس السيد حسين]:\n"
            for l in context["lectures"]:
                prompt += f"  - [{l['series_title']}/{l['lecture_title']}]: {l['content']}\n"
                
        prompt += "\n--------------------\n"
        prompt += (
            "عند الإجابة، يرجى الاستشهاد بالمصادر (مثل الآية أو عنوان الدرس) لتعزيز موثوقية المعلومة. "
            "أجب باللغة العربية الفصحى وبأسلوب رصين."
        )
        
        return prompt
