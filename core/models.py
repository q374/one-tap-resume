from dataclasses import dataclass, field, asdict
from typing import Optional
import json

@dataclass
class BasicInfo:
    id: Optional[int] = None
    name: str = ""
    phone: str = ""
    email: str = ""
    age: str = ""
    job_target: str = ""
    photo_path: str = ""

    def to_dict(self):
        d = asdict(self)
        d.pop("id", None)
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k != 'id'})

@dataclass
class Education:
    id: Optional[int] = None
    school: str = ""
    major: str = ""
    degree: str = "本科"
    start_date: str = ""
    end_date: str = ""
    sort_order: int = 0

    def to_dict(self):
        d = asdict(self)
        d.pop("id", None)
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k != 'id'})

@dataclass
class Internship:
    id: Optional[int] = None
    company: str = ""
    position: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""
    sort_order: int = 0

    def to_dict(self):
        d = asdict(self)
        d.pop("id", None)
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k != 'id'})

@dataclass
class Project:
    id: Optional[int] = None
    name: str = ""
    role: str = ""
    start_date: str = ""
    end_date: str = ""
    background: str = ""
    actions: str = ""
    results: str = ""
    tech_stack: str = ""
    sort_order: int = 0

    def to_dict(self):
        d = asdict(self)
        d.pop("id", None)
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k != 'id'})

@dataclass
class Skill:
    id: Optional[int] = None
    name: str = ""
    level: str = ""
    evidence: str = ""
    category: str = ""
    sort_order: int = 0

    def to_dict(self):
        d = asdict(self)
        d.pop("id", None)
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k != 'id'})

@dataclass
class Award:
    id: Optional[int] = None
    name: str = ""
    level: str = ""
    date: str = ""
    sort_order: int = 0

    def to_dict(self):
        d = asdict(self)
        d.pop("id", None)
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k != 'id'})

@dataclass
class SelfEvaluation:
    id: Optional[int] = None
    content: str = ""

    def to_dict(self):
        d = asdict(self)
        d.pop("id", None)
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k != 'id'})

@dataclass
class UserTemplate:
    id: Optional[int] = None
    name: str = ""
    html_content: str = ""
    mapping_json: str = ""  # AI识别的占位符映射表 JSON
    is_builtin: bool = False
    created_at: str = ""

    def to_dict(self):
        d = asdict(self)
        d.pop("id", None)
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k != 'id'})

@dataclass
class ResumeRecord:
    id: Optional[int] = None
    jd_text: str = ""
    jd_cleaned: str = ""
    template_name: str = ""
    html_content: str = ""
    cover_letter: str = ""
    interview_questions: str = ""
    company_analysis: str = ""
    created_at: str = ""

    def to_dict(self):
        d = asdict(self)
        d.pop("id", None)
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k != 'id'})
