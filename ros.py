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

def _check_clarification_gate(project: Path) -> tuple[bool, str]:
    """v0.8 澄清门禁：检查 intent_doc 是否含未回答的 clarifying_questions
    且标 blocks_plan_if_unanswered=true。返回 (是否通过, 拒绝原因)。
    借鉴 dzhng/deep-research 的 generateFeedback() 模式——意图置信度不够时
    必须先回答澄清问题再开调研，避免跑偏。
    """
    intent_path = project / "00-task" / "intent_doc.json"
    if not intent_path.exists():
        return True, ""  # 没有 intent_doc 不阻塞（兼容旧项目）
    try:
        intent = json.loads(intent_path.read_text(encoding="utf-8"))
    except Exception:
        return True, ""
    v07 = intent.get("v07") or intent
    questions = v07.get("clarifying_questions") or intent.get("clarifying_questions") or []
    unanswered = [q for q in questions if q.get("blocks_plan_if_unanswered") and not q.get("answered")]
    if not unanswered:
        return True, ""
    reasons = []
    for q in unanswered:
        q_text = q.get("question", "")[:80]
        reasons.append(f"  - {q_text}")
    msg = "intent_doc 含未回答的澄清问题且标记阻塞 plan/run:\n" + "\n".join(reasons)
    msg += "\n\n请用 `ros discover` 重新跑意图发现并回答这些问题，或手动编辑 intent_doc.json 把对应问题的 answered 字段设为 true。"
    return False, msg





def cmd_new(args: argparse.Namespace) -> int:
    return create_project(
        name=args.name,
        rtype=args.type,
        depth=args.depth,
        html=args.html,
        target_dir=args.target_dir,
    )


