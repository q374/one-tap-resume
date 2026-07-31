"""Dify API 客户端 — 封装 Chatflow/Workflow 调用"""

import json
import httpx
from typing import AsyncIterator, Optional

# ============================================================
# Dify 配置 — 从环境变量读取，支持为每个 Agent 配置独立 API Key
# ============================================================

import os
from dotenv import load_dotenv

load_dotenv()

DIFY_BASE_URL = os.environ.get("DIFY_BASE_URL", "http://localhost/v1")

# Agent A: 公司洞察 (Workflow 型应用)
DIFY_COMPANY_AGENT_API_KEY = os.environ.get("DIFY_COMPANY_AGENT_API_KEY", "")

# Agent B: AI模拟面试官 (Chatflow 型应用)
DIFY_INTERVIEW_AGENT_API_KEY = os.environ.get("DIFY_INTERVIEW_AGENT_API_KEY", "")


async def run_workflow(
    api_key: str,
    inputs: dict,
    user: str = "default-user",
    response_mode: str = "blocking",
    timeout: int = 30,
) -> dict:
    """调用 Dify Workflow 型应用（非对话式，适合公司分析等单次任务）

    Args:
        api_key: Dify 应用的 API Secret
        inputs: 输入变量字典
        user: 用户标识
        response_mode: "blocking" 或 "streaming"
        timeout: 超时秒数

    Returns:
        Workflow 执行结果字典，包含 outputs
    """
    url = f"{DIFY_BASE_URL}/workflows/run"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": inputs,
        "response_mode": response_mode,
        "user": user,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            if response_mode == "blocking":
                # blocking 模式: data.outputs 包含输出变量
                data = result.get("data", {})
                return data.get("outputs", data)
            return result
        except httpx.HTTPStatusError as e:
            return {"error": f"Dify API 返回错误 ({e.response.status_code})", "detail": str(e)}
        except httpx.TimeoutException:
            return {"error": "Dify API 请求超时"}
        except Exception as e:
            return {"error": f"Dify API 调用失败: {str(e)}"}


async def run_chatflow_stream(
    api_key: str,
    query: str,
    conversation_id: str = "",
    inputs: Optional[dict] = None,
    user: str = "default-user",
    timeout: int = 120,
) -> AsyncIterator[str]:
    """调用 Dify Chatflow 型应用（流式对话，适合模拟面试等交互式任务）

    Args:
        api_key: Dify 应用的 API Secret
        query: 用户消息文本
        conversation_id: 会话ID（为空则新建会话）
        inputs: 输入变量字典
        user: 用户标识
        timeout: 超时秒数

    Yields:
        SSE 事件文本块
    """
    url = f"{DIFY_BASE_URL}/chat-messages"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": inputs or {},
        "query": query,
        "response_mode": "streaming",
        "conversation_id": conversation_id,
        "user": user,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        if data_str:
                            yield data_str
        except httpx.HTTPStatusError as e:
            yield json.dumps({"event": "error", "message": f"Dify API error: {e.response.status_code}"})
        except httpx.TimeoutException:
            yield json.dumps({"event": "error", "message": "Dify API timeout"})
        except Exception as e:
            yield json.dumps({"event": "error", "message": str(e)})


async def run_chatflow_blocking(
    api_key: str,
    query: str,
    conversation_id: str = "",
    inputs: Optional[dict] = None,
    user: str = "default-user",
    timeout: int = 180,
) -> dict:
    """调用 Dify Chatflow/Agent 型应用（阻塞模式，返回完整结果）

    Dify Agent 型应用只支持 streaming，本函数内部使用流式调用，
    收集所有 SSE 事件后返回最终结果。
    """
    chunks = []
    final_answer = ""
    final_conversation_id = conversation_id
    async for chunk in run_chatflow_stream(
        api_key=api_key, query=query, conversation_id=conversation_id,
        inputs=inputs, user=user, timeout=timeout,
    ):
        chunks.append(chunk)
        try:
            event = json.loads(chunk)
            if event.get("event") == "message":
                final_answer = event.get("answer", final_answer) or final_answer
                final_conversation_id = event.get("conversation_id", final_conversation_id)
            elif event.get("event") == "agent_message":
                final_answer = event.get("answer", final_answer) or final_answer
            elif event.get("event") == "error":
                return {"error": event.get("message", "Dify streaming error"), "answer": final_answer}
        except json.JSONDecodeError:
            pass

    if not final_answer and chunks:
        # Fallback: try to extract answer from last chunk
        for chunk in reversed(chunks):
            try:
                ev = json.loads(chunk)
                ans = ev.get("answer", "")
                if ans:
                    final_answer = ans
                    break
            except json.JSONDecodeError:
                pass

    return {
        "answer": final_answer,
        "conversation_id": final_conversation_id,
        "error": "" if final_answer else "No answer received from Dify",
    }
