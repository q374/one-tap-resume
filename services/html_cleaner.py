import re


def clean_html_response(html_content):
    """清洗AI返回的HTML响应，去除markdown代码块、多余文本和AI套话"""
    if html_content is None:
        return None

    html_content = html_content.strip()

    html_content = re.sub(r'^```html\s*', '', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^```\s*$', '', html_content, flags=re.MULTILINE)

    start_idx = html_content.lower().find('<!doctype')
    if start_idx == -1:
        start_idx = html_content.lower().find('<html')
    if start_idx == -1:
        start_idx = 0

    end_idx = html_content.lower().rfind('</html>')
    if end_idx != -1:
        end_idx += len('</html>')
    else:
        end_idx = len(html_content)

    html_content = html_content[start_idx:end_idx].strip()

    buzzword_replacements = {
        '复盘': '总结', '落地': '实现', '产出': '完成', '迭代': '改进',
        '优化': '改进', '重构': '重新设计', '复用': '重复使用', '升级': '更新',
        '从0到1': '从零开始', '赋能': '支持', '闭环': '完整流程', '抓手': '切入点',
        '对齐': '协调', '沉淀': '积累', '拉齐': '统一', '打通': '连接',
        '数据驱动': '以数据为依据', '结果导向': '注重结果', '用户思维': '用户视角',
        '产品思维': '产品视角', '商业思维': '商业视角', '闭环思维': '系统化思维',
        '链路思维': '流程思维',
    }

    for buzzword, replacement in buzzword_replacements.items():
        html_content = html_content.replace(buzzword, replacement)

    absolute_guarantees = {
        '保证完成': '确保完成', '保证实现': '确保实现', '保证达成': '确保达成',
        '保证成功': '力求成功', '保证质量': '确保质量', '保证按时': '确保按时',
        '一定完成': '确保完成', '一定会': '将会', '肯定能': '力求',
        '绝对': '',
    }

    for phrase, replacement in absolute_guarantees.items():
        html_content = html_content.replace(phrase, replacement)

    unprofessional_phrases = {
        '我觉得': '', '我认为': '', '我感觉': '', '我想': '',
        '希望能': '', '希望可以': '', '希望能够': '', '我希望': '', '我期望': '',
        '我打算': '', '我计划': '', '我准备': '', '我要': '', '我会': '',
        '我可以': '', '我能够': '', '我愿意': '',
        '非常': '', '十分': '', '特别': '', '很': '', '超级': '', '巨': '', '贼': '',
        '真的': '', '确实': '', '事实上': '', '其实': '',
        '说实话': '', '实话说': '', '老实说': '', '说白了': '',
        '总之': '', '总而言之': '', '综上所述': '', '话不多说': '', '言归正传': '',
        '简单来说': '', '简而言之': '', '值得一提的是': '', '需要指出的是': '',
        '必须强调的是': '', '不可否认': '', '毫无疑问': '', '毋庸置疑': '',
        '显而易见': '', '不难看出': '', '可以看出': '', '不难发现': '', '由此可见': '',
    }

    for phrase, replacement in unprofessional_phrases.items():
        html_content = html_content.replace(phrase, replacement)

    # 兜底：清除 AI 误写入可见文本的 Markdown 粗体标记（**xxx** 应已由 <strong> 实现）
    html_content = html_content.replace('**', '')

    # 剥离项目要点开头的"标签："前缀（经验总结：/核心动作：/量化成果：/技术工具：等）
    html_content = re.sub(
        r'(<strong>|<li>)\s*(核心动作|量化成果|技术工具|技术/工具|背景与动作|经验总结|数据支持)\s*[:：]\s*',
        r'\1',
        html_content
    )

    return html_content



def validate_html(html_content):
    """验证HTML内容完整性"""
    required_tags = ['<html', '</html>', '<head', '</head>', '<body', '</body>', '<!DOCTYPE']

    for tag in required_tags:
        if tag.lower() not in html_content.lower():
            return False, f"缺少必要标签: {tag}"

    if not html_content.strip().startswith('<!DOCTYPE') and not html_content.strip().startswith('<html'):
        return False, "HTML结构不完整，缺少DOCTYPE声明"

    return True, "验证通过"


def validate_content_authenticity(html_content, experience_content):
    """验证生成内容与原始经历的一致性"""
    experience_lower = experience_content.lower()
    html_lower = html_content.lower()

    experience_keywords = set()
    for word in re.findall(r'[一-龥]{2,}|[a-zA-Z]{3,}', experience_content):
        experience_keywords.add(word.lower())

    if len(experience_keywords) < 3:
        return True, "经历内容过少，跳过真实性验证"

    found_keywords = 0
    for keyword in experience_keywords:
        if keyword in html_lower:
            found_keywords += 1

    if found_keywords == 0:
        return False, "生成内容中未找到经历库中的关键词"

    return True, f"验证通过，匹配到 {found_keywords} 个关键词"
