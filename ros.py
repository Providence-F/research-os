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

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
