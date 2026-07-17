def build_diagnosis_prompt(resume_html: str) -> str:
    return f"""你是一位HR视角的简历审阅者。快速扫描以下简历HTML，给出3条简短具体的改进建议。

简历HTML：
{resume_html}

以JSON返回：
{{
    "overall_score": "整体评价（1-2句话）",
    "suggestions": [
        {{"area": "问题区域", "issue": "具体问题", "fix": "改进建议"}}
    ]
}}

要求：
- 只给3条建议，每条20-40字
- 建议要具体可操作（如"第二个项目缺少量化成果数字"），不要笼统（如"内容可以更好"）
- 关注：量化数据、技能证据、语言自然度、排版可读性"""
