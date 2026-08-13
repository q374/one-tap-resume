"""简历质量诊断服务 — 客观分（代码算）+ AI 找茬（挑剔HR视角）+ 边界说明

设计原则：
- 客观分全部由代码计算（JD覆盖率/量化数字/页数估算/套话/硬性要求），AI 无法自评美化
- AI 只做"找茬"：以挑剔 HR 视角输出具体可改的问题，不给总分
- 永远附带边界说明：诊断只查硬伤，不承诺通过任何筛选

JD 关键词提取与别名展开统一走 prompts/skill_aliases.py：
- 与匹配度口径一致（同词表、同噪音过滤、同等价词簇展开）
- 解决"JD 写大模型/提示词、简历写 ChatGPT/Prompt"字面不命中问题
"""
import re

from core.deepseek_client import call_deepseek_json
from prompts.resume_diagnosis import build_diagnosis_prompt
from prompts.skill_aliases import extract_jd_keywords, expand_keyword, alias_hit


# 客观分各维度权重（共 100 分）
_WEIGHTS = {
    "jd_coverage": 25,
    "quantified": 25,
    "single_page": 15,
    "buzzwords": 15,
    "hard_req": 20,
}

# AI 套话/弱表达词表（与 html_cleaner 保持一致，另加常见弱词）
_BUZZWORDS = [
    "赋能", "抓手", "闭环", "沉淀", "复盘", "对齐", "拉齐", "打通", "落地",
    "产出", "迭代", "复用", "优化", "升级", "重构", "数据驱动", "结果导向",
    "用户思维", "产品思维", "商业思维", "闭环思维", "链路思维", "从0到1",
    "具备良好的", "有较强的", "扎实的", "丰富的经验", "优秀的", "良好的沟通",
    "较强的责任心", "出色的", "积极主动", "团队协作", "抗压能力", "学习能力强",
    "执行力强", "逻辑思维清晰", "创新性思维", "系统性思维", "熟练掌握", "精通",
    "我觉得", "我认为", "我感觉", "非常", "十分", "特别", "综上所述", "总而言之",
]

# 量化成果正则：数字 + 单位/百分号/倍率等
_QUANT_PATTERN = re.compile(
    r"[0-9]+(?:.[0-9]+)?\s*(?:%|％|倍|人|万|亿|千|ms|s|个|家|款|次|分|天|月|年|项|篇|页|行|份|台|套|单|门|名|QPS|TPS|K|k|MB|GB|TB|\+)"
)

_EDU_REQUIREMENT = ["本科", "硕士", "博士", "大专", "本科及以上", "统招"]


def _strip_html(html: str) -> str:
    """去标签/去 script/style，返回纯文本"""
    text = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|&amp;|&lt;|&gt;|&quot;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _compute_objective(resume_html: str, jd_text: str) -> dict:
    """计算客观分（5 项硬指标），AI 无法干预"""
    html_text = _strip_html(resume_html)
    text_lower = html_text.lower()
    checks = {}

    # 1. JD 关键词覆盖率（含等价词簇展开，中英文写法皆可命中）
    jd_kw = extract_jd_keywords(jd_text)
    if jd_kw:
        covered = [
            k for k in jd_kw
            if any(alias_hit(text_lower, a) for a in expand_keyword(k))
        ]
        ratio = len(covered) / len(jd_kw)
        checks["jd_coverage"] = {
            "pass": ratio >= 0.6,
            "detail": f"命中 {len(covered)}/{len(jd_kw)} 个JD关键词",
            "score": round(ratio * 100),
        }
    else:
        checks["jd_coverage"] = {"pass": True, "detail": "未提供JD，跳过", "score": 100}

    # 2. 量化成果数量
    quant_hits = _QUANT_PATTERN.findall(html_text)
    q = len(quant_hits)
    checks["quantified"] = {
        "pass": q >= 3,
        "detail": f"检测到 {q} 处量化表达（数字+单位）",
        "score": min(100, q * 20),
    }

    # 3. 单页估算（按文本字数粗估，中文一页约 900 字）
    est_pages = len(html_text) / 900
    checks["single_page"] = {
        "pass": est_pages <= 1.15,
        "detail": f"内容约 {est_pages:.1f} 页（按900字/页估算）",
        "score": max(0, 100 - int((est_pages - 1) * 120)),
    }

    # 4. AI 套话命中
    buzz_hits = [b for b in _BUZZWORDS if b in text_lower]
    checks["buzzwords"] = {
        "pass": len(buzz_hits) == 0,
        "detail": f"命中 {len(buzz_hits)} 处套话" + (f"：{'、'.join(buzz_hits[:5])}" if buzz_hits else ""),
        "score": max(0, 100 - len(buzz_hits) * 25),
    }

    # 5. 硬性要求覆盖（学历关键词）
    edu_in_jd = [w for w in _EDU_REQUIREMENT if w in jd_text]
    if edu_in_jd:
        has_edu = any(w in html_text for w in ["本科", "硕士", "博士", "大专"])
        checks["hard_req"] = {
            "pass": has_edu,
            "detail": "JD含学历要求，简历" + ("已体现学历" if has_edu else "未识别到学历信息"),
            "score": 100 if has_edu else 0,
        }
    else:
        checks["hard_req"] = {"pass": True, "detail": "JD未明确学历要求，跳过", "score": 100}

    # 汇总加权分
    total = sum(_WEIGHTS[k] * checks[k]["score"] / 100 for k in _WEIGHTS)
    total = max(0, min(100, round(total)))
    return {
        "score": total,
        "checks": [
            {"key": k, "label": _CHECK_LABELS[k], "pass": checks[k]["pass"], "detail": checks[k]["detail"]}
            for k in _WEIGHTS
        ],
    }


_CHECK_LABELS = {
    "jd_coverage": "JD关键词覆盖率",
    "quantified": "量化成果数量",
    "single_page": "单页限制（估算）",
    "buzzwords": "AI套话检查",
    "hard_req": "JD硬性要求覆盖",
}

_DISCLAIMER = (
    "本诊断只检查简历的硬伤与可改进点，不承诺通过任何公司筛选。"
    "约面结果受岗位竞争度、学历门槛、投递时机、公司偏好等大量因素影响，"
    "简历只是其中一环。"
)


class DiagnosisService:
    async def diagnose(self, resume_html: str, jd_text: str = "") -> dict:
        """简历质量诊断：客观分 + AI 找茬 + 边界说明"""
        objective = _compute_objective(resume_html, jd_text)

        ai_findings = {"suggestions": []}
        try:
            result = await call_deepseek_json(build_diagnosis_prompt(resume_html, jd_text))
            suggestions = result.get("suggestions") or []
            ai_findings = {"suggestions": [s for s in suggestions if isinstance(s, dict)]}
        except Exception:
            ai_findings = {"suggestions": [], "error": "AI找茬暂不可用，请稍后重试"}

        return {
            "objective": objective,
            "ai_findings": ai_findings,
            "disclaimer": _DISCLAIMER,
        }


diagnosis_service = DiagnosisService()
