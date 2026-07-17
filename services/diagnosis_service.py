from core.deepseek_client import call_deepseek_json
from prompts.resume_diagnosis import build_diagnosis_prompt

class DiagnosisService:
    async def diagnose(self, resume_html: str) -> dict:
        prompt = build_diagnosis_prompt(resume_html)
        try:
            return await call_deepseek_json(prompt)
        except Exception:
            return {"overall_score": "", "suggestions": []}

diagnosis_service = DiagnosisService()
