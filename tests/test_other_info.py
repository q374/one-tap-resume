# -*- coding: utf-8 -*-
"""「其他信息」模块测试：表结构 / 服务 CRUD / export_all / API 端点 / 导入去重"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.models import OtherInfo
from services.experience_service import experience_service


def test_other_info_table_exists(test_db):
    conn = test_db.get_connection()
    tables = [t["name"] for t in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert "other_info" in tables
    conn.close()


def test_other_info_service_crud(test_db):
    # add
    oid = experience_service.add_other(OtherInfo(title="CET-6", content="2023年通过"))
    items = experience_service.list_others()
    assert len(items) == 1
    assert items[0].title == "CET-6"
    assert items[0].content == "2023年通过"
    # update
    experience_service.update_other(OtherInfo(id=oid, title="CET-6", content="阅读248/写作212"))
    items = experience_service.list_others()
    assert items[0].content == "阅读248/写作212"
    # delete
    experience_service.delete_other(oid)
    assert len(experience_service.list_others()) == 0


def test_export_all_contains_others(test_db):
    experience_service.add_other(OtherInfo(title="普通话二甲", content="2024年通过"))
    text = experience_service.export_all()["text"]
    assert "其他信息：" in text
    assert "普通话二甲：2024年通过" in text


def test_api_others_endpoints(test_db):
    from fastapi.testclient import TestClient
    from app import app
    with TestClient(app) as client:
        # add
        r = client.post("/api/experiences/others", json={"title": "驾照C1", "content": "2021年取得"})
        assert r.status_code == 200, r.text
        oid = r.json()["id"]
        # all 接口含 others
        r = client.get("/api/experiences/all")
        assert r.status_code == 200
        data = r.json()
        assert "others" in data
        assert any(o["title"] == "驾照C1" for o in data["others"])
        # 通用列表端点
        r = client.get("/api/experiences/others")
        assert r.status_code == 200
        assert len(r.json()) == 1
        # update
        r = client.put(f"/api/experiences/others/{oid}", json={"title": "驾照C1", "content": "2021年取得，手动挡"})
        assert r.status_code == 200, r.text
        r = client.get("/api/experiences/others")
        assert r.json()[0]["content"] == "2021年取得，手动挡"
        # delete
        r = client.delete(f"/api/experiences/others/{oid}")
        assert r.status_code == 200
        r = client.get("/api/experiences/others")
        assert len(r.json()) == 0
        # clear-all 清空列表包含 others
        client.post("/api/experiences/others", json={"title": "x", "content": "y"})
        r = client.post("/api/experiences/clear-all")
        assert r.status_code == 200
        assert "other_info" in r.json()["cleared"]
        r = client.get("/api/experiences/others")
        assert len(r.json()) == 0


def test_import_check_dedup_others(test_db):
    """import-check 对 others 模块做本地精确去重"""
    from fastapi.testclient import TestClient
    from app import app
    with TestClient(app) as client:
        client.post("/api/experiences/others", json={"title": "CET-6", "content": "2023年通过"})
        r = client.post("/api/experiences/import-check", json={"items": {
            "others": [{"title": "CET-6", "content": "2023年通过"}]
        }})
        assert r.status_code == 200, r.text
        dup = r.json()
        assert dup["duplicates"], "应检测到完全重复的 others 条目"
        assert any(d["module"] == "others" for d in dup["duplicates"])
