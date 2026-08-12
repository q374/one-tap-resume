# -*- coding: utf-8 -*-
"""跨模块移动 + 技能字段严格限定测试"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from core.models import Skill, OtherInfo
from services.experience_service import experience_service


def test_move_skill_to_others(test_db):
    """技能里的证书 → 其他信息：主字段成 title，其余字段合并进 content"""
    sid = experience_service.add_skill(Skill(name="CET-6 英语六级", level="精通", evidence="2023年通过"))
    new_id = experience_service.move_item("skills", sid, "others")
    assert len(experience_service.list_skills()) == 0
    others = experience_service.list_others()
    assert len(others) == 1
    assert others[0].title == "CET-6 英语六级"
    assert "2023年通过" in others[0].content
    assert new_id == others[0].id


def test_move_others_to_skill(test_db):
    """其他信息里的技能 → 技能：title 成 name，content 进 evidence"""
    oid = experience_service.add_other(OtherInfo(title="Python", content="数据清洗与分析"))
    experience_service.move_item("others", oid, "skills")
    assert len(experience_service.list_others()) == 0
    skills = experience_service.list_skills()
    assert len(skills) == 1
    assert skills[0].name == "Python"
    assert skills[0].evidence == "数据清洗与分析"


def test_move_project_to_others(test_db):
    """项目 → 其他信息：name 进 title，背景/动作/成果合并"""
    from core.models import Project
    pid = experience_service.add_project(Project(name="用户留存分析", role="负责人", results="留存提升5个百分点"))
    experience_service.move_item("projects", pid, "others")
    others = experience_service.list_others()
    assert others[0].title == "用户留存分析"
    assert "负责人" in others[0].content
    assert "留存提升5个百分点" in others[0].content


def test_move_invalid(test_db):
    with pytest.raises(ValueError):
        experience_service.move_item("unknown", 1, "others")
    with pytest.raises(ValueError):
        experience_service.move_item("skills", 99999, "others")


def test_api_move(test_db):
    from fastapi.testclient import TestClient
    from app import app
    with TestClient(app) as client:
        client.post("/api/experiences/skills", json={"name": "普通话二级甲等", "level": "二甲"})
        r = client.get("/api/experiences/skills")
        sid = r.json()[0]["id"]
        rr = client.post("/api/experiences/move", json={"from_module": "skills", "item_id": sid, "to_module": "others"})
        assert rr.status_code == 200, rr.text
        r = client.get("/api/experiences/skills")
        assert len(r.json()) == 0
        r = client.get("/api/experiences/others")
        assert r.json()[0]["title"] == "普通话二级甲等"
        # 未知模块 → 400
        rr = client.post("/api/experiences/move", json={"from_module": "nope", "item_id": 1, "to_module": "others"})
        assert rr.status_code == 400


def test_parse_prompt_strict_skill_rule():
    from prompts.experience_parse import EXPERIENCE_PARSE_PROMPT
    assert "技能字段严格限定" in EXPERIENCE_PARSE_PROMPT
    assert "CET-4/6、雅思、托福、普通话等级" in EXPERIENCE_PARSE_PROMPT
    assert "放入 skills" in EXPERIENCE_PARSE_PROMPT
