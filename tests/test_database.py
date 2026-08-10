from core.database import db
from core.models import BasicInfo, Education, Project, Skill

def test_database_init():
    db.init_db()
    conn = db.get_connection()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = [t['name'] for t in tables]
    assert 'basic_info' in table_names
    assert 'education' in table_names
    assert 'internships' in table_names
    assert 'projects' in table_names
    assert 'skills' in table_names
    assert 'awards' in table_names
    assert 'self_evaluation' in table_names
    assert 'user_templates' in table_names
    assert 'resume_records' in table_names
    conn.close()

def test_basic_info_crud(test_db):
    conn = test_db.get_connection()
    conn.execute("INSERT INTO basic_info (name, phone) VALUES (?, ?)", ("张三", "13800138000"))
    conn.commit()

    row = conn.execute("SELECT * FROM basic_info WHERE name=?", ("张三",)).fetchone()
    info = BasicInfo.from_row(row)
    assert info.name == "张三"
    assert info.phone == "13800138000"

    info_dict = info.to_dict()
    assert "name" in info_dict
    assert info_dict["id"] == row["id"]  # to_dict 应包含 id，供前端使用

    conn.close()

def test_project_crud(test_db):
    conn = test_db.get_connection()
    for i in range(3):
        conn.execute(
            "INSERT INTO projects (name, role, sort_order) VALUES (?, ?, ?)",
            (f"项目{i}", f"角色{i}", i)
        )
    conn.commit()

    rows = conn.execute("SELECT * FROM projects ORDER BY sort_order").fetchall()
    projects = [Project.from_row(r) for r in rows]
    assert len(projects) == 3
    assert projects[0].name == "项目0"
    assert projects[2].name == "项目2"

    conn.close()
