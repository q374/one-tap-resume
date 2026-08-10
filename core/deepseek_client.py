import json
import re
from openai import AsyncOpenAI
from config import API_KEY, BASE_URL, MODEL_NAME

_client: AsyncOpenAI | None = None

def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=API_KEY,
            base_url=BASE_URL,
            timeout=120.0,
            max_retries=3,
        )
    return _client


async def call_deepseek(
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.1,
    max_tokens: int = 4096,
) -> str:
    """调用 DeepSeek API，返回纯文本响应"""
    client = _get_client()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


async def call_deepseek_json(
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.1,
) -> dict:
    """调用 DeepSeek API 并要求返回 JSON"""
    json_prompt = prompt + "\n\n请只返回JSON格式，不要包含任何其他文字、markdown代码块或解释。直接以 { 或 [ 开头。"
    text = await call_deepseek(
        prompt=json_prompt,
        system_prompt=system_prompt,
        temperature=temperature,
    )

    # 清洗可能的 markdown 代码块
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```$', '', text.strip())

    # 提取第一个完整 JSON 值（raw_decode 替代贪婪正则，容忍前后夹解释/纯文本）
    return _extract_json(text)


def _extract_json(text: str):
    """从 AI 响应中提取第一个完整的 JSON 值"""
    decoder = json.JSONDecoder()
    candidates = []
    for start in ('{', '['):
        idx = text.find(start)
        if idx != -1:
            candidates.append((start, idx))
    if not candidates:
        raise ValueError(f"AI 响应中未找到有效 JSON：{text[:200]}...")
    # 按出现位置最靠前的起始符优先解析（数组输入时避免误取内部对象）
    candidates.sort(key=lambda c: c[1])
    for _start, idx in candidates:
        try:
            obj, _end = decoder.raw_decode(text[idx:])
            return obj
        except json.JSONDecodeError:
            continue
    raise ValueError(f"AI 响应中未找到有效 JSON：{text[:200]}...")
