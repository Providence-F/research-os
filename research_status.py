#!/usr/bin/env python3
"""Research OS v0.5 status inspector.

Read project state and protocol files, then emit a concise machine-readable
status with the next required action.

v0.5 changes from v0.3:
- STEP_ORDER expanded from 10 steps to 15 steps (matching 14-研究执行状态机.md)
- Added: scaffold / route / task_card / discarded / conflicts / analysis / reader_simulation / publish
- Added 3 human confirmation points (task_card / research_plan / html_build)
- Next-action logic aligned with 14-研究执行状态机.md section 2
- infer_status now considers reader_simulation step before marking complete
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

VALIDATOR = Path(__file__).with_name("validate_research_project.py")

# v0.5: 完整 15 步状态机（对齐 14-研究执行状态机.md）
# 每一项: (step_key, expected_path, must_be_non_empty)
STEP_ORDER = [
    ("scaffold", "research_state.json", True),
    ("route", "01-plan/route_result.json", True),
    ("task_card", "00-task/task-card.md", True),
    ("research_plan", "01-plan/research-plan.md", True),
    ("candidates", "02-sources/candidates.md", True),
    ("discarded", "02-sources/discarded.md", True),
    ("evidence", "03-evidence/evidence_matrix.md", True),
    ("hypothesis", "03-evidence/hypothesis_ledger.json", True),
    ("conflicts", "03-evidence/conflicts.md", True),
    ("analysis", "05-analysis", True),
    ("red_team", "06-review/red_team.md", True),
    ("report", "07-output/final-report.md", True),
    ("trace", "07-output/trace-manifest.json", True),
    ("view_model", "07-output/view-model.json", False),  # narrative 报告可空
    ("html", "08-html/index.html", False),  # R0/R1 可不要 HTML
]

# v0.5: 下一步动作映射
NEXT_ACTION_BY_STEP = {
    "scaffold": "create_or_fix_research_state",
    "route": "run_research_router",
    "task_card": "fill_task_card_then_wait_for_human_confirmation",
    "research_plan": "run_research_planner_then_wait_for_human_confirmation",
    "candidates": "fill_candidates_md",
    "discarded": "fill_discarded_md",
    "evidence": "fill_evidence_matrix",
    "hypothesis": "update_hypothesis_ledger",
    "conflicts": "fill_conflicts_md",
    "analysis": "run_multi_agent_analysis",
    "red_team": "run_red_team_review",
    "report": "write_final_report_draft",
    "reader_simulation": "run_reader_simulation_and_rewrite",
    "trace": "write_trace_manifest",
    "view_model": "write_view_model",
    "html": "build_html_then_check_aesthetics",
    "validate": "fix_validator_failures",
    "publish": "publish_to_desktop",
    "done": "none",
}

# v0.5: 3 个人工确认点
HUMAN_CONFIRMATION_STEPS = {"task_card", "research_plan", "html"}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def run_validator(project: Path) -> dict[str, Any]:
    if not VALIDATOR.exists():
        return {"exit_code": None, "summary": "validator missing", "fails": None, "warns": None}
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), str(project)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    summary = ""
    fails = warns = None
    for line in proc.stdout.splitlines():
        if line.startswith("Summary:"):
            summary = line
            parts = line.replace("Summary:", "").replace(",", "").split()
            try:
                passes = int(parts[0])
                warns = int(parts[2])
                fails = int(parts[4])
            except (ValueError, IndexError):
                pass
    return {
        "exit_code": proc.returncode,
        "summary": summary,
        "fails": fails,
        "warns": warns,
    }


def content_state(project: Path) -> dict[str, Any]:
    candidate_pool = read_json(project / "02-sources" / "candidate_pool.json")
    candidates = candidate_pool.get("items") or []
    ledger = read_json(project / "03-evidence" / "hypothesis_ledger.json")
    hypotheses = ledger.get("hypotheses") or []
    trace_manifest = read_json(project / "07-output" / "trace-manifest.json")
    claims = trace_manifest.get("claims") or []
    view_model = read_json(project / "07-output" / "view-model.json")

    # v0.5: 检查 05-analysis 目录下是否有分析文件
    analysis_dir = project / "05-analysis"
    analysis_files = []
    if analysis_dir.exists():
        analysis_files = [p.name for p in analysis_dir.glob("*.md") if p.is_file()]

    # v0.5: 检查 discarded.md 是否有真实内容（不只是模板占位）
    discarded_path = project / "02-sources" / "discarded.md"
    discarded_has_real = False
    if discarded_path.exists():
        dmd = discarded_path.read_text(encoding="utf-8-sig")
        # 模板里有 "（待填）"，去掉模板后还有真实行才算
        real_lines = [
            line for line in dmd.splitlines()
            if line.strip().startswith("|")
            and "（待填）" not in line
            and "源名" not in line
            and "---" not in line
        ]
        discarded_has_real = len(real_lines) > 0

    # v0.5: 检查 conflicts.md 是否有真实内容
    conflicts_path = project / "03-evidence" / "conflicts.md"
    conflicts_has_real = False
    if conflicts_path.exists():
        cmd = conflicts_path.read_text(encoding="utf-8-sig")
        if "（待填）" not in cmd and "冲突 1" in cmd and "（待填）" not in cmd.split("冲突 1")[-1]:
            conflicts_has_real = True

    return {
        "candidate_count": len(candidates) if isinstance(candidates, list) else 0,
        "discarded_candidate_count": len([i for i in candidates if isinstance(i, dict) and i.get("status") == "discarded"]),
        "discarded_md_has_real_entries": discarded_has_real,
        "hypothesis_count": len(hypotheses) if isinstance(hypotheses, list) else 0,
        "revised_hypothesis_count": len([
            h for h in hypotheses
            if isinstance(h, dict) and (h.get("status") in {"downgraded", "rejected"} or h.get("revision_history"))
        ]),
        "analysis_files_count": len(analysis_files),
        "conflicts_md_has_real_entries": conflicts_has_real,
        "trace_claim_count": len(claims) if isinstance(claims, list) else 0,
        "view_model_has_cards": bool(view_model.get("summary_cards") or view_model.get("object_cards") or view_model.get("advisor_cards")),
    }


def step_completion_from_state(state: dict[str, Any]) -> dict[str, str]:
    """v0.5: 从 research_state.json 的 steps 字段读取每步完成状态。"""
    steps_field = state.get("steps") or {}
    return {k: v for k, v in steps_field.items() if isinstance(v, str)}


def human_confirmations_from_state(state: dict[str, Any]) -> dict[str, bool]:
    """v0.5: 读取 3 个人工确认点状态。"""
    return state.get("human_confirmation_points") or {}


def inspect_project(project: Path) -> dict[str, Any]:
    project = project.resolve()
    state = read_json(project / "research_state.json")
    content = content_state(project)

    # v0.5: 计算缺失的步骤（按 STEP_ORDER 顺序）
    missing_steps: list[str] = []
    empty_steps: list[str] = []
    for step_key, rel, must_non_empty in STEP_ORDER:
        target = project / rel
        if not target.exists():
            missing_steps.append(step_key)
        elif must_non_empty and target.is_file():
            text = target.read_text(encoding="utf-8-sig")
            # 检查是否还是模板占位
            if "（待填）" in text and len(text) < 5000:
                # 简单启发：含占位符且很短，视为未填
                empty_steps.append(step_key)

    # v0.5: 状态机步骤状态
    step_states = step_completion_from_state(state)
    human_confirmations = human_confirmations_from_state(state)

    validator = run_validator(project)

    # v0.5: 下一步动作判定（对齐 14-研究执行状态机.md section 2）
    # 优先级：scaffold > route > task_card > research_plan > candidates/discarded
    # > hypothesis/conflicts > analysis > red_team > report > reader_simulation
    # > trace > validate > view_model > html > publish > done
    if "scaffold" in missing_steps:
        next_step = "scaffold"
    elif "route" in missing_steps:
        next_step = "route"
    elif "task_card" in missing_steps or "task_card" in empty_steps:
        next_step = "task_card"
    elif not human_confirmations.get("step_2_task_card", False):
        next_step = "task_card"  # 等待人工确认
    elif "research_plan" in missing_steps or "research_plan" in empty_steps:
        next_step = "research_plan"
    elif not human_confirmations.get("step_3_research_plan", False):
        next_step = "research_plan"  # 等待人工确认
    elif "candidates" in missing_steps or "candidates" in empty_steps:
        next_step = "candidates"
    elif "discarded" in missing_steps or not content["discarded_md_has_real_entries"]:
        next_step = "discarded"
    elif "evidence" in missing_steps or "evidence" in empty_steps:
        next_step = "evidence"
    elif "hypothesis" in missing_steps or content["hypothesis_count"] < 3:
        next_step = "hypothesis"
    elif content["revised_hypothesis_count"] == 0:
        next_step = "hypothesis"  # 至少 1 条降级/拒绝
    elif "conflicts" in missing_steps or not content["conflicts_md_has_real_entries"]:
        next_step = "conflicts"
    elif "analysis" in missing_steps or content["analysis_files_count"] == 0:
        next_step = "analysis"
    elif "red_team" in missing_steps or "red_team" in empty_steps:
        next_step = "red_team"
    elif "report" in missing_steps or "report" in empty_steps:
        next_step = "report"
    elif step_states.get("step_10_reader_simulation") != "done":
        # v0.5 关键创新：必须跑写-读-改闭环
        next_step = "reader_simulation"
    elif "trace" in missing_steps or content["trace_claim_count"] == 0:
        next_step = "trace"
    elif validator.get("fails"):
        next_step = "validate"
    elif "view_model" in missing_steps and state.get("view_type") != "narrative_report":
        next_step = "view_model"
    elif "html" in missing_steps and state.get("depth") in ("R2", "R3"):
        next_step = "html"
    elif not human_confirmations.get("step_13_html_build", False) and state.get("depth") in ("R2", "R3"):
        next_step = "html"  # 等待美学合规确认
    elif step_states.get("step_14_validate") != "done":
        next_step = "validate"
    elif step_states.get("step_15_publish") != "done":
        next_step = "publish"
    else:
        next_step = "done"

    return {
        "schema_version": "research-os-status-v0.5",
        "project": str(project),
        "project_name": state.get("project_name", project.name),
        "research_mode": state.get("research_mode", ""),
        "view_type": state.get("view_type", ""),
        "depth": state.get("depth", ""),
        "status": infer_status(project, state, validator),
        "missing_steps": missing_steps,
        "empty_steps": empty_steps,
        "step_states": step_states,
        "human_confirmations": human_confirmations,
        "content": content,
        "validation": validator,
        "next_required_action": NEXT_ACTION_BY_STEP[next_step],
    }


def infer_status(project: Path, state: dict[str, Any], validator: dict[str, Any] | None = None) -> str:
    """v0.5: 推断项目状态。

    State machine:
      planned          — 刚创建，未填任务卡
      task_card_pending — 任务卡已填，等待人工确认
      planning          — 任务卡确认，正在写调研方案
      plan_pending      — 调研方案已写，等待人工确认
      in_progress       — 方案确认后，进入研究执行阶段
      reader_simulating — 报告草稿已写，正在跑写-读-改闭环
      html_pending      — HTML 已构建，等待美学合规确认
      completed         — 全部 15 步完成，验证通过
      failed            — HTML 已构建但 validator 报 FAIL
    """
    if not state:
        return "planned"

    # 检查任务卡
    task_card = project / "00-task" / "task-card.md"
    if not task_card.exists():
        return "planned"
    confirmations = state.get("human_confirmation_points") or {}
    if not confirmations.get("step_2_task_card", False):
        return "task_card_pending"

    # 检查调研方案
    plan = project / "01-plan" / "research-plan.md"
    if not plan.exists():
        return "planning"
    if not confirmations.get("step_3_research_plan", False):
        return "plan_pending"

    # 检查 HTML 构建状态
    html_built = (project / "08-html" / "index.html").exists()
    depth = state.get("depth", "")
    step_states = (state.get("steps") or {})

    # 检查 reader_simulation 步骤（v0.5 关键）
    report = project / "07-output" / "final-report.md"
    if report.exists() and step_states.get("step_10_reader_simulation") != "done":
        return "reader_simulating"

    if depth not in ("R2", "R3"):
        # R0/R1：报告写完即可，不需要 HTML
        if report.exists():
            if validator is None:
                validator = run_validator(project)
            if validator.get("fails"):
                return "failed"
            return "completed"
        return "in_progress"

    # R2/R3
    if not html_built:
        return "in_progress"
    if not confirmations.get("step_13_html_build", False):
        return "html_pending"

    if validator is None:
        validator = run_validator(project)
    if validator.get("fails"):
        return "failed"

    # 检查 publish 步骤
    if step_states.get("step_15_publish") != "done":
        return "in_progress"

    return "completed"


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Research OS v0.5 project status")
    parser.add_argument("project", help="Path to research project directory")
    args = parser.parse_args()
    result = inspect_project(Path(args.project).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["validation"].get("fails") else 0


if __name__ == "__main__":
    raise SystemExit(main())
