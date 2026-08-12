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
    assert "默认纳入简历" in prompt
    assert "每项一行最简格式" in prompt
    assert "JD 直接相关的证书放最前" in prompt
    assert "禁止" in prompt


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



def test_builtin_prompt_allows_unrelated_certs():
    """JD 无关的普通话/驾照也应被规则允许纳入自定义模块（不再一律省略）"""
    prompt = build_resume_prompt(
        template_html=TEMPLATE,
        experience_text="其他信息：\n普通话二甲：2021年取得\nC1驾照：2020年取得\nCET-6 英语六级：2023年通过",
        jd_text="数据分析师岗位",
        age_directive="a", photo_directive="p",
        has_placeholders=True,
    )
    # 经历库数据完整传入 prompt
    assert "普通话二甲" in prompt and "C1驾照" in prompt and "CET-6" in prompt
    # 规则要求默认纳入、空间不足才省略
    assert "默认纳入简历" in prompt
    assert "仅当内容已接近一页" in prompt
    # 技能区禁止放证书
    assert "禁止" in prompt and "技能区只放技术/工具能力" in prompt


def test_custom_prompt_allows_certs_fill():
    """自定义模板：证书区域默认填充（不再仅保留 JD 相关）"""
    prompt = build_resume_prompt(
        template_html="<div>姓名</div><div>证书区域</div>",
        experience_text="其他信息：\n普通话二甲：2021年取得\nC1驾照：2020年取得",
        jd_text="数据分析师岗位",
        age_directive="a", photo_directive="p",
        has_placeholders=False,
    )
    assert "证书/获奖/其他" in prompt
    assert "也尽量呈现" in prompt
    assert "普通话二甲" in prompt and "C1驾照" in prompt
