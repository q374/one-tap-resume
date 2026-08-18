"""经历-岗位匹配度功能测试"""
from services.match_service import compute_match, build_match_context

EXP_HIGH = """姓名：张三
Python后端开发工程师
教育背景：清华大学 计算机科学与技术 本科
项目：用Python FastAPI开发电商订单系统，MySQL Redis Docker，微服务架构，高并发优化
技能：Python、FastAPI、MySQL、Redis、Docker"""

JD_HIGH = "Python后端开发工程师，要求本科，熟悉Python FastAPI MySQL Redis Docker，有微服务经验"

EXP_LOW = """姓名：李四
新媒体运营
公众号推文写作，短视频剪辑，活动策划，粉丝增长，社群运营"""
JD_LOW = "数据分析师，要求SQL Python pandas Tableau，AB测试，归因分析"


def test_high_match():
    r = compute_match(EXP_HIGH, JD_HIGH)
    assert r["level"] == "high"
    assert r["score"] >= 60
    assert r["total"] > 0


def test_low_match():
    r = compute_match(EXP_LOW, JD_LOW)
    assert r["level"] == "low"
    assert r["score"] < 35
    assert r["missing_keywords"]


def test_medium_match():
    r = compute_match(EXP_HIGH + " 数据分析 用户增长", "数据分析师，熟悉Python SQL，用户增长")
    assert r["level"] in ("medium", "high")


def test_no_jd_returns_unknown():
    r = compute_match(EXP_HIGH, "")
    assert r["level"] == "unknown"
    assert r["score"] is None


def test_no_keywords_returns_unknown():
    r = compute_match(EXP_HIGH, "随便一段没有关键词的话")
    assert r["level"] == "unknown"


def test_match_context_high_is_empty():
    r = compute_match(EXP_HIGH, JD_HIGH)
    assert build_match_context(r) == ""


def test_match_context_low_is_not_empty():
    r = compute_match(EXP_LOW, JD_LOW)
    ctx = build_match_context(r)
    assert "可迁移" in ctx
    assert "不编造" in ctx or "如实" in ctx
    assert "覆盖缺失词" in ctx or "未直接覆盖" in ctx


def test_match_missing_keywords_limited():
    r = compute_match(EXP_LOW, "SQL Python pandas numpy Tableau AB测试 归因分析 数据仓库 指标体系 埋点 可视化")
    assert len(r["missing_keywords"]) <= 12