def cmd_plan(args: argparse.Namespace) -> int:
    project = Path(args.project)
    if not project.exists():
        print(f"[FAIL] project path does not exist: {project}", file=sys.stderr)
        return 1
    ok, reason = _check_clarification_gate(project)
    if not ok and not args.force:
        print(f"[BLOCKED] 澄清门禁未通过（v0.8）:\n{reason}", file=sys.stderr)
        print("[hint] 用 --force 跳过门禁（不推荐），或先回答澄清问题", file=sys.stderr)
        return 1
    out = plan_project(project)
    print(f"Wrote {out}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    result = inspect_project(Path(args.project))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get("validation", {}).get("fails") else 0


def cmd_run(args: argparse.Namespace) -> int:
    project = Path(args.project)
    if not project.exists():
        print(f"[FAIL] project path does not exist: {project}", file=sys.stderr)
        return 1
    ok, reason = _check_clarification_gate(project)
    if not ok and not args.force:
        print(f"[BLOCKED] 澄清门禁未通过（v0.8）:\n{reason}", file=sys.stderr)
        print("[hint] 用 --force 跳过门禁（不推荐），或先回答澄清问题", file=sys.stderr)
        return 1
    return run_step(project, copy_desktop=not args.no_copy_desktop)


def cmd_validate(args: argparse.Namespace) -> int:
    project = Path(args.project)
    if not project.exists():
        print(f"[FAIL] project path does not exist: {project}", file=sys.stderr)
        return 1
    return print_checks(validate_project(project))


def cmd_build(args: argparse.Namespace) -> int:
    project = Path(args.project)
    # v0.10: 读者门禁 — 如果 final-report.md 已存在，跑 reader_simulation
    # 但 --skip-reader-gate 可绕过（用于快速迭代）
    if not args.skip_reader_gate:
        report_path = project / "07-output" / "final-report.md"
        if report_path.exists():
            try:
                import reader_simulation as rs
                report_md = report_path.read_text(encoding="utf-8-sig")
                passed, diag = rs.readability_gate(project, report_md)
                if not passed and not args.force:
                    feedback = rs.write_reader_feedback_markdown(diag, project)
                    print(f"[FAIL] 读者门禁未通过（整体读懂度 {diag.overall_score:.2f}，通过 {diag.passed_paragraphs}/{diag.total_paragraphs}）")
                    print(f"  反馈文件：{feedback}")
                    print(f"  请 agent 根据反馈重写后再次 build，或用 --force 强制跳过")
                    return 1
                elif not passed and args.force:
                    print(f"[WARN] 读者门禁未通过，但 --force 强制继续（读懂度 {diag.overall_score:.2f}）")
                else:
                    print(f"[ok] 读者门禁通过（整体读懂度 {diag.overall_score:.2f}）")
            except Exception as exc:
                print(f"[warn] reader_simulation 跳过：{exc}", file=sys.stderr)
    out = build(project, not args.no_copy_desktop)
    print(f"Wrote {out}")
    return 0


def cmd_rewrite(args: argparse.Namespace) -> int:
    """v0.10: 触发写-读-改闭环。

    加载研究产物，提示 agent 按 5 幕结构写初稿，然后触发读者门禁。
    agent 模式下，agent 应根据提示自己写初稿，再调 final_report_writer.write_read_rewrite_loop。
    """
    import final_report_writer as frw
    project = Path(args.project)
    if not project.exists():
        print(f"[FAIL] project not found: {project}", file=sys.stderr)
        return 1
    return frw.build_report(project)


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


def cmd_goal(args: argparse.Namespace) -> int:
    """v0.7: goal ledger management — status / propose / accept / reject / evaluate."""
    import goal_tracker
    project = Path(args.project)
    if not project.exists():
        print(f"[FAIL] project not found: {project}", file=sys.stderr)
        return 1
    subcmd = args.subcmd

    if subcmd == "status":
        print(goal_tracker.render_goal_status(project))
        return 0
    elif subcmd == "evaluate":
        result = goal_tracker.evaluate_goal_drift(project)
        # Auto-enqueue proposed adjustments
        if result.get("proposals"):
            ledger = goal_tracker.load_goal_ledger(project)
            if ledger:
                for p in result["proposals"]:
                    # Avoid duplicate adj_id
                    if not any(a.get("adjustment_id") == p.get("adjustment_id") for a in ledger.get("pending_adjustments", [])):
                        ledger["pending_adjustments"].append(p)
                goal_tracker._save(project, ledger)
                print(f"[ok] {len(result['proposals'])} 个调整已入队", file=sys.stderr)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    elif subcmd == "propose":
        adj_id = goal_tracker.propose_adjustment(
            project, args.type, args.rationale, args.signals or [], args.goal or "", requires_user=True
        )
        print(f"[ok] proposed {adj_id} — run `ros goal status` to see, `ros goal accept {adj_id}` to accept")
        return 0
    elif subcmd == "accept":
        r = goal_tracker.accept_adjustment(project, args.adjustment_id)
        print(f"[ok] {r['superseded']} → {r['new_goal_id']}")
        # Trigger replan
        try:
            from research_planner import replan_project
            out = replan_project(project, args.adjustment_id)
            print(f"[ok] replanned: {out}")
        except Exception as exc:
            print(f"[warn] replan failed: {exc}", file=sys.stderr)
        return 0
    elif subcmd == "reject":
        goal_tracker.reject_adjustment(project, args.adjustment_id, args.reason or "")
        print(f"[ok] rejected {args.adjustment_id}")
        return 0
    return 1


def cmd_iterate(args: argparse.Namespace) -> int:
    """v0.7: append a research round to iteration_log."""
    import iteration_log
    project = Path(args.project)
    if not project.exists():
        print(f"[FAIL] project not found: {project}", file=sys.stderr)
        return 1

    if args.subcmd == "init":
        path = iteration_log.init_log(project, args.breadth, args.depth)
        print(f"[ok] initialized {path}")
        return 0
    elif args.subcmd == "append":
        rid = iteration_log.append_round(
            project,
            learnings=args.learnings or [],
            next_directions=args.directions or [],
            evidence_ids=args.evidence or [],
            hypothesis_revisions=args.hypothesis_revisions or [],
            queries=args.queries or [],
            goal_drift_detected=args.drift,
        )
        print(f"[ok] appended round {rid}")
        return 0
    elif args.subcmd == "should-iterate":
        r = iteration_log.should_iterate(project)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    elif args.subcmd == "summary":
        print(iteration_log.render_log_summary(project))
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
    p_run.add_argument("--no-copy-desktop", action="store_true", help="不拷贝到桌面（默认拷贝）")
    p_run.set_defaults(func=cmd_run)

    p_validate = sub.add_parser("validate", help="Validate project against quality gates")
    p_validate.add_argument("project", help="Path to research project directory")
    p_validate.set_defaults(func=cmd_validate)

    p_build = sub.add_parser("build", help="Build reader-first HTML from final-report.md")
    p_build.add_argument("--project", required=True, help="Path to research project directory")
    p_build.add_argument("--no-copy-desktop", action="store_true", help="不拷贝到桌面（默认拷贝）")
    p_build.add_argument("--skip-reader-gate", action="store_true", help="v0.10: 跳过读者门禁")
    p_build.add_argument("--force", action="store_true", help="v0.10: 门禁未通过也强制 build")
    p_build.set_defaults(func=cmd_build)

    p_rewrite = sub.add_parser(
        "rewrite",
        help="v0.10: 触发写-读-改闭环。加载研究产物，提示 agent 按 5 幕结构写初稿，然后跑读者门禁。",
    )
    p_rewrite.add_argument("project", help="Path to research project directory")
    p_rewrite.set_defaults(func=cmd_rewrite)

    p_confirm = sub.add_parser(
        "confirm",
        help="v0.10: 用户确认门禁。把 agent 理解的意图给用户确认，防止方向错。",
    )
    p_confirm.add_argument("project", help="Path to research project directory")
    p_confirm.set_defaults(func=cmd_confirm)

    p_dashboard = sub.add_parser(
        "dashboard",
        help="v0.10: 生成系统看板 HTML（项目列表 + 系统演化 + 工作流可视化）",
    )
    p_dashboard.add_argument("--no-copy-desktop", action="store_true", help="不拷贝到桌面（默认拷贝）")
    p_dashboard.add_argument("--open", action="store_true", help="生成后浏览器打开")
    p_dashboard.set_defaults(func=cmd_dashboard)

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

    # v0.7: goal ledger management
    p_goal = sub.add_parser("goal", help="v0.7: goal ledger management (status/evaluate/propose/accept/reject)")
    p_goal_sub = p_goal.add_subparsers(dest="subcmd", required=True)
    p_goal_status = p_goal_sub.add_parser("status", help="Show current goal + pending adjustments")
    p_goal_status.add_argument("project", help="Path to research project")
    p_goal_status.set_defaults(func=cmd_goal)
    p_goal_eval = p_goal_sub.add_parser("evaluate", help="Scan for goal drift signals")
    p_goal_eval.add_argument("project", help="Path to research project")
    p_goal_eval.set_defaults(func=cmd_goal)
    p_goal_prop = p_goal_sub.add_parser("propose", help="Manually propose a goal adjustment")
    p_goal_prop.add_argument("project", help="Path to research project")
    p_goal_prop.add_argument("--type", required=True, choices=["narrow", "broaden", "pivot", "split_subresearch", "downgrade_depth"])
    p_goal_prop.add_argument("--rationale", required=True)
    p_goal_prop.add_argument("--goal", default="")
    p_goal_prop.add_argument("--signals", nargs="*", default=[])
    p_goal_prop.set_defaults(func=cmd_goal)
    p_goal_acc = p_goal_sub.add_parser("accept", help="Accept a proposed adjustment")
    p_goal_acc.add_argument("project", help="Path to research project")
    p_goal_acc.add_argument("adjustment_id")
    p_goal_acc.set_defaults(func=cmd_goal)
    p_goal_rej = p_goal_sub.add_parser("reject", help="Reject a proposed adjustment")
    p_goal_rej.add_argument("project", help="Path to research project")
    p_goal_rej.add_argument("adjustment_id")
    p_goal_rej.add_argument("--reason", default="")
    p_goal_rej.set_defaults(func=cmd_goal)

    # v0.7: iteration log
    p_iter = sub.add_parser("iterate", help="v0.7: iteration log management (init/append/should-iterate/summary)")
    p_iter_sub = p_iter.add_subparsers(dest="subcmd", required=True)
    p_iter_init = p_iter_sub.add_parser("init", help="Initialize iteration_log.json")
    p_iter_init.add_argument("project", help="Path to research project")
    p_iter_init.add_argument("--breadth", type=int, default=4)
    p_iter_init.add_argument("--depth", type=int, default=2)
    p_iter_init.set_defaults(func=cmd_iterate)
    p_iter_app = p_iter_sub.add_parser("append", help="Append a round")
    p_iter_app.add_argument("project", help="Path to research project")
    p_iter_app.add_argument("--learnings", nargs="*", default=[])
    p_iter_app.add_argument("--directions", nargs="*", default=[])
    p_iter_app.add_argument("--evidence", nargs="*", default=[])
    p_iter_app.add_argument("--hypothesis-revisions", nargs="*", default=[])
    p_iter_app.add_argument("--queries", nargs="*", default=[])
    p_iter_app.add_argument("--drift", action="store_true")
    p_iter_app.set_defaults(func=cmd_iterate)
    p_iter_sh = p_iter_sub.add_parser("should-iterate", help="Check if another round needed")
    p_iter_sh.add_argument("project", help="Path to research project")
    p_iter_sh.set_defaults(func=cmd_iterate)
    p_iter_sum = p_iter_sub.add_parser("summary", help="Render readable summary")
    p_iter_sum.add_argument("project", help="Path to research project")
    p_iter_sum.set_defaults(func=cmd_iterate)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())


