# AI简历定制工具 V2

本地 Web 应用，帮助用户根据目标岗位智能生成个性化简历。

## 快速开始

1. 克隆仓库: `git clone <repo-url>`
2. 安装依赖: `pip install -r requirements.txt`
3. 配置 API Key: 复制 `.env.example` 为 `.env`，填入你的 DeepSeek API Key
4. 安装 Tesseract OCR (可选，用于截图识别):
   - Windows: 下载安装 https://github.com/UB-Mannheim/tesseract/wiki
   - Mac: `brew install tesseract`
   - Linux: `sudo apt install tesseract-ocr`
5. 运行: `python app.py`
6. 打开浏览器访问: http://localhost:8765
