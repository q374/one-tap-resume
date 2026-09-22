# 安装与启动

## 环境要求

- Windows 10 / 11
- Python 3.10 或更高版本
- 可选：用于真实模型与联网功能的 API 服务

## 安装

```powershell
git clone https://github.com/q374/one-tap-resume.git
cd one-tap-resume
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

根据 `.env.example` 在本地 `.env` 中填写需要启用的服务配置。不要将密钥提交到 Git。

## 启动

```powershell
python app.py
```

浏览器打开 `http://localhost:8765`。

## 运行测试

```powershell
python -m pytest tests -q
```

如果只需查看基础界面，可先不配置联网服务；调用模型、公司速查等能力时再补充对应配置。

