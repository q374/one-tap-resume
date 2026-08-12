"""经历-岗位匹配度计算

用于生成简历前判断「经历库与目标JD」的匹配程度：
- 低/中匹配时触发「匹配增强模式」（可迁移改写 + 补位模块），注入生成 prompt
- 返回 match_score / missing_keywords / level，供前端展示预警与补录引导

原则：匹配度只做「相关性提示」，永不虚构经历——事实始终来自经历库。
"""
import re

from prompts.industry_profiles import INDUSTRY_PROFILES

_STOP_WORDS = {
    "and", "the", "for", "with", "you", "your", "will", "have", "has",
    "are", "not", "that", "this", "our", "all", "can", "who", "what",
    "how", "why", "but", "from", "into", "about", "over", "also", "was",
    "等等", "以及", "要求", "任职", "岗位", "职位", "工作", "负责", "熟悉",
    "优先", "经验", "能力", "相关", "以上", "我们", "进行", "能够", "具备",
}


def _extract_jd_keywords(jd_text: str) -> list:
    """从 JD 提取关键词：行业知识库关键词（命中JD者）+ 英文技术词（去停用词）"""
    jd_lower = jd_text.lower()
    keywords = set()
    for profile in INDUSTRY_PROFILES.values():
        for kw in profile.get("keywords", []):
            if kw and kw.lower() in jd_lower:
                keywords.add(kw.lower())
    for word in re.findall(r"[a-zA-Z][a-zA-Z0-9+#.]{2,}", jd_text):
        if word.lower() not in _STOP_WORDS:
            keywords.add(word.lower())
    return sorted(keywords)


def compute_match(experience_text: str, jd_text: str) -> dict:
    """计算经历库与 JD 的匹配度

    返回：{score, level(high/medium/low/unknown), matched, missing_keywords, total, detail}
    """
    if not jd_text.strip():
        return {"score": None, "level": "unknown", "matched": [],
                "missing_keywords": [], "total": 0, "detail": "未提供JD"}

    jd_kw = _extract_jd_keywords(jd_text)
    if not jd_kw:
        return {"score": None, "level": "unknown", "matched": [],
                "missing_keywords": [], "total": 0, "detail": "JD未识别到关键词"}

    exp_lower = experience_text.lower()
    matched = [k for k in jd_kw if k in exp_lower]
    missing = [k for k in jd_kw if k not in exp_lower]

    ratio = len(matched) / len(jd_kw)
    score = round(ratio * 100)
    if ratio >= 0.6:
        level = "high"
    elif ratio >= 0.35:
        level = "medium"
    else:
        level = "low"

    return {
        "score": score,
        "level": level,
        "matched": matched,
        "missing_keywords": missing[:12],
        "total": len(jd_kw),
        "detail": f"JD关键词命中 {len(matched)}/{len(jd_kw)}",
    }


def build_match_context(match: dict) -> str:
    """低/中匹配时生成「匹配增强模式」上下文，注入生成 prompt；高匹配返回空串"""
    if not match or match.get("level") not in ("low", "medium"):
        return ""
    level_cn = "偏低" if match.get("level") == "low" else "一般"
    score = match.get("score", 0)
    detail = match.get("detail", "")
    missing = "、".join(match.get("missing_keywords", [])[:8]) or "无"
    return (
        f"【经历-岗位匹配度{level_cn}（JD关键词命中 {score} 分 / {detail}），启用匹配增强模式】\n"
        "你的任务是在不编造的前提下，尽量提高简历与目标岗位的相关度：\n"
        "1. 【可迁移改写】把现有经历按目标岗位视角重新提炼表述：事实不变，突出与JD要求相关的可迁移能力（如运营经历投数据岗→突出数据分析、用户洞察、活动复盘；销售经历投产品岗→突出用户需求挖掘、方案落地）。禁止虚构经历或数据。\n"
        "2. 【补位模块】当项目/工作经历不足时，充分利用：技能区按JD要求拆分并标注使用场景、自我评价强化可迁移优势+学习能力+求职动机、获奖/证书/课程项目全部拉入正文。\n"
        "3. 【如实原则】JD中完全没做过的内容（如从未做过AB测试）不得写成「做过」，只能从现有经历提炼可迁移表述。\n"
        "4. 【一页兜底】内容不足时通过合理排版与补位模块让简历接近一页，禁止空洞重复或注水。\n"
        f"JD中以下要求你的经历库未直接覆盖：{missing}。"
    )
