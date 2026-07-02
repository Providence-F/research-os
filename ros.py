#!/usr/bin/env python3
"""Research OS unified CLI.

Single entry point that dispatches to the underlying workflow scripts.

Usage:
    ros new --name "..." --type product --depth R2 --html
    ros plan <project>
    ros status <project>
    ros run <project>
    ros validate <project>
    ros build --project <project>
    ros config
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import config
from create_research_project import create_project, DEPTH_CHOICES, TYPE_CHOICES
from research_planner import plan_project
from research_status import inspect_project
from research_run_step import run_step
from validate_research_project import validate_project, print_checks
from build_research_html import build
from intent_discovery import discover as discover_intent


def cmd_new(args: argparse.Namespace) -> int:
    return create_project(
        name=args.name,
        rtype=args.type,
        depth=args.depth,
        html=args.html,
        target_dir=args.target_dir,
    )


def cmd_plan(args: argparse.Namespace) -> int:
    out = plan_project(Path(args.project))
    print(f"Wrote {out}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    result = inspect_project(Path(args.project))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get("validation", {}).get("fails") else 0


def cmd_run(args: argparse.Namespace) -> int:
    return run_step(Path(args.project), copy_desktop=args.copy_desktop)


def cmd_validate(args: argparse.Namespace) -> int:
    project = Path(args.project)
    if not project.exists():
        print(f"[FAIL] project path does not exist: {project}", file=sys.stderr)
        return 1
    return print_checks(validate_project(project))


def cmd_build(args: argparse.Namespace) -> int:
    out = build(Path(args.project), args.copy_desktop)
    print(f"Wrote {out}")
    return 0


def cmd_config(args: argparse.Namespace) -> int:
    for key, value in config.as_dict().items():
        print(f"{key}: {value}")
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    project = Path(args.project)
    if not project.exists():
        print(f"[FAIL] project path does not exist: {project}", file=sys.stderr)
        return 1
    try:
        result = discover_intent(project)
    except Exception as exc:
        print(f"[FAIL] intent discovery failed: {exc}", file=sys.stderr)
        return 1
    print(f"[ok] intent_doc written to {project / '00-task' / 'intent_doc.md'}")
    print(f"[ok] open_questions written to {project / '00-task' / 'open_questions.md'}")
    print(f"[ok] stated_intent: {result.get('stated_intent', '')[:80]}")
    hidden = result.get("hidden_intents", [])
    print(f"[ok] hidden_intents: {len(hidden)}")
    seeds = result.get("surfaced_seeds", [])
    print(f"[ok] surfaced_seeds: {len(seeds)}")
    return 0


def cmd_reflect(args: argparse.Namespace) -> int:
    # Lazy import - intent_tracker depends on llm_client which is only
    # needed when actually running reflect, not at ros startup.
    from intent_tracker import reflect as reflect_intent
    project = Path(args.project)
    if not project.exists():
        print(f"[FAIL] project path does not exist: {project}", file=sys.stderr)
        return 1
    try:
        result = reflect_intent(project)
    except Exception as exc:
        print(f"[FAIL] intent reflection failed: {exc}", file=sys.stderr)
        return 1
    print(f"[ok] intent revision written to {result.get('revision_path', '?')}")
    print(f"[ok] revised_intent: {result.get('revised_intent', '')[:80]}")
    return 0


def cmd_discover_identity(args: argparse.Namespace) -> int:
    """Run identity extraction (dual-source: CLAUDE.md memory + Obsidian vault).
    Writes ~/.research-os/identity.draft.json. User must run `ros accept-identity`
    to promote draft to identity.json."""
    from identity_extractor import extract_identity, render_identity_summary
    try:
        result = extract_identity()
    except Exception as exc:
        print(f"[FAIL] identity extraction failed: {exc}", file=sys.stderr)
        return 1
    print(render_identity_summary(result))
    return 0


def cmd_accept_identity(args: argparse.Namespace) -> int:
    """Promote identity.draft.json to identity.json after user review."""
    from identity_extractor import accept_identity
    if accept_identity():
        print("[ok] identity.json written. Future ros new will surface this.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ros",
        description="Research OS - depth research workflow toolkit",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="Create a new research project")
    p_new.add_argument("--name", required=True, help="项目名")
    p_new.add_argument("--type", required=True, choices=TYPE_CHOICES, help="调研类型")
    p_new.add_argument("--depth", required=True, choices=DEPTH_CHOICES, help="深度档位")
    p_new.add_argument("--html", action="store_true", help="生成 HTML 模板位（R2+ 默认 True）")
    p_new.add_argument("--target-dir", default=None, help=f"项目根目录（默认 {config.PROJECTS_DIR}）")
    p_new.set_defaults(func=cmd_new)

    p_plan = sub.add_parser("plan", help="Generate execution plan for a project")
    p_plan.add_argument("project", help="Path to research project directory")
    p_plan.set_defaults(func=cmd_plan)

    p_status = sub.add_parser("status", help="Show project status and next required action")
    p_status.add_argument("project", help="Path to research project directory")
    p_status.set_defaults(func=cmd_status)

    p_run = sub.add_parser("run", help="Run the next safe mechanical step")
    p_run.add_argument("project", help="Path to research project directory")
    p_run.add_argument("--copy-desktop", action="store_true", help="Copy built HTML to Desktop when action is build_html")
    p_run.set_defaults(func=cmd_run)

    p_validate = sub.add_parser("validate", help="Validate project against quality gates")
    p_validate.add_argument("project", help="Path to research project directory")
    p_validate.set_defaults(func=cmd_validate)

    p_build = sub.add_parser("build", help="Build reader-first HTML from final-report.md")
    p_build.add_argument("--project", required=True, help="Path to research project directory")
    p_build.add_argument("--copy-desktop", action="store_true", help="Copy output HTML to Desktop")
    p_build.set_defaults(func=cmd_build)

    p_config = sub.add_parser("config", help="Show current configuration")
    p_config.set_defaults(func=cmd_config)

    p_discover = sub.add_parser(
        "discover",
        help="Run intent discovery on a project (re-generates intent_doc)",
    )
    p_discover.add_argument("project", help="Path to research project directory")
    p_discover.set_defaults(func=cmd_discover)

    p_reflect = sub.add_parser(
        "reflect",
        help="Run mid-research intent reflection based on behavior signals",
    )
    p_reflect.add_argument("project", help="Path to research project directory")
    p_reflect.set_defaults(func=cmd_reflect)

    p_discover_identity = sub.add_parser(
        "discover-identity",
        help="Extract user identity (employment/products/tracks) from CLAUDE.md + Obsidian. Writes draft for review.",
    )
    p_discover_identity.set_defaults(func=cmd_discover_identity)

    p_accept_identity = sub.add_parser(
        "accept-identity",
        help="Promote identity.draft.json to identity.json after user review.",
    )
    p_accept_identity.set_defaults(func=cmd_accept_identity)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
