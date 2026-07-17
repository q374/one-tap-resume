def build_cover_letter_prompt(experience_text: str, jd_text: str) -> str:
    return f"""你是一个求职信撰写助手。基于以下信息写一段200-300字的求职信/自我介绍。

个人经历：
{experience_text}

目标岗位JD：
{jd_text}

要求：
- 200-300字
- 说明为什么投这个岗位、你为什么适合
- 语气自然真诚，像人写的不是AI写的
- 结合个人经历中的具体项目和技能，不要泛泛而谈
- 禁止使用：赋能、抓手、闭环、从0到1、数据驱动、结果导向等套话"""
