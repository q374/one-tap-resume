"""面试出题质量测试 — 验证JD相关性和对话自然度（真实DeepSeek集成测试，默认跳过）"""
import sys, os, asyncio, json
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.deepseek_client import call_deepseek_json, call_deepseek
from prompts.interview import build_interview_prompt

# 候选人的通用经历
EXPERIENCE = """姓名：李明
电话：13800138000 | 邮箱：liming@email.com | 年龄：28 | 求职意向：软件开发

教育背景：
华中科技大学 软件工程 本科 2016.09-2020.06

工作经历：
1. 字节跳动 后端开发工程师 2023.07-至今：负责推荐系统后台开发，设计并实现了高并发API网关，日均处理千万级请求；使用Go重构了核心推荐链路，延迟降低了60%
2. 美团 Java开发实习 2022.06-2022.09：参与订单系统开发，负责支付模块的设计与实现

项目经历：
1. 电商后台系统（后端负责人）：背景-旧系统性能瓶颈导致双11宕机；动作-主导架构设计，从单体拆分为微服务，独立完成核心模块开发；成果-QPS从1000提升至10000；技术栈-Python FastAPI PostgreSQL Redis Docker K8s
2. 实时数据处理平台（核心开发者）：背景-业务方需要实时报表；动作-设计并实现了基于Kafka+Flink的流处理管道；成果-报表延迟从T+1降至秒级；技术栈-Java Kafka Flink ClickHouse

技能：
Python（精通，3个商业项目后端）、Go（熟练，重构过推荐链路）、Java（熟练）、Kubernetes（熟练，管理过50+节点集群）

自我评价：
五年后端开发经验，主导过日均千万级请求的分布式系统架构设计。追求代码质量和系统稳定性。"""

# 测试JD列表
TEST_JDS = [
    {
        "name": "Python后端",
        "jd": """职位：Python后端开发工程师
岗位职责：
1. 负责公司核心业务系统的后端设计与开发
2. 参与系统架构设计，保证系统的高可用和高性能
3. 编写技术文档，参与代码评审
任职要求：
1. 3年以上Python开发经验，熟悉FastAPI/Django框架
2. 熟练使用MySQL、Redis等数据库，有性能优化经验
3. 有分布式系统和微服务架构经验优先
4. 熟悉Docker、Kubernetes容器化部署
5. 良好的沟通能力和团队协作精神"""
    },
    {
        "name": "数据分析",
        "jd": """职位：数据分析师
岗位职责：
1. 负责业务数据的采集、清洗和分析，产出数据报告
2. 搭建数据指标体系，监控业务健康度
3. 与产品、运营团队协作，通过数据驱动业务决策
任职要求：
1. 2年以上数据分析经验
2. 精通SQL，熟练使用Python进行数据处理
3. 熟悉Tableau/PowerBI等可视化工具
4. 有统计学基础，了解AB测试原理
5. 逻辑清晰，有良好的数据敏感度"""
    },
    {
        "name": "Go后端",
        "jd": """职位：Go后端开发工程师
岗位职责：
1. 负责公司推荐系统后台服务的开发与维护
2. 优化系统性能，解决高并发场景下的技术挑战
3. 参与技术方案设计和评审
任职要求：
1. 3年以上Go开发经验
2. 熟悉微服务架构，有分布式系统设计经验
3. 熟练使用消息队列（Kafka/RabbitMQ）
4. 熟悉Linux操作系统，有性能调优经验
5. 加分项：有大厂推荐系统开发经验"""
    }
]


# 依赖真实 DeepSeek API（慢、耗token），默认跳过；需要验证出题质量时去掉 skip 或加 -m interview 运行
pytestmark = pytest.mark.skip(reason="真实DeepSeek集成测试，默认跳过；按需运行")


