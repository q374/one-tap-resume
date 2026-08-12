# -*- coding: utf-8 -*-
"""「证书与其他信息」生成规则测试：prompt 包含规则 + 生成流程携带其他信息数据"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import io as _io

from prompts.resume_generation import build_resume_prompt

TEMPLATE = _io.open(os.path.join(os.path.dirname(__file__), "..", "templates", "default.html"),
                    encoding="utf-8", newline="").read()


def test_builtin_prompt_contains_others_rule():
    prompt = build_resume_prompt(
        template_html=TEMPLATE, experience_text="其他信息：\nCET-6 英语六级：2023年通过",
        jd_text="要求英语六级", age_directive="a", photo_directive="p",
        has_placeholders=True,
    )
    assert "证书与其他信息规则" in prompt
    assert "{{自定义模块}}" in prompt
    assert "JD 明确要求或高度相关" in prompt
    assert "每项一行最简格式" in prompt
    assert "与 JD 无关的其他信息一律省略" in prompt


def test_custom_prompt_contains_others_rule():
    prompt = build_resume_prompt(
        template_html="<div>姓名</div><div>证书区域</div>",
        experience_text="其他信息：\nCET-6 英语六级",
        jd_text="要求英语六级", age_directive="a", photo_directive="p",
        has_placeholders=False,
    )
    assert "证书/获奖/其他" in prompt
    assert "不要新增区域" in prompt


def test_generate_flow_carries_others_text(monkeypatch):
    """mock DeepSeek：生成流程能携带「其他信息」数据且不崩"""
    async def fake_call_deepseek(prompt, max_tokens=0):
        # 简单有效的简历 HTML
        return "<html><body><h1>张三</h1><p>数据分析师</p></body></html>"
    monkeypatch.setattr("services.resume_service.call_deepseek", fake_call_deepseek)

    import asyncio
    from services.resume_service import resume_service
    exp_text = "姓名：张三\n教育背景：\n某大学，计算机，本科，2019-2023\n其他信息：\nCET-6 英语六级：2023年通过\n普通话二甲：2021年取得"
    result = asyncio.run(resume_service.generate(
        template_html=TEMPLATE, experience_text=exp_text,
        jd_text="数据分析师，要求英语六级",
    ))
    assert result["html"] is not None, result.get("issues")
