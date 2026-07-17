import re
import os
import base64
from core.deepseek_client import call_deepseek
from prompts.resume_generation import build_resume_prompt
from services.html_cleaner import clean_html_response, validate_html, validate_content_authenticity
from config import BASE_DIR

class ResumeService:
    async def generate(self, template_html: str, experience_text: str,
                       jd_text: str, photo_path: str = "") -> dict:
        """生成简历 HTML，返回 {html, valid, issues}"""
        age_match = re.search(r'年龄[^0-9]*(\d+)', experience_text)
        age_directive = (
            f"年龄字段已提供，值为：{age_match.group(1)}。请将{{{{年龄}}}}占位符替换为<span class=\"age-normal\">{age_match.group(1)}</span>。"
            if age_match else
            '年龄字段未提供，请将{{{{年龄}}}}占位符替换为<span class="editable-placeholder" contenteditable="true">请输入你的年龄</span>。'
        )

        photo_directive = '照片未提供，请将{{{{照片}}}}占位符替换为<span class="editable-placeholder" contenteditable="true">请上传照片</span>。'

        prompt = build_resume_prompt(
            template_html=template_html,
            experience_text=experience_text,
            jd_text=jd_text,
            age_directive=age_directive,
            photo_directive=photo_directive,
        )

        html_content = await call_deepseek(prompt, max_tokens=8192)
        if not html_content:
            return {"html": None, "valid": False, "issues": ["API调用失败"]}

        html_content = clean_html_response(html_content)

        if photo_path:
            abs_path = photo_path if os.path.isabs(photo_path) else os.path.join(BASE_DIR, photo_path)
            if os.path.exists(abs_path):
                try:
                    with open(abs_path, 'rb') as f:
                        img_data = f.read()
                        img_b64 = base64.b64encode(img_data).decode('utf-8')
                        html_content = html_content.replace(
                            'src="' + os.path.basename(photo_path) + '"',
                            f'src="data:image/jpeg;base64,{img_b64}"'
                        )
                except Exception:
                    pass

        valid, msg = validate_html(html_content)
        content_ok, content_msg = validate_content_authenticity(html_content, experience_text)

        issues = []
        if not valid:
            issues.append(f"HTML验证: {msg}")
        if not content_ok:
            issues.append(f"内容真实性: {content_msg}")

        return {"html": html_content, "valid": valid and content_ok, "issues": issues}


resume_service = ResumeService()
