"""行业侧重点分析功能测试"""
import asyncio
from unittest.mock import patch, AsyncMock

import pytest

from prompts.industry_profiles import FALLBACK_INDUSTRY
from prompts.resume_generation import build_resume_prompt
from services.template_filler import build_filler_prompt
from services.industry_service import industry_service
from services.resume_service import resume_service


def _run(coro):
    return asyncio.run(coro)


# ---------- 1. 关键词初筛 ----------

@pytest.mark.parametrize("expected, jd", [
    ("互联网/科技", "Python后端开发工程师，负责微服务架构、高并发系统、MySQL Redis，熟悉Docker K8s"),
    ("金融/银行/证券", "银行对公客户经理，负责信贷风控、合规审查，熟悉金融市场和风险管理"),
    ("快消/消费品/零售", "快消品牌市场专员，负责渠道销售、电商运营、品牌营销和门店促销"),
    ("制造/汽车/工业", "质量工程师，负责汽车零部件产线良率提升、精益生产、六西格玛改进"),
    ("医疗/医药/生物", "临床研究专员，负责药品注册、GMP规范、医疗器械研发"),
])
def test_keyword_matching(expected, jd):
    key, score, conf = industry_service.match_industry_keyword(jd)
    assert key == expected
    assert score >= 1
    assert conf == "high"


def test_keyword_matching_unknown_returns_fallback():
    key, score, conf = industry_service.match_industry_keyword("不限专业，招应届生，要求吃苦耐劳")
    assert key == FALLBACK_INDUSTRY
    assert score == 0
    assert conf == "low"


# ---------- 2. AI 精析 ----------

def test_analyze_with_override_skips_ai():
    """手动指定行业：直接返回内置 profile，不调 AI"""
    with patch("services.industry_service.call_deepseek_json", new=AsyncMock()) as mock_ai:
        result = _run(industry_service.analyze("任意JD", industry_override="互联网/科技"))
        assert result["industry"] == "互联网/科技"
        assert result["confidence"] == "user"
        assert result["focus_points"]
        mock_ai.assert_not_awaited()


def test_analyze_ai_success():
    """AI 正常返回 JSON"""
    fake = {
        "industry": "互联网/科技", "confidence": "high",
        "focus_points": ["项目必须有量化成果"], "avoid": ["堆砌技能"],
        "tone": "简洁", "reason": "JD含大量技术栈",
    }
    with patch("services.industry_service.call_deepseek_json", new=AsyncMock(return_value=fake)):
        result = _run(industry_service.analyze("Python后端 JD"))
        assert result["industry"] == "互联网/科技"
        assert "项目必须有量化成果" in result["focus_points"]
        assert result["reason"] == "JD含大量技术栈"


def test_analyze_ai_unknown_industry_falls_back():
    """AI 返回未知行业名 → 用初筛结果兜底"""
    fake = {"industry": "宇宙级行业", "reason": "瞎猜的"}
    with patch("services.industry_service.call_deepseek_json", new=AsyncMock(return_value=fake)):
        result = _run(industry_service.analyze("Python后端 JD"))
        assert result["industry"] == "互联网/科技"
        assert result["confidence"] == "medium"


def test_analyze_ai_failure_falls_back():
    """AI 抛异常 → 内置 profile 兜底，不抛异常"""
    with patch("services.industry_service.call_deepseek_json",
               new=AsyncMock(side_effect=Exception("API down"))):
        result = _run(industry_service.analyze("Python后端 JD"))
        assert result["industry"] == "互联网/科技"
        assert result["focus_points"]
        assert result["avoid"]


def test_analyze_empty_jd():
    result = _run(industry_service.analyze("   "))
    assert result["industry"] == FALLBACK_INDUSTRY


# ---------- 3. 注入验证 ----------

def test_build_resume_prompt_includes_industry_context():
    ctx = industry_service.build_industry_context({
        "industry": "互联网/科技", "confidence": "high",
        "focus_points": ["项目必须量化"], "avoid": ["堆砌技能"], "tone": "简洁",
    })
    prompt = build_resume_prompt(
        "<html>{{name}}</html>", "经历", "JD", "年龄", "照片",
        has_placeholders=True, industry_context=ctx,
    )
    assert "【行业侧重点分析】" in prompt
    assert "项目必须量化" in prompt
    assert "行业侧重点遵循" in prompt


def test_custom_template_prompt_includes_industry_context():
    ctx = industry_service.build_industry_context({
        "industry": "金融/银行/证券", "confidence": "high",
        "focus_points": ["证书优先"], "avoid": [], "tone": "严谨",
    })
    prompt = build_filler_prompt(["教育背景"], "经历", "JD", industry_context=ctx)
    assert "【行业侧重点分析】" in prompt
    assert "证书优先" in prompt


# ---------- 4. 生成流程不中断 ----------

def test_generate_not_blocked_on_industry_failure():
    """行业分析失败不影响简历生成（降级铁律）"""
    tpl = "<html><body><h1>{{name}}</h1><p>{{技能列表}}</p></body></html>"
    with patch.object(industry_service, "analyze", new=AsyncMock(side_effect=Exception("boom"))), \
         patch("services.resume_service.call_deepseek",
               new=AsyncMock(return_value="<html><body><h1>张三</h1></body></html>")):
        result = _run(resume_service.generate(tpl, "张三 项目经历", "Python后端 JD"))
        assert result.get("html")
        assert result.get("industry") == ""


def test_generate_includes_industry_name():
    """正常路径：生成结果带 industry 字段"""
    tpl = "<html><body><h1>{{name}}</h1><p>{{技能列表}}</p></body></html>"
    fake_analysis = {
        "industry": "互联网/科技", "confidence": "high",
        "focus_points": ["项目必须量化"], "avoid": [], "tone": "简洁", "reason": "测试",
    }
    with patch.object(industry_service, "analyze", new=AsyncMock(return_value=fake_analysis)), \
         patch("services.resume_service.call_deepseek",
               new=AsyncMock(return_value="<html><body><h1>张三</h1></body></html>")):
        result = _run(resume_service.generate(tpl, "张三 项目经历", "Python后端 JD"))
        assert result.get("industry") == "互联网/科技"
