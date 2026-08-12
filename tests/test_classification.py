# -*- coding: utf-8 -*-
"""导入分类兜底测试：证书/资格/等级类误入技能区时自动移到其他信息"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.experience_service import sanitize_classification


def test_sanitize_moves_certs_out_of_skills():
    result = {
        "skills": [
            {"name": "Python", "level": "熟练", "evidence": "pandas/numpy"},
            {"name": "SQL", "level": "", "evidence": "千万级数据"},
            {"name": "CFA", "level": "三级", "evidence": "2024年通过"},
            {"name": "证券从业资格", "level": "", "evidence": "2023年取得"},
            {"name": "普通话二甲", "level": "", "evidence": "2021年取得"},
            {"name": "C1驾照", "level": "", "evidence": ""},
        ],
        "others": [{"title": "CET-6", "content": "2023年通过"}],
    }
    out = sanitize_classification(result)
    names = [s["name"] for s in out["skills"]]
    assert names == ["Python", "SQL"], names
    titles = [o["title"] for o in out["others"]]
    assert "CFA" in titles and "证券从业资格" in titles
    assert "普通话二甲" in titles and "C1驾照" in titles
    assert "CET-6" in titles  # 原有 other 保留
    # CFA 的 content 携带原 evidence/level
    cfa = next(o for o in out["others"] if o["title"] == "CFA")
    assert cfa["content"] == "三级，2024年通过"


def test_sanitize_keeps_normal_skills():
    result = {
        "skills": [
            {"name": "Python", "evidence": "数据分析"},
            {"name": "Excel", "evidence": "数据透视表"},
            {"name": "Tableau", "evidence": "可视化看板"},
            {"name": "Git/GitHub", "evidence": "开源协作"},
        ],
        "others": [],
    }
    out = sanitize_classification(result)
    assert len(out["skills"]) == 4
    assert len(out["others"]) == 0


def test_sanitize_handles_missing_fields():
    result = {"skills": None, "others": None}
    out = sanitize_classification(result)
    assert out["skills"] == []
    assert out["others"] == []
    result2 = {}
    out2 = sanitize_classification(result2)
    assert out2["skills"] == [] and out2["others"] == []


def test_parse_text_api_applies_sanitize(monkeypatch):
    """parse-text 接口：AI 返回误分类结果也会被后端兜底修正"""
    from fastapi.testclient import TestClient
    from app import app

    async def fake_call_deepseek_json(prompt, **kw):
        return {
            "skills": [
                {"name": "Python", "level": "", "evidence": ""},
                {"name": "会计证", "level": "", "evidence": "初级"},
                {"name": "基金从业资格", "level": "", "evidence": ""},
            ],
            "others": [],
        }

    monkeypatch.setattr("app.call_deepseek_json", fake_call_deepseek_json)
    with TestClient(app) as client:
        r = client.post("/api/experiences/parse-text", json={"text": "测试文本"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert [s["name"] for s in data["skills"]] == ["Python"]
        titles = [o["title"] for o in data["others"]]
        assert "会计证" in titles and "基金从业资格" in titles
