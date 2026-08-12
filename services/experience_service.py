import re

from core.database import db
from core.models import BasicInfo, Education, Internship, Project, Skill, Award, SelfEvaluation, OtherInfo

_MODEL_MAP = {
    "education": (Education, "education"),
    "internships": (Internship, "internships"),
    "projects": (Project, "projects"),
    "skills": (Skill, "skills"),
    "awards": (Award, "awards"),
    "others": (OtherInfo, "other_info"),
}

# 跨模块移动：各模块的「主字段」（移动时作为目标模块的名称/标题）
_MAIN_FIELD = {
    "education": "school",
    "internships": "company",
    "projects": "name",
    "skills": "name",
    "awards": "name",
    "others": "title",
}

# 跨模块移动：各模块的「内容字段」（源其余字段合并后填入）
_CONTENT_FIELD = {
    "education": "major",
    "internships": "description",
    "projects": "results",
    "skills": "evidence",
    "awards": "level",
    "others": "content",
}

def strip_markdown(text: str) -> str:
    """清除经历文本中的 Markdown 残留标记（**、反引号、行首列表符）"""
    if not text:
        return text
    text = text.replace('**', '')
    text = text.replace('`', '')
    text = re.sub(r'(?m)^\s*[-*+]\s+', '', text)
    return text


