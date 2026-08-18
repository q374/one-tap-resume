import re
from core.deepseek_client import call_deepseek_json
from prompts.jd_clean import build_jd_clean_prompt

_BUZZWORD_MAP = {
    '赋能': '支持', '抓手': '切入点', '对齐': '协调', '沉淀': '积累',
    '拉齐': '统一', '打通': '连接', '落地': '实现', '产出': '完成',
    '迭代': '改进', '复用': '重复使用', '复盘': '总结',
    '从0到1': '从零开始', '闭环': '完整流程', '数据驱动': '以数据为依据',
    '结果导向': '注重结果', '用户思维': '用户视角',
}

class JDService:
    async def clean(self, jd_text: str) -> dict:
        """规则清洗 + AI 提取，返回结构化 JD"""
        cleaned = jd_text
        for buzz, replacement in _BUZZWORD_MAP.items():
            cleaned = cleaned.replace(buzz, replacement)

        prompt = build_jd_clean_prompt(cleaned)
        try:
            result = await call_deepseek_json(prompt)
            result["raw_jd"] = jd_text
            result["cleaned_jd"] = cleaned
            return result
        except Exception:
            return {
                "job_title": "", "company_name": "",
                "hard_requirements": [], "nice_to_have": [],
                "job_summary": "", "salary_range": "", "location": "", "url": "",
                "raw_jd": jd_text, "cleaned_jd": cleaned
            }


jd_service = JDService()
