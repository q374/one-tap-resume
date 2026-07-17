def build_interview_prompt(experience_text: str, jd_text: str) -> str:
    return f"""你是面试官。基于以下JD和候选人经历，出8-10道面试题，分三类：

目标岗位：
{jd_text}

候选人经历：
{experience_text}

请以JSON返回面试题：
{{
    "tech_questions": [
        {{"question": "技术题", "purpose": "考察什么能力"}}
    ],
    "project_deep_dive": [
        {{"question": "项目深挖题", "purpose": "考察什么能力"}}
    ],
    "behavioral_questions": [
        {{"question": "行为题", "purpose": "考察什么能力"}}
    ]
}}

要求：
- 技术题结合JD要求的具体技能
- 项目深挖题基于候选人实际项目经历
- 行为题关注沟通、协作、解决问题能力
- 每题要有明确考察目的"""