class ExperienceService:
    # === Basic Info ===
    def get_basic_info(self) -> BasicInfo:
        with db.connection() as conn:
            row = conn.execute("SELECT * FROM basic_info ORDER BY id DESC LIMIT 1").fetchone()
        return BasicInfo.from_row(row) if row else BasicInfo()

    def save_basic_info(self, data: BasicInfo) -> None:
        d = data.to_dict()
        with db.connection() as conn:
            existing = conn.execute("SELECT id FROM basic_info ORDER BY id DESC LIMIT 1").fetchone()
            if existing:
                conn.execute(
                    "UPDATE basic_info SET name=?, phone=?, email=?, age=?, job_target=?, photo_path=? WHERE id=?",
                    (d["name"], d["phone"], d["email"], d["age"], d["job_target"], d["photo_path"], existing["id"])
                )
            else:
                conn.execute(
                    "INSERT INTO basic_info (name, phone, email, age, job_target, photo_path) VALUES (?, ?, ?, ?, ?, ?)",
                    (d["name"], d["phone"], d["email"], d["age"], d["job_target"], d["photo_path"])
                )

    # === Generic CRUD for list-type tables ===
    def _list(self, model_class, table_name: str) -> list:
        with db.connection() as conn:
            rows = conn.execute(f"SELECT * FROM {table_name} ORDER BY sort_order, id").fetchall()
        return [model_class.from_row(r) for r in rows]

    def _add(self, item, table_name: str) -> int:
        item = self._clean_item(item)
        d = item.to_dict()
        columns = ", ".join(d.keys())
        placeholders = ", ".join(["?"] * len(d))
        with db.connection() as conn:
            cursor = conn.execute(
                f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
                list(d.values())
            )
            item_id = cursor.lastrowid
        return item_id

    def _update(self, item, table_name: str) -> None:
        item = self._clean_item(item)
        d = item.to_dict()
        item_id = d.pop("id") if "id" in d else item.id
        if not item_id:
            return
        set_clause = ", ".join([f"{k}=?" for k in d.keys()])
        with db.connection() as conn:
            conn.execute(
                f"UPDATE {table_name} SET {set_clause} WHERE id=?",
                list(d.values()) + [item_id]
            )

    def _clean_item(self, item):
        """对条目内所有字符串字段做 Markdown 清洗"""
        d = item.to_dict()
        for k, v in d.items():
            if isinstance(v, str):
                d[k] = strip_markdown(v)
        return item.__class__(**d)

    def _delete(self, table_name: str, item_id: int) -> None:
        with db.connection() as conn:
            conn.execute(f"DELETE FROM {table_name} WHERE id=?", (item_id,))

    # === Education ===
    def list_education(self): return self._list(Education, "education")
    def add_education(self, item: Education) -> int: return self._add(item, "education")
    def update_education(self, item: Education): self._update(item, "education")
    def delete_education(self, id: int): self._delete("education", id)

    # === Internships ===
    def list_internships(self): return self._list(Internship, "internships")
    def add_internship(self, item: Internship) -> int: return self._add(item, "internships")
    def update_internship(self, item: Internship): self._update(item, "internships")
    def delete_internship(self, id: int): self._delete("internships", id)

    # === Projects ===
    def list_projects(self): return self._list(Project, "projects")
    def add_project(self, item: Project) -> int: return self._add(item, "projects")
    def update_project(self, item: Project): self._update(item, "projects")
    def delete_project(self, id: int): self._delete("projects", id)

    # === Skills ===
    def list_skills(self): return self._list(Skill, "skills")
    def add_skill(self, item: Skill) -> int: return self._add(item, "skills")
    def update_skill(self, item: Skill): self._update(item, "skills")
    def delete_skill(self, id: int): self._delete("skills", id)

    # === Awards ===
    def list_awards(self): return self._list(Award, "awards")
    def add_award(self, item: Award) -> int: return self._add(item, "awards")
    def update_award(self, item: Award): self._update(item, "awards")
    def delete_award(self, id: int): self._delete("awards", id)

    # === Others ===
    def list_others(self): return self._list(OtherInfo, "other_info")
    def add_other(self, item: OtherInfo) -> int: return self._add(item, "other_info")
    def update_other(self, item: OtherInfo): self._update(item, "other_info")
    def delete_other(self, id: int): self._delete("other_info", id)

    # === Move across modules ===
    def move_item(self, from_module: str, item_id: int, to_module: str) -> int:
        """把一条经历从 from_module 移动到 to_module。

        映射规则：源主字段 → 目标主字段（名称/标题）；源其余非空字段合并进目标内容字段。
        """
        if from_module not in _MODEL_MAP or to_module not in _MODEL_MAP:
            raise ValueError(f"未知模块: {from_module} -> {to_module}")
        if from_module == to_module:
            return item_id
        from_model, from_table = _MODEL_MAP[from_module]
        to_model, to_table = _MODEL_MAP[to_module]
        with db.connection() as conn:
            row = conn.execute(f"SELECT * FROM {from_table} WHERE id=?", (item_id,)).fetchone()
            if row is None:
                raise ValueError("条目不存在")
            src = {k: row[k] for k in row.keys()}
            src_main_field = _MAIN_FIELD.get(from_module)
            src_main = src.get(src_main_field) or next((v for v in src.values() if v), "")
            rest = [str(v) for k, v in src.items()
                    if v and k not in ("id", "sort_order", src_main_field)]
            merged = "；".join(rest)
            target_main = _MAIN_FIELD.get(to_module)
            target_content = _CONTENT_FIELD.get(to_module)
            new_data = {target_main: src_main}
            if target_content:
                new_data[target_content] = merged
            new_item = to_model(**new_data)
            d = new_item.to_dict()
            cols = ", ".join(d.keys())
            ph = ", ".join(["?"] * len(d))
            cur = conn.execute(
                f"INSERT INTO {to_table} ({cols}) VALUES ({ph})", list(d.values()))
            conn.execute(f"DELETE FROM {from_table} WHERE id=?", (item_id,))
            return cur.lastrowid

    # === Self Evaluation ===
    def get_self_evaluation(self) -> SelfEvaluation:
        with db.connection() as conn:
            row = conn.execute("SELECT * FROM self_evaluation ORDER BY id DESC LIMIT 1").fetchone()
        return SelfEvaluation.from_row(row) if row else SelfEvaluation()

    def save_self_evaluation(self, data: SelfEvaluation) -> None:
        d = data.to_dict()
        with db.connection() as conn:
            existing = conn.execute("SELECT id FROM self_evaluation ORDER BY id DESC LIMIT 1").fetchone()
            if existing:
                conn.execute("UPDATE self_evaluation SET content=? WHERE id=?", (d["content"], existing["id"]))
            else:
                conn.execute("INSERT INTO self_evaluation (content) VALUES (?)", (d["content"],))

    # === Reorder ===
    def reorder_items(self, module: str, ids: list[int]) -> None:
        """按 id 顺序重排条目（module 必须为白名单内的模块名）"""
        entry = _MODEL_MAP.get(module)
        if entry is None:
            raise ValueError(f"未知模块: {module}")
        table_name = entry[1]
        with db.connection() as conn:
            for i, item_id in enumerate(ids):
                conn.execute(f"UPDATE {table_name} SET sort_order=? WHERE id=?", (i, item_id))

    # === Export all for prompt ===
    def export_all(self) -> dict:
        """导出所有经历为组织好的文本，用于嵌入 prompt"""
        info = self.get_basic_info()

        sections = []
        if info.name:
            sections.append(f"姓名：{info.name}")
        if info.phone:
            sections.append(f"电话：{info.phone}")
        if info.email:
            sections.append(f"邮箱：{info.email}")
        if info.age:
            sections.append(f"年龄：{info.age}")
        if info.job_target:
            sections.append(f"求职意向：{info.job_target}")
        if info.photo_path:
            sections.append(f"照片：{info.photo_path}")

        edu_list = self.list_education()
        if edu_list:
            sections.append("\n教育背景：")
            for edu in edu_list:
                sections.append(f"{edu.school}，{edu.major}，{edu.degree}，{edu.start_date}-{edu.end_date}")

        intern_list = self.list_internships()
        if intern_list:
            sections.append("\n实习经历：")
            for i, intern in enumerate(intern_list, 1):
                sections.append(f"{i}. {intern.company}，{intern.position}，{intern.start_date}-{intern.end_date}：{intern.description}")

        proj_list = self.list_projects()
        if proj_list:
            sections.append("\n项目经历：")
            for i, proj in enumerate(proj_list, 1):
                sections.append(f"{i}. {proj.name}（{proj.role}）：背景-{proj.background}，动作-{proj.actions}，成果-{proj.results}，技术栈-{proj.tech_stack}")

        skill_list = self.list_skills()
        if skill_list:
            sections.append("\n技能：")
            for skill in skill_list:
                evidence = f"（{skill.evidence}）" if skill.evidence else ""
                sections.append(f"{skill.name}{evidence}")

        award_list = self.list_awards()
        if award_list:
            sections.append("\n获奖情况：")
            for award in award_list:
                sections.append(f"{award.name}，{award.level}，{award.date}")

        other_list = self.list_others()
        if other_list:
            sections.append("\n其他信息：")
            for other in other_list:
                suffix = f"：{other.content}" if other.content else ""
                sections.append(f"{other.title}{suffix}")

        ev = self.get_self_evaluation()
        if ev.content:
            sections.append(f"\n自我评价：\n{ev.content}")

        text = strip_markdown("\n".join(sections))
        return {
            "text": text,
            "has_photo": bool(info.photo_path),
            "photo_path": info.photo_path,
        }


