"""技能别名映射（JD关键词命中率修复）功能测试

覆盖：技能中英双写、别名展开、噪音词过滤、跨语言匹配、诊断覆盖率口径
"""
from prompts.skill_aliases import (
    extract_jd_keywords, expand_keyword, annotate_skill_name, alias_hit,
)
from services.match_service import compute_match
from services.diagnosis_service import _compute_objective


def test_annotate_skill_name_english_tool():
    """英文工具名补中文行业叫法"""
    assert annotate_skill_name("ChatGPT") == "大模型应用（ChatGPT）"
    assert annotate_skill_name("Prompt") == "提示词工程（Prompt）"
    assert annotate_skill_name("Midjourney") == "AI绘画（Midjourney）"
    assert annotate_skill_name("Runway") == "AI视频生成（Runway）"


def test_annotate_skill_name_keep_common():
    """常用技术名与中文名不画蛇添足"""
    assert annotate_skill_name("SQL") == "SQL"
    assert annotate_skill_name("Python") == "Python"
    assert annotate_skill_name("数据分析") == "数据分析"
    assert annotate_skill_name("内容运营") == "内容运营"


def test_expand_keyword_cross_language():
    """中文行业词展开出英文工具名，反之亦然"""
    assert "chatgpt" in expand_keyword("大模型")
    assert "大模型" in expand_keyword("chatgpt")
    assert "prompt" in expand_keyword("提示词")
    assert "提示词" in expand_keyword("prompt")
    assert expand_keyword("sql") == {"sql"}


def test_alias_hit_word_boundary_for_short_english():
    """短英文词用词边界，避免 ai 误命中 email"""
    assert alias_hit("熟悉ai绘画", "ai") is True
    assert alias_hit("email 处理", "ai") is False
    assert alias_hit("会用大模型", "大模型") is True


def test_extract_jd_keywords_no_noise():
    """提示词工程不应误提取出泛化噪音词"工程"""
    kw = extract_jd_keywords("岗位要求：掌握提示词工程，负责内容策划与增长运营")
    assert "工程" not in kw
    assert "策划" not in kw
    assert "提示词" in kw


def test_match_chinese_jd_vs_english_skills():
    """核心痛点：中文JD vs 英文技能库，之前40分，现在应high"""
    jd = "熟悉大模型应用开发，擅长智能体搭建与提示词优化，做过AI内容自动化生成项目，有增长运营经验"
    exp = "技能：\nChatGPT\nCoze\nDify\nPrompt\nAIGC\n互联网\n人工智能\n内容增长\n数据分析"
    r = compute_match(exp, jd)
    assert r["level"] == "high"
    assert r["score"] >= 60
    assert "大模型" in r["matched"]
    assert "提示词" in r["matched"]
    assert "智能体" in r["matched"]


def test_match_reverse_bridge():
    """反向桥接：JD写ChatGPT，经历库写大模型，同样命中"""
    r = compute_match("技能：\n大模型\n智能体\n提示词工程", "熟悉ChatGPT、Dify等大模型工具，会提示词优化")
    assert r["score"] >= 80
    assert "chatgpt" in r["matched"]
    assert "dify" in r["matched"]


def test_diagnosis_coverage_uses_alias():
    """诊断JD覆盖率：简历双写后，中文JD关键词可命中"""
    resume = (
        "<html><body><p>负责AI内容自动化生成项目，"
        "用大模型应用（ChatGPT/Coze/Dify）搭建工作流</p>"
        "<p>技能：<strong>大模型应用</strong>（ChatGPT/Coze/Dify） · "
        "<strong>提示词工程</strong>（Prompt）</p></body></html>"
    )
    jd = "熟悉大模型应用开发，擅长智能体搭建与提示词优化，做过AI内容自动化生成项目"
    obj = _compute_objective(resume, jd)
    cov = [c for c in obj["checks"] if c["key"] == "jd_coverage"][0]
    assert cov["pass"] is True
    assert "4/4" in cov["detail"]

def test_export_all_annotates_english_skill(test_db):
    """经历库技能导出自动补中文叫法，已有数据无需重新录入"""
    from core.models import Skill
    from services.experience_service import experience_service

    experience_service.add_skill(Skill(name="ChatGPT", category="工具"))
    experience_service.add_skill(Skill(name="SQL", category="编程语言"))
    exported = experience_service.export_all()
    text = exported["text"]
    assert "大模型应用（ChatGPT）" in text
    assert "SQL" in text
    assert "技能：" in text

