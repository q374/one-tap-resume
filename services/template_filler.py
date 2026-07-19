"""自定义模板填充器 — 将模板文字替换为占位符，AI只出文本，代码负责拼回HTML"""

import re
from core.deepseek_client import call_deepseek


def _extract_text_segments(html: str) -> tuple[list[str], str]:
    """提取HTML中所有标签间的文字内容，替换为 __SEG_N__ 占位符

    返回: (segments, skeleton_html)
    segments[i] = 原始文字
    skeleton_html 中对应位置为 __SEG_N__
    """
    segments = []

    def _replacer(match):
        text = match.group(1)
        stripped = text.strip()
        if not stripped:
            # 保留空白换行
            return match.group(0)

        idx = len(segments)
        segments.append(stripped)
        before = match.group(0)[:match.group(0).find(text)]
        after = match.group(0)[match.group(0).find(text) + len(text):]
        return f'{before}__SEG_{idx}__{after}'

    # 匹配 > 和 < 之间的文本
    pattern = re.compile(r'>([^<]+)<', re.DOTALL)
    skeleton = pattern.sub(_replacer, html)

    return segments, skeleton


def build_filler_prompt(segments: list[str], experience_text: str, jd_text: str) -> str:
    """构建「只返回文字内容」的 prompt"""
    seg_list = '\n'.join([f'[SEG_{i}] {s}' for i, s in enumerate(segments) if s.strip()])

    return f"""你是简历内容撰写助手。下面是一份简历模板中需要填充的文字段落。

**你的任务**：对每个 [SEG_N] 段落，用【个人经历库】中的真实经历重新撰写，保留原段落的结构风格，只替换内容。

**规则**：
- 每个段落保持与原文相同的篇幅（段落数量不增不减）
- 保留原文的 HTML 内联标签（如 <strong>、<em>）不做改动
- 用经历库中的真实数据替换示例内容
- 如果某段落与经历库无关（如联系方式、姓名等），在输出中标注 KEEP 保持不变
- 根据 JD 调整措辞侧重点
- 语言自然，避免套话

**输出格式**（严格遵守）：
对每个 [SEG_N] 返回一行：
SEG_N: 替换后的文本
如果不需要替换，返回：
SEG_N: KEEP

【经历库】
{experience_text}

【目标JD】
{jd_text}

【待填充段落】
{seg_list}

请按 SEG_N: 格式逐行输出，不要加任何额外解释。"""


def parse_filler_response(response: str, segments: list[str]) -> list[str]:
    """解析 AI 返回的 SEG_N: text 格式响应"""
    result = segments.copy()  # 默认保持原样

    for line in response.strip().split('\n'):
        line = line.strip()
        match = re.match(r'SEG_(\d+):\s*(.*)', line)
        if match:
            idx = int(match.group(1))
            text = match.group(2).strip()
            if 0 <= idx < len(segments) and text and text != 'KEEP':
                result[idx] = text

    return result


def _sanitize(text: str) -> str:
    """清理文本中的非法 Unicode 代理字符"""
    try:
        return text.encode('utf-8', errors='surrogateescape').decode('utf-8', errors='replace')
    except Exception:
        return text


def _rebuild_html(skeleton: str, filled_segments: list[str]) -> str:
    """将填充后的文字放回 HTML 骨架"""
    html = skeleton
    for i, text in enumerate(filled_segments):
        html = html.replace(f'__SEG_{i}__', _sanitize(text))
    return html


async def fill_custom_template(template_html: str, experience_text: str,
                               jd_text: str) -> str | None:
    """自定义模板填充主流程

    1. 抽取模板文字 → 占位符骨架
    2. AI 只生成每个段落的替换文本
    3. 把 AI 文本拼回 HTML 骨架

    返回完整 HTML，失败返回 None
    """
    segments, skeleton = _extract_text_segments(template_html)

    if not segments:
        return template_html  # 模板无文字，直接返回

    prompt = build_filler_prompt(segments, experience_text, jd_text)

    try:
        response = await call_deepseek(prompt, max_tokens=8192)
    except Exception:
        return None

    if not response:
        return None

    filled = parse_filler_response(response, segments)
    html = _rebuild_html(skeleton, filled)
    return html
