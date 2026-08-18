# AI 简历定制工具（one-tap-resume）

> 一次录入经历，针对每个岗位的 JD 自动定制一份专属简历。
> 同一份真实经历，可重构成无数个岗位的答案——不用再为投不同岗位反复改简历。

本地 Web 应用，覆盖求职全流程：**经历管理 → JD 行业分析 → 简历生成 → AI 质量诊断 → AI 辅助修改 → 模拟面试 → 公司速查 → 投递追踪**。

---

## 一、功能总览

| 页面（Tab） | 功能 |
|------------|------|
| 经历管理 | 录入 / 编辑 / 分类个人经历（教育、工作/实习、项目、技能、获奖、证书、其他信息）；支持文字导入、简历文件导入（PDF/Word 自动抽文本）、照片上传、自动去重 |
| 简历生成 | 粘贴 JD → 自动识别行业侧重点 → **生成前关键词覆盖率检测**（可补命中率 + 缺失词补法建议）→ 一键生成；**生成后 AI 初筛预判**（预计能否过机筛）；内置模板 + 支持自定义模板导入 |
| 简历修改 | AI 辅助修改指定模块（加技能、改措辞、删/增模块），红绿对比区分修改前后 |
| 模拟面试 | 按岗位生成定制题目，AI 逐题点评并追问，结束后出整体评估 |
| 公司速查 | 输入公司名，联网背调：基本情况 / 薪资 / 工作强度 / 发展空间 / 风险提示 |
| 投递记录 | 记录投递的公司、岗位、时间与进度，方便跟进 |

**AI 初筛护航**：生成前自动检测 JD 可补关键词命中率（剔除公司名/行业属性/JD上下文词等噪音），缺失词给出补法建议并一键跳转补录；可补命中率不足 70% 时自动启用「过初筛强化模式」，把缺失词作为硬性清单让 AI 在不编造前提下尽力覆盖；生成后直接给出「预计能过 AI 初筛 / 压线 / 大概率被卡」判定。

**核心铁律**：简历内容 100% 来自你录入的真实经历，绝不编造；信息不足时诚实留白。

---

## 二、环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10/11（首选）、macOS、Linux |
| Python | 3.10 及以上（3.13 实测可用） |
| DeepSeek API Key | **必填**（简历生成、面试、诊断等 AI 功能都依赖） |
| Tesseract OCR | 可选（仅「截图识别岗位信息」功能需要） |
| 网络 | 需要能访问 DeepSeek API；公司速查需要联网搜索 |

---

## 三、安装步骤（从零开始）

### 第 1 步：安装 Python

