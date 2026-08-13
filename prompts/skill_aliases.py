"""技能别名映射表 — 解决「JD 用中文行业术语、经历库用英文工具名」导致的字面匹配失败

核心痛点：用户录的是 ChatGPT / Coze / Prompt，JD 写的是"大模型 / 智能体 / 提示词"，
纯字符串包含匹配会判"不命中"。本模块提供三层能力：
1. expand_keyword(kw)：把单个关键词展开成等价词簇（含自身），跨语言/跨写法命中
2. annotate_skill_name(name)：给技能名补中文行业叫法（ChatGPT → 大模型应用（ChatGPT））
3. extract_jd_keywords(jd_text)：统一提取 JD 关键词（行业知识库 + 英文技术词 + 噪音过滤），
   match_service 与 diagnosis_service 共用，保证匹配度与诊断口径一致
4. alias_hit(text, alias)：别名匹配（短英文词用词边界，避免 'ai' 误命中 'email'）
"""
import re

from prompts.industry_profiles import INDUSTRY_PROFILES

# 等价技能词簇：cn=中文行业叫法；names=该技能的所有常见写法（中英混排）
SKILL_ALIAS_CLUSTERS = [
    {
        "cn": "大模型应用",
        "names": {
            "大模型", "大语言模型", "llm", "chatgpt", "claude", "coze", "dify",
            "kimi", "文心一言", "通义千问", "豆包", "deepseek", "gpt", "glm",
            "智能体", "agent", "rag", "对话式ai",
        },
    },
    {
        "cn": "提示词工程",
        "names": {"提示词", "提示词工程", "prompt", "prompt engineering", "prompt优化"},
    },
    {
        "cn": "AI绘画",
        "names": {"ai绘画", "aigc绘画", "midjourney", "stable diffusion", "stablediffusion"},
    },
    {
        "cn": "AI视频生成",
        "names": {"ai视频", "ai视频生成", "视频生成", "runway", "runwayml", "可灵", "sora", "veo", "pika", "数字人", "aigc视频"},
    },
    {
        "cn": "AIGC内容创作",
        "names": {"aigc", "ai生成", "ai创作", "ai内容生成", "人工智能生成", "aigc内容", "aigc创作"},
    },
    {
        "cn": "内容运营",
        "names": {"内容运营", "新媒体运营", "内容营销", "自媒体运营"},
    },
    {
        "cn": "用户增长",
        "names": {"用户增长", "增长运营", "增长策略", "增长"},
    },
    {
        "cn": "数据分析",
        "names": {"数据分析", "数据可视化", "数据洞察", "报表分析", "数据报表"},
    },
    {
        "cn": "人工智能",
        "names": {"人工智能", "ai"},
    },
    {
        "cn": "自媒体运营",
        "names": {"自媒体", "新媒体", "公众号", "小红书", "抖音", "视频号", "短视频运营"},
    },
]

# 泛化噪音词：作为"简历须命中的关键词"没有区分度（如"提示词工程"会被误提取出"工程"）
NOISE_KEYWORDS = {
    "工程", "策划", "设计", "管理", "开发", "运营", "软件", "视频",
    "内容", "流量", "增长", "数据", "产品", "市场", "技术", "分析",
    "平台", "项目", "经验", "相关", "优先", "能力", "工作", "岗位",
    "服务", "系统", "应用", "支持",
}

_STOP_WORDS = {
    "and", "the", "for", "with", "you", "your", "will", "have", "has",
    "are", "not", "that", "this", "our", "all", "can", "who", "what",
    "how", "why", "but", "from", "into", "about", "over", "also", "was",
    "等等", "以及", "要求", "任职", "岗位", "职位", "工作", "负责", "熟悉",
    "优先", "经验", "能力", "相关", "以上", "我们", "进行", "能够", "具备",
}


def _cluster_of(kw: str):
    """返回关键词所在的簇（字典），不在任何簇返回 None"""
    kw_l = kw.lower()
    for cluster in SKILL_ALIAS_CLUSTERS:
        if kw_l in {n.lower() for n in cluster["names"]}:
            return cluster
    return None


def expand_keyword(kw: str) -> set:
    """把单个关键词展开成等价词簇（含自身），用于跨语言/跨写法命中"""
    kw_l = kw.lower()
    cluster = _cluster_of(kw)
    if cluster is None:
        return {kw_l}
    return {n.lower() for n in cluster["names"]}


def alias_hit(text_lower: str, alias: str) -> bool:
    """别名匹配：短英文词用词边界（避免 'ai' 误命中 'email'），其余用子串"""
    alias = alias.lower().strip()
    if not alias:
        return False
    if alias.isascii() and len(alias) < 4:
        return re.search(
            r'(?<![a-z0-9])' + re.escape(alias) + r'(?![a-z0-9])',
            text_lower,
        ) is not None
    return alias in text_lower


def annotate_skill_name(name: str) -> str:
    """技能名补中文行业叫法：ChatGPT → 大模型应用（ChatGPT）；中文名/无簇不补"""
    if not name:
        return name
    n = name.strip()
    if not n.isascii():
        return n
    n_low = n.lower()
    for cluster in SKILL_ALIAS_CLUSTERS:
        if n_low in {x.lower() for x in cluster["names"]}:
            return f"{cluster['cn']}（{n}）"
    return n


def extract_jd_keywords(jd_text: str) -> list:
    """统一提取 JD 关键词：行业知识库关键词（命中JD且非噪音）+ 英文技术词（去停用词）

    match_service 与 diagnosis_service 共用，保证匹配度与诊断口径一致。
    """
    jd_lower = jd_text.lower()
    keywords = set()
    for profile in INDUSTRY_PROFILES.values():
        for kw in profile.get("keywords", []):
            if not kw:
                continue
            kl = kw.lower()
            if kl in NOISE_KEYWORDS:
                continue
            if kl in jd_lower:
                keywords.add(kl)
    for word in re.findall(r"[a-zA-Z][a-zA-Z0-9+#.]{2,}", jd_text):
        if word.lower() not in _STOP_WORDS:
            keywords.add(word.lower())
    return sorted(keywords)
