"""生成链路集成匹配度测试（mock AI，不消耗真实调用）"""
import asyncio
from unittest.mock import patch, AsyncMock

from services.resume_service import resume_service

TEMPLATE = '<html><body><h1>{{姓名}}</h1><p>{{项目经历}}</p></body></html>'
MOCK_HTML = '<html><body><h1>李四</h1><p>新媒体运营经历</p></body></html>'

EXP_LOW = """姓名：李四
新媒体运营
公众号推文写作，短视频剪辑，活动策划，粉丝增长"""
JD_LOW = "数据分析师，要求SQL Python pandas Tableau AB测试 归因分析"

EXP_HIGH = """姓名：张三
Python后端开发
项目：用Python FastAPI开发订单系统，MySQL Redis Docker"""
JD_HIGH = "Python后端开发工程师，熟悉Python FastAPI MySQL Redis Docker"


def _run_generate(exp, jd):
    async def _inner():
        with patch("services.resume_service.call_deepseek", new=AsyncMock(return_value=MOCK_HTML)) as m_ai, \
              patch("services.resume_service.clean_html_response", side_effect=lambda x: x):
            result = await resume_service.generate(
                TEMPLATE, exp, jd, "",
                industry_override="综合/其他",
            )
            return result, m_ai
    return asyncio.run(_inner())


def test_low_match_returns_info_and_injects_context():
    result, m_ai = _run_generate(EXP_LOW, JD_LOW)
    assert result["match_info"]["level"] == "low"
    assert result["match_info"]["missing_keywords"]
    prompt = m_ai.call_args[0][0]
    assert "匹配增强模式" in prompt
    assert "可迁移改写" in prompt


def test_high_match_no_enhancement():
    result, m_ai = _run_generate(EXP_HIGH, JD_HIGH)
    assert result["match_info"]["level"] in ("high", "medium")
    prompt = m_ai.call_args[0][0]
    # 高匹配不应注入增强指令
    assert "匹配增强模式" not in prompt or "（匹配度正常" in prompt
