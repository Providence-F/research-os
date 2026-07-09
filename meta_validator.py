#!/usr/bin/env python3
"""Research OS v1.0 - Meta Validator（元审计层）

第一性原理：Research OS 是信任转化器——把不可信的 AI 认知劳动转化为
人类敢押注真实后果的决策输入。validator 审计研究报告产物，审计 Agent
审计报告质量，但没有任何机制审计"工具本身是否越界""信任是否真实在转化"。

meta_validator 就是这第四权——审计工具本身和信任链。

三类检查：
  A. 工具越界检测（静态扫描 .py，检出硬编码语义判断 / 文本改写 / 假装 smart）
  B. 信任链完整性检测（验证从 intent → report 每一环是否真实存在，不造假）
  C. 路径契约检测（验证所有工具引用的文件路径一致，不出现幽灵文件）

设计原则（继承 Smart Agent. Dumb Tools.）：
  - meta_validator 只做机械的静态扫描和文件存在性检查
  - 不做语义判断（不评价工具设计好不好，只检测是否违反明文禁令）
  - 检出项必须可追溯到具体文件和行号

用法：
  python meta_validator.py                          # 审计整个仓库的工具
  python meta_validator.py --project <项目路径>      # 审计某个项目的信任链
  python meta_validator.py --repo <仓库路径> --project <项目路径>  # 全部审计
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


# ============================================================
# 仓库根目录（meta_validator.py 所在目录即为仓库根）
# ============================================================

REPO_ROOT = Path(__file__).resolve().parent


# ============================================================
# A. 工具越界检测（静态扫描）
# ============================================================

# 状态机 14-研究执行状态机.md 第 4 节明文禁止工具做的语义动作。
# 每条禁令对应一个可机械检测的代码模式。
TOOL_BOUNDARY_VIOLATIONS = [
    {
        "id": "B01",
        "name": "硬编码路由关键词列表",
        "forbidden_pattern": r"^(DECISION_KEYWORDS|OPPORTUNITY_KEYWORDS|PRODUCT_KEYWORDS|USER_VOICE_KEYWORDS)\s*=\s*\[",
        "reason": "状态机第 4 节明令'路由判断（改为 Agent 显式选择）'是工具永远不做的。"
                  "关键词列表让工具替 Agent 做路由决策。",
        "severity": "FAIL",
    },
    {
        "id": "B02",
        "name": "硬编码核心生成器字典",
        "forbidden_pattern": r"^DEFAULT_CORE_GENERATORS\s*=\s*\{",
        "reason": "ljg-rank 降秩是高度语义化的智力活动，结果不应固化为查找表。"
                  "每个领域的生成器应由 Agent 现场降秩产出。",
        "severity": "FAIL",
    },
    {
        "id": "B03",
        "name": "硬编码 AI 味检测列表",
        "forbidden_pattern": r"^AI_TELLS\s*=\s*\[",
        "reason": "状态机第 4 节明令'AI 味检测（改为审计 Agent 评估）'是工具永远不做的。",
        "severity": "FAIL",
    },
    {
        "id": "B04",
        "name": "工具内文本改写（re.sub 删除语义内容）",
        "forbidden_pattern": r're\.sub\(r["\'].*(?:本质上|反常识|反直觉|不是.{0,25}?而是)',
        "reason": "strip_ai_tell / 任何 re.sub 删除语义内容都是工具替 Agent 做改写决策。"
                  "工具只能做结构性模式匹配（如删除 [E003] 内部编号），不能改写语义内容。",
        "severity": "FAIL",
    },
    {
        "id": "B05",
        "name": "项目名语义联想（if '开源' in name 等）",
        "forbidden_pattern": r'if\s+["\'](?:开源|github|深度调研|调研系统)["\']\s+in\s+(?:name|project_name|text)',
        "reason": "硬编码项目名语义联想是 v0.7.1 已修复的 check_core_object_mentions 同类错误。"
                  "工具不应基于项目名做语义推断。",
        "severity": "FAIL",
    },
    {
        "id": "B06",
        "name": "假装 smart（exploration_method 字段暗示探索已完成）",
        "forbidden_pattern": r'exploration_method["\']?\s*:\s*["\'](?:brainstorming_integrated|3rounds|multi_round)',
        "reason": "字段名暗示探索已完成，但实际 result 为 None。这是信任源头造假——"
                  "在信任链入口注入伪信任。",
        "severity": "FAIL",
    },
]

# 被豁免的目录（归档、测试、本文件自身）
EXEMPT_DIRS = {"archive", ".git", "__pycache__", "node_modules", "dashboard"}


@dataclass
class MetaCheck:
    level: str  # PASS / WARN / FAIL
    category: str  # boundary / trust_chain / path_contract
    check_id: str
    name: str
    file: str  # 相对仓库根的路径
    line: int
    detail: str


def scan_tool_boundary_violations(repo_root: Path) -> list[MetaCheck]:
    """A 类检查：静态扫描所有 .py，检测工具是否越界做语义判断。"""
    checks: list[MetaCheck] = []

    for py_file in repo_root.rglob("*.py"):
        parts = py_file.parts
        if any(exempt in parts for exempt in EXEMPT_DIRS):
            continue
        if py_file.name == "meta_validator.py":
            continue

        try:
            lines = py_file.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue

        rel = str(py_file.relative_to(repo_root))

        for violation in TOOL_BOUNDARY_VIOLATIONS:
            pattern = violation["forbidden_pattern"]
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    checks.append(MetaCheck(
                        level=violation["severity"],
                        category="boundary",
                        check_id=violation["id"],
                        name=violation["name"],
                        file=rel,
                        line=i,
                        detail=f"{violation['reason']} | 匹配行: {line.strip()[:100]}",
                    ))

    boundary_fails = [c for c in checks if c.level == "FAIL"]
    if not boundary_fails:
        checks.append(MetaCheck(
            level="PASS",
            category="boundary",
            check_id="B00",
            name="工具越界检测",
            file="-",
            line=0,
            detail=f"扫描 {len(list(repo_root.rglob('*.py')))} 个 .py 文件，未发现工具越界做语义判断",
        ))

    return checks


# ============================================================
# B. 信任链完整性检测
# ============================================================

def read_json_safe(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def read_text_safe(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8-sig")
    except Exception:
        return ""


def check_trust_chain(project: Path) -> list[MetaCheck]:
    """B 类检查：验证从 intent → report 的信任链每一环是否真实存在。"""
    checks: list[MetaCheck] = []
    try:
        rel_project = str(project.relative_to(REPO_ROOT))
    except ValueError:
        rel_project = str(project)

    # B10: intent_doc 必须真实完成探索（不能是 skeleton_pending_agent）
    intent_path = project / "00-task" / "intent_doc.json"
    intent = read_json_safe(intent_path)
    if not intent:
        checks.append(MetaCheck(
            level="WARN", category="trust_chain", check_id="B10",
            name="意图文档存在性", file=f"{rel_project}/00-task/intent_doc.json",
            line=0, detail="intent_doc.json 不存在——意图探索未启动",
        ))
    else:
        status = intent.get("status", "")
        exploration_history = intent.get("exploration_history", [])
        has_fake_method = bool(intent.get("exploration_method"))
        has_real_results = (
            isinstance(exploration_history, list)
            and len(exploration_history) > 0
            and any(h.get("result") for h in exploration_history if isinstance(h, dict))
        )
        # 旧 schema 检测：缺 status 或 exploration_history 字段
        has_new_schema_fields = ("status" in intent) or ("exploration_history" in intent)
        if has_fake_method and not has_real_results:
            checks.append(MetaCheck(
                level="FAIL", category="trust_chain", check_id="B11",
                name="意图探索伪信任", file=f"{rel_project}/00-task/intent_doc.json",
                line=0, detail="exploration_method 字段声称已完成探索，但 exploration_history 为空或 result 全为 None。"
                               "这是信任源头造假——在信任链入口注入伪信任。",
            ))
        elif not has_new_schema_fields:
            checks.append(MetaCheck(
                level="WARN", category="trust_chain", check_id="B14",
                name="意图文档使用旧 schema", file=f"{rel_project}/00-task/intent_doc.json",
                line=0, detail="intent_doc.json 缺 status/exploration_history 字段（旧 schema）。"
                               "信任链入口未接入新协议——无法验证意图探索是否由 Agent 真实完成。",
            ))
        elif status == "skeleton_pending_agent":
            checks.append(MetaCheck(
                level="WARN", category="trust_chain", check_id="B12",
                name="意图探索未完成", file=f"{rel_project}/00-task/intent_doc.json",
                line=0, detail="status=skeleton_pending_agent，意图探索尚未由 Agent 完成",
            ))
        elif has_real_results or status == "exploration_complete":
            checks.append(MetaCheck(
                level="PASS", category="trust_chain", check_id="B13",
                name="意图探索真实完成", file=f"{rel_project}/00-task/intent_doc.json",
                line=0, detail="exploration_history 含真实结果，意图探索已由 Agent 完成",
            ))
        else:
            checks.append(MetaCheck(
                level="WARN", category="trust_chain", check_id="B15",
                name="意图探索状态不明", file=f"{rel_project}/00-task/intent_doc.json",
                line=0, detail=f"status={status!r}，既非 skeleton_pending_agent 也非 exploration_complete，"
                               "且无真实 exploration_history——意图探索状态无法判定。",
            ))

    # B20: 核心生成器必须由 Agent 降秩产出（不能是工具硬编码或为空）
    plan_path = project / "01-plan" / "research-plan.md"
    plan_text = read_text_safe(plan_path)
    if not plan_text:
        checks.append(MetaCheck(
            level="WARN", category="trust_chain", check_id="B23",
            name="研究计划缺失", file=f"{rel_project}/01-plan/research-plan.md",
            line=0, detail="research-plan.md 不存在——Agent 尚未产出研究计划，核心生成器降秩未启动",
        ))
    else:
        has_generators_section = bool(re.search(r"^##\s+核心生成器", plan_text, re.MULTILINE))
        if not has_generators_section:
            checks.append(MetaCheck(
                level="WARN", category="trust_chain", check_id="B24",
                name="核心生成器章节缺失", file=f"{rel_project}/01-plan/research-plan.md",
                line=0, detail="research-plan.md 无 ## 核心生成器 章节——Agent 未用 ljg-rank 降秩，"
                               "信任链第二环（生成器来源）无法验证",
            ))
        else:
            section_content = _extract_section(plan_text, "核心生成器")
            real_items = [l for l in section_content.splitlines()
                          if l.strip().startswith("-") and "（待填）" not in l and len(l.strip()) > 5]
            if real_items:
                checks.append(MetaCheck(
                    level="PASS", category="trust_chain", check_id="B21",
                    name="核心生成器由 Agent 降秩", file=f"{rel_project}/01-plan/research-plan.md",
                    line=0, detail=f"research-plan.md 含 {len(real_items)} 个由 Agent 降秩产出的核心生成器",
                ))
            else:
                checks.append(MetaCheck(
                    level="WARN", category="trust_chain", check_id="B22",
                    name="核心生成器为空", file=f"{rel_project}/01-plan/research-plan.md",
                    line=0, detail="## 核心生成器 章节存在但无真实条目——Agent 尚未降秩",
                ))

    # B30: 独立审计必须含真实引用（不能是模板占位）
    audit_path = project / "06-review" / "audit_report.md"
    audit_text = read_text_safe(audit_path)
    if not audit_text:
        checks.append(MetaCheck(
            level="WARN", category="trust_chain", check_id="B33",
            name="独立审计缺失", file=f"{rel_project}/06-review/audit_report.md",
            line=0, detail="audit_report.md 不存在——独立审计 Agent 未执行，信任链第三环缺失",
        ))
    else:
        has_template_placeholder = bool(re.search(r"（如有[，,].*列出）", audit_text))
        has_real_evidence = bool(re.search(r"引用报告原文[：:]\s*\S", audit_text))
        if has_template_placeholder and not has_real_evidence:
            checks.append(MetaCheck(
                level="FAIL", category="trust_chain", check_id="B31",
                name="独立审计为模板占位", file=f"{rel_project}/06-review/audit_report.md",
                line=0, detail="audit_report.md 仍是模板占位文字，未含真实证据引用。"
                               "门禁 PASS 是假的——审计未真正执行。",
            ))
        elif has_real_evidence:
            checks.append(MetaCheck(
                level="PASS", category="trust_chain", check_id="B32",
                name="独立审计含真实证据", file=f"{rel_project}/06-review/audit_report.md",
                line=0, detail="audit_report.md 含真实报告引用，审计已执行",
            ))
        else:
            checks.append(MetaCheck(
                level="WARN", category="trust_chain", check_id="B34",
                name="独立审计状态不明", file=f"{rel_project}/06-review/audit_report.md",
                line=0, detail="audit_report.md 存在但既非模板占位也无真实证据引用——审计质量无法判定",
            ))

    # B40: 读者模拟闭环——如果 failed_paragraphs 非空，iteration_state 必须显示至少 1 轮重写
    diag_path = project / "06-review" / "reader_diagnosis.json"
    iter_path = project / "06-review" / "iteration_state.json"
    diag = read_json_safe(diag_path)
    if not diag:
        checks.append(MetaCheck(
            level="WARN", category="trust_chain", check_id="B43",
            name="读者模拟缺失", file=f"{rel_project}/06-review/reader_diagnosis.json",
            line=0, detail="reader_diagnosis.json 不存在——读者模拟未执行，写-读-改闭环未启动",
        ))
    else:
        failed = diag.get("failed_paragraphs", [])
        passed = diag.get("passed", True)
        if failed and not passed:
            iter_state = read_json_safe(iter_path)
            iterations = iter_state.get("iterations", 0)
            history = iter_state.get("history", [])
            if iterations == 0 and not history:
                checks.append(MetaCheck(
                    level="FAIL", category="trust_chain", check_id="B41",
                    name="读者模拟未闭环", file=f"{rel_project}/06-review/reader_diagnosis.json",
                    line=0, detail=f"读者诊断有 {len(failed)} 个失败段落，但 iteration_state.json 无重写记录。"
                                   "写-读-改闭环未执行——审计未闭环。",
                ))
            else:
                checks.append(MetaCheck(
                    level="PASS", category="trust_chain", check_id="B42",
                    name="读者模拟已闭环", file=f"{rel_project}/06-review/iteration_state.json",
                    line=0, detail=f"读者诊断有失败段落，已执行 {iterations} 轮重写",
                ))
        elif passed:
            checks.append(MetaCheck(
                level="PASS", category="trust_chain", check_id="B44",
                name="读者模拟通过", file=f"{rel_project}/06-review/reader_diagnosis.json",
                line=0, detail="读者诊断 passed=True，写-读-改闭环已完成",
            ))

    # B50: 状态-产物一致性——step done 但产物缺失
    state = read_json_safe(project / "research_state.json")
    if not state:
        checks.append(MetaCheck(
            level="WARN", category="trust_chain", check_id="B51",
            name="状态文件缺失", file=f"{rel_project}/research_state.json",
            line=0, detail="research_state.json 不存在——无法验证状态-产物一致性",
        ))
    else:
        steps = state.get("steps", {})
        if not steps:
            checks.append(MetaCheck(
                level="WARN", category="trust_chain", check_id="B52",
                name="状态文件无 steps", file=f"{rel_project}/research_state.json",
                line=0, detail="research_state.json 无 steps 字段（旧 schema）——"
                               "无法验证状态-产物一致性，信任链第五环无法审计",
            ))
        else:
            done_count = 0
            for step_key, step_status in steps.items():
                if step_status != "done":
                    continue
                done_count += 1
                artifact_check = _get_step_artifact_rel(step_key)
                if not artifact_check:
                    continue
                artifact_path = project / artifact_check
                if not artifact_path.exists():
                    checks.append(MetaCheck(
                        level="FAIL", category="trust_chain", check_id="B50",
                        name="状态-产物不一致", file=f"{rel_project}/research_state.json",
                        line=0, detail=f"{step_key} 标记 done 但产物 {artifact_check} 不存在",
                    ))
            if done_count > 0:
                # 检查是否有任何 FAIL，没有则 PASS
                b50_fails = [c for c in checks if c.check_id == "B50"]
                if not b50_fails:
                    checks.append(MetaCheck(
                        level="PASS", category="trust_chain", check_id="B53",
                        name="状态-产物一致", file=f"{rel_project}/research_state.json",
                        line=0, detail=f"{done_count} 个 done 步骤的产物全部存在",
                    ))

    return checks


def _extract_section(md_text: str, section_name: str) -> str:
    """提取 ## section_name 到下一个 ## 之间的内容。"""
    pattern = rf"^##\s+{re.escape(section_name)}.*?(?=^##\s|\Z)"
    match = re.search(pattern, md_text, re.MULTILINE | re.DOTALL)
    return match.group(0) if match else ""


