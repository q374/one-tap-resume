import re
import os
import base64
from core.deepseek_client import call_deepseek
from prompts.resume_generation import build_resume_prompt
from services.html_cleaner import clean_html_response, validate_html, validate_content_authenticity
from services.template_filler import fill_custom_template
from services.industry_service import industry_service
from services.match_service import compute_match, build_match_context
from services.experience_service import strip_markdown
from config import BASE_DIR

PHOTO_MARKER = '__PHOTO_BASE64__'

# 行业特定职业资格证词库：与目标岗位方向无关时禁止写入简历
OCCUPATIONAL_CERT_KEYWORDS = [
    "海员", "四小证", "船员", "救生", "消防", "急救", "驾驶证", "驾照", "健康证",
    "体检", "教师资格", "普通话", "导游", "会计", "证券", "基金", "银行从业",
    "法律职业", "护士", "医师", "药师", "焊工", "电工", "叉车", "起重机",
    "特种设备", "营养师", "厨师", "保安", "安检",
]

_OTHERS_SECTION_END_MARKS = ["教育背景", "实习经历", "项目经历", "获奖情况", "自我评价"]


def _annotate_irrelevant_certs(experience_text: str, jd_text: str) -> str:
    """把经历文本'其他信息'中与JD明显无关的职业资格证标注为『禁止写入简历』

    保留：与JD相关的、作品/经历类（参赛/开源/调研/PRD等）、语言等级（CET等）。
    标注：命中行业特定职业资格证词库 且 JD 未提及 → 追加『（与目标岗位无关，禁止写入简历）』。
    """
    if "其他信息" not in experience_text:
        return experience_text
    jd = jd_text or ""
    lines = experience_text.split("\n")
    in_others = False
    out = []
    for line in lines:
        stripped = line.strip()
        if "其他信息" in line:
            in_others = True
            out.append(line)
            continue
        if in_others:
            if not stripped:
                out.append(line)
                continue
            if any(k in line for k in _OTHERS_SECTION_END_MARKS):
                in_others = False
                out.append(line)
                continue
            title = line.split("：")[0].split(":")[0].strip()
            if not title:
                out.append(line)
                continue
            occ_words = [k for k in OCCUPATIONAL_CERT_KEYWORDS if k in title]
            if occ_words:
                # JD 是否提及这些资格词或其行业词
                jd_mentions = any(w in jd for w in occ_words)
                if not jd_mentions:
                    out.append(line + "（与目标岗位无关，禁止写入简历）")
                    continue
        out.append(line)
    return "\n".join(out)



