import sys
import os
import pytest
import tempfile
import shutil

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.database import Database

@pytest.fixture
def test_db():
    """使用临时目录的数据库进行测试"""
    import config
    original_path = config.DB_PATH
    tmp_dir = tempfile.mkdtemp()
    config.DB_PATH = os.path.join(tmp_dir, "test.db")
    config.DATA_DIR = tmp_dir

    # 重新初始化数据库实例
    Database._instance = None
    db = Database()
    db.init_db()

    yield db

    # 清理
    db.close()
    Database._instance = None
    config.DB_PATH = original_path
    shutil.rmtree(tmp_dir, ignore_errors=True)
