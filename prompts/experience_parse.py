EXPERIENCE_PARSE_PROMPT = """你是一个专业的简历信息提取助手。请从以下用户输入的经历文本中，提取结构化信息。

用户文本：
{user_text}

请提取以下信息并以JSON格式返回（找不到的字段用空字符串或空数组）：

【重要规则】
1. "work_experience" 字段用于存储所有工作经历，包括：全职工作、实习、兼职、外包等一切职业经历。无论用户写的是"工作经历""实习经历""工作履历"，全部归入此字段。不要遗漏任何一条。
2. 职位名称要完全忠实于原文，用户写什么就保留什么，绝对不要自动添加"实习""助理"等修饰词。
3. "awards" 字段存获奖和荣誉（比赛、竞赛、奖学金、演讲嘉宾等），"skills" 字段存技能（编程语言、工具、框架等）。区分标准：如果是"比赛/竞赛/评选"的结果 → awards；如果是"会用的技术/工具" → skills。
4. "category" 字段请从以下标准分类中选择：编程语言、框架、数据库、工具、消息队列、容器与运维、架构、管理、行业知识、其他。
5. "others" 字段用于存储不属于教育/工作/项目/技能/获奖的零散信息：证书、语言能力、培训经历、资格认证、兴趣爱好、志愿服务等。每条用 title 概括标题（如"CET-6英语六级"），content 写具体内容（时间、分数、说明等）。
6. **技能字段严格限定**："skills" 只存可直接操作的技术/工具能力（编程语言、框架、数据库、软件工具、办公软件等）。以下内容**禁止**放入 skills，一律归入 "others"：语言等级证书（CET-4/6、雅思、托福、普通话等级）、职业/资格证（会计证、教师资格证、驾照）、培训营/课程经历、兴趣爱好、志愿服务。即使原文把这些写在"技能/特长"标题下，也要按此标准归类。

返回格式：
{{
    "basic_info": {{"name": "", "phone": "", "email": "", "age": "", "job_target": ""}},
    "education": [{{"school": "", "major": "", "degree": "", "start_date": "", "end_date": ""}}],
    "work_experience": [{{"company": "", "position": "", "start_date": "", "end_date": "", "description": ""}}],
    "projects": [{{"name": "", "role": "", "start_date": "", "end_date": "", "background": "", "actions": "", "results": "", "tech_stack": ""}}],
    "skills": [{{"name": "", "level": "", "evidence": "", "category": ""}}],
    "awards": [{{"name": "", "level": "", "date": ""}}],
    "others": [{{"title": "", "content": ""}}],
    "self_evaluation": {{"content": ""}}
}}"""
