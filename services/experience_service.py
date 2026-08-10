from core.database import db
from core.models import BasicInfo, Education, Internship, Project, Skill, Award, SelfEvaluation

_MODEL_MAP = {
    "education": (Education, "education"),
    "internships": (Internship, "internships"),
    "projects": (Project, "projects"),
    "skills": (Skill, "skills"),
    "awards": (Award, "awards"),
}

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

        ev = self.get_self_evaluation()
        if ev.content:
            sections.append(f"\n自我评价：\n{ev.content}")

        return {
            "text": "\n".join(sections),
            "has_photo": bool(info.photo_path),
            "photo_path": info.photo_path,
        }


experience_service = ExperienceService()
