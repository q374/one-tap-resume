def build_template_parse_prompt(template_html: str) -> str:
    return f"""分析以下简历HTML模板，识别其中所有的内容区域。

模板HTML：
{template_html}

请以JSON返回：
{{
    "sections": [
        {{
            "name": "区域名称（如姓名、教育背景、项目经历、专业技能、自我评价、实习经历、获奖情况等）",
            "position_hint": "位置描述（如：第一个h2、header区域、技能列表div）",
            "content_type": "对应的系统字段类型（basic_info/education/projects/skills/self_evaluation/internships/awards）",
            "confidence": "识别置信度（high/medium/low）"
        }}
    ],
    "has_print_style": true/false,
    "has_photo_area": true/false,
    "template_name_suggestion": "建议的模板名称"
}}

要求：
- 至少识别5个区域
- content_type 必须是以下之一：basic_info, education, internships, projects, skills, awards, self_evaluation"""
