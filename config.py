import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "app.db")
PHOTOS_DIR = os.path.join(DATA_DIR, "photos")
EXPORTS_DIR = os.path.join(DATA_DIR, "exports")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# 确保运行时目录存在
for d in [DATA_DIR, PHOTOS_DIR, EXPORTS_DIR,
          os.path.join(BASE_DIR, "static"),
          os.path.join(BASE_DIR, "static", "css"),
          os.path.join(BASE_DIR, "static", "js", "components"),
          os.path.join(BASE_DIR, "templates"),
          os.path.join(BASE_DIR, "tests")]:
    os.makedirs(d, exist_ok=True)

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-chat")
BASE_URL = os.environ.get("BASE_URL", "https://api.deepseek.com")
