#!/usr/bin/env python3
"""
Research OS v0.1 - create_research_project.py
Scaffold a new research project from the template library.

Usage:
    ros new --name "Mizzen Insight 产品深度拆解" --type product --depth R2 --html

    # Or directly:
    python create_research_project.py \
        --name "Mizzen Insight 产品深度拆解" \
        --type product \
        --depth R2 \
        --html
"""

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path

import config
from research_router import build_empty_view_model, route_research

TEMPLATE_DIR = config.TEMPLATES
DEFAULT_TARGET = config.PROJECTS_DIR

# depth -> 目录结构
SIMPLE_DIRS = ["00-task", "01-plan", "03-evidence", "06-review", "07-output"]
FULL_DIRS = [
    "00-task",
    "01-plan",
    "02-sources",
    "03-evidence",
    "04-captures",
    "05-analysis",
    "06-review",
    "07-output",
    "08-html",
    "09-publish",
]

# 模板文件 -> 目标子目录 + 目标文件名
TEMPLATE_MAP = {
    "01-调研任务卡.md": ("00-task", "task-card.md"),
    "02-调研方案.md": ("01-plan", "research-plan.md"),
    "03-证据矩阵.md": ("03-evidence", "evidence_matrix.md"),
    "07-反方审计.md": ("06-review", "red_team.md"),
    "08-最终报告.md": ("07-output", "final-report.md"),
}
FULL_EXTRA_MAP = {
    "04-平台审计矩阵.md": ("02-sources", "platform-audit.md"),
    "05-用户原声库.md": ("02-sources", "user-voice.md"),
    "06-JD逐句拆解.md": ("02-sources", "jd-breakdown.md"),
}

DEPTH_CHOICES = ["R0", "R1", "R2", "R3"]
TYPE_CHOICES = [
    "company-jd",
    "product",
    "user-research",
    "industry",
    "competitor",
    "topic",
    "portfolio",
    "mixed",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Research OS v0.1 - scaffold a new research project"
    )
    p.add_argument("--name", required=True, help="项目名")
    p.add_argument("--type", required=True, choices=TYPE_CHOICES, help="调研类型")
    p.add_argument(
        "--depth", required=True, choices=DEPTH_CHOICES, help="深度档位"
    )
    p.add_argument(
        "--html",
        action="store_true",
        help="是否生成 HTML 模板位（R2+ 默认 True）",
    )
    p.add_argument(
        "--target-dir",
        default=str(DEFAULT_TARGET),
        help=f"项目根目录（默认 {DEFAULT_TARGET}）",
    )
    return p.parse_args()


def slugify(name: str) -> str:
    """把项目名转成目录安全的 slug。中文字符保留。"""
    bad = '\\/:*?"<>|'
    out = "".join(c for c in name if c not in bad)
    out = out.strip().rstrip(".")
    return out or "untitled-project"


def build_state(name: str, rtype: str, depth: str) -> dict:
    html_required = depth in ("R2", "R3")
    route = route_research(name, rtype, depth)
    return {
        "project_name": name,
        "research_type": rtype,
        "research_mode": route["research_mode"],
        "view_type": route["view_type"],
        "visual_modules": route["visual_modules"],
        "depth": depth,
        "status": "planned",
        "decision_served": "",
        "agents": [],
        "evidence_count": 0,
        "discarded_source_count": 0,
        "open_questions": [],
        "final_report_mode": "reader_first",
        "html_source": "07-output/final-report.md" if html_required else "",
        "view_model_source": "07-output/view-model.json" if html_required else "",
        "trace_manifest_source": "07-output/trace-manifest.json" if html_required else "",
        "research_plan_source": "01-plan/research-execution-plan.md" if html_required else "",
        "candidate_pool_source": "02-sources/candidate_pool.json" if html_required else "",
        "hypothesis_ledger_source": "03-evidence/hypothesis_ledger.json" if html_required else "",
        "validation_required": True,
        "next_required_action": "run_research_planner" if html_required else "fill_research_plan",
        "folded_sections": [
            "附录",
            "证据标准",
            "信息淘汰说明",
            "核心事实表",
            "结论溯源表",
            "反方审计摘要",
            "来源与附录",
            "最终置信度",
        ],
        "quality_gates": {
            "mimo_search_summary_default_grade": "C",
            "require_source_independence": True,
            "require_ssr_login_wall_plan": True,
            "require_red_team_writeback": True,
            "require_reader_first_report": True,
            "html_must_build_from_final_report": html_required,
            "view_model_required": html_required and route["view_type"] != "narrative_report",
            "visual_modules_required": html_required and route["view_type"] != "narrative_report",
            "candidate_pool_required": html_required,
            "hypothesis_ledger_required": html_required,
            "trace_manifest_required": html_required,
            "strong_claims_must_trace": html_required,
        },
        "last_updated": date.today().isoformat(),
    }


def copy_templates(project_root: Path, depth: str) -> list:
    """复制模板到项目目录。返回 (template_src, dest) 列表，供日志打印。"""
    copied = []
    mapping = dict(TEMPLATE_MAP)
    if depth in ("R2", "R3"):
        mapping.update(FULL_EXTRA_MAP)
    for src_name, (subdir, dest_name) in mapping.items():
        src = TEMPLATE_DIR / src_name
        if not src.exists():
            print(f"[warn] 模板缺失: {src}", file=sys.stderr)
            continue
        dest_dir = project_root / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / dest_name
        shutil.copyfile(src, dest)
        copied.append((src_name, str(dest)))
    return copied


