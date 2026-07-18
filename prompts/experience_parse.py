EXPERIENCE_PARSE_PROMPT = """你是一个专业的简历信息提取助手。请从以下用户输入的经历文本中，提取结构化信息。

用户文本：
{user_text}

请提取以下信息并以JSON格式返回（找不到的字段用空字符串或空数组）：

【重要规则】
1. "work_experience" 字段用于存储所有工作经历，包括：全职工作、实习、兼职、外包等一切职业经历。无论用户写的是"工作经历""实习经历""工作履历"，全部归入此字段。不要遗漏任何一条。
2. 职位名称要完全忠实于原文，用户写什么就保留什么，绝对不要自动添加"实习""助理"等修饰词。
3. "awards" 字段存获奖和荣誉（比赛、竞赛、奖学金、演讲嘉宾等），"skills" 字段存技能（编程语言、工具、框架等）。区分标准：如果是"比赛/竞赛/评选"的结果 → awards；如果是"会用的技术/工具" → skills。
4. "category" 字段请从以下标准分类中选择：编程语言、框架、数据库、工具、消息队列、容器与运维、架构、管理、行业知识、其他。

返回格式：
{{
    "basic_info": {{"name": "", "phone": "", "email": "", "age": "", "job_target": ""}},
    "education": [{{"school": "", "major": "", "degree": "", "start_date": "", "end_date": ""}}],
    "work_experience": [{{"company": "", "position": "", "start_date": "", "end_date": "", "description": ""}}],
    "projects": [{{"name": "", "role": "", "start_date": "", "end_date": "", "background": "", "actions": "", "results": "", "tech_stack": ""}}],
    "skills": [{{"name": "", "level": "", "evidence": "", "category": ""}}],
    "awards": [{{"name": "", "level": "", "date": ""}}],
    "self_evaluation": {{"content": ""}}
}}"""
