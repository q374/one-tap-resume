import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

import io
import os
import json
import asyncio
import uuid
from datetime import datetime

from config import BASE_DIR
from core import database as core_db
from core.database import db
from core.models import BasicInfo, Education, Internship, Project, Skill, Award, SelfEvaluation
from core.deepseek_client import call_deepseek, call_deepseek_json
from core.company_lookup import lookup_company
from services.experience_service import experience_service
from services.resume_service import resume_service
from services.jd_service import jd_service
from services.cover_letter_service import cover_letter_service
from services.interview_service import interview_service
from services.diagnosis_service import diagnosis_service
from services.template_service import template_service
from services.ocr_service import ocr_service
from services.export_service import export_service
from prompts.experience_parse import EXPERIENCE_PARSE_PROMPT
from prompts.dedup import DEDUP_PROMPT
from prompts.company_analysis import build_company_analysis_prompt

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
    from fastapi.responses import FileResponse, HTMLResponse
    index_path = os.path.join(BASE_DIR, "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse(
        "<html><body style='font-family:sans-serif;padding:40px;text-align:center'>"
        "<h1>AI简历定制工具</h1><p>服务已启动，等待前端页面...</p></body></html>"
    )

# 路由将在后续任务中注册

# ==================== Experience Routes ====================

@app.get("/api/experiences/all")
async def get_all_experiences():
    """获取所有经历数据，供前端展示"""
    return {
        "basic_info": experience_service.get_basic_info().to_dict(),
        "education": [e.to_dict() for e in experience_service.list_education()],
        "internships": [i.to_dict() for i in experience_service.list_internships()],
        "projects": [p.to_dict() for p in experience_service.list_projects()],
        "skills": [s.to_dict() for s in experience_service.list_skills()],
        "awards": [a.to_dict() for a in experience_service.list_awards()],
        "self_evaluation": experience_service.get_self_evaluation().to_dict(),
    }

class BasicInfoInput(BaseModel):
    name: str = ""
    phone: str = ""
    email: str = ""
    age: str = ""
    job_target: str = ""
    photo_path: str = ""

@app.post("/api/experiences/basic-info")
async def save_basic_info(data: BasicInfoInput):
    info = BasicInfo(**data.model_dump())
    experience_service.save_basic_info(info)
    return {"status": "ok"}

# 通用 CRUD 端点
VALID_MODULES = ["education", "internships", "projects", "skills", "awards"]

@app.get("/api/experiences/{module}")
async def list_module(module: str):
    if module not in VALID_MODULES:
        raise HTTPException(404, f"Unknown module: {module}")
    items = getattr(experience_service, f"list_{module}")()
    return [item.to_dict() for item in items]

@app.post("/api/experiences/{module}")
async def add_module_item(module: str, data: dict):
    if module not in VALID_MODULES:
        raise HTTPException(404, f"Unknown module: {module}")
    model_class = {
        "education": Education, "internships": Internship,
        "projects": Project, "skills": Skill, "awards": Award
    }[module]
    item = model_class(**data)
    item_id = getattr(experience_service, f"add_{module[:-1] if module.endswith('s') else module}")(item)
    return {"status": "ok", "id": item_id}

@app.put("/api/experiences/{module}/{item_id}")
async def update_module_item(module: str, item_id: int, data: dict):
    if module not in VALID_MODULES:
        raise HTTPException(404, f"Unknown module: {module}")
    model_class = {
        "education": Education, "internships": Internship,
        "projects": Project, "skills": Skill, "awards": Award
    }[module]
    data["id"] = item_id
    item = model_class(**data)
    getattr(experience_service, f"update_{module[:-1] if module.endswith('s') else module}")(item)
    return {"status": "ok"}

@app.delete("/api/experiences/{module}/{item_id}")
async def delete_module_item(module: str, item_id: int):
    if module not in VALID_MODULES:
        raise HTTPException(404, f"Unknown module: {module}")
    getattr(experience_service, f"delete_{module[:-1] if module.endswith('s') else module}")(item_id)
    return {"status": "ok"}

@app.put("/api/experiences/{module}/reorder")
async def reorder_module(module: str, ids: list[int]):
    if module not in VALID_MODULES:
        raise HTTPException(404, f"Unknown module: {module}")
    experience_service.reorder_items(module, ids)
    return {"status": "ok"}

# Self evaluation
@app.get("/api/experiences/self-evaluation")
async def get_self_eval():
    return experience_service.get_self_evaluation().to_dict()

@app.post("/api/experiences/self-evaluation")
async def save_self_eval(data: dict):
    ev = SelfEvaluation(content=data.get("content", ""))
    experience_service.save_self_evaluation(ev)
    return {"status": "ok"}

# AI parse pasted text
class ParseTextInput(BaseModel):
    text: str

@app.post("/api/experiences/parse-text")
async def parse_text(data: ParseTextInput):
    """AI 解析用户粘贴的经历文本为结构化数据"""
    prompt = EXPERIENCE_PARSE_PROMPT.format(user_text=data.text)
    result = await call_deepseek_json(prompt)
    return result

# Semantic dedup check
class DedupInput(BaseModel):
    module: str
    new_text: str

