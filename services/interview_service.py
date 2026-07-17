from core.deepseek_client import call_deepseek_json
from prompts.interview import build_interview_prompt

class InterviewService:
    async def generate(self, experience_text: str, jd_text: str) -> dict:
        prompt = build_interview_prompt(experience_text, jd_text)
        try:
            return await call_deepseek_json(prompt)
        except Exception:
            return {"tech_questions": [], "project_deep_dive": [], "behavioral_questions": []}

interview_service = InterviewService()
