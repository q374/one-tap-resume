"""AI简历修改服务 — CSS保护 + 图片保护 + del/ins diff"""

import re
from core.deepseek_client import call_deepseek
from services.html_cleaner import clean_html_response, validate_html


def _extract_base64_images(html_content: str) -> tuple[dict[str, str], str]:
    """抽取HTML中的base64图片，替换为短占位符"""
    images = {}
    pattern = re.compile(
        r'(<img[^>]*?src=")(data:image/[^;]+;base64,[^"]+)("[^>]*>)',
        re.IGNORECASE
    )

    def _replacer(match):
        idx = len(images)
        images[f'IMG_{idx}'] = match.group(2)
        return f'{match.group(1)}##IMG_PLACEHOLDER_{idx}##{match.group(3)}'

    html_clean = pattern.sub(_replacer, html_content)
    return images, html_clean


def _restore_base64_images(html_content: str, images: dict[str, str]) -> str:
    """还原base64图片占位符"""
    if not images:
        return html_content
    for key, value in images.items():
        idx = key.split('_')[1]
        placeholder = f'##IMG_PLACEHOLDER_{idx}##'
        html_content = html_content.replace(placeholder, value)
    return html_content


def _extract_css(html_content: str) -> tuple[list[dict], str]:
    """抽取HTML中的所有<style>块"""
    css_blocks = []
    pattern = re.compile(
        r'(<style[^>]*>)(.*?)(</style>)',
        re.DOTALL | re.IGNORECASE
    )

    def _replacer(match):
        css_blocks.append({
            'full': match.group(0),
            'content': match.group(2),
        })
        return f'<!--CSS_BLOCK_{len(css_blocks) - 1}-->'

    html_without = pattern.sub(_replacer, html_content)
    return css_blocks, html_without


def _restore_css(html_content: str, css_blocks: list[dict]) -> str:
    """强制还原原始CSS，删除AI可能生成的多余style"""
    if not css_blocks:
        return html_content

    # Step 1: 尝试替换占位符
    for i, block in enumerate(css_blocks):
        placeholder = f'<!--CSS_BLOCK_{i}-->'
        html_content = html_content.replace(placeholder, block['full'])

    # Step 2: 删除所有style块（AI可能新增的）
    pattern = re.compile(r'<style[^>]*>.*?</style>', re.DOTALL | re.IGNORECASE)
    html_content = pattern.sub('', html_content)

    # Step 3: 在</head>前精确注入原始CSS
    head_close = html_content.find('</head>')
    if head_close != -1:
        for block in reversed(css_blocks):
            html_content = (
                html_content[:head_close] + '\n' + block['full'] + '\n' +
                html_content[head_close:]
            )

    return html_content


def _validate_structure(original: str, revised: str) -> tuple[bool, list[str]]:
    """验证修改后的HTML结构"""
    issues = []

    def _count_tags(html: str, tag_name: str) -> int:
        return len(re.findall(rf'<{tag_name}\b[^>]*>', html, re.IGNORECASE))

    def _has_class(html: str, class_name: str) -> int:
        return len(re.findall(
            rf'class=["\'][^"\']*{class_name}[^"\']*["\']',
            html, re.IGNORECASE
        ))

    # 关键标签检查
    for tag in ['html', 'body', 'head']:
        o = _count_tags(original, tag)
        r = _count_tags(revised, tag)
        if o > 0 and r == 0:
            issues.append(f"关键标签 <{tag}> 丢失")

    # h2 标签
    o_h2 = _count_tags(original, 'h2')
    r_h2 = _count_tags(revised, 'h2')
    if o_h2 > 0 and abs(o_h2 - r_h2) > 2:
        issues.append(f"<h2> 数量异常：{o_h2}→{r_h2}")

    # class='item'
    o_item = _has_class(original, 'item')
    r_item = _has_class(revised, 'item')
    if o_item > 0 and abs(o_item - r_item) > 3:
        issues.append(f"class='item' 异常：{o_item}→{r_item}")

    return len(issues) == 0, issues


def _accept_revision(html_content: str) -> str:
    """接受修改：删除del标签及其内容，删除ins标签保留内容"""
    # 删除 <del class="ai-change">...</del>
    clean = re.sub(
        r'<del\s+class="ai-change"[^>]*>.*?</del>',
        '', html_content,
        flags=re.DOTALL | re.IGNORECASE
    )
    # 删除 <ins class="ai-change"> 和 </ins>
    clean = re.sub(
        r'<ins\s+class="ai-change"[^>]*>', '', clean,
        flags=re.IGNORECASE
    )
    clean = re.sub(r'</ins>', '', clean, flags=re.IGNORECASE)
    return clean


