"""行业侧重点分析服务 — 关键词初筛 + DeepSeek 精析 + 内置知识库兜底

职责：
1. 从 JD 中识别目标行业（关键词打分初筛）
2. 结合内置行业知识库锚点，让 DeepSeek 精析该行业的简历侧重点
3. AI 失败时回退内置知识库，保证永不抛异常、不阻断简历生成
"""
import re

from core.deepseek_client import call_deepseek_json
from prompts.industry_profiles import (
    INDUSTRY_PROFILES,
    FALLBACK_INDUSTRY,
    get_profile,
    industry_keys,
)


class IndustryService:
    def _matches(self, text_lower: str, keyword: str) -> bool:
        """关键词匹配：英文用词边界（避免 'ai' 误命中 'email'），中文用子串"""
        kw = keyword.lower()
        if kw.isascii():
            return re.search(r'\b' + re.escape(kw) + r'\b', text_lower) is not None
        return kw in text_lower

    def match_industry_keyword(self, jd_text: str) -> tuple:
        """关键词打分初筛，返回 (industry_key, score, confidence)

        confidence:
        - high:   命中明显且分差大（top>=2 且比第二名高>=2）
        - medium: 有命中但不明显
        - low:    未命中任何行业
        """
        text_lower = (jd_text or "").lower()
        scores = {}
        for key, profile in INDUSTRY_PROFILES.items():
            if key == FALLBACK_INDUSTRY:
                continue
            scores[key] = sum(
                1 for kw in profile.get("keywords", []) if self._matches(text_lower, kw)
            )

        if not scores or max(scores.values()) == 0:
            return FALLBACK_INDUSTRY, 0, "low"

        ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_key, top_score = ordered[0]
        second_score = ordered[1][1] if len(ordered) > 1 else 0

        if top_score >= 2 and (top_score - second_score) >= 2:
            confidence = "high"
        elif top_score >= 1:
            confidence = "medium"
        else:
            confidence = "low"
        return top_key, top_score, confidence

    def _profile_to_analysis(self, industry_key: str, confidence: str, reason: str = "") -> dict:
        """把内置 profile 转成统一的分析结果结构"""
        profile = get_profile(industry_key)
        return {
            "industry": industry_key,
            "confidence": confidence,
            "focus_points": profile.get("focus_points", []),
            "avoid": profile.get("avoid", []),
            "tone": profile.get("tone", ""),
            "reason": reason or (f"根据JD内容初步判断为「{industry_key}」行业"),
        }

    def build_industry_prompt(self, jd_text: str, matched_key: str, matched_conf: str) -> str:
        """构造 AI 精析 prompt：内置锚点 + 行业判断指令"""
        profile = get_profile(matched_key)
        anchor = "\n".join(f"- {p}" for p in profile.get("focus_points", []))
        avoid = "\n".join(f"- {a}" for a in profile.get("avoid", []))
        valid_keys = "、".join(industry_keys())
        if matched_conf == "high":
            judge_instruction = (
                f"根据关键词匹配，JD 很可能属于「{matched_key}」行业。"
                "请结合下方内置侧重点锚点，对这份JD做精析，聚焦最关键的简历侧重点。"
            )
        else:
            judge_instruction = (
                "JD 行业特征不明显，请基于你的职业常识独立判断最可能的行业，"
                "再结合该行业特点给出简历侧重点。"
            )
        return f"""你是资深HR简历顾问，专帮应届生判断「目标行业看重简历里的什么」。

【任务】分析下面的招聘JD，输出：所属行业、该行业简历侧重点、减分项、语言风格。

【初步判断】{matched_key}（置信度：{matched_conf}）

【内置行业侧重点锚点（可参考或修正）】
{anchor}

【该行业常见减分项锚点】
{avoid}

{judge_instruction}

【招聘JD】
{jd_text}

以JSON返回，不要任何解释：
{{
    "industry": "行业名称",
    "confidence": "high/medium/low",
    "focus_points": ["该行业简历侧重点1", "侧重点2", "侧重点3", "侧重点4"],
    "avoid": ["减分项1", "减分项2", "减分项3"],
    "tone": "语言风格建议",
    "reason": "一句话说明判断依据"
}}

要求：
- focus_points 3-5条，必须具体可操作（如「项目必须给出量化成果」），不要空话
- avoid 2-3条，是该行业真正会扣分的点
- industry 必须与以下列表之一完全一致：{valid_keys}、综合/其他"""

    async def analyze(self, jd_text: str, industry_override: str = "") -> dict:
        """行业侧重点分析主入口（永不抛异常）

        - industry_override 合法时：直接用内置 profile（不调 AI，省成本）
        - 否则：关键词初筛 → AI 精析；AI 失败回退内置 profile
        """
        if not jd_text or not jd_text.strip():
            return self._profile_to_analysis(FALLBACK_INDUSTRY, "low", "JD为空，无法判断行业")

        if industry_override and industry_override in INDUSTRY_PROFILES:
            return self._profile_to_analysis(
                industry_override, "user", f"用户手动指定行业：{industry_override}"
            )

        matched_key, _score, matched_conf = self.match_industry_keyword(jd_text)

        try:
            result = await call_deepseek_json(
                self.build_industry_prompt(jd_text, matched_key, matched_conf)
            )
            industry = (result.get("industry") or "").strip()
            if industry not in INDUSTRY_PROFILES:
                # AI 返回了未知行业名 → 用初筛结果兜底
                return self._profile_to_analysis(
                    matched_key, "medium", result.get("reason", "")
                )
            return {
                "industry": industry,
                "confidence": result.get("confidence") or matched_conf,
                "focus_points": result.get("focus_points")
                    or get_profile(matched_key).get("focus_points", []),
                "avoid": result.get("avoid")
                    or get_profile(matched_key).get("avoid", []),
                "tone": result.get("tone")
                    or get_profile(matched_key).get("tone", ""),
                "reason": result.get("reason", ""),
            }
        except Exception:
            return self._profile_to_analysis(matched_key, matched_conf)

    def build_industry_context(self, analysis: dict) -> str:
        """把分析结果格式化成注入简历生成 prompt 的段落"""
        if not analysis:
            return ""
        lines = [
            "【行业侧重点分析】",
            f"识别行业：{analysis.get('industry', '')}（置信度：{analysis.get('confidence', '')}）",
        ]
        focus_points = analysis.get("focus_points") or []
        if focus_points:
            lines.append("该行业简历侧重点：")
            lines.extend(f"- {p}" for p in focus_points)
        avoid = analysis.get("avoid") or []
        if avoid:
            lines.append("该行业减分项（生成时避免）：")
            lines.extend(f"- {a}" for a in avoid)
        if analysis.get("tone"):
            lines.append(f"语言风格：{analysis.get('tone', '')}")
        return "\n".join(lines)


industry_service = IndustryService()
