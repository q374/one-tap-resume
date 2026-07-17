import os
from core.database import db
from core.deepseek_client import call_deepseek_json
from prompts.template_parse import build_template_parse_prompt
from config import TEMPLATES_DIR
from datetime import datetime

class TemplateService:
    BUILTIN_TEMPLATES = {
        "default": "default.html",
        "education": "education-first.html",
    }

    def get_template_html(self, template_type: str) -> str:
        if template_type in self.BUILTIN_TEMPLATES:
            path = os.path.join(TEMPLATES_DIR, self.BUILTIN_TEMPLATES[template_type])
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()

        try:
            tid = int(template_type)
            conn = db.get_connection()
            row = conn.execute("SELECT * FROM user_templates WHERE id=?", (tid,)).fetchone()
            conn.close()
            if row:
                return row["html_content"]
        except (ValueError, TypeError):
            pass

        path = os.path.join(TEMPLATES_DIR, "default.html")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def list_templates(self) -> list[dict]:
        templates = [
            {"id": "default", "name": "默认模板（项目经历优先）", "is_builtin": True},
            {"id": "education", "name": "教育背景前置模板", "is_builtin": True},
        ]
        conn = db.get_connection()
        rows = conn.execute("SELECT id, name, is_builtin, created_at FROM user_templates ORDER BY id").fetchall()
        conn.close()
        for row in rows:
            templates.append({
                "id": str(row["id"]),
                "name": row["name"],
                "is_builtin": bool(row["is_builtin"]),
                "created_at": row["created_at"],
            })
        return templates

    async def upload_template(self, name: str, html_content: str) -> dict:
        parse_result = await self.parse_template(html_content)
        mapping_json = str(parse_result)

        conn = db.get_connection()
        cursor = conn.execute(
            """INSERT INTO user_templates (name, html_content, mapping_json, is_builtin, created_at)
               VALUES (?, ?, ?, 0, ?)""",
            (name, html_content, mapping_json, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        tid = cursor.lastrowid
        conn.close()

        return {"id": tid, "name": name, "parse_result": parse_result}

    async def parse_template(self, html_content: str) -> dict:
        prompt = build_template_parse_prompt(html_content)
        try:
            return await call_deepseek_json(prompt)
        except Exception:
            return {"sections": [], "has_print_style": False, "has_photo_area": False,
                    "template_name_suggestion": "", "error": "AI解析失败"}

    def delete_template(self, template_id: int) -> None:
        conn = db.get_connection()
        conn.execute("DELETE FROM user_templates WHERE id=? AND is_builtin=0", (template_id,))
        conn.commit()
        conn.close()


template_service = TemplateService()