DIFF_CSS = (
    '<style>'
    'del.ai-change{background:#fecaca!important;color:#991b1b!important;'
    'text-decoration:none!important;padding:1px 3px!important;border-radius:2px!important;}'
    'ins.ai-change{background:#bbf7d0!important;color:#166534!important;'
    'text-decoration:none!important;padding:1px 3px!important;border-radius:2px!important;'
    'font-weight:bold!important;}'
    '</style>'
)


class ReviseService:
    """AI简历修改服务"""

    async def revise(self, current_html: str, instruction: str) -> tuple[str | None, str]:
        """根据用户指令修改简历HTML

        返回: (revised_html, message)
        """
        if not current_html or not current_html.strip():
            return None, "简历内容为空"
        if not instruction or not instruction.strip():
            return None, "修改指令为空"

        # Step 0: 清理残留的diff CSS和del/ins标签
        current_html = re.sub(
            r'<style>[^<]*ai-change[^<]*</style>',
            '', current_html,
            flags=re.DOTALL | re.IGNORECASE
        )
        current_html = re.sub(
            r'</?del\s+class="ai-change"[^>]*>', '', current_html,
            flags=re.IGNORECASE
        )
        current_html = re.sub(
            r'</?ins\s+class="ai-change"[^>]*>', '', current_html,
            flags=re.IGNORECASE
        )

        # Step 1: 抽取base64图片
        images, html_noimg = _extract_base64_images(current_html)

        # Step 2: 抽取CSS
        css_blocks, html_clean = _extract_css(html_noimg)

        # Step 3: 构建prompt
        prompt = f"""你是一个专业的简历精修助手。你的任务是精准执行用户的修改指令。

【格式铁律 - 违反即失败】
以下规则优先级最高，遵守它们比完成修改指令更重要：
1. **禁止修改 <!--CSS_BLOCK_N--> 注释**：它们是样式占位符，绝对不能动。
2. **禁止修改 ##IMG_PLACEHOLDER_N## 标记**：它们是图片占位符。
3. **禁止修改 HTML 标签名**：h2 永远是 h2，不能变成 p、div 或其他。
4. **禁止修改 class 属性值**：所有 class="xxx" 必须保持原样。
5. **禁止添加 inline style**：不要在标签内写 style="..."。
6. **禁止删除或新增 HTML 标签**：保持原有标签结构。
7. **你只能修改标签之间的纯文字内容**。改文字时用 <del class="ai-change"> 和 <ins class="ai-change"> 包裹。

【修改标记规则】
- 删除旧文字：用 <del class="ai-change">旧文字</del> 包裹
- 新增文字：用 <ins class="ai-change">新文字</ins> 包裹
- 替换文字：<del class="ai-change">旧</del><ins class="ai-change">新</ins> 紧挨
- del/ins 标签必须放在现有HTML标签的内部，不能破坏标签嵌套
- 禁止使用 mark 标签，只能用 del 和 ins

【关键约束】
- 只改指令要求的内容，其他部分原封不动
- 保持原文的语言风格和口吻
- 如果指令要求缩短/精简，结果必须明显变短
- 禁止修改任何 style 或 CSS 相关内容

【用户修改指令】
{instruction}

【当前简历HTML】
{html_clean}"""

        try:
            html_content = await call_deepseek(prompt, max_tokens=16384)
        except Exception as e:
            return None, f"API调用失败: {str(e)}"

        if not html_content:
            return None, "API返回空内容"

        html_content = clean_html_response(html_content)

        # Step 4: 还原CSS
        html_content = _restore_css(html_content, css_blocks)

        # Step 5: 还原图片
        html_content = _restore_base64_images(html_content, images)

        # Step 6: 验证结构
        is_valid, issues = _validate_structure(current_html, html_content)
        if not issues:
            pass  # 结构完全正常

        # Step 7: 注入diff CSS
        html_content = html_content.replace('</head>', DIFF_CSS + '</head>', 1)

        return html_content, "修改成功"

    def accept(self, html_content: str) -> str | None:
        """接受所有修改，返回干净的HTML"""
        if not html_content:
            return None
        return _accept_revision(html_content)


revise_service = ReviseService()
