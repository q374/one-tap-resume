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
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k in row.keys()})

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
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k in row.keys()})

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
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k in row.keys()})

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
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k in row.keys()})

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
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k in row.keys()})

@dataclass
class Award:
    id: Optional[int] = None
    name: str = ""
    level: str = ""
    date: str = ""
    sort_order: int = 0

    def to_dict(self):
        d = asdict(self)
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k in row.keys()})

@dataclass
class SelfEvaluation:
    id: Optional[int] = None
    content: str = ""

    def to_dict(self):
        d = asdict(self)
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k in row.keys()})

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
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k in row.keys()})

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
    company_name: str = ""
    job_title: str = ""
    is_delivered: int = 0
    delivery_time: str = ""
    delivery_url: str = ""
    delivery_status: str = "pending"

    def to_dict(self):
        d = asdict(self)
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k in row.keys()})


@dataclass
class InterviewSession:
    id: Optional[int] = None
    session_id: str = ""
    status: str = "active"
    basic_info_json: str = "{}"
    jd_text: str = ""
    experience_text: str = ""
    questions_json: str = "[]"
    current_question_index: int = 0
    chat_history_json: str = "[]"
    evaluation_json: str = ""
    started_at: str = ""
    ended_at: str = ""

    def to_dict(self):
        d = asdict(self)
        return d

    @classmethod
    def from_row(cls, row):
        if row is None:
            return cls()
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k in row.keys()})
