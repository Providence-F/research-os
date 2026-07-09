#!/usr/bin/env python3
"""Research OS v0.7 - Dumb Validator

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
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


# ============================================================
# v0.7 配置
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
    },
    "03-evidence/hypothesis_ledger.json": {
        "hypotheses": list,
    },
    "02-sources/candidate_pool.json": {
        "items": list,
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
    "step_2_task_card": {"required": ["00-task/task-card.md"]},
    "step_3_research_plan": {"required": ["01-plan/research-plan.md"]},
    "step_4_candidates": {"required": ["02-sources/candidates.md", "02-sources/discarded.md"]},
    "step_5_evidence_matrix": {"required": ["03-evidence/evidence_matrix.md"]},
    "step_6_hypothesis": {"required": ["03-evidence/hypothesis_ledger.json"]},
    "step_6_5_core_objects_fetch": {"required": ["04-captures/core_objects_fetch_log.md"]},
    "step_7_analysis": {"required": ["05-analysis/"], "any_md": True},
    "step_8_red_team": {"required": ["06-review/red_team.md"]},
    "step_9_final_report_draft": {"required": ["07-output/final-report.md"]},
    "step_9_5_independent_audit": {"required": ["06-review/audit_report.md"]},
    "step_10_reader_simulation": {"required": ["06-review/reader_diagnosis.json", "06-review/reader_feedback.md"]},
    "step_11_trace_manifest": {"required": ["07-output/trace-manifest.json"]},
    "step_12_view_model": {"required": ["07-output/view-model.json"]},
    "step_13_html_build": {"required": ["08-html/index.html"]},
}

STEP_DEPENDENCIES = {
    "step_6_5_core_objects_fetch": ["step_2_task_card", "step_3_research_plan"],
    "step_7_analysis": ["step_6_5_core_objects_fetch", "step_5_evidence_matrix"],
    "step_8_red_team": ["step_7_analysis"],
    "step_9_final_report_draft": ["step_7_analysis", "step_8_red_team"],
    "step_9_5_independent_audit": ["step_9_final_report_draft"],
    "step_10_reader_simulation": ["step_9_5_independent_audit"],
    "step_13_html_build": ["step_10_reader_simulation", "step_12_view_model"],
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

HTML_FORBIDDEN_PATTERNS = {
    "toc_scrollbar": {
        "pattern": r"aside\.toc\s*\{[^}]*overflow-y:\s*auto",
        "message": "目录栏禁止使用 overflow-y: auto（滚轮问题）",
    },
    "unclosed_div": {
        "pattern": r"<div class=\"source-section\">[^<]*<h1",
        "message": "source-section div 未正确闭合（附录 div bug）",
    },
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
# v0.7 新增检查函数
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
# v1.0 面向读者的质量检查
# ============================================================

# 开发者术语——不应出现在面向读者的字段中
DEVELOPER_TERMS = [
    "step_", "final-report", "view-model", ".json", "schema_version",
    "_design", "intent_doc", "research_state", "meta_validator",
    "trust_ledger", "build_research_html", "dumb_tools",
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
    check_source_citation_format(project, checks)
    check_html_existence(project, checks)
    check_version_consistency(project, checks)

    # v0.7 新增
    check_json_field_values(project, checks)
    check_task_card_field_values(project, checks)
    check_step_dependencies(project, checks)
    check_depth_metrics(project, checks)
    check_html_forbidden_patterns(project, checks)
    check_core_object_mentions(project, checks)
    check_prerequisite_gate(project, checks)

    # v1.0 面向读者的质量检查
    check_view_model_reader_facing(project, checks)
    check_action_plan_proportion(project, checks)

    return checks


def main():
    parser = argparse.ArgumentParser(description="Research OS v0.7 Dumb Validator")
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
        print(f"Research OS v0.7 Dumb Validator")
        print(f"Project: {project.name}")
        print(f"{'=' * 60}\n")
        for c in checks:
            print(f"[{c.level:5}] {c.name}: {c.message}")
        print(f"\n{'=' * 60}")
        print(f"Summary: {pass_count} PASS / {warn_count} WARN / {fail_count} FAIL")
        print(f"{'=' * 60}\n")

    return 1 if any(c.level == "FAIL" for c in checks) else 0


if __name__ == "__main__":
    sys.exit(main())
