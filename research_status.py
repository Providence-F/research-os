#!/usr/bin/env python3
"""Research OS v0.3 status inspector.

Read project state and protocol files, then emit a concise machine-readable
status with the next required action.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

VALIDATOR = Path(__file__).with_name("validate_research_project.py")

STEP_ORDER = [
    ("route", "research_state.json"),
    ("plan", "01-plan/research-execution-plan.md"),
    ("collect", "02-sources/candidate_pool.json"),
    ("evidence", "03-evidence/evidence_matrix.md"),
    ("hypothesize", "03-evidence/hypothesis_ledger.json"),
    ("red_team", "06-review/red_team.md"),
    ("report", "07-output/final-report.md"),
    ("trace", "07-output/trace-manifest.json"),
    ("view_model", "07-output/view-model.json"),
    ("html", "08-html/index.html"),
]

NEXT_ACTION_BY_STEP = {
    "route": "create_or_fix_research_state",
    "plan": "run_research_planner",
    "collect": "fill_candidate_pool",
    "evidence": "fill_evidence_matrix",
    "hypothesize": "update_hypothesis_ledger",
    "red_team": "run_red_team_review",
    "report": "write_reader_first_report",
    "trace": "write_trace_manifest",
    "view_model": "write_view_model",
    "html": "build_html",
    "validate": "fix_validator_failures",
    "done": "none",
}


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
    return {
        "candidate_count": len(candidates) if isinstance(candidates, list) else 0,
        "discarded_candidate_count": len([i for i in candidates if isinstance(i, dict) and i.get("status") == "discarded"]),
        "hypothesis_count": len(hypotheses) if isinstance(hypotheses, list) else 0,
        "revised_hypothesis_count": len([
            h for h in hypotheses
            if isinstance(h, dict) and (h.get("status") in {"downgraded", "rejected"} or h.get("revision_history"))
        ]),
        "trace_claim_count": len(claims) if isinstance(claims, list) else 0,
        "view_model_has_cards": bool(view_model.get("summary_cards") or view_model.get("object_cards") or view_model.get("advisor_cards")),
    }


def inspect_project(project: Path) -> dict[str, Any]:
    project = project.resolve()
    state = read_json(project / "research_state.json")
    missing_steps = [step for step, rel in STEP_ORDER if not (project / rel).exists()]
    content = content_state(project)
    validator = run_validator(project)

    if "route" in missing_steps:
        next_step = "route"
    elif "plan" in missing_steps:
        next_step = "plan"
    elif content["candidate_count"] == 0 or content["discarded_candidate_count"] == 0:
        next_step = "collect"
    elif content["hypothesis_count"] < 3 or content["revised_hypothesis_count"] == 0:
        next_step = "hypothesize"
    elif "report" not in missing_steps and ("trace" in missing_steps or content["trace_claim_count"] == 0):
        next_step = "trace"
    elif validator.get("fails"):
        next_step = "validate"
    elif missing_steps:
        next_step = missing_steps[0]
    else:
        next_step = "done"

    return {
        "project": str(project),
        "project_name": state.get("project_name", project.name),
        "research_mode": state.get("research_mode", ""),
        "view_type": state.get("view_type", ""),
        "status": state.get("status", ""),
        "missing_steps": missing_steps,
        "content": content,
        "validation": validator,
        "next_required_action": NEXT_ACTION_BY_STEP[next_step],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Research OS project status")
    parser.add_argument("project", help="Path to research project directory")
    args = parser.parse_args()
    result = inspect_project(Path(args.project).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["validation"].get("fails") else 0


if __name__ == "__main__":
    raise SystemExit(main())
