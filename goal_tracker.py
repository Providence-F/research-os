#!/usr/bin/env python3
"""Research OS v0.7 goal ledger — living contract for research goals.

Borrowed pattern: assafelovic/gpt-researcher `multi_agents/agents/plan_review.py`
`route_human_feedback()` with MAX_REVISIONS counter. Adjustments are proposed
by evidence/red-team, must be explicitly accepted/rejected, and block the
pipeline until resolved.

Borrowed pattern: dzhng/deep-research iterative `learnings + next_directions`
evolution — goals evolve across rounds, not frozen at intent_discovery time.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

MAX_GOAL_REVISIONS = 3
SCHEMA_VERSION = "research-os-goal-ledger-v0.5"


def _ledger_path(project: Path) -> Path:
    return project / "00-task" / "goal_ledger.json"


def load_goal_ledger(project: Path) -> dict[str, Any] | None:
    path = _ledger_path(project)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid {path}: {exc}") from exc


def initialize_from_intent_doc(project: Path, intent_doc: dict[str, Any]) -> Path:
    """Bootstrap goal_ledger.json from intent_discovery output. Idempotent:
    does not overwrite if ledger already exists with current_goal.
    """
    path = _ledger_path(project)
    existing = load_goal_ledger(project)
    if existing and existing.get("current_goal"):
        return path

    stated = intent_doc.get("stated_intent", "")
    hidden = intent_doc.get("hidden_intents", [])
    primary_hidden = hidden[0].get("intent", "") if hidden else ""
    sub_qs = intent_doc.get("suggested_sub_questions", [])
    non_goals_raw = intent_doc.get("non_goals", [])  # optional

    statement = primary_hidden or stated or "(未命名目标)"
    decision_served = stated or "(待补)"
    scope = sub_qs[:5] if sub_qs else []
    non_goals = non_goals_raw if non_goals_raw else []

    ledger = {
        "schema_version": SCHEMA_VERSION,
        "project_name": project.name,
        "current_goal": {
            "goal_id": "G001",
            "statement": statement,
            "decision_served": decision_served,
            "scope": scope,
            "non_goals": non_goals,
            "confidence": "medium",
            "source": "intent_discovery",
            "created_at": date.today().isoformat(),
        },
        "goal_history": [],
        "pending_adjustments": [],
        "revision_count": 0,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def evaluate_goal_drift(project: Path) -> dict[str, Any]:
    """Scan hypothesis_ledger / red_team / evidence_matrix for drift signals.
    Returns dict with proposed adjustments (does not auto-accept them).
    """
    ledger = load_goal_ledger(project)
    if not ledger:
        return {"drift_score": 0, "proposals": [], "reason": "no goal_ledger"}

    proposals: list[dict[str, Any]] = []
    drift_score = 0

    # Signal 1: red_team meta/framing attack without adjustment record
    red_team_path = project / "06-review" / "red_team.md"
    if red_team_path.exists():
        red_text = red_team_path.read_text(encoding="utf-8-sig").lower()
        meta_keywords = ["自我合理化", "框架攻击", "问题框架", "meta", "framing", "用 research os 自我合理化"]
        has_meta = any(kw in red_text for kw in meta_keywords)
        already_addressed = any(
            adj.get("trigger_signals")
            and any("red_team:meta" in (s or "") for s in adj["trigger_signals"])
            for adj in ledger.get("pending_adjustments", [])
        )
        already_in_history = any(
            "red_team:meta" in (str(hist.get("trigger_evidence")) + str(hist.get("reason"))).lower()
            for hist in ledger.get("goal_history", [])
        )
        if has_meta and not already_addressed and not already_in_history:
            drift_score += 2
            proposals.append({
                "adjustment_id": f"A{len(ledger['pending_adjustments']) + 1:03d}",
                "type": "narrow",
                "proposed_goal": "限定研究范围到核心决策点；拒绝为研究本身找理由",
                "rationale": "red_team 含 framing 攻击，提示目标可能过宽或为自我合理化",
                "trigger_signals": ["red_team:meta"],
                "status": "proposed",
                "requires_user": True,
                "created_at": date.today().isoformat(),
            })

    # Signal 2: many hypothesis revisions suggests goal is unstable
    hyp_path = project / "03-evidence" / "hypothesis_ledger.json"
    if hyp_path.exists():
        try:
            hyp_data = json.loads(hyp_path.read_text(encoding="utf-8-sig"))
            hyps = hyp_data.get("hypotheses", [])
            revised = [h for h in hyps if h.get("revision_history")]
            if len(revised) >= 3:
                drift_score += 1
                proposals.append({
                    "adjustment_id": f"A{len(ledger['pending_adjustments']) + len(proposals) + 1:03d}",
                    "type": "pivot",
                    "proposed_goal": "假设多次修订，原目标可能错配，建议重新审视",
                    "rationale": f"{len(revised)} 个假设有 revision_history",
                    "trigger_signals": [f"hypothesis_revised:{h.get('id', '?')}" for h in revised[:3]],
                    "status": "proposed",
                    "requires_user": True,
                    "created_at": date.today().isoformat(),
                })
        except json.JSONDecodeError:
            pass

    # Signal 3: evidence_matrix scope mismatch — too few sources vs goal breadth
    evi_path = project / "03-evidence" / "evidence_matrix.md"
    if evi_path.exists():
        evi_text = evi_path.read_text(encoding="utf-8-sig")
        evi_count = evi_text.count("| E")
        scope_breadth = len(ledger["current_goal"].get("scope", []))
        if scope_breadth >= 4 and evi_count < scope_breadth * 2:
            drift_score += 1
            proposals.append({
                "adjustment_id": f"A{len(ledger['pending_adjustments']) + len(proposals) + 1:03d}",
                "type": "broaden",
                "proposed_goal": "扩大证据搜集范围，当前证据不足以支撑目标广度",
                "rationale": f"scope 有 {scope_breadth} 项但 evidence 仅 {evi_count} 条",
                "trigger_signals": [f"evidence_count:{evi_count}", f"scope_breadth:{scope_breadth}"],
                "status": "proposed",
                "requires_user": False,
                "created_at": date.today().isoformat(),
            })

    return {
        "drift_score": drift_score,
        "proposals": proposals,
        "current_goal_id": ledger["current_goal"]["goal_id"],
    }


def propose_adjustment(
    project: Path,
    adjustment_type: str,
    rationale: str,
    trigger_signals: list[str] | None = None,
    proposed_goal: str = "",
    requires_user: bool = True,
) -> str:
    """Manually propose a goal adjustment. Returns adjustment_id."""
    ledger = load_goal_ledger(project)
    if not ledger:
        raise RuntimeError("goal_ledger.json not initialized; run ros discover first")

    if ledger.get("revision_count", 0) >= MAX_GOAL_REVISIONS:
        raise RuntimeError(
            f"MAX_GOAL_REVISIONS ({MAX_GOAL_REVISIONS}) exceeded. "
            f"Cannot propose more adjustments to {project.name}."
        )

    adj_id = f"A{len(ledger['pending_adjustments']) + 1:03d}"
    adjustment = {
        "adjustment_id": adj_id,
        "type": adjustment_type,
        "proposed_goal": proposed_goal,
        "rationale": rationale,
        "trigger_signals": trigger_signals or [],
        "status": "proposed",
        "requires_user": requires_user,
        "created_at": date.today().isoformat(),
    }
    ledger["pending_adjustments"].append(adjustment)
    _save(project, ledger)
    return adj_id


def accept_adjustment(project: Path, adjustment_id: str) -> dict[str, Any]:
    """Accept a proposed adjustment: supersede current_goal, write goal_history."""
    ledger = load_goal_ledger(project)
    if not ledger:
        raise RuntimeError("goal_ledger.json not initialized")

    adj = next(
        (a for a in ledger["pending_adjustments"] if a["adjustment_id"] == adjustment_id),
        None,
    )
    if not adj:
        raise ValueError(f"adjustment {adjustment_id} not found in pending")
    if adj["status"] != "proposed":
        raise ValueError(f"adjustment {adjustment_id} already {adj['status']}")

    old_goal = ledger["current_goal"]
    new_goal_id = f"G{int(old_goal['goal_id'][1:]) + 1:03d}"
    new_goal = {
        "goal_id": new_goal_id,
        "statement": adj.get("proposed_goal") or old_goal["statement"],
        "decision_served": old_goal.get("decision_served", ""),
        "scope": old_goal.get("scope", []),
        "non_goals": old_goal.get("non_goals", []),
        "confidence": "medium",
        "source": f"adjustment:{adj['type']}",
        "created_at": date.today().isoformat(),
        "supersedes": old_goal["goal_id"],
        "trigger_adjustment": adjustment_id,
    }
    history_entry = {
        "goal_id": old_goal["goal_id"],
        "superseded_by": new_goal_id,
        "reason": adj["rationale"],
        "trigger_evidence": adj["trigger_signals"],
        "trigger_adjustment": adjustment_id,
        "at": date.today().isoformat(),
    }
    ledger["goal_history"].append(history_entry)
    ledger["current_goal"] = new_goal
    adj["status"] = "accepted"
    ledger["revision_count"] = ledger.get("revision_count", 0) + 1
    _save(project, ledger)
    return {"new_goal_id": new_goal_id, "superseded": old_goal["goal_id"]}


def reject_adjustment(project: Path, adjustment_id: str, reason: str = "") -> None:
    """Reject a proposed adjustment; record reason for audit."""
    ledger = load_goal_ledger(project)
    if not ledger:
        raise RuntimeError("goal_ledger.json not initialized")
    adj = next(
        (a for a in ledger["pending_adjustments"] if a["adjustment_id"] == adjustment_id),
        None,
    )
    if not adj:
        raise ValueError(f"adjustment {adjustment_id} not found")
    adj["status"] = "rejected"
    adj["rejection_reason"] = reason
    _save(project, ledger)


def list_pending(project: Path) -> list[dict[str, Any]]:
    ledger = load_goal_ledger(project)
    if not ledger:
        return []
    return [a for a in ledger.get("pending_adjustments", []) if a["status"] == "proposed"]


def render_goal_status(project: Path) -> str:
    """Human-readable status for `ros goal status` CLI."""
    ledger = load_goal_ledger(project)
    if not ledger:
        return f"[goal_ledger] {project.name}: 未初始化（跑 ros discover 自动创建）"

    cg = ledger["current_goal"]
    lines = [
        f"# {project.name} — 目标账本",
        "",
        f"**当前目标**: {cg['goal_id']} — {cg['statement']}",
        f"  - 决策服务: {cg.get('decision_served', '?')}",
        f"  - 置信度: {cg.get('confidence', '?')}",
        f"  - 来源: {cg.get('source', '?')}",
        f"  - scope: {', '.join(cg.get('scope', []) or [])}",
        f"  - non_goals: {', '.join(cg.get('non_goals', []) or [])}",
        f"  - 修订次数: {ledger.get('revision_count', 0)} / {MAX_GOAL_REVISIONS}",
        "",
    ]

    history = ledger.get("goal_history", [])
    if history:
        lines.append("## 目标演化历史")
        for h in history:
            lines.append(f"- {h['goal_id']} → {h['superseded_by']}: {h['reason']}")
            if h.get("trigger_evidence"):
                lines.append(f"  - 触发证据: {', '.join(h['trigger_evidence'])}")
        lines.append("")

    pending = [a for a in ledger.get("pending_adjustments", []) if a["status"] == "proposed"]
    if pending:
        lines.append(f"## 待决调整 ({len(pending)})")
        for a in pending:
            lines.append(f"- **{a['adjustment_id']}** [{a['type']}]: {a.get('proposed_goal', '')}")
            lines.append(f"  - 理由: {a['rationale']}")
            if a["trigger_signals"]:
                lines.append(f"  - 触发信号: {', '.join(a['trigger_signals'])}")
            lines.append(f"  - 状态: {a['status']} | 需用户确认: {a.get('requires_user', True)}")
        lines.append("")
        lines.append("_跑 `ros goal accept <id>` 接受 / `ros goal reject <id> --reason ...` 拒绝_")
    else:
        lines.append("_无待决调整_")

    return "\n".join(lines)


def _save(project: Path, ledger: dict[str, Any]) -> None:
    path = _ledger_path(project)
    path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Research OS v0.7 goal ledger")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_status = sub.add_parser("status", help="Show current goal + pending adjustments")
    p_status.add_argument("project", help="Path to research project")

    p_eval = sub.add_parser("evaluate", help="Scan for goal drift signals")
    p_eval.add_argument("project", help="Path to research project")

    p_prop = sub.add_parser("propose", help="Manually propose a goal adjustment")
    p_prop.add_argument("project", help="Path to research project")
    p_prop.add_argument("--type", required=True, choices=["narrow", "broaden", "pivot", "split_subresearch", "downgrade_depth"])
    p_prop.add_argument("--rationale", required=True)
    p_prop.add_argument("--goal", default="")
    p_prop.add_argument("--signals", nargs="*", default=[])

    p_acc = sub.add_parser("accept", help="Accept a proposed adjustment")
    p_acc.add_argument("project", help="Path to research project")
    p_acc.add_argument("adjustment_id")

    p_rej = sub.add_parser("reject", help="Reject a proposed adjustment")
    p_rej.add_argument("project", help="Path to research project")
    p_rej.add_argument("adjustment_id")
    p_rej.add_argument("--reason", default="")

    args = parser.parse_args()
    project = Path(args.project).resolve()
    if not project.exists():
        print(f"[error] project not found: {project}", file=sys.stderr)
        return 1

    try:
        if args.cmd == "status":
            print(render_goal_status(project))
        elif args.cmd == "evaluate":
            result = evaluate_goal_drift(project)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            if result["proposals"]:
                for p in result["proposals"]:
                    ledger = load_goal_ledger(project)
                    if ledger:
                        ledger["pending_adjustments"].append(p)
                        _save(project, ledger)
                print(f"[ok] {len(result['proposals'])} 个调整已入队，跑 `ros goal status` 查看", file=sys.stderr)
        elif args.cmd == "propose":
            adj_id = propose_adjustment(
                project, args.type, args.rationale, args.signals, args.goal
            )
            print(f"[ok] proposed {adj_id}")
        elif args.cmd == "accept":
            r = accept_adjustment(project, args.adjustment_id)
            print(f"[ok] {r['superseded']} → {r['new_goal_id']}")
        elif args.cmd == "reject":
            reject_adjustment(project, args.adjustment_id, args.reason)
            print(f"[ok] rejected {args.adjustment_id}")
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