def _get_step_artifact_rel(step_key: str) -> str:
    """step_key → 关键产物相对路径（用于状态-产物一致性检查）。"""
    mapping = {
        "step_2_task_card": "00-task/task-card.md",
        "step_3_research_plan": "01-plan/research-plan.md",
        "step_4_candidates": "02-sources/candidates.md",
        "step_5_evidence_matrix": "03-evidence/evidence_matrix.md",
        "step_6_hypothesis": "03-evidence/hypothesis_ledger.json",
        "step_6_5_core_objects_fetch": "04-captures/core_objects_fetch_log.md",
        "step_8_red_team": "06-review/red_team.md",
        "step_9_final_report_draft": "07-output/final-report.md",
        "step_9_5_independent_audit": "06-review/audit_report.md",
        "step_10_reader_simulation": "06-review/reader_diagnosis.json",
        "step_13_html_build": "08-html/index.html",
    }
    return mapping.get(step_key, "")


# ============================================================
# C. 路径契约检测
# ============================================================

# 所有关键协议文件的"正确路径"——单一真相源
# 任何工具引用这些文件时，路径前缀必须与这里一致
PATH_CONTRACTS = {
    "intent_doc.json": "00-task/",
    "goal_ledger.json": "00-task/",
    "task-card.md": "00-task/",
    "research-plan.md": "01-plan/",
    "candidates.md": "02-sources/",
    "discarded.md": "02-sources/",
    "evidence_matrix.md": "03-evidence/",
    "hypothesis_ledger.json": "03-evidence/",
    "conflicts.md": "03-evidence/",
    "core_objects_fetch_log.md": "04-captures/",
    "red_team.md": "06-review/",
    "audit_report.md": "06-review/",
    "reader_diagnosis.json": "06-review/",
    "reader_feedback.md": "06-review/",
    "final-report.md": "07-output/",
    "trace-manifest.json": "07-output/",
    "view-model.json": "07-output/",
    "index.html": "08-html/",
    "research_state.json": "",
}

