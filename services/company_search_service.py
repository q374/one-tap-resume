"""公司洞察服务 — 生成6模块结构化分析报告

支持两种后端：
  - Dify Workflow (优先，如已配置 DIFY_COMPANY_AGENT_API_KEY)
  - DeepSeek 直接调用 (降级方案)
"""

from core.deepseek_client import call_deepseek
from services.dify_client import run_chatflow_blocking, DIFY_COMPANY_AGENT_API_KEY


COMPANY_REPORT_PROMPT = """你是一位专业的求职顾问和企业分析师。请基于你对以下公司的了解，生成一份结构化分析报告。

【公司名称】
{company_name}

【所在地】
{location}

【分析要求】
请按以下6个模块输出报告。如果某个模块无法获取信息，请诚实标注（见下方各模块说明）。

---

## 🏢 公司概览
- 行业分类
- 大致规模（人员规模、业务范围）
- 融资阶段（如能判断）
- 成立时间
- 如信息不足，标注：此部分为AI推测，建议通过天眼查核实

## 📰 近期动态
- 近6个月的重要新闻（扩招/裁员/新产品/融资等）
- ⚠️ 标注：此部分基于AI训练数据，可能不是最新信息。建议通过天眼查等平台查询最新动态。

## 💬 舆论风向
- 员工口碑关键词（基于脉脉、知乎等平台的公开讨论记忆）
- 标注情感倾向（正面/中性/负面）
- 每条信息标注来源类型（如"据知乎网友反馈"、"脉脉讨论中提及"）
- 如信息不足，标注：暂无足够公开讨论信息

## 💰 薪资参考
- 招聘平台或公开渠道的薪酬范围（如能获取）
- 标注数据来源和时效性
- 如信息不足，标注：建议通过Boss直聘、拉勾等招聘平台查询该公司的薪资范围

## ⚠️ 注意事项
- 风险提示（法律诉讼、经营异常等公开信息）
- 相关讨论中的集中槽点
- 如有多个同名公司，请提示用户确认公司全称和所在地

## 📋 声明
本报告基于公开信息自动生成，仅供参考，不构成任何建议。部分数据可能不是最新信息，建议结合天眼查、爱企查等平台的最新工商数据进行综合判断。

---

【输出格式要求】
- 直接输出 Markdown 格式的完整报告
- 所有关键信息尽量标注来源（如"据XX平台信息"）
- 无法确认的信息标注不确定性
- 语言客观中立，不制造恐慌也不盲目乐观
- 使用emoji作为模块图标，增强可读性"""


async def analyze_company(company_name: str, location: str = "") -> dict:
    """分析公司，返回6模块结构化报告

    Args:
        company_name: 公司全称
        location: 公司所在地（选填）

    Returns:
        {"success": bool, "report": str, "company_name": str, "source": "dify"|"deepseek", "error": str}
    """
    if not company_name or not company_name.strip():
        return {"success": False, "error": "请输入公司名称", "report": "", "company_name": ""}

    company_name = company_name.strip()
    location = location.strip() if location else "未指定"

    # 方案1: 尝试 Dify Agent（如果已配置）
    if DIFY_COMPANY_AGENT_API_KEY:
        result = await run_chatflow_blocking(
            api_key=DIFY_COMPANY_AGENT_API_KEY,
            query=f"请分析以下公司：{company_name}，所在地：{location}",
            timeout=180,
        )
        if "error" not in result or not result.get("error"):
            report = result.get("answer", "")
            if report:
                return {
                    "success": True,
                    "report": report,
                    "company_name": company_name,
                    "source": "dify",
                }

    # 方案2: 降级为 DeepSeek 直接调用
    prompt = COMPANY_REPORT_PROMPT.format(
        company_name=company_name,
        location=location,
    )
    try:
        report = await call_deepseek(prompt, max_tokens=4096)
        if report:
            return {
                "success": True,
                "report": report,
                "company_name": company_name,
                "source": "deepseek",
            }
        else:
            return {
                "success": False,
                "error": "AI 生成报告失败，请稍后重试",
                "report": "",
                "company_name": company_name,
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"分析失败: {str(e)}",
            "report": "",
            "company_name": company_name,
        }