experience_service = ExperienceService()


# ========== 导入分类兜底：证书/资格/等级类误入技能区时自动纠正 ==========

_CERT_KEYWORDS = (
    "资格", "从业", "执业", "执照", "驾照", "驾驶证", "普通话",
    "CET", "雅思", "托福", "IELTS", "TOEFL", "CFA", "CPA", "ACCA",
    "职称", "等级", "四六级",
)


def _is_cert_like(name: str, evidence: str = "") -> bool:
    """判断某条技能条目是否实际是证书/资格/等级类（应归入 other_info）"""
    blob = (name + " " + evidence).upper()
    if any(k in blob for k in _CERT_KEYWORDS):
        return True
    if name.upper().endswith("证"):  # 会计证、教师资格证、证券从业资格证……
        return True
    return False


def sanitize_classification(result: dict) -> dict:
    """AI 解析结果兜底：把误入 skills 的证书/资格/等级类条目移到 others。

    入参为 parse-text 返回的结构（含 skills/others 列表），原地修正并返回。
    纯规则判断，不调用 AI，不抛异常。
    """
    skills = result.get("skills") or []
    others = result.get("others") or []
    kept, moved = [], []
    for s in skills:
        name = (s.get("name") or "").strip()
        evidence = (s.get("evidence") or "").strip()
        level = (s.get("level") or "").strip()
        if not name:
            continue
        if _is_cert_like(name, evidence):
            parts = [p for p in (level, evidence) if p]
            content = "，".join(parts)
            moved.append({"title": name, "content": content})
        else:
            kept.append(s)
    result["skills"] = kept
    result["others"] = list(others) + moved
    return result