# 路径使用的三种真实模式（不匹配提示文字中的文件名提及）：
#   1. 路径拼接：identifier / "subdir/file.ext"
#   2. 字典 key："subdir/file.ext": (
#   3. _source 赋值：xxx_source": "subdir/file.ext"  或  xxx_source = "subdir/file.ext"
_PATH_CONCAT_PATTERN = re.compile(r'\w+\s*/\s*["\']([^"\']+)["\']')
_DICT_KEY_PATTERN = re.compile(r'["\']([^"\']+)["\']\s*:\s*\(')
_SOURCE_ASSIGN_PATTERN = re.compile(r'_source["\']?\s*[:=]\s*["\']([^"\']+)["\']')


def check_path_contracts(repo_root: Path) -> list[MetaCheck]:
    """C 类检查：验证所有 .py 引用的协议文件路径一致。

    只检测真正的路径使用（路径拼接 / 字典 key / _source 赋值），
    不检测 print/f-string 里的提示文字。
    """
    checks: list[MetaCheck] = []
    seen: set[tuple[str, int, str]] = set()

    for py_file in repo_root.rglob("*.py"):
        parts = py_file.parts
        if any(exempt in parts for exempt in EXEMPT_DIRS):
            continue
        if py_file.name == "meta_validator.py":
            continue

        try:
            lines = py_file.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue

        rel = str(py_file.relative_to(repo_root))

        for i, line in enumerate(lines, 1):
            stripped = line.lstrip()
            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                continue

            # 收集本行所有被引用的路径
            found_paths: list[str] = []
            for m in _PATH_CONCAT_PATTERN.finditer(line):
                found_paths.append(m.group(1))
            for m in _DICT_KEY_PATTERN.finditer(line):
                found_paths.append(m.group(1))
            for m in _SOURCE_ASSIGN_PATTERN.finditer(line):
                found_paths.append(m.group(1))

            # 检查每个路径是否违反契约
            for found_path in found_paths:
                for filename, expected_prefix in PATH_CONTRACTS.items():
                    if filename not in found_path:
                        continue
                    if not found_path.endswith(filename):
                        continue
                    expected_full = expected_prefix + filename if expected_prefix else filename
                    if found_path == expected_full:
                        continue
                    # 排除：found_path 包含完整期望路径（如更长的路径里含正确子路径）
                    if expected_full in found_path and found_path != filename:
                        continue

                    key = (rel, i, found_path)
                    if key in seen:
                        continue
                    seen.add(key)

                    checks.append(MetaCheck(
                        level="FAIL", category="path_contract", check_id="C01",
                        name="路径契约违反", file=rel, line=i,
                        detail=f"引用 {found_path}，但契约规定 {filename} 应在 {expected_prefix or '根目录'}。"
                               f"这会导致幽灵文件——创建者和读取者路径不一致。",
                    ))

    if not any(c.level == "FAIL" and c.category == "path_contract" for c in checks):
        checks.append(MetaCheck(
            level="PASS", category="path_contract", check_id="C00",
            name="路径契约检测", file="-", line=0,
            detail="所有 .py 引用的协议文件路径与契约一致",
        ))

    return checks