def create_dirs(project_root: Path, depth: str) -> list:
    dirs = FULL_DIRS if depth in ("R2", "R3") else SIMPLE_DIRS
    created = []
    for d in dirs:
        p = project_root / d
        p.mkdir(parents=True, exist_ok=True)
        # 空目录放 .gitkeep
        keep = p / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
        created.append(str(p))
    return created


def write_state(project_root: Path, state: dict) -> Path:
    f = project_root / "research_state.json"
    f.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return f


def write_view_model(project_root: Path, state: dict) -> Path | None:
    if state.get("depth") not in ("R2", "R3"):
        return None
    route = {
        "research_mode": state.get("research_mode", ""),
        "view_type": state.get("view_type", ""),
        "visual_modules": state.get("visual_modules", []),
    }
    f = project_root / "07-output" / "view-model.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(
        json.dumps(build_empty_view_model(state["project_name"], route), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return f


def write_trace_manifest(project_root: Path, state: dict) -> Path | None:
    if state.get("depth") not in ("R2", "R3"):
        return None
    trace_manifest = {
        "schema_version": "research-os-trace-manifest-v0.4",
        "project_name": state["project_name"],
        "claims": [],
    }
    trace_path = project_root / "07-output" / "trace-manifest.json"
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.write_text(json.dumps(trace_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return trace_path


def write_protocol_files(project_root: Path, state: dict) -> list[Path]:
    if state.get("depth") not in ("R2", "R3"):
        return []
    candidate_pool = {
        "schema_version": "research-os-candidate-pool-v0.3",
        "project_name": state["project_name"],
        "items": [],
    }
    hypothesis_ledger = {
        "schema_version": "research-os-hypothesis-ledger-v0.3",
        "project_name": state["project_name"],
        "hypotheses": [],
    }
    outputs = []
    candidate_path = project_root / "02-sources" / "candidate_pool.json"
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(json.dumps(candidate_pool, ensure_ascii=False, indent=2), encoding="utf-8")
    outputs.append(candidate_path)

    ledger_path = project_root / "03-evidence" / "hypothesis_ledger.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(hypothesis_ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    outputs.append(ledger_path)
    return outputs


def create_project(
    name: str,
    rtype: str,
    depth: str,
    html: bool = False,
    target_dir: str | None = None,
) -> int:
    """Create a new research project. Returns 0 on success, non-zero on error."""
    if not TEMPLATE_DIR.exists():
        print(f"[error] 模板库不存在: {TEMPLATE_DIR}", file=sys.stderr)
        print(f"[error] 设置 RESEARCH_OS_TEMPLATES 环境变量指向模板目录", file=sys.stderr)
        return 1

    target = Path(target_dir) if target_dir else DEFAULT_TARGET
    target.mkdir(parents=True, exist_ok=True)

    slug = slugify(name)
    project_root = target / slug
    if project_root.exists():
        print(f"[error] 项目目录已存在: {project_root}", file=sys.stderr)
        return 2

    project_root.mkdir(parents=True)

    created_dirs = create_dirs(project_root, depth)
    copied = copy_templates(project_root, depth)
    state = build_state(name, rtype, depth)
    state_file = write_state(project_root, state)
    view_model_file = write_view_model(project_root, state)
    trace_manifest_file = write_trace_manifest(project_root, state)
    protocol_files = write_protocol_files(project_root, state)

    print(f"[ok] 项目已创建: {project_root}")
    print(f"[ok] 目录数: {len(created_dirs)}")
    print(f"[ok] 模板数: {len(copied)}")
    print(f"[ok] 状态文件: {state_file}")
    if view_model_file:
        print(f"[ok] 视图模型: {view_model_file}")
    if trace_manifest_file:
        print(f"[ok] 结论溯源: {trace_manifest_file}")
    for protocol_file in protocol_files:
        print(f"[ok] 协议文件: {protocol_file}")
    print(f"[ok] 初始状态: {state['status']}")
    print(f"[ok] 路由: {state['research_mode']} / {state['view_type']}")
    print()
    print("下一步:")
    print(f"  1. 填 {project_root / '00-task' / 'task-card.md'}")
    if depth in ("R2", "R3"):
        print(f'  2. 生成执行计划: ros plan "{project_root}"')
        print(f"  3. 填候选池并显式淘汰弱来源: {project_root / '02-sources' / 'candidate_pool.json'}")
        print(f"  4. 填证据矩阵: {project_root / '03-evidence' / 'evidence_matrix.md'}")
        print(f"  5. 更新假设账本，至少修正/降级/拒绝一个假设: {project_root / '03-evidence' / 'hypothesis_ledger.json'}")
        print(f"  6. 做反方审计: {project_root / '06-review' / 'red_team.md'}")
        print(f"  7. 写读者版最终报告: {project_root / '07-output' / 'final-report.md'}")
        print(f"  8. 填结论溯源清单: {project_root / '07-output' / 'trace-manifest.json'}")
        print(f"  9. 填视图模型: {project_root / '07-output' / 'view-model.json'}")
        print(f'  10. 生成 HTML: ros build --project "{project_root}"')
        print(f'  11. 查看状态: ros status "{project_root}"')
        print(f'  12. 验证项目: ros validate "{project_root}"')
    else:
        print(f"  2. 填 {project_root / '01-plan' / 'research-plan.md'}")
        print(f"  3. 写读者版最终报告: {project_root / '07-output' / 'final-report.md'}")
        print(f"  4. 更新 research_state.json 的 status")
    return 0


def main() -> int:
    args = parse_args()
    return create_project(
        name=args.name,
        rtype=args.type,
        depth=args.depth,
        html=args.html,
        target_dir=args.target_dir,
    )


if __name__ == "__main__":
    sys.exit(main())
