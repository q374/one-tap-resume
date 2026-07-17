def build_jd_clean_prompt(jd_text: str) -> str:
    return f"""你是一个招聘信息分析助手。从以下JD中提取核心信息，去除水份和套话。

原始JD：
{jd_text}

请以JSON返回：
{{
    "job_title": "岗位名称",
    "company_name": "公司名称（如有，没有则为空字符串）",
    "hard_requirements": ["学历要求", "经验年限要求", "必备技能1", "必备技能2"],
    "nice_to_have": ["加分项1", "加分项2"],
    "job_summary": "一句话工作内容概括",
    "salary_range": "薪资范围（如有）",
    "location": "工作地点（如有）"
}}

要求：hard_requirements 只列出具体的、可验证的硬性要求。不要把JD里的套话（如"有责任心""团队协作"）列为硬性要求。"""