@pytest.mark.parametrize("jd_info", TEST_JDS)
async def test_jd_questions(jd_info):
    """测试单个JD的面试题生成质量"""
    prompt = build_interview_prompt(EXPERIENCE, jd_info["jd"])
    result = await call_deepseek_json(prompt)

    tech = result.get("tech_questions", [])
    project = result.get("project_deep_dive", [])
    behavior = result.get("behavioral_questions", [])
    all_qs = tech + project + behavior

    print(f"\n{'='*60}")
    print(f"📋 {jd_info['name']}")
    print(f"{'='*60}")
    print(f"总题数: {len(all_qs)} (技术{len(tech)} + 项目{len(project)} + 行为{len(behavior)})")

    # JD关键词提取
    jd_keywords = []
    for kw in ["Python", "FastAPI", "Django", "Go", "Java", "MySQL", "Redis", "Kafka",
               "Docker", "Kubernetes", "微服务", "分布式", "高并发", "SQL", "Tableau",
               "AB测试", "K8s", "性能优化", "数据分析", "推荐系统", "消息队列", "Flink"]:
        if kw.lower() in jd_info["jd"].lower():
            jd_keywords.append(kw)

    # 检查题目是否覆盖JD关键词
    covered = []
    missed = []
    for kw in jd_keywords:
        found = any(kw.lower() in q.get("question", "").lower() or
                   kw.lower() in q.get("purpose", "").lower()
                   for q in all_qs)
        if found:
            covered.append(kw)
        else:
            missed.append(kw)

    print(f"JD关键词: {jd_keywords}")
    print(f"覆盖: {covered}")
    print(f"未覆盖: {missed}")

    # 展示题目
    print("\n--- 技术题 ---")
    for i, q in enumerate(tech):
        print(f"  {i+1}. {q['question'][:120]}")
        print(f"     考察: {q.get('purpose', '')[:80]}")
    print("\n--- 项目深挖 ---")
    for i, q in enumerate(project):
        print(f"  {i+1}. {q['question'][:120]}")
    print("\n--- 行为/动机 ---")
    for i, q in enumerate(behavior):
        print(f"  {i+1}. {q['question'][:120]}")

    # 质量评分
    score = 0
    max_score = 4

    # 1. JD覆盖率 (关键词覆盖超过60%)
    coverage = len(covered) / len(jd_keywords) if jd_keywords else 0
    if coverage >= 0.6:
        score += 1
        print(f"  ✅ JD覆盖: {coverage:.0%}")
    else:
        print(f"  ❌ JD覆盖: {coverage:.0%}")

    # 2. 题目总数合理 (5-10)
    if 5 <= len(all_qs) <= 10:
        score += 1
        print(f"  ✅ 题数合理: {len(all_qs)}")
    else:
        print(f"  ❌ 题数: {len(all_qs)} (应5-10)")

    # 3. 技术题足够 (至少占30%)
    if len(tech) >= len(all_qs) * 0.3:
        score += 1
        print(f"  ✅ 技术题占比: {len(tech)/len(all_qs):.0%}")
    else:
        print(f"  ❌ 技术题占比不足")

    # 4. 没有问JD没要求的技能
    jd_skills = set()
    for kw in jd_keywords:
        jd_skills.add(kw.lower())
    extra_skills = set()
    for q in all_qs:
        qt = q.get("question", "") + q.get("purpose", "")
        for word in ["Python", "Go", "Java", "Spark", "Hadoop", "TensorFlow", "React", "Vue"]:
            if word.lower() in qt.lower() and word.lower() not in jd_skills:
                extra_skills.add(word)
    if not extra_skills:
        score += 1
        print(f"  ✅ 无多余技能")
    else:
        print(f"  ⚠️ 额外提到: {extra_skills}")

    print(f"\n  质量分: {score}/{max_score}")
    return {"name": jd_info["name"], "score": score, "max": max_score,
            "total_q": len(all_qs), "coverage": coverage, "covered": covered, "missed": missed}


async def test_followup():
    """测试追问的自然度"""
    print(f"\n{'='*60}")
    print(f"💬 追问自然度测试")
    print(f"{'='*60}")

    test_cases = [
        ("能说说你是怎么排查线上性能问题的吗？", "我们主要通过监控告警发现，然后用链路追踪定位到慢SQL，加了索引和缓存之后就好了，QPS恢复到了正常水平。",
         "详细但可以追问具体工具"),
        ("你做的微服务拆分，具体是怎么决定的？", "按业务拆的。",
         "太简短，AI应该追问"),
    ]

    for q, a, desc in test_cases:
        print(f"\n--- {desc} ---")
        print(f"  问: {q}")
        print(f"  答: {a}")

        prompt = f"""你正在面试一位候选人。面试氛围是专业但轻松的。

你刚才问的问题：
"{q}"

候选人的回答：
"{a}"

【你的任务】
1. 先简短自然地对候选人的回答做一个回应
2. 然后决定下一步：追问（__FOLLOWUP__）或进入下一题（__NEXT__）

先写回应，再写__FOLLOWUP__或__NEXT__。"""

        resp = await call_deepseek(prompt, max_tokens=200)
        print(f"  AI: {resp[:200]}")


async def main():
    results = []
    for jd in TEST_JDS:
        results.append(await test_jd_questions(jd))

    await test_followup()

    print(f"\n{'='*60}")
    print(f"📊 总结")
    print(f"{'='*60}")
    avg = sum(r['score'] for r in results) / len(results)
    for r in results:
        print(f"  {r['name']}: {r['score']}/{r['max']} | JD覆盖率 {r['coverage']:.0%} | 题数 {r['total_q']}")
    print(f"  平均分: {avg:.1f}/{results[0]['max']}")

if __name__ == "__main__":
    asyncio.run(main())
