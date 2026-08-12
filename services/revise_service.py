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

        # Step 3b: 调用 AI 生成带 del/ins diff 标记的修改
        # AI 偶发"只改文字不加标记"，检测到无任何 diff 标记时用更强提示重试 1 次
        html_content = None
        for _attempt in range(2):
            try:
                html_content = await call_deepseek(prompt, max_tokens=16384)
            except Exception as e:
                return None, f"API调用失败: {str(e)}"
            if not html_content:
                return None, "API返回空内容"
            html_content = clean_html_response(html_content)
            if "<del" in html_content or "<ins" in html_content:
                break
            if _attempt == 0:
                prompt += '\n\n【再次强调，违反即失败】你刚才的输出没有任何 <del class="ai-change"> / <ins class="ai-change"> 标记。本次修改必须：删除旧文字用 <del class="ai-change">旧文字</del> 包裹、新增文字用 <ins class="ai-change">新文字</ins> 包裹。即使只改一个词也必须用标记，绝不允许直接替换文字而不加标记。'

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

    async def expand(self, current_html: str, jd_text: str = "") -> tuple[str | None, str]:
        """AI 自动扩写：内容不足一页时，基于真实经历把描述写得更饱满（不编造事实）

        返回: (expanded_html, message)
        """
        if not current_html or not current_html.strip():
            return None, "简历内容为空"

        current_html = _accept_revision(current_html)
        images, html_noimg = _extract_base64_images(current_html)
        css_blocks, html_clean = _extract_css(html_noimg)

        prompt = f"""你是一个简历内容丰富化助手。当前简历内容不足 A4 一页，请基于现有真实内容扩写，使内容更饱满、接近一页。

【扩写策略】（按优先级）
1. 每条项目/实习要点补充更多细节：具体场景、执行过程、使用的方法与工具、量化结果
2. 项目经历若要点不足 3 条，补充到 3-4 条（用已有信息合理展开）
3. 技能区每条技能补充简短说明（不超过8字）
4. 自我评价扩写到 2-3 句话
5. 教育背景、实习经历、获奖情况可补充时间、职责等合理描述

【真实性铁律】
- 只基于简历中已有的信息扩写句式与表述，把话说完整、说具体
- **禁止新增任何具体数字、项目、公司、学校、奖项、证书等事实性信息**
- 禁止编造经历、禁止无中生有

【格式铁律 - 违反即失败】
1. **禁止修改 <!--CSS_BLOCK_N--> 注释**（样式占位符）
2. **禁止修改 ##IMG_PLACEHOLDER_N## 标记**（图片占位符）
3. **禁止修改 HTML 标签名和 class 属性值**，禁止添加 inline style
4. **禁止删除 html/head/body 等外层结构标签**
5. **禁止出现任何 Markdown 标记（**、*、#）**
6. 直接输出扩写后的完整 HTML，不要用 del/ins 标记，不要任何解释

【目标岗位JD】（用于组织扩写侧重点）
{jd_text or "（无，按通用简历标准）"}

【当前简历HTML】
{html_clean}"""

        try:
            html_content = await call_deepseek(prompt, max_tokens=16384)
        except Exception as e:
            return None, f"API调用失败: {str(e)}"
        if not html_content:
            return None, "API返回空内容"

        html_content = clean_html_response(html_content)
        html_content = _restore_css(html_content, css_blocks)
        html_content = _restore_base64_images(html_content, images)

        is_valid, issues = _validate_structure(current_html, html_content)
        return html_content, "扩写成功"

    async def trim(self, current_html: str, jd_text: str = "") -> tuple[str | None, str]:
        """AI 自动精简简历以适配一页（直接输出干净HTML，无 diff 标记）

        返回: (trimmed_html, message)
        """
        if not current_html or not current_html.strip():
            return None, "简历内容为空"

        # 先清掉可能残留的 diff 标记，保证干净输入
        current_html = _accept_revision(current_html)

        # 抽取 base64 图片与 CSS（保护机制，与 revise 一致）
        images, html_noimg = _extract_base64_images(current_html)
        css_blocks, html_clean = _extract_css(html_noimg)

        prompt = f"""你是一个简历精简助手。当前简历内容超出 A4 一页，请自动精简使它刚好能放进一页。

【精简策略】（按优先级执行）
1. 优先删除 P2 次要模块（获奖、证书、社团活动等非核心模块），可整体删除整个模块（含其 h2 标题和内容）
2. 项目/实习经历最多保留 3 条与目标岗位最相关的，其余整个条目删除
3. 每条要点压缩到最短：删掉修饰词、合并重复信息，保留量化成果和关键动作
4. 技能区只保留最相关的 6-8 项
5. 自我评价压缩到一句话
6. 只删减/压缩已有内容，绝不编造任何数据、经历或技能

【格式铁律 - 违反即失败】
1. **禁止修改 <!--CSS_BLOCK_N--> 注释**（样式占位符）
2. **禁止修改 ##IMG_PLACEHOLDER_N## 标记**（图片占位符）
3. **禁止修改 HTML 标签名和 class 属性值**，禁止添加 inline style
4. **禁止删除 html/head/body 等外层结构标签**
5. **禁止出现任何 Markdown 标记（**、*、#）**
6. 直接输出精简后的完整 HTML，不要用 del/ins 标记，不要任何解释

【目标岗位JD】（用于判断哪些内容最相关）
{jd_text or "（无，按通用简历标准精简）"}

【当前简历HTML】
{html_clean}"""

        try:
            html_content = await call_deepseek(prompt, max_tokens=16384)
        except Exception as e:
            return None, f"API调用失败: {str(e)}"
        if not html_content:
            return None, "API返回空内容"

        html_content = clean_html_response(html_content)
        html_content = _restore_css(html_content, css_blocks)
        html_content = _restore_base64_images(html_content, images)

        is_valid, issues = _validate_structure(current_html, html_content)
        return html_content, "精简成功"

    def accept(self, html_content: str) -> str | None:
        """接受所有修改，返回干净的HTML"""
        if not html_content:
            return None
        return _accept_revision(html_content)


revise_service = ReviseService()
