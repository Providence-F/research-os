#!/usr/bin/env python3
"""Research OS v0.3/v0.7 planner.

Generate a mode-aware research execution plan, candidate-pool seed, and
hypothesis-ledger seed. v0.7 extensions: consume goal_ledger + 8 contracts
(reader_model/intent_tree/concept_ladder/personalization_plan/report_contract/
layout_spec/clarifying_questions/iteration_strategy); block plan when
clarifying_questions unanswered; bind goal_id to hypotheses.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

import goal_tracker


MODE_PLANS: dict[str, dict[str, Any]] = {
    "evidence_intelligence": {
        "questions": [
            "哪些事实必须核验？",
            "哪些来源是官方、原始、可追溯的？",
            "哪些信息来自搜索摘要或传抄，必须降级？",
            "哪些结论可能存在冲突？",
            "最终读者需要基于这份研究做什么决定？",
        ],
        "hypotheses": [
            "核心事实可以被 A/B 级来源支撑。",
            "搜索摘要只能作为线索，不能支撑强结论。",
            "最终结论需要按置信度分层。",
        ],
    },
    "thinking_decision": {
        "questions": [
            "这个问题是不是问错了，真正决策是什么？",
            "这件事值得投入到什么程度：合规、轻资产、战略资产还是逃逸？",
            "主要机会成本是什么？",
            "每个候选选项的最小可行版本是什么？",
            "哪些变量必须联系、实测或外部验证？",
            "如果反方成立，当前推荐要如何降级？",
        ],
        "hypotheses": [
            "最优解可能不是选最强选项，而是控制投入强度。",
            "候选项需要按成本、复用价值、风险和可完成性比较。",
            "至少一个看似强的结论需要被反方审计降级。",
        ],
    },
    "opportunity_map": {
        "questions": [
            "候选池的召回边界是什么？",
            "排序维度和淘汰规则是什么？",
            "哪些对象必须进入 Top N 深拆？",
            "哪些来源是官方/招聘/数据库/媒体/搜索摘要？",
            "最终列表如何支持行动：投递、联系、购买、继续研究？",
        ],
        "hypotheses": [
            "候选池需要先广泛召回，再按明确维度淘汰。",
            "Top N 结论必须能追溯到评分依据和风险。",
            "至少一部分高曝光对象会因不匹配被淘汰。",
        ],
    },
    "product_teardown": {
        "questions": [
            "产品到底解决哪个用户问题？",
            "核心机制是什么，哪一步是真壁垒？",
            "公开材料中哪些是营销话术，哪些可验证？",
            "用户场景、竞品和替代方案是什么？",
            "产品最大未验证假设是什么？",
            "如何把产品观察转成可对外输出的表达（面试/作品集/写作）？",
        ],
        "hypotheses": [
            "产品真正卖点不一定等于官网最显眼的话术。",
            "至少一个增长/效率/客户说法需要被降级。",
            "产品是否值得关注取决于核心机制能否实测成立。",
        ],
    },
    "user_voice": {
        "questions": [
            "用户原声来自哪些渠道？代表性边界是什么？",
            "高频痛点、强情绪点、少数但尖锐的需求分别是什么？",
            "哪些表达可能是平台偏差或幸存者偏差？",
            "用户语言如何转成产品需求，而不是直接照抄？",
            "哪些需求需要继续访谈或实验验证？",
        ],
        "hypotheses": [
            "高频观点不一定是最高价值洞察。",
            "强情绪和异常个案需要单独保留。",
            "用户原声必须标注来源偏差。",
        ],
    },
    "career_strategy": {
        "questions": [
            "目标岗位真正筛什么信号？",
            "用户背景如何转译成岗位语言？",
            "公司/JD 中哪些信息可验证，哪些只是包装？",
            "投递优先级如何分层？",
            "面试中最差异化的表达是什么？",
        ],
        "hypotheses": [
            "岗位匹配不是看标签重合，而是看能力证据能否转译。",
            "至少一个看似相关的机会会因信号弱或成本高被降级。",
            "最终建议必须输出可执行投递和面试动作。",
        ],
    },
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_plan_markdown(state: dict[str, Any], plan: dict[str, Any], v07: dict[str, Any] | None = None, goal: dict[str, Any] | None = None) -> str:
    questions = plan["questions"]
    hypotheses = plan["hypotheses"]
    rows = "\n".join(
        f"| Q{idx:02d} | {question} | {state.get('research_mode', '')} | candidate_pool / evidence_matrix / hypothesis_ledger | 待执行 |"
        for idx, question in enumerate(questions, start=1)
    )
    goal_id = goal.get("goal_id", "?") if goal else "?"
    hypothesis_rows = "\n".join(
        f"| H{idx:03d} | {hypothesis} | active | medium | {goal_id} | 待证据填充 |"
        for idx, hypothesis in enumerate(hypotheses, start=1)
    )

    v07_section = ""
    if v07:
        v07_section = _build_v07_plan_section(v07, goal)

    return f"""# v0.3/v0.7 研究执行计划

