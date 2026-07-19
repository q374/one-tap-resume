import re
import os
import base64
from core.deepseek_client import call_deepseek
from prompts.resume_generation import build_resume_prompt
from services.html_cleaner import clean_html_response, validate_html, validate_content_authenticity
from services.template_filler import fill_custom_template
from config import BASE_DIR

PHOTO_MARKER = '__PHOTO_BASE64__'


class ResumeService:
    async def generate(self, template_html: str, experience_text: str,
                       jd_text: str, photo_path: str = "") -> dict:
        """生成简历 HTML，返回 {html, valid, issues}"""
        # 年龄指令
        age_match = re.search(r'年龄[^0-9]*(\d+)', experience_text)
        age_directive = (
            f'年龄字段已提供，值为：{age_match.group(1)}。请将{{{{年龄}}}}占位符替换为<span class="age-normal">{age_match.group(1)}</span>。'
            if age_match else
            '年龄字段未提供，请将{{{{年龄}}}}占位符替换为<span class="editable-placeholder" contenteditable="true">请输入你的年龄</span>。'
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

        # 检测是否为自定义模板（无 {{}} 占位符，如 Word/PDF 导入的）
        has_placeholders = '{{' in template_html

        if not has_placeholders:
            # 自定义模板：用 filler 管道（AI只出文本，代码负责拼回HTML）
            html_content = await fill_custom_template(
                template_html, experience_text, jd_text
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

        return {"html": html_content, "valid": valid and content_ok, "issues": issues}


resume_service = ResumeService()
