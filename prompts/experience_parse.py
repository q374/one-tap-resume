EXPERIENCE_PARSE_PROMPT = """你是一个专业的简历信息提取助手。请从以下用户输入的经历文本中，提取结构化信息。

用户文本：
{user_text}

请提取以下信息并以JSON格式返回（找不到的字段用空字符串或空数组）：
{{
    "basic_info": {{"name": "", "phone": "", "email": "", "age": "", "job_target": ""}},
    "education": [{{"school": "", "major": "", "degree": "", "start_date": "", "end_date": ""}}],
    "internships": [{{"company": "", "position": "", "start_date": "", "end_date": "", "description": ""}}],
    "projects": [{{"name": "", "role": "", "start_date": "", "end_date": "", "background": "", "actions": "", "results": "", "tech_stack": ""}}],
    "skills": [{{"name": "", "level": "", "evidence": "", "category": ""}}],
    "awards": [{{"name": "", "level": "", "date": ""}}],
    "self_evaluation": {{"content": ""}}
}}"""
