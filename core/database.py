import sqlite3
import os
from contextlib import contextmanager

import config

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

    @property
    def db_path(self):
        """动态读取 DB 路径，便于测试环境切换"""
        return config.DB_PATH

    def get_connection(self):
        conn = sqlite3.connect(config.DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def connection(self):
        """上下文管理器：自动 commit / rollback / close"""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS basic_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                email TEXT DEFAULT '',
                age TEXT DEFAULT '',
                job_target TEXT DEFAULT '',
                photo_path TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS education (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school TEXT DEFAULT '',
                major TEXT DEFAULT '',
                degree TEXT DEFAULT '本科',
                start_date TEXT DEFAULT '',
                end_date TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS internships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT DEFAULT '',
                position TEXT DEFAULT '',
                start_date TEXT DEFAULT '',
                end_date TEXT DEFAULT '',
                description TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT DEFAULT '',
                role TEXT DEFAULT '',
                start_date TEXT DEFAULT '',
                end_date TEXT DEFAULT '',
                background TEXT DEFAULT '',
                actions TEXT DEFAULT '',
                results TEXT DEFAULT '',
                tech_stack TEXT DEFAULT '',
                tags TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT DEFAULT '',
                level TEXT DEFAULT '',
                evidence TEXT DEFAULT '',
                category TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS awards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT DEFAULT '',
                level TEXT DEFAULT '',
                date TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS self_evaluation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS other_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT DEFAULT '',
                content TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS user_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT DEFAULT '',
                html_content TEXT DEFAULT '',
                mapping_json TEXT DEFAULT '',
                is_builtin INTEGER DEFAULT 0,
                created_at TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS resume_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jd_text TEXT DEFAULT '',
                jd_cleaned TEXT DEFAULT '',
                template_name TEXT DEFAULT '',
                html_content TEXT DEFAULT '',
                cover_letter TEXT DEFAULT '',
                interview_questions TEXT DEFAULT '',
                company_analysis TEXT DEFAULT '',
                created_at TEXT DEFAULT '',
                company_name TEXT DEFAULT '',
                job_title TEXT DEFAULT '',
                is_delivered INTEGER DEFAULT 0,
                delivery_time TEXT DEFAULT '',
                delivery_url TEXT DEFAULT '',
                delivery_status TEXT DEFAULT 'pending'
            );

            CREATE TABLE IF NOT EXISTS interview_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'active',
                basic_info_json TEXT DEFAULT '{}',
                jd_text TEXT DEFAULT '',
                experience_text TEXT DEFAULT '',
                questions_json TEXT DEFAULT '[]',
                current_question_index INTEGER DEFAULT 0,
                chat_history_json TEXT DEFAULT '[]',
                evaluation_json TEXT DEFAULT '',
                started_at TEXT DEFAULT '',
                ended_at TEXT DEFAULT ''
            );
        """)

        # 迁移：兼容旧库缺少 projects.tags 列（2026-08-18 select_top_projects 引入）
        try:
            cols = [r[1] for r in cursor.execute("PRAGMA table_info(projects)").fetchall()]
            if "tags" not in cols:
                cursor.execute("ALTER TABLE projects ADD COLUMN tags TEXT DEFAULT ''")
        except Exception:
            pass

        # 迁移：为已有的 resume_records 表补充新字段
        try:
            cursor.execute("ALTER TABLE resume_records ADD COLUMN company_name TEXT DEFAULT ''")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE resume_records ADD COLUMN job_title TEXT DEFAULT ''")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE resume_records ADD COLUMN is_delivered INTEGER DEFAULT 0")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE resume_records ADD COLUMN delivery_time TEXT DEFAULT ''")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE resume_records ADD COLUMN delivery_url TEXT DEFAULT ''")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE resume_records ADD COLUMN delivery_status TEXT DEFAULT 'pending'")
        except Exception:
            pass

        conn.commit()
        conn.close()

    def close(self):
        pass  # SQLite 连接由各服务自行管理


db = Database()
