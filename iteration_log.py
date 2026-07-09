#!/usr/bin/env python3
"""Research OS v1.0 iteration log — depth × breadth iterative research loopBorrowed pattern: dzhng/deep-research `deepResearch({query, breadth, depth,
learnings, visitedUrls})` recursive loop. Each round outputs `learnings[]` +
`next_directions[]` which feed back into the next round's planner context.

Unlike dzhng's auto-recursive TS impl, we keep rounds explicit and human-
gated: each round appends to iteration_log.json; the user/LLM decides
whether to iterate again based on `should_iterate()`.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "research-os-iteration-log-v0.1"
DEFAULT_MAX_DEPTH = 2
DEFAULT_BREADTH = 4


def _log_path(project: Path) -> Path:
    return project / "00-task" / "iteration_log.json"


def load_log(project: Path) -> dict[str, Any] | None:
    path = _log_path(project)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid {path}: {exc}") from exc


def init_log(project: Path, breadth: int = DEFAULT_BREADTH, depth: int = DEFAULT_MAX_DEPTH) -> Path:
    """Initialize iteration_log.json. Idempotent."""
    path = _log_path(project)
    if path.exists():
        return path
    log = {
        "schema_version": SCHEMA_VERSION,
        "project_name": project.name,
        "config": {"max_depth": depth, "default_breadth": breadth},
        "rounds": [],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def append_round(
    project: Path,
    learnings: list[str],
    next_directions: list[str],
    evidence_ids: list[str] | None = None,
    hypothesis_revisions: list[str] | None = None,
    queries: list[str] | None = None,
    goal_drift_detected: bool = False,
) -> int:
    """Append a round to iteration_log. Returns new round_id."""
    log = load_log(project)
    if not log:
        init_log(project)
        log = load_log(project)

    round_id = len(log["rounds"]) + 1
    entry = {
        "round_id": round_id,
        "breadth": log["config"].get("default_breadth", DEFAULT_BREADTH),
        "depth_remaining": max(0, log["config"].get("max_depth", DEFAULT_MAX_DEPTH) - round_id + 1),
        "queries": queries or [],
        "learnings": learnings,
        "next_directions": next_directions,
        "evidence_ids": evidence_ids or [],
        "hypothesis_revisions": hypothesis_revisions or [],
        "goal_drift_detected": goal_drift_detected,
        "at": date.today().isoformat(),
    }
    log["rounds"].append(entry)
    _save(project, log)
    return round_id


def should_iterate(project: Path) -> dict[str, Any]:
    """Decide if another round is warranted."""
    log = load_log(project)
    if not log:
        return {"should_iterate": False, "reason": "no iteration_log"}

    rounds = log.get("rounds", [])
    max_depth = log["config"].get("max_depth", DEFAULT_MAX_DEPTH)
    if len(rounds) >= max_depth:
        return {"should_iterate": False, "reason": f"reached max_depth={max_depth}"}

    if not rounds:
        return {"should_iterate": True, "reason": "no rounds yet"}

    last = rounds[-1]
    if last.get("goal_drift_detected"):
        return {"should_iterate": False, "reason": "goal drift detected; resolve goal adjustment first"}

    if not last.get("learnings"):
        return {"should_iterate": False, "reason": "last round produced no learnings"}

    if not last.get("next_directions"):
        return {"should_iterate": False, "reason": "no next_directions queued"}

    return {
        "should_iterate": True,
        "reason": f"round {len(rounds)} done, depth remaining {max_depth - len(rounds)}",
        "next_round_id": len(rounds) + 1,
        "carry_over_directions": last["next_directions"],
        "carry_over_learnings": last["learnings"],
    }


def render_log_summary(project: Path) -> str:
    log = load_log(project)
    if not log:
        return f"[iteration_log] {project.name}: 未初始化"

    rounds = log.get("rounds", [])
    if not rounds:
        return f"[iteration_log] {project.name}: 已初始化但无 round 记录"

    lines = [f"# {project.name} — 迭代日志", ""]
    lines.append(f"_max_depth={log['config'].get('max_depth')} / breadth={log['config'].get('default_breadth')}_")
    lines.append("")
    for r in rounds:
        lines.append(f"## Round {r['round_id']} ({r.get('at', '?')})")
        lines.append(f"_depth remaining: {r.get('depth_remaining', '?')} | drift: {r.get('goal_drift_detected', False)}_")
        if r.get("queries"):
            lines.append("**本轮查询:**")
            for q in r["queries"]:
                lines.append(f"- {q}")
        if r.get("learnings"):
            lines.append("**Learnings:**")
            for l in r["learnings"]:
                lines.append(f"- {l}")
        if r.get("next_directions"):
            lines.append("**下一轮方向:**")
            for d in r["next_directions"]:
                lines.append(f"- {d}")
        if r.get("hypothesis_revisions"):
            lines.append(f"**假设修订:** {', '.join(r['hypothesis_revisions'])}")
        if r.get("evidence_ids"):
            lines.append(f"**新增证据:** {', '.join(r['evidence_ids'])}")
        lines.append("")

    s = should_iterate(project)
    if s["should_iterate"]:
        lines.append(f"→ 可继续 round {s['next_round_id']}（{s['reason']}）")
    else:
        lines.append(f"→ 终止迭代（{s['reason']}）")

    return "\n".join(lines)


def _save(project: Path, log: dict[str, Any]) -> None:
    path = _log_path(project)
    path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Research OS v0.7 iteration log")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize iteration_log.json")
    p_init.add_argument("project")
    p_init.add_argument("--breadth", type=int, default=DEFAULT_BREADTH)
    p_init.add_argument("--depth", type=int, default=DEFAULT_MAX_DEPTH)

    p_app = sub.add_parser("append", help="Append a round")
    p_app.add_argument("project")
    p_app.add_argument("--learnings", nargs="*", required=True)
    p_app.add_argument("--directions", nargs="*", default=[])
    p_app.add_argument("--evidence", nargs="*", default=[])
    p_app.add_argument("--hypothesis-revisions", nargs="*", default=[])
    p_app.add_argument("--queries", nargs="*", default=[])
    p_app.add_argument("--drift", action="store_true")

    p_sh = sub.add_parser("should-iterate", help="Check if another round is needed")
    p_sh.add_argument("project")

    p_sum = sub.add_parser("summary", help="Render readable summary")
    p_sum.add_argument("project")

    args = parser.parse_args()
    project = Path(args.project).resolve()
    if not project.exists():
        print(f"[error] project not found: {project}", file=sys.stderr)
        return 1

    try:
        if args.cmd == "init":
            init_log(project, args.breadth, args.depth)
            print(f"[ok] iteration_log initialized at {_log_path(project)}")
        elif args.cmd == "append":
            rid = append_round(
                project,
                args.learnings,
                args.directions,
                args.evidence,
                args.hypothesis_revisions,
                args.queries,
                args.drift,
            )
            print(f"[ok] appended round {rid}")
        elif args.cmd == "should-iterate":
            r = should_iterate(project)
            print(json.dumps(r, ensure_ascii=False, indent=2))
        elif args.cmd == "summary":
            print(render_log_summary(project))
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