def cmd_confirm(args: argparse.Namespace) -> int:
    """v0.10: 用户确认门禁。把 agent 理解的意图给用户确认，防止方向错。"""
    import json
    project = Path(args.project)
    intent_path = project / "00-task" / "intent_doc.json"
    if not intent_path.exists():
        print(f"[FAIL] intent_doc.json not found: {intent_path}", file=sys.stderr)
        return 1

    intent = json.loads(intent_path.read_text(encoding="utf-8-sig"))
    stated = intent.get("stated_intent", "")
    resolved = intent.get("resolved_intent", "")
    confidence = intent.get("confidence", "")

    print("\n" + "=" * 60)
    print("意图确认门禁 — 请确认 agent 对你需求的理解")
    print("=" * 60)
    print(f"\n你说的需求：")
    print(f"  {stated}")
    print(f"\nagent 理解你实际要的：")
    print(f"  {resolved}")
    print(f"\nagent 置信度：{confidence}")
    print("\n" + "-" * 60)
    print("请回答以下问题（直接输入，回车确认）：")
    print("-" * 60)

    # 收集用户确认
    answers = {}
    answers["understanding_correct"] = input("\n1. agent 的理解对吗？(y/n/部分): ").strip()
    if answers["understanding_correct"].lower() in ("n", "部分", "no", "不对", "部分对"):
        answers["corrected_intent"] = input("   请修正 agent 的理解：").strip()
    else:
        answers["corrected_intent"] = ""

    answers["missing_needs"] = input("2. 有没有 agent 没理解到的需求？(没有则回车跳过): ").strip()
    answers["priority_clarification"] = input("3. 这次调研最不能错的结论是什么？: ").strip()
    answers["scope_confirmation"] = input("4. 范围确认：有什么是明确不要的？: ").strip()

    # 写入 user_confirmation 字段
    intent["user_confirmation"] = {
        "confirmed_at": __import__("datetime").datetime.now().isoformat(),
        "understanding_correct": answers["understanding_correct"],
        "corrected_intent": answers["corrected_intent"],
        "missing_needs": answers["missing_needs"],
        "priority_clarification": answers["priority_clarification"],
        "scope_confirmation": answers["scope_confirmation"],
    }
    intent_path.write_text(
        json.dumps(intent, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[ok] 确认已写入 {intent_path}")
    print(f"  后续 ros plan 会读取 user_confirmation 字段")
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    """v0.10: 生成系统看板 HTML。"""
    import build_dashboard
    out = build_dashboard.build_dashboard(copy_desktop=not args.no_copy_desktop)
    print(f"看板已生成：{out}")
    if not args.no_copy_desktop:
        import shutil
        desktop = Path.home() / "Desktop" / "Research OS 看板.html"
        print(f"桌面副本：{desktop}")
    if args.open:
        import webbrowser
        webbrowser.open(f"file:///{out.as_posix()}")
    return 0