## 项目

- 项目名：{state.get('project_name', '')}
- research_type：{state.get('research_type', '')}
- research_mode：{state.get('research_mode', '')}
- view_type：{state.get('view_type', '')}
- 生成日期：{date.today().isoformat()}

## 子问题矩阵

| id | 子问题 | 研究模式 | 主要落点 | 状态 |
|---|---|---|---|---|
{rows}

## 初始假设

| id | 假设 | 状态 | 初始置信度 | goal_id | 下一步 |
|---|---|---|---|---|---|
{hypothesis_rows}

## 执行顺序

1. 先把输入材料和搜索结果写入 `02-sources/candidate_pool.json`。
2. 明确 accepted / discarded / conflict，并写具体淘汰理由。
3. 把可用证据写入 `03-evidence/evidence_matrix.md`。
4. 用证据更新 `03-evidence/hypothesis_ledger.json`。
5. Red team 必须至少导致一个假设降级、拒绝或修正。
6. 最终报告只写经过假设账本和证据矩阵支撑的结论。
7. HTML 通过 `07-output/view-model.json` 提供结构化入口。
{v07_section}"""


def _build_v07_plan_section(v07: dict[str, Any], goal: dict[str, Any] | None) -> str:
    lines = ["", "## v0.7 契约摘要", ""]
    if goal:
        lines.append(f"**当前目标** ({goal.get('goal_id', '?')}): {goal.get('statement', '')}")
        lines.append(f"  - 决策服务: {goal.get('decision_served', '')}")
        lines.append(f"  - scope: {', '.join(goal.get('scope', []) or [])}")
        lines.append("")

    rm = v07.get("reader_model", {})
    if rm:
        lines.append("### 读者模型")
        lines.append(f"- 背景: {rm.get('background', '')}")
        unknown = rm.get("unknown_concepts", [])
        if unknown:
            lines.append(f"- 陌生概念: {', '.join(unknown)}")
        lines.append(f"- 注意力预算: {rm.get('attention_budget', '?')} | 偏好: {rm.get('preferred_explanation_style', '?')}")
        lines.append("")

    tree = v07.get("intent_tree", [])
    if tree:
        lines.append("### 意图树 (5 层)")
        for it in tree:
            lines.append(f"- {it.get('intent_id', '?')}: {it.get('stated', '')} → {it.get('real_problem', '')} (置信: {it.get('confidence', '?')})")
        lines.append("")

    if v07.get("concept_ladder_needed"):
        seed = v07.get("concept_ladder_seed", [])
        lines.append(f"### 概念阶梯（{len(seed)} 个术语，首次出现前必须解释）")
        for term in seed:
            lines.append(f"- {term}")
        lines.append("")

    pp = v07.get("personalization_plan", {})
    if pp:
        lines.append("### 个性化 7 落点")
        for key, label in [
            ("case_selection", "案例"), ("analogy_strategy", "类比"),
            ("depth_control", "深度"), ("risk_filter", "风险"),
            ("career_story", "求职叙事"), ("product_insight", "产品"),
            ("track_judgment", "赛道"),
        ]:
            val = pp.get(key, "")
            if val:
                lines.append(f"- {label}: {val}")
        lines.append("")

    ls = v07.get("layout_spec", {})
    if ls:
        lines.append(f"### 布局: theme={ls.get('theme', '?')} | density={ls.get('visual_density', '?')}")
        blocks = ls.get("blocks", [])
        if blocks:
            lines.append(f"- blocks: {' → '.join(blocks)}")
        lines.append("")

    rc = v07.get("report_contract", {})
    if rc:
        req = rc.get("required_sections", [])
        if req:
            lines.append(f"### 报告必需章节: {', '.join(req)}")
        lines.append("")

    strat = v07.get("iteration_strategy", {})
    if strat:
        lines.append(f"### 迭代: breadth={strat.get('breadth', '?')}, depth={strat.get('depth', '?')}")
        lines.append("")

    return "\n".join(lines)


def seed_candidate_pool(project: Path, state: dict[str, Any]) -> None:
    path = project / "02-sources" / "candidate_pool.json"
    data = read_json(path)
    if data.get("items"):
        return
    write_json(path, {
        "schema_version": "research-os-candidate-pool-v0.5",
        "project_name": state.get("project_name", ""),
        "items": [
            {
                "id": "S001",
                "title": "用户输入 / 初始材料",
                "url_or_path": "",
                "source_type": "user_file",
                "claim": "待填写：用户提供的原始问题、文件或背景",
                "expected_use": "建立研究边界和初始事实",
                "evidence_grade": "A/D",
                "independence": "user_provided",
                "status": "candidate",
                "discard_reason": "",
            }
        ],
    })


def seed_hypothesis_ledger(project: Path, state: dict[str, Any], plan: dict[str, Any], goal_id: str = "?") -> None:
    path = project / "03-evidence" / "hypothesis_ledger.json"
    data = read_json(path)
    if data.get("hypotheses"):
        return
    hypotheses = []
    for idx, hypothesis in enumerate(plan["hypotheses"], start=1):
        hypotheses.append({
            "id": f"H{idx:03d}",
            "hypothesis": hypothesis,
            "status": "active",
            "confidence": "medium",
            "goal_id": goal_id,
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "revision_history": [],
        })
    write_json(path, {
        "schema_version": "research-os-hypothesis-ledger-v0.3",
        "project_name": state.get("project_name", ""),
        "hypotheses": hypotheses,
    })


def has_hypothesis_revision(hypotheses: list[dict[str, Any]]) -> bool:
    for item in hypotheses:
        if item.get("status") in {"downgraded", "rejected"}:
            return True
        if item.get("revision_history"):
            return True
    return False


def infer_next_required_action(project: Path, state: dict[str, Any]) -> str:
    # v0.7: if goal_ledger has pending adjustments, block here
    try:
        pending = goal_tracker.list_pending(project)
        if pending:
            return "review_goal_adjustment"
    except Exception:
        pass

    # v0.7: if clarifying_questions unanswered, block plan
    cq_path = project / "00-task" / "clarifying_questions.md"
    if cq_path.exists():
        text = cq_path.read_text(encoding="utf-8-sig")
        # Check if any question has empty answer
        if "## Q" in text and "**你的回答:**" in text:
            # Find sections and check if answers are empty
            import re
            sections = re.split(r"## Q\d+\.", text)
            for sec in sections[1:]:
                if "**你的回答:**" in sec:
                    after = sec.split("**你的回答:**", 1)[1].strip()
                    if not after:
                        return "answer_clarifying_questions"

    candidates = read_json(project / "02-sources" / "candidate_pool.json").get("items") or []
    hypotheses = read_json(project / "03-evidence" / "hypothesis_ledger.json").get("hypotheses") or []
    discarded_count = len([
        item for item in candidates
        if isinstance(item, dict) and item.get("status") == "discarded"
    ])
    hypothesis_count = len(hypotheses) if isinstance(hypotheses, list) else 0
    valid_hypotheses = [item for item in hypotheses if isinstance(item, dict)] if isinstance(hypotheses, list) else []

    if len(candidates) == 0 or discarded_count == 0:
        return "fill_candidate_pool"
    if hypothesis_count < 3 or not has_hypothesis_revision(valid_hypotheses):
        return "update_hypothesis_ledger"
    if not (project / "06-review" / "red_team.md").exists():
        return "run_red_team_review"
    if not (project / "07-output" / "final-report.md").exists():
        return "write_reader_first_report"
    trace_claims = read_json(project / "07-output" / "trace-manifest.json").get("claims") or []
    if state.get("depth") in ("R2", "R3") and len(trace_claims) == 0:
        return "write_trace_manifest"
    if state.get("depth") in ("R2", "R3") and not (project / "07-output" / "view-model.json").exists():
        return "write_view_model"
    if state.get("depth") in ("R2", "R3") and not (project / "08-html" / "index.html").exists():
        return "build_html"
    return "none"


def update_state(project: Path, state: dict[str, Any]) -> None:
    state["research_plan_source"] = "01-plan/research-execution-plan.md"
    if state.get("depth") in ("R2", "R3"):
        state.setdefault("trace_manifest_source", "07-output/trace-manifest.json")
        quality_gates = state.setdefault("quality_gates", {})
        quality_gates.setdefault("trace_manifest_required", True)
        quality_gates.setdefault("strong_claims_must_trace", True)
    state["next_required_action"] = infer_next_required_action(project, state)
    # Upgrade status: planned → in_progress once plan exists. HTML build's
    # _sync_state_after_build further upgrades to completed/failed.
    if state.get("status") == "planned" and (project / "01-plan" / "research-execution-plan.md").exists():
        state["status"] = "in_progress"
    state["last_updated"] = date.today().isoformat()
    outputs = state.setdefault("outputs", [])
    for item in ["01-plan/research-execution-plan.md", "02-sources/candidate_pool.json", "03-evidence/hypothesis_ledger.json", "07-output/trace-manifest.json"]:
        if item not in outputs:
            outputs.append(item)
    write_json(project / "research_state.json", state)


def read_intent_doc(project: Path) -> dict[str, Any] | None:
    """Read 00-task/intent_doc.json if present. Returns None if missing or
    invalid so the caller can fall back to MODE_PLANS."""
    path = project / "00-task" / "intent_doc.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def plan_project(project: Path) -> Path:
    project = project.resolve()
    state = read_json(project / "research_state.json")
    if not state:
        raise FileNotFoundError(f"missing or invalid {project / 'research_state.json'}")
    mode = state.get("research_mode") or "evidence_intelligence"

    # v0.7: read goal_ledger (prefers current_goal if exists)
    ledger = goal_tracker.load_goal_ledger(project)
    goal = ledger.get("current_goal") if ledger else None

    # Prefer intent_doc (from intent_discovery) over hardcoded MODE_PLANS.
    # Falls back to MODE_PLANS for projects created before intent_discovery
    # existed, or when intent_discovery fails / is skipped.
    intent_doc = read_intent_doc(project)
    v07 = intent_doc.get("v07") if intent_doc else None
    if intent_doc and (
        intent_doc.get("suggested_sub_questions")
        or intent_doc.get("suggested_hypotheses")
    ):
        fallback = MODE_PLANS.get(mode, MODE_PLANS["evidence_intelligence"])
        plan = {
            "questions": intent_doc.get("suggested_sub_questions")
            or fallback["questions"],
            "hypotheses": intent_doc.get("suggested_hypotheses")
            or fallback["hypotheses"],
        }
        state["plan_source"] = "00-task/intent_doc.json"
    else:
        plan = MODE_PLANS.get(mode, MODE_PLANS["evidence_intelligence"])
        state["plan_source"] = "MODE_PLANS (hardcoded fallback)"

    out = project / "01-plan" / "research-execution-plan.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_plan_markdown(state, plan, v07, goal), encoding="utf-8")
    seed_candidate_pool(project, state)
    goal_id = goal.get("goal_id", "G001") if goal else "G001"
    seed_hypothesis_ledger(project, state, plan, goal_id=goal_id)
    update_state(project, state)
    return out


def replan_project(project: Path, accepted_adjustment_id: str) -> Path:
    """v0.7: regenerate execution plan after a goal adjustment was accepted.
    Appends new hypotheses bound to new goal_id; does not overwrite existing
    hypothesis_ledger (preserves revision history)."""
    project = project.resolve()
    state = read_json(project / "research_state.json")
    if not state:
        raise FileNotFoundError(f"missing research_state.json")

    ledger = goal_tracker.load_goal_ledger(project)
    if not ledger:
        raise RuntimeError("goal_ledger.json not initialized")
    new_goal = ledger["current_goal"]
    new_goal_id = new_goal["goal_id"]

    # Read existing hypotheses — keep them, add new ones bound to new goal
    hyp_path = project / "03-evidence" / "hypothesis_ledger.json"
    hyp_data = read_json(hyp_path)
    existing = hyp_data.get("hypotheses", []) if hyp_data else []

    # Generate new hypotheses from intent_doc (or MODE_PLANS fallback)
    intent_doc = read_intent_doc(project)
    fallback = MODE_PLANS.get(state.get("research_mode", ""), MODE_PLANS["evidence_intelligence"])
    new_hyp_texts = (intent_doc or {}).get("suggested_hypotheses") or fallback["hypotheses"]

    # Only add hypotheses that don't already exist (by text match)
    existing_texts = {h.get("hypothesis", "") for h in existing}
    next_idx = len(existing) + 1
    for hyp_text in new_hyp_texts:
        if hyp_text not in existing_texts:
            existing.append({
                "id": f"H{next_idx:03d}",
                "hypothesis": hyp_text,
                "status": "active",
                "confidence": "medium",
                "goal_id": new_goal_id,
                "supporting_evidence": [],
                "contradicting_evidence": [],
                "revision_history": [{"round": "replan", "note": f"added after {accepted_adjustment_id}", "at": date.today().isoformat()}],
            })
            next_idx += 1

    write_json(hyp_path, {
        "schema_version": "research-os-hypothesis-ledger-v0.3",
        "project_name": state.get("project_name", ""),
        "hypotheses": existing,
    })

    # Regenerate execution plan
    return plan_project(project)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Research OS v0.3 execution plan")
    parser.add_argument("project", help="Path to research project directory")
    args = parser.parse_args()
    out = plan_project(Path(args.project).resolve())
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
