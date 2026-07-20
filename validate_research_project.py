#!/usr/bin/env python3
"""Research OS v1.4 - Dumb Validator

v0.7 变更（从 v0.6.1）：
  - 新增 JSON 字段值非空检查（解决空 JSON 通过问题）
  - 新增 task-card 字段值检查（解决模板说明文字占字符数问题）
  - 新增步骤依赖检查（step N 需要 step N-1 done）
  - 新增内容深度指标（URL 数、数据点数、术语解释数）
  - 新增 HTML 滚轮检测（永久禁止 overflow-y: auto 在 aside.toc）
  - 新增 HTML 附录 div 闭合检测
  - 新增核心对象提及次数检查（从 task-card 读取声明，不硬编码）
  - 新增前置门禁（前期步骤必须完成）

v0.7.1 修复（Dumb Tools 合规）：
  - check_core_object_mentions 改为从 task-card.md 读取声明的核心对象
    （原来硬编码 ["MuseDAM", "atypica", "GEA", "System of Context"] 违反 Dumb Tools）
  - final_report_writer.py 的 action 分类改为只输出建议，由 Agent 决定

设计哲学不变：Smart Agent. Dumb Tools.
新增的检查都是机械的、客观的、可验证的。
工具不做语义判断，不硬编码项目特定信息。

v1.3 变更（从 v1.2）：
  - 新增方向选择检查（组件A: Kimi式方向选择，R2/R3强制）
  - 新增对抗式审核检查（组件C: adversarial_review.json结构化检查）
  - 新增第一性原理检查（组件D: intent_doc + final-report三层检查）
  - 新增human_confirmation强制检查（不再允许跳过确认点）
  - 增强独立审计检查（从"PASS字符串"升级为"5问结构化检查"）
  - 增强反方审计检查（从"字符数"升级为"攻击次数+降级次数"）
  - 新增 step_1_5 和 step_9_6 到 STEP_ARTIFACTS 和 STEP_DEPENDENCIES

v1.5 变更（从 v1.4）：
  - 新增 step_10_5 写-读-改闭环产物检查（rewrite_instructions.json + iteration_state.json）
  - 补全 step_10.5/11/12/13 依赖链（11 依赖 10.5，12 依赖 11，13 依赖 10.5+12）
  - JSON_FIELD_REQUIREMENTS 新增 rewrite_instructions/iteration_state 字段非空检查
  - 版本头统一 v1.5（治理修复）
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


# ============================================================
# v1.1 配置
# ============================================================

# 深度档位感知的最小字符数阈值
# R0 快速问答 / R1 标准调研 / R2 深度调研 / R3 极致深度
MIN_CONTENT_CHARS_BY_DEPTH = {
    "R0": {
        "00-task/task-card.md": 200,
        "07-output/final-report.md": 800,
    },
    "R1": {
        "00-task/task-card.md": 500,
        "01-plan/research-plan.md": 800,
        "02-sources/candidates.md": 300,
        "03-evidence/evidence_matrix.md": 500,
        "07-output/final-report.md": 1500,
    },
    "R2": {
        "00-task/task-card.md": 500,
        "01-plan/research-plan.md": 1000,
        "02-sources/candidates.md": 500,
        "03-evidence/evidence_matrix.md": 800,
        "03-evidence/hypothesis_ledger.json": 50,
        "04-captures/core_objects_fetch_log.md": 200,
        "05-analysis/narrative-plan.md": 500,
        "06-review/red_team.md": 300,
        "06-review/audit_report.md": 200,
        "07-output/final-report.md": 3000,
    },
    "R3": {
        "00-task/task-card.md": 800,
        "01-plan/research-plan.md": 1500,
        "02-sources/candidates.md": 800,
        "03-evidence/evidence_matrix.md": 1200,
        "03-evidence/hypothesis_ledger.json": 100,
        "04-captures/core_objects_fetch_log.md": 300,
        "05-analysis/narrative-plan.md": 800,
        "06-review/red_team.md": 500,
        "06-review/audit_report.md": 300,
        "07-output/final-report.md": 5000,
    },
}

# 向后兼容：默认使用 R1 阈值
MIN_CONTENT_CHARS = MIN_CONTENT_CHARS_BY_DEPTH["R1"]

JSON_FIELD_REQUIREMENTS = {
    "00-task/intent_doc.json": {
        "status": str,
        "exploration_history": list,
        "stated_intent": str,
        "first_principles_decomposition": list,
    },
    "03-evidence/hypothesis_ledger.json": {
        "hypotheses": list,
    },
    "02-sources/candidate_pool.json": {
        "items": list,
    },
    "06-review/rewrite_instructions.json": {
        "instructions": list,
    },
    "06-review/iteration_state.json": {
        "history": list,
    },
}

TASK_CARD_REQUIRED_SECTIONS = {
    "调研对象": "## 调研对象",
    "决策目的": "## 这次调研服务什么决策",
    "读者画像": "## 目标读者",
    "核心问题": "### 核心问题",
}

STEP_ARTIFACTS = {
    "step_0_scaffold": {"required": ["research_state.json"]},
    "step_1_5_direction_selection": {"required": ["00-task/direction_selection.json"]},
    "step_2_task_card": {"required": ["00-task/task-card.md"]},
    "step_3_research_plan": {"required": ["01-plan/research-plan.md"]},
    "step_4_candidates": {"required": ["02-sources/candidates.md", "02-sources/discarded.md"]},
    "step_5_evidence_matrix": {"required": ["03-evidence/evidence_matrix.md"]},
    "step_6_hypothesis": {"required": ["03-evidence/hypothesis_ledger.json"]},
    "step_6_5_core_objects_fetch": {"required": ["04-captures/core_objects_fetch_log.md"]},
    "step_7_analysis": {"required": ["05-analysis/"], "any_md": True},
    "step_7_5_narrative_plan": {"required": ["05-analysis/narrative-plan.md"]},
    "step_8_red_team": {"required": ["06-review/red_team.md"]},
    "step_9_final_report_draft": {"required": ["07-output/final-report.md"]},
    "step_9_5_independent_audit": {"required": ["06-review/audit_report.md"]},
    "step_9_6_adversarial_review": {"required": ["06-review/adversarial_review.json"]},
    "step_10_reader_simulation": {"required": ["06-review/reader_diagnosis.json", "06-review/reader_feedback.md"]},
    "step_10_5_write_read_rewrite": {"required": ["06-review/rewrite_instructions.json", "06-review/iteration_state.json"]},
    "step_11_trace_manifest": {"required": ["07-output/trace-manifest.json"]},
    "step_12_view_model": {"required": ["07-output/view-model.json"]},
    "step_13_html_build": {"required": ["08-html/index.html"]},
}

STEP_DEPENDENCIES = {
    "step_2_task_card": ["step_1_5_direction_selection"],
    "step_6_5_core_objects_fetch": ["step_2_task_card", "step_3_research_plan"],
    "step_7_analysis": ["step_6_5_core_objects_fetch", "step_5_evidence_matrix"],
    "step_7_5_narrative_plan": ["step_7_analysis"],
    "step_8_red_team": ["step_7_analysis", "step_7_5_narrative_plan"],
    "step_9_final_report_draft": ["step_7_5_narrative_plan", "step_8_red_team"],
    "step_9_5_independent_audit": ["step_9_final_report_draft"],
    "step_9_6_adversarial_review": ["step_9_5_independent_audit"],
    "step_10_reader_simulation": ["step_9_6_adversarial_review"],
    "step_10_5_write_read_rewrite": ["step_10_reader_simulation"],
    "step_11_trace_manifest": ["step_10_5_write_read_rewrite"],
    "step_12_view_model": ["step_11_trace_manifest"],
    "step_13_html_build": ["step_10_5_write_read_rewrite", "step_12_view_model"],
}

DEPTH_METRICS = {
    "07-output/final-report.md": {
        "min_urls": 5,
        "min_data_points": 10,
        "min_sections": 5,
    },
    "04-captures/core_objects_fetch_log.md": {
        "min_urls": 3,
        "min_objects": 3,
    },
}

# v1.1 新增：HTML 必须结构检查（不只是"禁止什么"，还要"必须有什么"）
# 这解决了 Smart Agent. Dumb Tools. 哲学的盲区：
# 工具原来只检查"禁止模式"（不能有什么），不检查"必须结构"（必须有什么）
# 导致 Agent 手写 HTML 缺失关键结构（如 aside.toc/vm-hero/page-shell）时验证器无法发现
# 这些检查是机械的（正则匹配字符串是否存在），不是语义判断，符合 Dumb Tools 原则
HTML_REQUIRED_STRUCTURES = {
    "page_shell": {
        "pattern": r'class="page-shell"',
        "message": "缺少 .page-shell 双列布局（规范要求 grid 侧栏+正文）",
    },
    "aside_toc": {
        "pattern": r'<aside class="toc"',
        "message": "缺少 aside.toc 固定侧栏（规范要求 sticky 左侧目录）",
    },
    "vm_hero": {
        "pattern": r'class="vm-hero"',
        "message": "缺少 .vm-hero Hero区（规范要求 kicker+hero-verdict+hero-summary+hero-meta）",
    },
    "hero_verdict": {
        "pattern": r'class="hero-verdict"',
        "message": "缺少 .hero-verdict 一句话结论（30px 衬线）",
    },
    "reading_progress": {
        "pattern": r'class="reading-progress"',
        "message": "缺少 .reading-progress 阅读进度条",
    },
    "chapter_section": {
        "pattern": r'<section class="chapter"',
        "message": "缺少 section.chapter 章节结构",
    },
    "lora_font": {
        "pattern": r"Lora",
        "message": "缺少 Lora 衬线字体加载",
    },
    "bg_color_faf9f5": {
        "pattern": r"#faf9f5",
        "message": "缺少米色背景 #faf9f5",
    },
    "accent_b85b44": {
        "pattern": r"#b85b44",
        "message": "缺少暖砖红 accent #b85b44",
    },
}

HTML_FORBIDDEN_PATTERNS = {
    # v1.1: aside.toc 允许 overflow-y: auto（长目录需要滚动，v0.7 的 overflow:hidden 导致目录截断）
    # 此检查已废弃，保留空模式避免破坏代码结构
    "unclosed_div": {
        "pattern": r"<div class=\"source-section\">[^<]*<h1",
        "message": "source-section div 未正确闭合（附录 div bug）",
    },
}

# v1.1: 视觉规范量化检查——色彩来自结构化块，不来自 inline code
# 参考基准：Lev8 报告（0 code, 9 blockquote, 161 strong, 12 table）
VISUAL_METRICS = {
    "inline_code_max": 5,        # <code> 元素上限（允许少量，但不允许密集）
    "blockquote_min": 6,         # <blockquote> 引用块下限
    "strong_min": 80,            # <strong> 强调下限
    "table_min": 6,              # <table> 表格下限
}


@dataclass
class Check:
    level: str
    name: str
    message: str


def add(checks, level, name, message):
    checks.append(Check(level=level, name=name, message=message))


def read_text(p):
    try:
        return p.read_text(encoding="utf-8") if p.exists() else ""
    except Exception:
        return ""


def read_json(p):
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception:
        return {}


# ============================================================
# v1.x 新增检查函数
# ============================================================

def check_json_field_values(project, checks):
    """v0.7: 检查 JSON 文件的字段值是否非空。"""
    for rel, fields in JSON_FIELD_REQUIREMENTS.items():
        p = project / rel
        if not p.exists():
            continue
        data = read_json(p)
        if not data:
            add(checks, "FAIL", f"json invalid: {rel}", "file exists but not valid JSON")
            continue

        for field_name, expected_type in fields.items():
            value = data.get(field_name)
            if value is None:
                add(checks, "FAIL", f"json field empty: {rel}.{field_name}", "field is null/missing")
            elif expected_type == str and not value.strip():
                add(checks, "FAIL", f"json field empty: {rel}.{field_name}", "string field is empty")
            elif expected_type == list and len(value) == 0:
                add(checks, "FAIL", f"json field empty: {rel}.{field_name}", "list field is empty")
            else:
                if expected_type == list:
                    add(checks, "PASS", f"json field: {rel}.{field_name}", f"{len(value)} items")
                else:
                    add(checks, "PASS", f"json field: {rel}.{field_name}", f"non-empty ({len(str(value))} chars)")


def check_task_card_field_values(project, checks):
    """v0.7: 检查 task-card 的字段值是否填写（不只是字段名存在）。"""
    task_card = read_text(project / "00-task" / "task-card.md")
    if not task_card:
        return

    lines = task_card.split("\n")
    for section_name, header in TASK_CARD_REQUIRED_SECTIONS.items():
        header_idx = None
        for i, line in enumerate(lines):
            if header in line:
                header_idx = i
                break

        if header_idx is None:
            add(checks, "WARN", f"task-card section: {section_name}", "section header missing")
            continue

        content_lines = []
        for j in range(header_idx + 1, len(lines)):
            if lines[j].startswith("## ") and j > header_idx:
                break
            content_lines.append(lines[j])

        actual_content = "\n".join(l for l in content_lines if not l.strip().startswith(">")).strip()

        if len(actual_content) < 10:
            add(checks, "FAIL", f"task-card value: {section_name}",
                f"section exists but content empty ({len(actual_content)} chars)")
        else:
            add(checks, "PASS", f"task-card value: {section_name}",
                f"filled ({len(actual_content)} chars)")


def check_step_dependencies(project, checks):
    """v0.7: 检查步骤依赖关系。step N done 则 step N-1 必须 done。"""
    state = read_json(project / "research_state.json")
    if not state:
        return

    steps = state.get("steps", {})
    violations = 0

    for step_name, deps in STEP_DEPENDENCIES.items():
        step_status = steps.get(step_name, "pending")
        if step_status != "done":
            continue

        for dep in deps:
            dep_status = steps.get(dep, "pending")
            if dep_status != "done":
                add(checks, "FAIL", f"step dependency: {step_name}",
                    f"{step_name} marked done but dependency {dep} is {dep_status}")
                violations += 1

    if violations == 0:
        add(checks, "PASS", "step dependencies", "all done steps have dependencies satisfied")


def check_depth_metrics(project, checks):
    """v0.7: 检查内容深度指标（URL 数、数据点数、章节数）。"""
    for rel, metrics in DEPTH_METRICS.items():
        p = project / rel
        if not p.exists():
            continue
        content = read_text(p)

        if "min_urls" in metrics:
            urls = re.findall(r"https?://[^\s\)\]]+", content)
            if len(urls) >= metrics["min_urls"]:
                add(checks, "PASS", f"depth urls: {rel}", f"{len(urls)} URLs (>= {metrics['min_urls']})")
            else:
                add(checks, "FAIL", f"depth urls: {rel}", f"only {len(urls)} URLs, need >= {metrics['min_urls']}")

        if "min_data_points" in metrics:
            data_points = re.findall(r"\d+\.?\d*\s*[%亿万美元万人民币人+倍]?", content)
            if len(data_points) >= metrics["min_data_points"]:
                add(checks, "PASS", f"depth data: {rel}", f"{len(data_points)} data points (>= {metrics['min_data_points']})")
            else:
                add(checks, "FAIL", f"depth data: {rel}", f"only {len(data_points)} data points, need >= {metrics['min_data_points']}")

        if "min_sections" in metrics:
            sections = re.findall(r"^##\s+", content, re.MULTILINE)
            if len(sections) >= metrics["min_sections"]:
                add(checks, "PASS", f"depth sections: {rel}", f"{len(sections)} sections (>= {metrics['min_sections']})")
            else:
                add(checks, "FAIL", f"depth sections: {rel}", f"only {len(sections)} sections, need >= {metrics['min_sections']}")

        if "min_objects" in metrics:
            objects = re.findall(r"^##\s+对象\s*\d+", content, re.MULTILINE)
            if len(objects) >= metrics["min_objects"]:
                add(checks, "PASS", f"depth objects: {rel}", f"{len(objects)} objects (>= {metrics['min_objects']})")
            else:
                add(checks, "FAIL", f"depth objects: {rel}", f"only {len(objects)} objects, need >= {metrics['min_objects']}")


def check_html_forbidden_patterns(project, checks):
    """v0.7: 检查 HTML 禁止模式（滚轮、未闭合 div）。"""
    html = read_text(project / "08-html" / "index.html")
    if not html:
        return

    for name, spec in HTML_FORBIDDEN_PATTERNS.items():
        if re.search(spec["pattern"], html, re.DOTALL):
            add(checks, "FAIL", f"html pattern: {name}", spec["message"])
        else:
            add(checks, "PASS", f"html pattern: {name}", "ok")


def check_html_required_structures(project, checks):
    """v1.1: 检查 HTML 必须结构（不只是禁止什么，还要必须有什么）。

    这修复了 Smart Agent. Dumb Tools. 哲学的盲区：
    - 原来只检查"禁止模式"（overflow-y:auto, div未闭合）
    - 不检查"必须结构"（page-shell, aside.toc, vm-hero 等）
    - 导致 Agent 手写 HTML 缺失关键结构时验证器无法发现

    新增的检查是机械的（正则匹配字符串是否存在），不是语义判断。
    """
    html = read_text(project / "08-html" / "index.html")
    if not html:
        return

    for name, spec in HTML_REQUIRED_STRUCTURES.items():
        if re.search(spec["pattern"], html):
            add(checks, "PASS", f"html structure: {name}", "found")
        else:
            add(checks, "FAIL", f"html structure: {name}", spec["message"])


def check_html_visual_metrics(project, checks):
    """v1.1: 检查 HTML 视觉规范量化指标。

    色彩来自结构化块（blockquote/table/strong），不来自 inline code。
    参考基准：Lev8 报告（0 code, 9 blockquote, 161 strong, 12 table）。
    这是机械检查（数 HTML 标签数量），不是语义判断。
    """
    html = read_text(project / "08-html" / "index.html")
    if not html:
        return

    # 统计各元素数量（排除 CSS 和 JS 中的出现，只数 HTML 标签）
    code_count = len(re.findall(r"<code>", html))
    blockquote_count = len(re.findall(r"<blockquote", html))
    strong_count = len(re.findall(r"<strong>", html))
    table_count = len(re.findall(r"<table>", html))

    # inline code 上限检查
    if code_count > VISUAL_METRICS["inline_code_max"]:
        add(checks, "FAIL", "visual: inline_code_count",
            f"{code_count} 个 <code>（上限 {VISUAL_METRICS['inline_code_max']}）——色彩不应来自 inline code 药丸，应用 strong/blockquote/table 等结构化块")
    else:
        add(checks, "PASS", "visual: inline_code_count", f"{code_count} 个（上限 {VISUAL_METRICS['inline_code_max']}）")

    # blockquote 下限检查
    if blockquote_count < VISUAL_METRICS["blockquote_min"]:
        add(checks, "FAIL", "visual: blockquote_count",
            f"{blockquote_count} 个 <blockquote>（下限 {VISUAL_METRICS['blockquote_min']}）——需要更多引用块提供色彩节奏")
    else:
        add(checks, "PASS", "visual: blockquote_count", f"{blockquote_count} 个（下限 {VISUAL_METRICS['blockquote_min']}）")

    # strong 下限检查
    if strong_count < VISUAL_METRICS["strong_min"]:
        add(checks, "FAIL", "visual: strong_count",
            f"{strong_count} 个 <strong>（下限 {VISUAL_METRICS['strong_min']}）——需要更多段首标签词服务扫读")
    else:
        add(checks, "PASS", "visual: strong_count", f"{strong_count} 个（下限 {VISUAL_METRICS['strong_min']}）")

    # table 下限检查
    if table_count < VISUAL_METRICS["table_min"]:
        add(checks, "FAIL", "visual: table_count",
            f"{table_count} 个 <table>（下限 {VISUAL_METRICS['table_min']}）——需要更多表格展示结构化数据")
    else:
        add(checks, "PASS", "visual: table_count", f"{table_count} 个（下限 {VISUAL_METRICS['table_min']}）")


def check_core_object_mentions(project, checks):
    """v0.7.1: 检查最终报告中核心对象被提及的次数。

    Dumb Tools 合规修复：
    - 核心对象列表由 Agent 在 task-card.md 中声明（## 核心对象 章节 + 列表）
    - 工具只机械检查"声明的对象是否在报告中被提及 >= 3 次"
    - 工具不硬编码任何产品名（那是语义判断，越界）

    声明格式（task-card.md 中）：
        ## 核心对象
        - MuseDAM
        - atypica
        - GEA
    """
    report = read_text(project / "07-output" / "final-report.md")
    if not report:
        return

    # 从 task-card.md 读取 Agent 声明的核心对象
    task_card = read_text(project / "00-task" / "task-card.md")
    if not task_card:
        return

    # 找到 ## 核心对象 章节，提取列表项
    core_objects = []
    in_section = False
    for line in task_card.split("\n"):
        if line.startswith("## ") and "核心对象" in line:
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break  # 进入下一章节
            # 匹配 "- 对象名" 或 "1. 对象名"
            m = re.match(r"^[-\d\.\s]+(.+)$", line.strip())
            if m:
                obj = m.group(1).strip()
                # 排除模板说明文字和过长的项
                if obj and not obj.startswith(">") and len(obj) < 50:
                    core_objects.append(obj)

    if not core_objects:
        add(checks, "WARN", "core objects declared",
            "task-card.md 未声明核心对象（需 ## 核心对象 章节 + 列表）")
        return

    add(checks, "PASS", "core objects declared",
        f"task-card.md 声明了 {len(core_objects)} 个核心对象")

    for obj in core_objects:
        count = len(re.findall(re.escape(obj), report, re.IGNORECASE))
        if count >= 3:
            add(checks, "PASS", f"core object mention: {obj}", f"mentioned {count} times")
        else:
            add(checks, "WARN", f"core object mention: {obj}", f"only mentioned {count} times")


def check_prerequisite_gate(project, checks):
    """v0.7: 前置门禁——核心对象直采前，任务卡和研究计划必须完成。"""
    state = read_json(project / "research_state.json")
    if not state:
        return

    steps = state.get("steps", {})

    if steps.get("step_6_5_core_objects_fetch") == "done":
        for prereq in ["step_2_task_card", "step_3_research_plan"]:
            if steps.get(prereq) != "done":
                add(checks, "FAIL", f"prerequisite gate: {prereq}",
                    f"step_6_5 done but {prereq} not done")
            else:
                add(checks, "PASS", f"prerequisite gate: {prereq}", "ok")


# ============================================================
# v1.0-v1.1 面向读者的质量检查
# ============================================================

# 开发者术语——不应出现在面向读者的字段中
DEVELOPER_TERMS = [
    "step_", "final-report", "view-model", ".json", "schema_version",
    "_design", "intent_doc", "research_state", "meta_validator",
    "trust_ledger", "build_html", "dumb_tools",
    "07-output", "00-task", "01-plan", "06-review",
]


def check_view_model_reader_facing(project, checks):
    """v1.0: 检查 view-model.json 的面向读者字段不含开发者术语。

    hero.verdict 和 hero.summary 是读者第一眼看到的内容，
    不应包含实现细节（step 编号、文件路径、schema 名词）。
    """
    vm = read_json(project / "07-output" / "view-model.json")
    if not vm:
        return

    hero = vm.get("hero", {})
    if not hero:
        return

    for field_name in ("verdict", "summary"):
        value = hero.get(field_name, "")
        if not value:
            continue
        found_terms = [term for term in DEVELOPER_TERMS if term in value.lower()]
        if found_terms:
            add(checks, "FAIL", f"reader-facing: hero.{field_name}",
                f"含开发者术语: {found_terms}（面向读者字段不应含实现细节）")
        else:
            add(checks, "PASS", f"reader-facing: hero.{field_name}",
                f"无开发者术语 ({len(value)} chars)")


def check_action_plan_proportion(project, checks):
    """v1.0: 检查行动方案章节占报告总字符数的比例。

    行动方案是读者最需要的部分（告诉读者怎么做），
    如果占比过低说明行动方案潦草。
    阈值：行动方案章节 >= 总报告的 15%。
    """
    report = read_text(project / "07-output" / "final-report.md")
    if not report or len(report) < 500:
        return

    # 找行动方案章节：标题含"行动""怎么修""方案""实施""建议"的章节
    import re
    # 先移除代码块（避免代码块内的 ## 被误认为章节标题）
    report_no_code = re.sub(r"```[\s\S]*?```", "", report)
    sections = re.split(r"^##\s+", report_no_code, flags=re.MULTILINE)
    total_chars = len(report)
    action_chars = 0
    action_found = False

    for sec in sections[1:]:  # 跳过第一部分（标题前的内容）
        title_line = sec.split("\n")[0].lower()
        if any(kw in title_line for kw in ["行动", "怎么修", "方案", "实施", "建议", "决策建议"]):
            action_found = True
            action_chars += len(sec)

    if not action_found:
        add(checks, "WARN", "action plan section",
            "未找到行动方案章节（标题应含'行动/方案/实施/建议'）")
        return

    proportion = action_chars / total_chars
    if proportion < 0.15:
        add(checks, "FAIL", "action plan proportion",
            f"行动方案仅占报告的 {proportion:.0%} ({action_chars}/{total_chars} chars)，应 >= 15%")
    else:
        add(checks, "PASS", "action plan proportion",
            f"行动方案占报告的 {proportion:.0%} ({action_chars}/{total_chars} chars)")




def check_concept_ladder_seed(project, checks):
    """v1.2 门禁1: concept_ladder_seed 非空检查。"""
    intent = read_json(project / "00-task" / "intent_doc.json")
    if not intent:
        return
    v07 = intent.get("v07", {})
    needed = v07.get("concept_ladder_needed", False)
    if not needed:
        return
    seed = v07.get("concept_ladder_seed", [])
    if not isinstance(seed, list):
        seed = []
    if len(seed) >= 3:
        add(checks, "PASS", "concept_ladder_seed", f"{len(seed)} 个种子术语 (>= 3)")
    else:
        add(checks, "FAIL", "concept_ladder_seed",
            f"concept_ladder_needed=true 但 seed 只有 {len(seed)} 个术语 (需 >= 3)——"
            f"Agent 在意图探索 Round 3 跳过了术语声明，整条概念解释链路将静默失效")


def check_reader_model(project, checks):
    """v1.2 门禁2: reader_model 非空检查。"""
    intent = read_json(project / "00-task" / "intent_doc.json")
    if not intent:
        return
    v07 = intent.get("v07", {})
    needed = v07.get("concept_ladder_needed", False)
    if not needed:
        return
    reader_model = v07.get("reader_model", {})
    if not isinstance(reader_model, dict):
        reader_model = {}
    background = reader_model.get("background", "")
    if isinstance(background, str) and background.strip():
        add(checks, "PASS", "reader_model", f"background 已声明 ({len(background)} chars)")
    else:
        add(checks, "FAIL", "reader_model",
            f"concept_ladder_needed=true 但 reader_model.background 为空——"
            f"reader_simulation 将退化为默认画像无法针对性检测术语缺口")


def check_term_explanation_coverage(project, checks):
    """v1.2 门禁3: seed 中每个术语在 final-report 中是否被解释。"""
    intent = read_json(project / "00-task" / "intent_doc.json")
    if not intent:
        return
    v07 = intent.get("v07", {})
    seed = v07.get("concept_ladder_seed", [])
    if not seed:
        return
    report = read_text(project / "07-output" / "final-report.md")
    if not report:
        return
    explanation_markers = [
        r"即[：:]", r"也就是", r"通俗", r"类比", r"意思是", r"指的是",
        r"本质是", r"简单说", r"大白话", r"换句话说", r"可以理解为",
        r"相当于", r"就是", r"——", r"（[^）]*）",
    ]
    explained_count = 0
    unexplained = []
    for term in seed:
        if not isinstance(term, str) or not term.strip():
            continue
        term_clean = term.strip()
        positions = [m.start() for m in re.finditer(re.escape(term_clean), report, re.IGNORECASE)]
        if not positions:
            unexplained.append(f"{term_clean} (未出现)")
            continue
        first_pos = positions[0]
        context_start = max(0, first_pos - 500)
        context_end = min(len(report), first_pos + len(term_clean) + 500)
        context = report[context_start:context_end]
        has_explanation = False
        for marker in explanation_markers:
            if re.search(marker, context):
                has_explanation = True
                break
        line_start = report.rfind("\n", 0, first_pos) + 1
        line_end = report.find("\n", first_pos)
        if line_end == -1:
            line_end = len(report)
        first_line = report[line_start:line_end]
        if first_line.lstrip().startswith(">"):
            has_explanation = True
        if has_explanation:
            explained_count += 1
        else:
            unexplained.append(f"{term_clean} (出现但无解释)")
    total = len([t for t in seed if isinstance(t, str) and t.strip()])
    if total == 0:
        return
    if explained_count == total:
        add(checks, "PASS", "term_explanation_coverage",
            f"{explained_count}/{total} 个种子术语在报告中有解释")
    elif explained_count >= total * 0.6:
        add(checks, "WARN", "term_explanation_coverage",
            f"{explained_count}/{total} 个种子术语有解释，未解释: {unexplained}")
    else:
        add(checks, "FAIL", "term_explanation_coverage",
            f"仅 {explained_count}/{total} 个种子术语有解释，未解释: {unexplained}")



# ============================================================
# v0.6 保留检查函数
# ============================================================

def check_file_existence(project, checks):
    required_files = [
        ("00-task/task-card.md", "task card"),
        ("01-plan/research-plan.md", "research plan"),
        ("02-sources/candidates.md", "candidates"),
        ("02-sources/discarded.md", "discarded sources"),
        ("03-evidence/evidence_matrix.md", "evidence matrix"),
        ("03-evidence/hypothesis_ledger.json", "hypothesis ledger"),
        ("06-review/red_team.md", "red team"),
        ("07-output/final-report.md", "final report"),
    ]
    for rel, name in required_files:
        p = project / rel
        if p.exists():
            add(checks, "PASS", f"{name} exists", f"found {rel}")
        else:
            add(checks, "FAIL", f"{name} exists", f"missing {rel}")


def check_min_content(project, checks):
    # 读取 depth 档位，默认 R1
    state = read_json(project / "research_state.json")
    depth = state.get("depth", "R1") if state else "R1"
    thresholds = MIN_CONTENT_CHARS_BY_DEPTH.get(depth, MIN_CONTENT_CHARS_BY_DEPTH["R1"])

    for rel, min_chars in thresholds.items():
        p = project / rel
        if not p.exists():
            continue
        # 05-analysis/ 目录特殊处理：检查目录下所有 .md 文件的总字符数
        if rel.endswith("/"):
            total = sum(len(read_text(f)) for f in p.glob("*.md"))
            if total < min_chars:
                add(checks, "FAIL", f"empty template: {rel}",
                    f"only {total} chars in {depth}, need >= {min_chars}")
            else:
                add(checks, "PASS", f"content sufficiency: {rel}",
                    f"{total} chars in {depth} (>= {min_chars})")
            continue
        content = read_text(p)
        if len(content) < min_chars:
            add(checks, "FAIL", f"empty template: {rel}",
                f"only {len(content)} chars in {depth}, need >= {min_chars}")
        else:
            add(checks, "PASS", f"content sufficiency: {rel}",
                f"{len(content)} chars in {depth} (>= {min_chars})")


def check_state_artifact_consistency(project, checks):
    state = read_json(project / "research_state.json")
    if not state:
        add(checks, "FAIL", "research_state.json", "missing or invalid")
        return

    steps = state.get("steps", {})
    fake_done_count = 0

    for step_name, artifact_spec in STEP_ARTIFACTS.items():
        step_status = steps.get(step_name, "pending")
        if step_status != "done":
            continue
        any_md = artifact_spec.get("any_md", False)
        for rel in artifact_spec["required"]:
            p = project / rel
            if not p.exists():
                add(checks, "FAIL",
                    f"state-artifact mismatch: {step_name}",
                    f"{step_name} marked done but {rel} missing")
                fake_done_count += 1
            elif any_md and rel.endswith("/"):
                # 检查目录下至少有一个 .md 文件（mode 无关）
                md_files = list(p.glob("*.md"))
                if not md_files:
                    add(checks, "FAIL",
                        f"state-artifact mismatch: {step_name}",
                        f"{step_name} marked done but {rel} has no .md files")
                    fake_done_count += 1
                else:
                    add(checks, "PASS",
                        f"state-artifact: {step_name}",
                        f"{rel} has {len(md_files)} .md file(s)")

    if fake_done_count == 0:
        add(checks, "PASS", "state-artifact consistency",
            "all done-marked steps have required artifacts")




def check_direction_selection(project, checks):
    """v1.3: 检查方向选择协议（Kimi式）- R2/R3强制"""
    state = read_json(project / "research_state.json")
    depth = state.get("research_depth", "R1")
    direction_file = project / "00-task" / "direction_selection.json"
    
    if depth in ("R2", "R3"):
        if not direction_file.exists():
            add(checks, "FAIL", "direction selection (R2/R3)", 
                f"missing 00-task/direction_selection.json (required for {depth})")
            return
        data = read_json(direction_file)
        directions = data.get("directions_proposed", [])
        if len(directions) < 2:
            add(checks, "FAIL", "direction selection", 
                f"only {len(directions)} directions proposed (need >=2)")
            return
        selection = data.get("user_selection", {})
        if not selection.get("selected_direction_id"):
            add(checks, "FAIL", "direction selection", "no user_selection.selected_direction_id")
            return
        if data.get("status") != "direction_confirmed":
            add(checks, "FAIL", "direction selection", f"status={data.get('status')} (need direction_confirmed)")
            return
        add(checks, "PASS", "direction selection", 
            f"confirmed: {selection.get('selected_direction_id')} from {len(directions)} directions")
    else:
        if direction_file.exists():
            add(checks, "PASS", "direction selection", "found (optional for R0/R1)")
        else:
            add(checks, "PASS", "direction selection", "skipped (R0/R1 optional)")


def check_adversarial_review(project, checks):
    """v1.3: 检查对抗式subagent审核"""
    adv_file = project / "06-review" / "adversarial_review.json"
    if not adv_file.exists():
        add(checks, "FAIL", "adversarial review", "missing 06-review/adversarial_review.json")
        return
    data = read_json(adv_file)
    
    attacks = data.get("attacks", [])
    if len(attacks) < 3:
        add(checks, "FAIL", "adversarial review", f"only {len(attacks)} attacks (need >=3)")
        return
    
    responses = data.get("responses", [])
    if len(responses) < len(attacks):
        add(checks, "FAIL", "adversarial review", 
            f"{len(attacks)} attacks but only {len(responses)} responses")
        return
    
    # 检查每个attack的必填字段
    for atk in attacks:
        if not all(k in atk for k in ["id", "type", "target", "attack_content", "attack_strength"]):
            add(checks, "FAIL", "adversarial review", 
                f"attack {atk.get('id', '?')} missing required fields")
            return
    
    # 检查每个response的必填字段
    for resp in responses:
        if not all(k in resp for k in ["attack_id", "response_type", "response_content"]):
            add(checks, "FAIL", "adversarial review",
                f"response for {resp.get('attack_id', '?')} missing required fields")
            return
    
    # 检查是否含first_principles类型攻击（v1.3组件D要求）
    has_fp_attack = any(a.get("type") == "first_principles" for a in attacks)
    if has_fp_attack:
        add(checks, "PASS", "adversarial review", 
            f"{len(attacks)} attacks, {len(responses)} responses, includes first_principles test")
    else:
        add(checks, "WARN", "adversarial review",
            f"{len(attacks)} attacks but no first_principles type attack")


def check_first_principles_report(project, checks):
    """v1.3: 检查最终报告是否含第一性原理章节"""
    report = read_text(project / "07-output" / "final-report.md")
    if not report:
        return
    
    # 检查是否含第一性原理关键词的章节标题
    fp_keywords = ["第一性原理", "本质", "为什么", "底层逻辑"]
    fp_section_found = False
    fp_section_content = ""
    
    for keyword in fp_keywords:
        pattern = rf"## .*(?:{keyword})"
        match = re.search(pattern, report)
        if match:
            # 提取该章节内容（从标题到下一个## 标题）
            start = match.start()
            next_section = re.search(r"\n## ", report[start + 1:])
            if next_section:
                end = start + 1 + next_section.start()
            else:
                end = len(report)
            fp_section_content = report[start:end]
            fp_section_found = True
            break
    
    if not fp_section_found:
        add(checks, "FAIL", "first principles section", 
            "final-report missing first-principles section (need title with: 第一性原理/本质/为什么/底层逻辑)")
        return
    
    if len(fp_section_content) < 500:
        add(checks, "WARN", "first principles section", 
            f"section too short ({len(fp_section_content)} chars, need >=500)")
        return
    
    add(checks, "PASS", "first principles section",
        f"found ({len(fp_section_content)} chars)")


def check_first_principles_intent(project, checks):
    """v1.3: 检查意图识别是否含第一性原理拆解"""
    intent = read_json(project / "00-task" / "intent_doc.json")
    if not intent:
        return
    
    fp_list = intent.get("first_principles_decomposition")
    if not fp_list or not isinstance(fp_list, list):
        add(checks, "FAIL", "first principles (intent)", 
            "intent_doc.json missing first_principles_decomposition field")
        return
    
    if len(fp_list) < 3:
        add(checks, "FAIL", "first principles (intent)",
            f"only {len(fp_list)} principles (need >=3)")
        return
    
    for fp in fp_list:
        if not all(k in fp for k in ["principle", "irreducibility_argument", "evidence_basis"]):
            add(checks, "FAIL", "first principles (intent)",
                f"principle missing required fields (need principle/irreducibility_argument/evidence_basis)")
            return
    
    add(checks, "PASS", "first principles (intent)",
        f"{len(fp_list)} principles with irreducibility arguments")


def check_human_confirmation_enforced(project, checks):
    """v1.3: 检查human_confirmation_points是否被强制执行"""
    state = read_json(project / "research_state.json")
    if not state:
        return
    
    hcp = state.get("human_confirmation_points", {})
    steps = state.get("steps", {})
    
    for step_key, required in hcp.items():
        if required and step_key in steps:
            step_status = steps[step_key]
            if step_status == "done":
                # 检查是否有confirmed标记
                # v1.3: 人工确认的步骤必须有 confirmed_by 字段
                confirmations = state.get("confirmations", {})
                if step_key not in confirmations:
                    add(checks, "WARN", "human confirmation", 
                        f"{step_key} marked done but no confirmation record (should have confirmed_by)")
                else:
                    add(checks, "PASS", "human confirmation",
                        f"{step_key} confirmed by {confirmations[step_key].get('confirmed_by', '?')}")


def check_audit_report_structured(project, checks):
    """v1.3增强: 检查审计报告是否含结构化字段（不再只检查PASS字符串）"""
    audit = project / "06-review" / "audit_report.md"
    if not audit.exists():
        add(checks, "FAIL", "audit report (structured)", "missing")
        return
    content = audit.read_text(encoding="utf-8")
    
    # v1.3: 不再只检查"PASS"字符串，检查5个审计问题是否都有明确结论
    audit_questions = ["Q1", "Q2", "Q3", "Q4", "Q5"]
    found_questions = sum(1 for q in audit_questions if q in content)
    
    if found_questions < 5:
        add(checks, "WARN", "audit report (structured)", 
            f"only {found_questions}/5 audit questions found")
        return
    
    # 检查每个问题是否都有PASS或FAIL结论
    pass_count = content.count("PASS") + content.count("✅")
    fail_count = content.count("FAIL") + content.count("❌")
    
    if pass_count + fail_count < 5:
        add(checks, "WARN", "audit report (structured)",
            f"only {pass_count + fail_count} verdicts for 5 questions")
        return
    
    add(checks, "PASS", "audit report (structured)",
        f"{found_questions} questions with {pass_count} PASS / {fail_count} FAIL")


def check_red_team_structured(project, checks):
    """v1.3增强: 检查反方审计是否含结构化攻击记录（不只检查字符数）"""
    red_team = project / "06-review" / "red_team.md"
    if not red_team.exists():
        add(checks, "FAIL", "red team (structured)", "missing")
        return
    content = red_team.read_text(encoding="utf-8")
    
    # 检查攻击次数（通过"攻击"/"attack"关键词计数）
    attack_patterns = [r"攻击\s*\d", r"Attack\s*\d", r"###\s*(攻击|Attack)"]
    attack_count = 0
    for pattern in attack_patterns:
        attack_count = max(attack_count, len(re.findall(pattern, content, re.IGNORECASE)))
    
    # 检查降级记录
    downgrade_patterns = [r"降级", r"downgrade", r"修正为"]
    downgrade_count = sum(len(re.findall(p, content, re.IGNORECASE)) for p in downgrade_patterns)
    
    if attack_count >= 4:
        add(checks, "PASS", "red team attacks", f"{attack_count} attacks found")
    else:
        add(checks, "WARN", "red team attacks", 
            f"only {attack_count} attacks detected (need >=4)")
    
    if downgrade_count >= 1:
        add(checks, "PASS", "red team downgrades", f"{downgrade_count} downgrades found")
    else:
        add(checks, "WARN", "red team downgrades", "no downgrade records found")


def check_mandatory_gates(project, checks):
    core_objects_log = project / "04-captures" / "core_objects_fetch_log.md"
    if core_objects_log.exists():
        content = core_objects_log.read_text(encoding="utf-8")
        if len(content) > 200:
            add(checks, "PASS", "core objects fetch log", f"found and non-empty ({len(content)} chars)")
        else:
            add(checks, "WARN", "core objects fetch log", "appears empty")
    else:
        add(checks, "FAIL", "core objects fetch log", "missing 04-captures/core_objects_fetch_log.md")

    audit_report = project / "06-review" / "audit_report.md"
    if audit_report.exists():
        content = audit_report.read_text(encoding="utf-8")
        if "PASS" in content or "FAIL" in content:
            add(checks, "PASS", "audit report", "found with PASS/FAIL verdict")
        else:
            add(checks, "WARN", "audit report", "no PASS/FAIL verdict")
    else:
        add(checks, "FAIL", "audit report", "missing 06-review/audit_report.md")

    reader_diagnosis = project / "06-review" / "reader_diagnosis.json"
    reader_feedback = project / "06-review" / "reader_feedback.md"

    if reader_diagnosis.exists():
        diag = read_json(reader_diagnosis)
        if diag.get("overall_score") is not None:
            add(checks, "PASS", "reader diagnosis", f"found, overall_score={diag.get('overall_score')}")
        else:
            add(checks, "WARN", "reader diagnosis", "no overall_score")
    else:
        add(checks, "FAIL", "reader diagnosis", "missing 06-review/reader_diagnosis.json")

    if reader_feedback.exists():
        add(checks, "PASS", "reader feedback", "found")
    else:
        add(checks, "FAIL", "reader feedback", "missing 06-review/reader_feedback.md")


def check_source_citation_format(project, checks):
    report = read_text(project / "07-output" / "final-report.md")
    if not report:
        return

    if "信息来源" in report or "参考资料" in report or "References" in report:
        add(checks, "PASS", "source citation section", "final-report contains source section")
    else:
        add(checks, "WARN", "source citation section", "final-report missing source section")

    internal_citations = re.findall(r"\[S\d+\]", report[:len(report) // 2])
    if len(internal_citations) > 5:
        add(checks, "WARN", "internal citation format", f"{len(internal_citations)} [S00X] in main body")
    else:
        add(checks, "PASS", "internal citation format", "no excessive internal citations")


def check_html_existence(project, checks):
    html = project / "08-html" / "index.html"
    if html.exists():
        content = html.read_text(encoding="utf-8")
        add(checks, "PASS", "index.html exists", f"found ({len(content)} chars)")
        process_markers = ["# 调研任务卡", "# 证据矩阵", "# 反方审计"]
        marker_count = sum(1 for m in process_markers if m in content)
        if marker_count >= 2:
            add(checks, "FAIL", "HTML reader-first", f"HTML pastes process files ({marker_count} markers)")
        else:
            add(checks, "PASS", "HTML reader-first", "ok")
    else:
        add(checks, "WARN", "index.html exists", "missing")


def check_version_consistency(project, checks):
    versions = []
    for md_file in project.rglob("*.md"):
        if ".git" in str(md_file):
            continue
        content = md_file.read_text(encoding="utf-8")[:200]
        match = re.search(r"ros-version:\s*(v[\d.]+)", content)
        if match:
            versions.append((str(md_file.relative_to(project)), match.group(1)))

    if not versions:
        add(checks, "WARN", "version consistency", "no ros-version headers")
        return

    unique_versions = set(v for _, v in versions)
    if len(unique_versions) == 1:
        add(checks, "PASS", "version consistency", f"all {len(versions)} files use {unique_versions.pop()}")
    else:
        add(checks, "WARN", "version consistency", f"multiple versions: {unique_versions}")


def check_latex_rendering(project, checks):
    """v0.8: 检查HTML是否包含LaTeX公式渲染支持。

    当报告包含 $...$ 或 $$...$$ 公式时，HTML必须引入MathJax或KaTeX，
    否则公式会以原始LaTeX源码显示（对读者而言是乱码）。
    """
    report = read_text(project / "07-output" / "final-report.md")
    if not report:
        return

    # 检测报告中是否包含LaTeX公式
    has_inline_math = bool(re.search(r"\$[^\$\n]{3,}\$", report))
    has_display_math = "$$" in report

    if not (has_inline_math or has_display_math):
        return  # 报告无公式，跳过检查

    html = read_text(project / "08-html" / "index.html")
    if not html:
        return

    has_mathjax = "mathjax" in html.lower() or "MathJax" in html
    has_katex = "katex" in html.lower()

    formula_count = len(re.findall(r"\$[^\$\n]{3,}\$", report)) + report.count("$$") // 2

    if has_mathjax or has_katex:
        lib = "MathJax" if has_mathjax else "KaTeX"
        add(checks, "PASS", "latex rendering",
            f"HTML includes {lib}, {formula_count} formulas renderable")
    else:
        add(checks, "FAIL", "latex rendering",
            f"report has {formula_count} LaTeX formulas but HTML lacks MathJax/KaTeX")


# ============================================================
# 主验证函数
# ============================================================

def validate_project(project):
    checks = []
    # v0.6 保留
    check_file_existence(project, checks)
    check_min_content(project, checks)
    check_state_artifact_consistency(project, checks)
    check_mandatory_gates(project, checks)
    check_direction_selection(project, checks)
    check_adversarial_review(project, checks)
    check_first_principles_report(project, checks)
    check_first_principles_intent(project, checks)
    check_human_confirmation_enforced(project, checks)
    check_audit_report_structured(project, checks)
    check_red_team_structured(project, checks)
    check_source_citation_format(project, checks)
    check_html_existence(project, checks)
    check_version_consistency(project, checks)

    # v1.x 检查
    check_json_field_values(project, checks)
    check_task_card_field_values(project, checks)
    check_step_dependencies(project, checks)
    check_depth_metrics(project, checks)
    check_html_forbidden_patterns(project, checks)
    check_core_object_mentions(project, checks)
    check_prerequisite_gate(project, checks)

    # v1.0-v1.1 面向读者的质量检查
    check_view_model_reader_facing(project, checks)
    check_action_plan_proportion(project, checks)

    # v1.2 术语科普门禁
    check_concept_ladder_seed(project, checks)
    check_reader_model(project, checks)
    check_term_explanation_coverage(project, checks)

    # v1.1 HTML 必须结构检查
    check_html_required_structures(project, checks)

    # v1.1 HTML 视觉规范量化检查（色彩来自结构化块，不来自 inline code）
    check_html_visual_metrics(project, checks)

    # v0.8 LaTeX公式渲染检查
    check_latex_rendering(project, checks)

    # v1.4 新增检查
    check_narrative_plan(project, checks)
    check_first_principles_position(project, checks)

    return checks


def main():
    parser = argparse.ArgumentParser(description="Research OS v1.2 Dumb Validator")
    parser.add_argument("project", help="项目路径")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    if not project.exists():
        print(f"[ERROR] Project not found: {project}", file=sys.stderr)
        return 1

    checks = validate_project(project)

    if args.json:
        output = [{"level": c.level, "name": c.name, "message": c.message} for c in checks]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        pass_count = sum(1 for c in checks if c.level == "PASS")
        warn_count = sum(1 for c in checks if c.level == "WARN")
        fail_count = sum(1 for c in checks if c.level == "FAIL")
        print(f"\n{'=' * 60}")
        print(f"Research OS v1.2 Dumb Validator")
        print(f"Project: {project.name}")
        print(f"{'=' * 60}\n")
        for c in checks:
            print(f"[{c.level:5}] {c.name}: {c.message}")
        print(f"\n{'=' * 60}")
        print(f"Summary: {pass_count} PASS / {warn_count} WARN / {fail_count} FAIL")
        print(f"{'=' * 60}\n")

    return 1 if any(c.level == "FAIL" for c in checks) else 0


# ============================================================
# v1.4 新增：narrative-plan 检查
# ============================================================

def check_narrative_plan(project_root: Path, results: list):
    """v1.4: 检查 narrative-plan.md 存在性 + 关键词 + 元原则检查 section"""
    np_path = project_root / "05-analysis" / "narrative-plan.md"

    # 检查 1: 文件存在性
    if not np_path.exists():
        add(results, "FAIL", "narrative_plan_exists", "narrative-plan.md 不存在（step_7.5 产物缺失）")
        return

    content = np_path.read_text(encoding="utf-8-sig", errors="ignore")

    # 检查 2: 最小字符数
    if len(content) < 500:
        add(results, "FAIL", "narrative_plan_min_chars", f"narrative-plan.md 字符数 {len(content)} 小于 500")
    else:
        add(results, "PASS", "narrative_plan_min_chars", f"narrative-plan.md 字符数 {len(content)} 大于等于 500")

    # 检查 3: 关键词检查
    required_keywords = ["认知类型", "三级节点", "章节顺序", "第一性原理位置"]
    missing_keywords = [kw for kw in required_keywords if kw not in content]

    if missing_keywords:
        add(results, "FAIL", "narrative_plan_keywords", f"narrative-plan.md 缺少关键词: {missing_keywords}")
    else:
        add(results, "PASS", "narrative_plan_keywords", "narrative-plan.md 关键词检查通过")

    # 检查 4: 元原则检查 section
    if "元原则检查" not in content:
        add(results, "FAIL", "narrative_plan_principles_section", "narrative-plan.md 缺少元原则检查section")
    else:
        add(results, "PASS", "narrative_plan_principles_section", "narrative-plan.md 包含元原则检查section")


def check_first_principles_position(project_root: Path, results: list):
    """v1.4: 检查第一性原理章节是否在调研对象章节之后"""
    report_path = project_root / "07-output" / "final-report.md"

    if not report_path.exists():
        return  # 报告不存在时其他检查会报错

    content = report_path.read_text(encoding="utf-8-sig", errors="ignore")

    # 查找调研对象章节位置
    object_pattern = r'##.*(?:调研对象|对象到底|对象是什么)'
    fp_pattern = r'##.*(?:第一性原理|本质|底层逻辑)'

    object_match = re.search(object_pattern, content)
    fp_match = re.search(fp_pattern, content)

    if object_match and fp_match:
        if fp_match.start() < object_match.start():
            add(results, "FAIL", "first_principles_position", "第一性原理章节在调研对象章节之前（v1.4要求在之后）")
        else:
            add(results, "PASS", "first_principles_position", "第一性原理章节在调研对象章节之后")
    elif fp_match and not object_match:
        add(results, "WARN", "first_principles_position", "报告含第一性原理章节但未找到调研对象章节")




if __name__ == "__main__":
    sys.exit(main())
