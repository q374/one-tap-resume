"""经历-岗位匹配度计算

用于生成简历前判断「经历库与目标JD」的匹配程度：
- 低/中匹配时触发「匹配增强模式」（可迁移改写 + 补位模块），注入生成 prompt
- 返回 match_score / missing_keywords / level，供前端展示预警与补录引导

原则：匹配度只做「相关性提示」，永不虚构经历——事实始终来自经历库。
关键词提取与别名展开统一走 prompts/skill_aliases.py：
- JD 关键词 = 行业知识库（去噪音）+ 英文技术词（去停用词）
- 每个关键词展开成等价词簇（如"大模型"→{大模型, chatgpt, coze, dify,...}），
  命中任一同义词即算命中，解决"JD 中文术语 vs 经历库英文工具名"不命中问题
"""
import re
from prompts.skill_aliases import extract_jd_keywords, expand_keyword, alias_hit


# 行业/赛道属性词：无法通过"补录经历"命中，不计入可补命中率（避免用户对着无法补的词干瞪眼）
_INDUSTRY_ATTR_KEYWORDS = {
    "saas", "b2b", "b2c", "o2o", "互联网", "云计算", "大数据", "人工智能",
    "ai", "医疗", "医药", "生物", "金融", "银行", "证券", "保险", "基金",
    "快消", "消费品", "零售", "电商", "制造", "工业", "汽车", "新能源",
    "教育", "咨询", "传媒", "能源", "建筑", "地产", "游戏", "内容",
    "企业服务", "半导体", "芯片", "数字化", "智能",
}


def _is_unfillable(kw: str) -> bool:
    """判断缺失关键词是否"不可补"：行业/公司属性词、英文专名（公司/产品名）"""
    k = kw.lower()
    if len(expand_keyword(kw)) > 1 or k in _SKILL_KEYWORDS or k in _EXPERIENCE_KEYWORDS:
        return False
    if k.isascii() and re.fullmatch(r"[a-z0-9+#.]{2,}", k):
        return True  # 英文但非技能/经历词 → 多为公司/产品专名或无关词，不可补
    return k in _INDUSTRY_ATTR_KEYWORDS

# 技能类补充词：不在 SKILL_ALIAS_CLUSTERS 里的硬技能/工具（供"怎么补"建议分类用）
_SKILL_KEYWORDS = {
    "sql", "python", "excel", "tableau", "finebi", "metabase", "powerbi", "bi",
    "figma", "axure", "墨刀", "pandas", "numpy", "matplotlib", "mysql", "redis",
    "docker", "fastapi", "git", "github", "linux", "html", "css", "javascript",
    "react", "vue", "node", "flask", "django", "codex", "claude", "gemini",
    "deepseek", "vibe coding", "comfyui",
}

# 经历/工作类关键词：JD 常要求"做过"的动作或产出，建议落到经历里
_EXPERIENCE_KEYWORDS = {
    "prd", "需求文档", "需求分析", "需求调研", "用户调研", "用户访谈", "竞品分析",
    "原型", "原型设计", "项目管理", "跨部门", "团队协作", "推动落地", "上线验收",
    "数据监控", "数据看板", "指标体系", "埋点", "ab测试", "a/b测试", "实验设计",
    "产品迭代", "用户反馈", "bad case", "质量评估", "评测报告", "数据标注",
    "运营", "推广", "投放", "内容创作", "短视频", "自媒体", "会议纪要",
}


def _suggest_for_keyword(kw: str) -> dict:
    """给单个缺失关键词生成"怎么补"建议：技能类补技能区、经历类补经历、其余通用"""
    k = kw.lower()
    if _is_unfillable(kw):
        if k in _INDUSTRY_ATTR_KEYWORDS:
            return {
                "keyword": kw, "type": "行业属性",
                "suggestion": "属于行业/赛道属性词，可在技能或自我评价中顺带提及（可选，非必须）",
            }
        return {
            "keyword": kw, "type": "专名",
            "suggestion": "这是公司/产品专名或无关英文词，无需写入简历，可忽略",
        }
    if len(expand_keyword(kw)) > 1 or k in _SKILL_KEYWORDS:
        return {
            "keyword": kw, "type": "技能",
            "suggestion": f"到「经历管理 → 专业技能」补充「{kw}」（仅当你确实会用时）",
        }
    if k in _EXPERIENCE_KEYWORDS:
        return {
            "keyword": kw, "type": "经历",
            "suggestion": f"在项目/实习经历中写一条「{kw}」相关动作（真实做过才写）",
        }
    return {
        "keyword": kw, "type": "其他",
        "suggestion": f"可在技能区或自我评价中表达「{kw}」相关能力",
    }


def compute_match(experience_text: str, jd_text: str) -> dict:
    """计算经历库与 JD 的匹配度

    返回：{score, level(high/medium/low/unknown), matched, missing_keywords, total, detail}
    """
    if not jd_text.strip():
        return {"score": None, "level": "unknown", "matched": [],
                "missing_keywords": [], "total": 0, "detail": "未提供JD"}

    jd_kw = extract_jd_keywords(jd_text)
    if not jd_kw:
        return {"score": None, "level": "unknown", "matched": [],
                "missing_keywords": [], "total": 0, "detail": "JD未识别到关键词"}

    exp_lower = experience_text.lower()
    matched = []
    missing = []
    for k in jd_kw:
        if any(alias_hit(exp_lower, a) for a in expand_keyword(k)):
            matched.append(k)
        else:
            missing.append(k)

    missing_limited = missing[:12]
    unfillable = [k for k in missing_limited if _is_unfillable(k)]
    fillable_missing = [k for k in missing_limited if not _is_unfillable(k)]
    fillable_total = max(len(jd_kw) - len(unfillable), 1)
    fillable_score = round(len(matched) / fillable_total * 100)
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
        "missing_keywords": missing_limited,
        "suggestions": [_suggest_for_keyword(k) for k in missing_limited],
        "total": len(jd_kw),
        "detail": f"JD关键词命中 {len(matched)}/{len(jd_kw)}",
        "fillable_score": fillable_score,
        "fillable_missing": fillable_missing,
        "unfillable": unfillable,
        "unfillable_n": len(unfillable),
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
