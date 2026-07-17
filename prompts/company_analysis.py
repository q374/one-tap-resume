def build_company_analysis_prompt(company_data: str, jd_text: str) -> str:
    return f"""你是企业风险分析助手。分析以下公司信息，给出求职者角度的建议。

公司工商信息：
{company_data}

招聘JD摘要：
{jd_text}

以JSON返回：
{{
    "summary": "公司基本情况总结（1-2句话）",
    "risk_level": "low/medium/high/unknown",
    "risks": ["风险点1", "风险点2"],
    "positives": ["正面因素1", "正面因素2"],
    "advice": "给求职者的具体建议（如：建议面试时确认社保缴纳情况、公司成立时间短需谨慎等）",
    "verdict": "整体靠谱，可投 / 有风险，建议进一步了解 / 数据不足，无法判断"
}}

要求：
- 用语客观，不要制造恐慌，也不要盲目乐观
- 数据不足时诚实标注 unknown
- advice 要具体可执行"""
