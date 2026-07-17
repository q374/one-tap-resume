import sqlite3
import os
from config import DB_PATH

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
        self.db_path = DB_PATH

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

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
                created_at TEXT DEFAULT ''
            );
        """)

        conn.commit()
        conn.close()

    def close(self):
        pass  # SQLite 连接由各服务自行管理


db = Database()
