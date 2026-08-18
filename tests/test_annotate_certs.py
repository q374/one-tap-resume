# -*- coding: utf-8 -*-
"""硬过滤单测：与JD无关的职业资格证标注为『禁止写入简历』"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.resume_service import _annotate_irrelevant_certs


JD_AI = "AI产品实习生：负责AI产品需求分析、PRD撰写、用户调研、数据分析，跟进模型迭代"


def test_海员证被标注():
    exp = "其他信息：\n海员证：无限航区\n四小证（船舶消防/救生艇筏/基本急救/个人安全）：有\n体检：2024年\n"
    out = _annotate_irrelevant_certs(exp, JD_AI)
    assert "禁止写入简历" in out
    assert "海员证" in out and "禁止写入简历" in out
    assert "四小证" in out and "禁止写入简历" in out


def test_无关证书被标注_语言等级保留():
    exp = "其他信息：\nCET-6 英语六级：550分\n普通话二级甲等：2024\nC1驾照：2021\n"
    out = _annotate_irrelevant_certs(exp, JD_AI)
    assert "CET-6 英语六级：550分" in out  # 语言等级不标注
    for kw in ("普通话", "驾照"):
        seg = [l for l in out.split("\n") if kw in l]
        assert seg and "禁止写入简历" in seg[0], f"{kw} 应被标注"


def test_jd提及则保留():
    exp = "其他信息：\n海员证：无限航区\n"
    out = _annotate_irrelevant_certs(exp, "招聘海员，要求持有海员证、四小证")
    assert "禁止写入简历" not in out


def test_无其他信息段原样返回():
    exp = "项目经历：\n做过AI简历工具\n"
    assert _annotate_irrelevant_certs(exp, JD_AI) == exp


def test_作品经历类不标注():
    exp = "其他信息：\n互联网+大赛省银奖：2024\n开源GitHub项目：one-tap-resume\n"
    out = _annotate_irrelevant_certs(exp, JD_AI)
    assert "禁止写入简历" not in out


def test_空jd安全():
    exp = "其他信息：\n海员证：x\n"
    out = _annotate_irrelevant_certs(exp, "")
    assert "禁止写入简历" in out

def test_build_github_link_正常提取():
    from services.resume_service import _build_github_link_html
    exp = "其他信息：\nGitHub 开源：https://github.com/q374/one-tap-resume\n"
    out = _build_github_link_html(exp)
    assert "github.com/q374/one-tap-resume" in out
    assert "GitHub：" in out
    assert out.startswith("<a href=")


def test_build_github_link_无链接返回空():
    from services.resume_service import _build_github_link_html
    assert _build_github_link_html("项目经历：\n做过的项目\n") == ""
    assert _build_github_link_html("") == ""


def test_build_github_link_中文标点截断():
    from services.resume_service import _build_github_link_html
    exp = "开源：https://github.com/q374/one-tap-resume，欢迎star"
    out = _build_github_link_html(exp)
    assert "q374/one-tap-resume" in out
    assert "欢迎star" not in out


def test_build_github_link_http也识别():
    from services.resume_service import _build_github_link_html
    out = _build_github_link_html("http://github.com/foo/bar 其他")
    assert "foo/bar" in out