@app.post("/api/experiences/check-duplicate")
async def check_duplicate(data: DedupInput):
    """检查新录入内容是否与已有经历语义重复"""
    existing_items = getattr(experience_service, f"list_{data.module}")()
    if not existing_items:
        return {"is_duplicate": False, "similar_items": [], "suggestion": ""}

    existing_text = "\n".join([
        str(item.to_dict()) for item in existing_items
    ])
    prompt = DEDUP_PROMPT.format(
        module=data.module,
        existing_items=existing_text,
        new_item=data.new_text
    )
    result = await call_deepseek_json(prompt)
    return result

# ==================== Resume Generation Route ====================

class GenerateRequest(BaseModel):
    jd_text: str
    template_type: str = "default"

@app.post("/api/resumes/generate")
async def generate_resume(req: GenerateRequest):
    """主生成接口 — 并行生成简历 + 求职信 + 面试题 + 诊断"""
    exp_data = experience_service.export_all()
    experience_text = exp_data["text"]
    photo_path = exp_data.get("photo_path", "")

    template_html = template_service.get_template_html(req.template_type)

    jd_result = await jd_service.clean(req.jd_text)

    company_name = jd_result.get("company_name", "")
    clean_jd = jd_result.get("cleaned_jd", req.jd_text)

    resume_task = resume_service.generate(template_html, experience_text, clean_jd, photo_path)
    cover_task = cover_letter_service.generate(experience_text, clean_jd)
    interview_task = interview_service.generate(experience_text, clean_jd)

    results = await asyncio.gather(resume_task, cover_task, interview_task)

    resume_result = results[0]
    cover_letter = results[1]
    interview_questions = results[2]

    diagnosis = {}
    if resume_result["html"]:
        diagnosis = await diagnosis_service.diagnose(resume_result["html"])

    company_analysis = {}
    if company_name:
        company_data = lookup_company(company_name)
        if company_data:
            try:
                company_analysis = await call_deepseek_json(
                    build_company_analysis_prompt(company_data, clean_jd)
                )
            except Exception:
                company_analysis = {"verdict": "数据不足，无法判断", "risk_level": "unknown"}

    conn = db.get_connection()
    conn.execute(
        """INSERT INTO resume_records
           (jd_text, jd_cleaned, template_name, html_content, cover_letter,
            interview_questions, company_analysis, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (req.jd_text, clean_jd, req.template_type,
         resume_result.get("html", ""), cover_letter,
         json.dumps(interview_questions, ensure_ascii=False),
         json.dumps(company_analysis, ensure_ascii=False),
         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

    return {
        "resume_html": resume_result.get("html"),
        "resume_valid": resume_result.get("valid", False),
        "resume_issues": resume_result.get("issues", []),
        "cover_letter": cover_letter,
        "interview_questions": interview_questions,
        "jd_analysis": jd_result,
        "diagnosis": diagnosis,
        "company_analysis": company_analysis,
    }

# ==================== Template Routes ====================

@app.get("/api/templates")
async def list_templates():
    return template_service.list_templates()

class TemplateUploadInput(BaseModel):
    name: str
    html_content: str

@app.post("/api/templates/upload")
async def upload_template(data: TemplateUploadInput):
    result = await template_service.upload_template(data.name, data.html_content)
    return result

@app.delete("/api/templates/{template_id}")
async def delete_template(template_id: int):
    template_service.delete_template(template_id)
    return {"status": "ok"}

# ==================== JD Routes ====================

@app.post("/api/jd/clean")
async def clean_jd(data: dict):
    jd_text = data.get("jd_text", "")
    if not jd_text:
        raise HTTPException(400, "jd_text is required")
    result = await jd_service.clean(jd_text)
    return result

# ==================== OCR Routes ====================

@app.post("/api/ocr/extract")
async def ocr_extract(files: list[UploadFile] = File(...)):
    """上传截图，返回 OCR 识别文本"""
    import aiofiles

    texts = []
    for file in files:
        tmp_path = os.path.join(BASE_DIR, "data", f"ocr_{uuid.uuid4().hex}.png")
        async with aiofiles.open(tmp_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        text = await ocr_service._ocr_single(tmp_path)
        texts.append({"filename": file.filename, "text": text})

        try:
            os.remove(tmp_path)
        except Exception:
            pass

    merged = "\n\n---\n\n".join([t["text"] for t in texts])
    return {"texts": texts, "merged_text": merged}

# ==================== Export Routes ====================

class ExportRequest(BaseModel):
    html_content: str

@app.post("/api/export/pdf")
async def export_pdf(data: ExportRequest):
    try:
        pdf_bytes = export_service.to_pdf(data.html_content)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=resume.pdf"}
        )
    except Exception as e:
        raise HTTPException(500, str(e))

# ==================== AI Chat Routes ====================

class ModifyRequest(BaseModel):
    selected_text: str
    instruction: str
    experience_context: str = ""

@app.post("/api/ai/modify")
async def ai_modify(data: ModifyRequest):
    """选中文本 + 修改要求 → AI 返回修改后的文本段落"""
    prompt = f"""你是简历修改助手。用户选中了简历中的一段文字，要求修改。

【选中的原文】
{data.selected_text}

【用户的修改要求】
{data.instruction}

【用户的经历库参考（如有）】
{data.experience_context}

请只返回修改后的文本段落（不要包含任何解释、不要返回整份简历、不要加markdown代码块）。
直接输出替换选中段落后应该写入的新文本。保持相似的篇幅和格式。"""
    result = await call_deepseek(prompt, max_tokens=1024)
    return {"modified_text": result}

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8765, reload=True)
