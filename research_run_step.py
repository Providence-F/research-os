#!/usr/bin/env python3
"""Research OS v0.4 safe step runner.

Runs only low-risk mechanical steps. Judgment-heavy research steps are surfaced as
instructions so the system does not fabricate research work for the sake of automation.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from research_status import inspect_project

ROOT = Path(__file__).resolve().parent
PLANNER = ROOT / "research_planner.py"
BUILDER = ROOT / "build_research_html.py"

MANUAL_ACTIONS = {
    "fill_candidate_pool": "Fill 02-sources/candidate_pool.json with recalled sources/objects, then explicitly discard weak or irrelevant candidates with discard_reason.",
    "fill_evidence_matrix": "Fill 03-evidence/evidence_matrix.md with usable evidence, source independence, evidence grade, and limits.",
    "update_hypothesis_ledger": "Update 03-evidence/hypothesis_ledger.json so at least one hypothesis is revised, downgraded, or rejected based on evidence/red-team pressure.",
    "run_red_team_review": "Write 06-review/red_team.md and force at least one conclusion to be challenged, downgraded, or explicitly defended.",
    "write_reader_first_report": "Write 07-output/final-report.md as a reader-first report supported by evidence_matrix and hypothesis_ledger.",
    "write_trace_manifest": "Write 07-output/trace-manifest.json so strong final-report claims link to hypothesis_ids and evidence_ids or limitations.",
    "write_view_model": "Fill 07-output/view-model.json with hero, cards, tabs, matrices, and other visual modules needed by the HTML builder.",
    "fix_validator_failures": "Run validate_research_project.py, inspect FAIL items, and fix the underlying project files rather than bypassing validation.",
    "create_or_fix_research_state": "Create or fix research_state.json before continuing.",
}


def run_python(script: Path, project: Path, *args: str) -> int:
    proc = subprocess.run(
        [sys.executable, str(script), str(project), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode


def run_step(project: Path, copy_desktop: bool = False) -> int:
    project = project.resolve()
    status = inspect_project(project)
    action = status.get("next_required_action", "")
    print(f"project: {status.get('project')}")
    print(f"next_required_action: {action}")

    if action == "none":
        print("No action required.")
        return 0
    if action == "run_research_planner":
        return run_python(PLANNER, project)
    if action == "build_html":
        args = ("--copy-desktop",) if copy_desktop else ()
        return run_python(BUILDER, project, *args)
    if action in MANUAL_ACTIONS:
        print(MANUAL_ACTIONS[action])
        return 2

    print(f"Unknown action: {action}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the next safe Research OS step")
    parser.add_argument("project", help="Path to research project directory")
    parser.add_argument("--copy-desktop", action="store_true", help="Copy built HTML to desktop when action is build_html")
    args = parser.parse_args()
    return run_step(Path(args.project).resolve(), copy_desktop=args.copy_desktop)


if __name__ == "__main__":
    raise SystemExit(main())