class ResumeService:
    async def generate(self, template_html: str, experience_text: str,
                       jd_text: str, photo_path: str = "",
                       industry_override: str = "") -> dict:
        """生成简历 HTML，返回 {html, valid, issues, industry}"""
        # 清除经历文本中的 Markdown 残留（** 等），防止污染输出
        experience_text = strip_markdown(experience_text)
        # 硬过滤：与JD无关的职业资格证（海员证/四小证/体检等）标注为禁止写入
        experience_text = _annotate_irrelevant_certs(experience_text, jd_text)

        # 行业侧重点分析（降级铁律：失败不影响简历生成）
        industry_ctx = ""
        industry_name = ""
        try:
            industry_analysis = await industry_service.analyze(
                jd_text, industry_override=industry_override
            )
            industry_name = industry_analysis.get("industry", "")
            industry_ctx = industry_service.build_industry_context(industry_analysis)
        except Exception:
            industry_ctx = ""
            industry_name = ""

        # 经历-岗位匹配度（低/中匹配时触发增强模式，失败不影响生成）
        match_info = {"score": None, "level": "unknown", "missing_keywords": [], "total": 0, "detail": ""}
        match_ctx = ""
        try:
            match_info = compute_match(experience_text, jd_text)
            match_ctx = build_match_context(match_info)
        except Exception:
            pass

        # 年龄指令
        age_match = re.search(r'年龄[^0-9]*(\d+)', experience_text)
        age_directive = (
            f'年龄字段已提供，值为：{age_match.group(1)}。请将{{{{年龄}}}}占位符替换为<span class="age-normal">{age_match.group(1)}</span>。'
            if age_match else
            '年龄字段未提供，请将{{{{年龄}}}}占位符替换为<span class="age-placeholder" data-placeholder="请输入你的年龄" contenteditable="true"></span>。'
        )

        # 照片：模板中用占位符，AI 生成后替换（避免 base64 截断）
        photo_base64 = ''
        if photo_path:
            abs_path = photo_path if os.path.isabs(photo_path) else os.path.join(BASE_DIR, photo_path)
            if os.path.exists(abs_path):
                try:
                    with open(abs_path, 'rb') as f:
                        img_data = f.read()
                    img_b64 = base64.b64encode(img_data).decode('utf-8')
                    ext = os.path.splitext(abs_path)[1].lower()
                    mime = 'image/png' if ext == '.png' else 'image/gif' if ext == '.gif' else 'image/jpeg'
                    photo_base64 = f'data:{mime};base64,{img_b64}'
                except Exception:
                    pass

        if photo_base64:
            # 替换模板中的照片占位符为简单标记
            template_html = template_html.replace(
                '<span contenteditable="true" class="editable-placeholder">请上传照片</span>',
                f'<img src="{PHOTO_MARKER}" alt="照片" style="width:100%;height:100%;object-fit:contain">'
            )
            photo_directive = '照片占位符已嵌入模板，请保持header-right区域中 src="__PHOTO_BASE64__" 的img标签不变。'
        else:
            photo_directive = '照片未提供，请将照片区域保持为<span class="editable-placeholder" contenteditable="true">请上传照片</span>。'

        # 根据经历库数据动态裁剪模板模块：有数据的模块保留，无数据的模块移除
        # （防止 AI 编造不存在的经历，数据来源唯一红线）
        _MODULE_RULES = [
            ("WORK_MODULE", r"工作经历|实习经历"),
            ("PROJECT_MODULE", r"项目经历"),
            ("EDU_MODULE", r"教育背景"),
            ("SKILL_MODULE", r"技能"),
            ("CUSTOM_MODULE", r"获奖情况|其他信息"),
            ("SELF_MODULE", r"自我评价"),
        ]
        for _marker, _title_pat in _MODULE_RULES:
            if not re.search(rf'^(?:{_title_pat})[：:]', experience_text, re.M):
                template_html = re.sub(
                    rf'<!-- {_marker}_START -->[\s\S]*?<!-- {_marker}_END -->',
                    '', template_html)

        # 检测是否为自定义模板（无 {{}} 占位符，如 Word/PDF 导入的）
        has_placeholders = '{{' in template_html

        if not has_placeholders:
            # 自定义模板：用 filler 管道（AI只出文本，代码负责拼回HTML）
            html_content = await fill_custom_template(
                template_html, experience_text, jd_text,
                industry_context=(industry_ctx + "\n" + match_ctx) if match_ctx else industry_ctx,
            )
            if not html_content:
                return {"html": None, "valid": False, "issues": ["模板填充失败"]}
        else:
            # 内置模板：用传统 prompt 方式
            prompt = build_resume_prompt(
                template_html=template_html,
                experience_text=experience_text,
                jd_text=jd_text,
                age_directive=age_directive,
                photo_directive=photo_directive,
                has_placeholders=True,
                industry_context=industry_ctx,
                match_context=match_ctx,
            )

            html_content = await call_deepseek(prompt, max_tokens=16384)
            if not html_content:
                return {"html": None, "valid": False, "issues": ["API调用失败"]}

            html_content = clean_html_response(html_content)

        # 后处理：用真实 base64 替换占位符
        if photo_base64 and PHOTO_MARKER in html_content:
            html_content = html_content.replace(PHOTO_MARKER, photo_base64)

        valid, msg = validate_html(html_content)
        content_ok, content_msg = validate_content_authenticity(html_content, experience_text)

        issues = []
        if not valid:
            issues.append(f"HTML验证: {msg}")
        if not content_ok:
            issues.append(f"内容真实性: {content_msg}")

        # 结构校验：AI 不得新增模板中被裁剪的模块（防编造核心经历）
        core_modules = {
            "项目经历": "PROJECT_MODULE",
            "工作经历": "WORK_MODULE",
            "教育背景": "EDU_MODULE",
            "专业技能": "SKILL_MODULE",
            "自我评价": "SELF_MODULE",
        }
        for title, marker in core_modules.items():
            if f"<!-- {marker}_START -->" not in template_html:
                if re.search(rf'<h2[^>]*>\s*{title}\s*</h2>', html_content):
                    issues.append(f"结构校验: AI 新增了模板中不存在的「{title}」模块，可能含编造内容，请人工核对")

        return {
            "html": html_content,
            "valid": valid and content_ok,
            "issues": issues,
            "industry": industry_name,
            "match_info": match_info,
        }


resume_service = ResumeService()
