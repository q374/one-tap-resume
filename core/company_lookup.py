import urllib.parse

def lookup_company(name: str) -> str:
    """查询公司工商信息，返回格式化文本。"""
    if not name or not name.strip():
        return ""

    name = name.strip()
    lines = []

    aiqicha_url = f"https://aiqicha.baidu.com/s?q={urllib.parse.quote(name)}"
    tianyancha_url = f"https://www.tianyancha.com/search?key={urllib.parse.quote(name)}"

    lines.append(f"公司名称：{name}")
    lines.append(f"爱企查搜索：{aiqicha_url}")
    lines.append(f"天眼查搜索：{tianyancha_url}")
    lines.append(f"（注：详细工商数据需通过企业信用信息公示系统查询。本工具提供免费公开渠道的搜索链接，深度数据如参保人数需付费API。）")

    return "\n".join(lines)
