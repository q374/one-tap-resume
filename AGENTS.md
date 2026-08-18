# AI 简历工具（one-tap-resume）· Codex 工作规则

> 项目根：`E:\ai简历定制工具\ai-resume-builder-v2`
> 用户指南：README.md ｜ 状态：STATUS.md ｜ 本文件 = AI 协作规则（新对话自动读取）

## 一、这是什么

简历定制工具：一次录入个人经历 → 粘贴岗位 JD → AI 按行业/岗位自动匹配生成定制简历。
- **Web 版**：app.py（FastAPI），端口 8765，`启动简历工具.bat` 一键启动
- **Skill 版**：one-tap-resume-skill（科大讯飞 Astron 比赛提交物，SKILL.md 驱动）
- **开源**：GitHub https://github.com/q374/one-tap-resume

## 二、核心功能（6 Tab）

1. AI 经历导入（按指定提示词把经历录进经历库）
2. 经历管理（分类：教育/实习/项目/技能/其他；可编辑、手动去重）
3. 简历生成（内置黑白简约模板 ×2 + 行业侧重点分析 + 一键适配一页）
4. 简历修改（网页预览 + AI 辅助修改，红/绿区分增删）
5. 模拟面试（粘贴岗位信息，AI 按岗位+简历定制出题，答完分析总结）
6. 投递记录 + 公司洞察/公司速查

## 三、技术栈

- FastAPI + SQLite（`data/app.db`）+ Jinja2/静态页（`static/`）
- DeepSeek API：`config.py` 读环境变量（`.env`：DEEPSEEK_API_KEY / MODEL_NAME / BASE_URL）
- 导出：HTML→PDF（xhtml2pdf）/ Word（python-docx）
- 行业知识库：`prompts/industry_profiles.py`（12 行业 profile）
- 测试：`tests/`（pytest，测试用临时库，禁污染 data/app.db）

## 四、用户偏好（改代码/生成简历前必读）

- 简历硬性要求：**刚好一页 A4**；正文 11.5px，标题/正文字体层级必须区分明显
- 超页处理优先级：先压正文/行高/间距 → 仍超才 AI 精简（禁删真实数据、禁编造）
- 专业技能等专业模块不换行；经历不匹配分类时落"其他信息"兜底
- **预览与导出一致**（打印边距已定死，导出页别让用户再调）
- 所有交互文案/弹窗全中文，禁英文
- AI 绝不编造事实：宁留白不造假；证书/普通话/驾照等归类"其他"
- 一键清理经历库按钮保留（去掉"测试专用"字样，属正常功能）

## 五、关键命令

- 启动：`启动简历工具.bat` 或 `python app.py` → http://127.0.0.1:8765
- 测试：`pytest tests/ -v`
- 装依赖：`pip install -r requirements.txt`
- 中文写入注意：PowerShell 管道写中文会 GBK 乱码，走 UTF-8 脚本/base64

## 六、比赛与发布红线

- 科大讯飞"人才匹配与发展智能辅助Skill开发挑战赛"（2026，专家榜+热度榜）
- 提交物：`one-tap-resume.zip`；SKILL.md frontmatter `name` 必须 = `one-tap-resume`
- **审核红线（连续两次被打回）**：发布包内禁止出现 Claude/OpenAI/ChatGPT/GPT 等外部客户端或模型名——全量搜索 `SKILL.md`、`scripts/`（含 skill_aliases.py、industry_profiles.py）、README、注释、测试，改成通用中文类目或国内可用工具名
- 版本更新：每次改完 = 版本号 +1（GitHub 与 SkillHub 同步）
- SkillHub：https://skill.xfyun.cn/space/global/one-tap-resume

## 七、待办 / 后续方向（用户确认过）

- 已落地：行业侧重点分析(v2.1)、一键适配一页、AI辅助修改红绿区分、公司洞察/速查、一键清理经历库
- 后续方向（存 `docs/后续升级方案`）：批量图片导入、对话式AI修改、自定义模板导入、公司洞察深挖（天眼查类 API）、投递真闭环
- 简历质量：AI 质量诊断可靠性、避免 AI 自评高分（需人工/规则兜底）
## 八、AI 产品经理面试准备入口（2026-08-15）

当用户开新对话做「AI 产品经理 / 助理实习」面试准备时：

1. **先读** 本地私有资料 docs/面试准备/（不入库，含两个项目的经历素材 + 答题框架 + 模拟面试用法）
2. **模拟面试**：优先引导用户用本工具"模拟面试" Tab（真实产品闭环）；也可 AI 直接对话式扮演面试官
3. **生成简历**：用 AI 产品经理 JD 走生成链路（含行业侧重点分析）
4. 面试准备产出物（可选）：经历库录入这段经历、AI产品经理定制简历、模拟面试记录