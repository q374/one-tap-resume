import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import BASE_DIR

app = FastAPI(title="AI简历定制工具", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/")
async def root():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))

# 路由将在后续任务中注册

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8765, reload=True)
