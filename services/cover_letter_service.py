from core.deepseek_client import call_deepseek
from prompts.cover_letter import build_cover_letter_prompt

class CoverLetterService:
    async def generate(self, experience_text: str, jd_text: str) -> str:
        prompt = build_cover_letter_prompt(experience_text, jd_text)
        return await call_deepseek(prompt, max_tokens=1024)

cover_letter_service = CoverLetterService()