# ============================================================
# D. Trust Ledger 生成（信任账本）
# ============================================================

def generate_trust_ledger(project: Path) -> dict:
    """为项目生成 trust_ledger.json——记录信任链每一环的状态。

    这是信任转化器的"收据"——让用户一眼看到：
      - 这份报告的结论，有多少比例的信任是真实的
      - 哪些环节有信任缺口

    Args:
        project: 研究项目目录

    Returns:
        trust_ledger dict，同时写入 project/trust_ledger.json
    """
    from datetime import datetime

    checks = check_trust_chain(project)
    trust_chain = []
    pass_count = 0
    total_weight = 0

    # 信任链各环节的权重（总和 = 1.0）
    stage_weights = {
        "B1": 0.20,  # 意图探索（信任源头）
        "B2": 0.15,  # 核心生成器
        "B3": 0.20,  # 独立审计
        "B4": 0.15,  # 读者模拟闭环
        "B5": 0.30,  # 状态-产物一致性
    }

    # 按 check_id 前缀分组
    for prefix, weight in stage_weights.items():
        stage_checks = [c for c in checks if c.check_id.startswith(prefix)]
        if not stage_checks:
            continue

        # 取该阶段最差的状态
        worst = "PASS"
        for c in stage_checks:
            if c.level == "FAIL":
                worst = "FAIL"
                break
            elif c.level == "WARN" and worst != "FAIL":
                worst = "WARN"

        stage_name = stage_checks[0].name if stage_checks else ""
        evidence = stage_checks[0].detail if stage_checks else ""

        if worst == "PASS":
            score = weight
            status = "verified"
            pass_count += 1
        elif worst == "WARN":
            score = weight * 0.5
            status = "partial"
        else:
            score = 0.0
            status = "fake" if "伪信任" in evidence or "造假" in evidence or "模板占位" in evidence else "missing"

        total_weight += weight
        trust_chain.append({
            "stage": stage_checks[0].check_id,
            "stage_name": stage_name,
            "status": status,
            "evidence": evidence[:200],
            "trust_score": round(score / weight, 2),
            "weight": weight,
            "verified_by": "meta_validator",
        })

    # 计算总信任分
    earned = sum(s["trust_score"] * s["weight"] for s in trust_chain)
    if total_weight == 0:
        # 所有阶段都无检查项——这是元审计本身的失败，不是"0 分"而是"未审计"
        overall = 0.0
        decision_ready = False
        trust_gaps = []
        # 添加一个显式的"未审计"标记
        trust_chain.append({
            "stage": "META",
            "stage_name": "元审计未覆盖",
            "status": "unaudited",
            "evidence": "check_trust_chain 返回 0 个检查项——元审计逻辑未覆盖该项目的任何信任环节",
            "trust_score": 0.0,
            "weight": 1.0,
            "verified_by": "meta_validator",
        })
    else:
        overall = round(earned / total_weight, 2)
        decision_ready = overall >= 0.7
        # trust_gaps 包含所有非 verified 状态——partial/fake/missing/unaudited 都是信任缺口
        trust_gaps = [s for s in trust_chain if s["status"] != "verified"]

    ledger = {
        "schema_version": "research-os-trust-ledger-v1.0",
        "project_name": project.name,
        "generated_at": datetime.now().isoformat(),
        "trust_chain": trust_chain,
        "overall_trust": overall,
        "trust_gaps": [f"{s['stage']}: {s['stage_name']} ({s['status']})" for s in trust_gaps],
        "decision_ready": decision_ready,
        "last_meta_audit": datetime.now().isoformat(),
    }

    # 写入项目目录
    ledger_path = project / "trust_ledger.json"
    import json as _json
    ledger_path.write_text(_json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")

    return ledger

# ============================================================
# 主审计函数
# ============================================================

def run_meta_audit(repo_root: Path | None = None, project: Path | None = None) -> dict:
    """运行完整元审计。"""
    if repo_root is None:
        repo_root = REPO_ROOT

    checks: list[MetaCheck] = []

    # A 类：工具越界（总是跑，审计仓库本身）
    checks.extend(scan_tool_boundary_violations(repo_root))

    # C 类：路径契约（总是跑，审计仓库本身）
    checks.extend(check_path_contracts(repo_root))

    # B 类：信任链（仅当指定 project 时跑）
    if project:
        checks.extend(check_trust_chain(project))

    summary = {
        "PASS": sum(1 for c in checks if c.level == "PASS"),
        "WARN": sum(1 for c in checks if c.level == "WARN"),
        "FAIL": sum(1 for c in checks if c.level == "FAIL"),
    }

    trust_gaps = []
    for c in checks:
        if c.level == "FAIL" and c.category == "trust_chain":
            trust_gaps.append(f"[{c.check_id}] {c.name}: {c.detail}")

    return {
        "checks": checks,
        "summary": summary,
        "trust_gaps": trust_gaps,
    }


def render_report(audit: dict) -> str:
    """渲染可读的元审计报告。"""
    lines = []
    lines.append("=" * 70)
    lines.append("Research OS Meta Validator — 元审计报告")
    lines.append("审计对象：工具本身 + 信任链（不审计研究报告产物）")
    lines.append("=" * 70)
    lines.append("")

    checks = audit["checks"]
    summary = audit["summary"]

    for category, label in [("boundary", "A. 工具越界检测"), ("path_contract", "C. 路径契约检测"), ("trust_chain", "B. 信任链完整性")]:
        cat_checks = [c for c in checks if c.category == category]
        if not cat_checks:
            continue
        lines.append(f"--- {label} ---")
        for c in cat_checks:
            loc = f"{c.file}:{c.line}" if c.line else c.file
            lines.append(f"[{c.level:5}] {c.check_id} {c.name} ({loc})")
            lines.append(f"         {c.detail}")
        lines.append("")

    lines.append("=" * 70)
    lines.append(f"Summary: {summary['PASS']} PASS / {summary['WARN']} WARN / {summary['FAIL']} FAIL")
    if audit["trust_gaps"]:
        lines.append("")
        lines.append("信任缺口（FAIL 级 trust_chain 问题）:")
        for gap in audit["trust_gaps"]:
            lines.append(f"  - {gap}")
    lines.append("=" * 70)

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Research OS Meta Validator — 元审计层（审计工具本身和信任链）"
    )
    parser.add_argument("--repo", default=str(REPO_ROOT), help="仓库根目录")
    parser.add_argument("--project", default=None, help="审计某个研究项目的信任链")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--trust-ledger", action="store_true", help="生成 trust_ledger.json 信任账本")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    project = Path(args.project).resolve() if args.project else None

    audit = run_meta_audit(repo_root=repo, project=project)

    # 生成 trust_ledger（如果指定了 project）
    if args.trust_ledger and project:
        ledger = generate_trust_ledger(project)
        print()
        print(f"Trust Ledger 已生成: {project / 'trust_ledger.json'}")
        print(f"Overall Trust: {ledger['overall_trust']}")
        print(f"Decision Ready: {'YES' if ledger['decision_ready'] else 'NO (trust < 0.7)'}")
        if ledger['trust_gaps']:
            print(f"Trust Gaps: {len(ledger['trust_gaps'])}")
            for gap in ledger['trust_gaps']:
                print(f"  - {gap}")
        return 0

    if args.json:
        output = {
            "summary": audit["summary"],
            "trust_gaps": audit["trust_gaps"],
            "checks": [
                {
                    "level": c.level,
                    "category": c.category,
                    "check_id": c.check_id,
                    "name": c.name,
                    "file": c.file,
                    "line": c.line,
                    "detail": c.detail,
                }
                for c in audit["checks"]
            ],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(render_report(audit))

    return 1 if audit["summary"]["FAIL"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
