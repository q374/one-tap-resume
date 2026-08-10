"""简历质量诊断功能测试"""
import asyncio
from unittest.mock import patch, AsyncMock

import pytest

from services.diagnosis_service import diagnosis_service, _compute_objective

GOOD_HTML = """<html><head></head><body><h1>陈默</h1><p>Python后端开发工程师</p>
<p>本科</p><p>主导订单模块，支付成功率99.2%，响应180ms，服务800+用户，日均120单</p>
<p>Python FastAPI MySQL Redis Docker</p></body></html>"""

BAD_HTML = """<html><head></head><body><h1>李某</h1><p>工程师</p>
<p>具备良好的沟通能力，团队协作，抗压能力强，非常积极主动，赋能业务，沉淀经验</p></body></html>"""

JD = "Python后端开发工程师，要求本科及以上，熟悉Python FastAPI MySQL Redis，有Docker经验"


# ---------- 客观分（代码算，AI无法干预） ----------

def test_objective_good_resume_high_score():
    r = _compute_objective(GOOD_HTML, JD)
    assert r["score"] >= 80


def test_objective_bad_resume_low_score():
    r = _compute_objective(BAD_HTML, JD)
    assert r["score"] < 60


def test_objective_score_clamped_to_100():
    html = GOOD_HTML + "<p>" + "非常" * 500 + "</p>"
    r = _compute_objective(html, JD)
    assert 0 <= r["score"] <= 100


def test_objective_has_five_checks():
    r = _compute_objective(GOOD_HTML, JD)
    assert len(r["checks"]) == 5
    labels = [c["label"] for c in r["checks"]]
    assert "JD关键词覆盖率" in labels
    assert "量化成果数量" in labels


def test_objective_quantified_detects_variants():
    html = '<html><body><p>效率提升40%，服务2000+用户，覆盖5个模块，QPS 1000</p></body></html>'
    r = _compute_objective(html, "")
    quantified = [c for c in r["checks"] if c["key"] == "quantified"][0]
    assert quantified["pass"] is True


# ---------- 诊断组装（客观分 + AI找茬 + 边界说明） ----------

def test_diagnose_ai_success():
    fake = {"suggestions": [{"area": "项目经历", "issue": "缺量化", "fix": "加数字"}]}
    with patch("services.diagnosis_service.call_deepseek_json", new=AsyncMock(return_value=fake)):
        result = asyncio.run(diagnosis_service.diagnose(GOOD_HTML, JD))
        assert result["objective"]["score"] >= 80
        assert result["ai_findings"]["suggestions"][0]["fix"] == "加数字"
        assert "不承诺" in result["disclaimer"]


def test_diagnose_ai_failure_falls_back():
    with patch("services.diagnosis_service.call_deepseek_json",
               new=AsyncMock(side_effect=Exception("boom"))):
        result = asyncio.run(diagnosis_service.diagnose(GOOD_HTML, JD))
        assert result["objective"]["score"] >= 80
        assert "error" in result["ai_findings"]