1. 到 [python.org/downloads](https://www.python.org/downloads/) 下载 Python 3.10+ 安装包
2. 安装时**务必勾选 “Add Python to PATH”**（否则命令行找不到 python）
3. 安装完成后，打开终端（Windows 用 PowerShell 或 CMD）验证：

   ```bash
   python --version
   ```

   能输出版本号（如 `Python 3.13.9`）即成功。

### 第 2 步：获取代码

```bash
git clone https://github.com/q374/one-tap-resume
cd one-tap-resume
```

> 没有安装 Git？也可以到仓库页面点 **Code → Download ZIP**，解压后进入该目录，后续命令都在这个目录里执行。

### 第 3 步：创建虚拟环境（强烈推荐）

用虚拟环境可以避免依赖与系统其他 Python 项目冲突：

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

激活成功后，命令行前面会出现 `(.venv)` 标记。

### 第 4 步：安装依赖

```bash
pip install -r requirements.txt
```

**国内网络下载慢 / 超时？** 用清华镜像加速：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 第 5 步：配置 API Key

1. 复制配置文件模板：

   ```bash
   # Windows
   copy .env.example .env
   # macOS / Linux
   cp .env.example .env
   ```

2. 用记事本打开 `.env`，填入你的 DeepSeek API Key：

   ```ini
   DEEPSEEK_API_KEY=sk-你的key
   MODEL_NAME=deepseek-chat
   BASE_URL=https://api.deepseek.com
   ```

3. **没有 DeepSeek Key？** 到 [platform.deepseek.com](https://platform.deepseek.com) 注册 → 左侧「API Keys」→「创建 API Key」→ 复制以 `sk-` 开头的一串字符，粘贴到 `.env`。新用户通常有赠送额度，够测试用。

> ⚠️ `.env` 已加入 `.gitignore`，不会被提交到 GitHub，可放心填写。也请勿把 Key 截图发到公开渠道。

### 第 6 步：启动

**方式 A（推荐，Windows 双击即可）：**

双击根目录下的 **`启动简历工具.bat`**。脚本会自动：清理占用 8765 端口的残留进程 → 启动服务 → 等待就绪 → 自动打开浏览器。

**方式 B（命令行）：**

```bash
python app.py
```

看到 `Uvicorn running on http://127.0.0.1:8765` 后，浏览器打开：

```
http://localhost:8765
```

**注意：启动后请勿关闭那个黑色服务窗口，关掉即停止服务。**

---

## 四、使用流程（主链路）

1. **录入经历** → 「经历管理」页：粘贴你的教育、工作/实习、项目、技能、获奖、证书等信息。可以用「AI 经历导入」：先复制页面上的采集提示词，去任意大模型（豆包、DeepSeek 等）对话里说出你的经历，把返回的文本粘回工具一键解析入库。
2. **粘贴 JD** → 「简历生成」页：把招聘软件上的岗位描述复制进来（也可以截图后用「截图识别」转文字）。
3. **生成简历** → 点「分析 JD」查看行业侧重点，再点「生成简历」。工具自动按行业 + JD 关键词匹配你的经历，生成一页式 HTML 简历。
4. **修改** → 生成后可直接在「简历修改」页用 AI 指令改指定模块；不满意的地方用对话式修改。
5. **导出** → 简历预览页点「打印 / 导出 PDF」，或直接在浏览器里 `Ctrl + P` 打印为 PDF。
6. **面试 & 投递** → 用「模拟面试」练题、「公司速查」做背调、「投递记录」跟踪进度。

---

## 五、常见问题排查

### Q1：`pip install` 报错 / 超时 / 网络连接失败
- 用国内镜像：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
- 个别包（如 pywin32）只支持 Windows，macOS/Linux 会自动跳过，不影响使用。

### Q2：启动报「端口被占用 / address already in use」
- 上次异常退出可能残留了服务进程。Windows 下：
  ```bash
  netstat -ano | findstr ":8765"
  taskkill /f /pid <PID>
  ```
- 直接双击 `启动简历工具.bat` 会自动清理残留再启动。

### Q3：提示「AI 解析暂不可用」或简历生成失败
- 最常见原因：**API Key 无效或余额不足**。检查 `.env` 里 `DEEPSEEK_API_KEY` 是否填对、是否多空格。
- 也可能是网络无法访问 DeepSeek API，换个网络或稍后重试。

### Q4：没装 Tesseract 会怎样？
- 只有「截图识别岗位信息」用不了，其他功能全部正常。
- 需要时再装：Windows 到 [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) 下载安装；macOS：`brew install tesseract`；Linux：`sudo apt install tesseract-ocr`。

### Q5：导出 PDF 中文乱码 / 排版不对？
- 工具优先用 xhtml2pdf 生成 PDF，个别复杂 CSS 或中文字体支持有限时会自动降级为 HTML 下载。
- 最稳妥的方式：在简历预览页按 `Ctrl + P`，目标打印机选「另存为 PDF」，这就是浏览器渲染的一页效果。

### Q6：数据存在哪里？换电脑怎么迁移？
- 所有数据都在 `data/` 目录（SQLite 数据库 `data/app.db` + 照片）。
- 换电脑：把整个 `data/` 目录拷贝到新机器同位置即可，经历、简历记录、投递记录全都在。

### Q7：命令行找不到 `python`
- 安装 Python 时没勾选 “Add to PATH”。重新运行安装包，选 Modify → 勾选 Add to PATH；或改用 `py`（Windows 自带启动器）代替 `python`。

### Q8：截图识别出的文字乱码 / 不准确
- 确认 Tesseract 安装了**简体中文语言包**（安装时勾选 Chinese (Simplified)）。

### Q9：生成出来的简历超一页 / 不满一页
- 工具内置自动适配：超一页会自动压缩字号/间距，不满一页会自动放大填充；仍不理想时可用「AI 辅助修改」调整内容，或用「一键适配一页」微调。

### Q10：如何更新到最新版？
```bash
git pull
```
如果提示本地有修改冲突，先 `git stash` 再 pull。

---

## 六、已知限制

1. 依赖用户提供真实经历，经历库越详细生成效果越好
2. 复杂表格排版可能需要生成后手动微调
3. 照片需用户手动上传，AI 不自动生成
4. 简历以 HTML 输出为主，PDF 导出依赖 xhtml2pdf，复杂样式建议用浏览器 Ctrl+P
5. 公司速查依赖联网搜索，信息准确度受搜索源影响；查不到的字段如实标注
6. 目前主要面向中文场景
7. 行业识别基于关键词打分，跨行业岗位（如“金融科技”）置信度可能不高，可手动指定行业
8. 简历文件导入（PDF/Word）只做文本抽取，复杂版式内容可能丢失格式

---

## 七、开发与测试

```bash
# 运行全部测试
python -m pytest tests/ -v
```

项目结构：

```
one-tap-resume/
├── app.py                  # FastAPI 入口（所有接口）
├── config.py               # 路径与配置
├── requirements.txt        # 依赖清单
├── core/                   # 数据模型 / 数据库 / DeepSeek 客户端
├── services/               # 业务逻辑（简历/经历/模板/面试/导出等）
├── prompts/                # AI 提示词
├── templates/              # HTML 简历模板
├── static/                 # 前端页面与 JS
├── data/                   # 运行数据（SQLite / 照片 / 导出，不入库）
└── tests/                  # 自动化测试
```

---

## 许可

MIT License
