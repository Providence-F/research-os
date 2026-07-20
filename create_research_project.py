#!/usr/bin/env python3
"""
Research OS v1.4 - create_research_project.py
Scaffold a new research project from the template library.

Changes from v0.1:
- Copy all 14 required templates (not just 5)
- Initialize candidates.md + discarded.md (not just candidate_pool.json)
- Initialize intent_doc.json + goal_ledger.json
- Upgrade schema_version to v0.5
- Add version header to all generated files
- Align with 00-使用说明.md v0.5

Usage:
    ros new --name "Mizzen Insight 产品深度拆解" --type product --depth R2 --html

    # Or directly:
    python create_research_project.py \\
        --name "Mizzen Insight 产品深度拆解" \\
        --type product \\
        --depth R2 \\
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
from intent_discovery import discover as discover_intent

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

# v0.5: 完整模板映射（14 个必产物 + 4 个场景模板）
# 之前 v0.1 只复制 5 个模板，导致 validator FAIL
TEMPLATE_MAP = {
    # 核心必产物
    "01-调研任务卡.md": ("00-task", "task-card.md"),
    "02-调研方案.md": ("01-plan", "research-plan.md"),
    "03-证据矩阵.md": ("03-evidence", "evidence_matrix.md"),
    "04-假设账本.md": ("03-evidence", "hypothesis_ledger_template.md"),  # JSON 模板参考
    "07-反方审计.md": ("06-review", "red_team.md"),
    "08-最终报告.md": ("07-output", "final-report.md"),
    "12-候选池.md": ("02-sources", "candidates.md"),
    "14-研究执行状态机.md": ("01-plan", "state-machine-ref.md"),  # 参考
    "15-结论溯源清单.md": ("07-output", "trace-manifest-template.md"),  # 参考
}

# 场景模板（按需，R2+ 复制）
SCENARIO_MAP = {
    "04-平台审计矩阵.md": ("02-sources", "platform-audit.md"),
    "05-用户原声库.md": ("02-sources", "user-voice.md"),
    "06-JD逐句拆解.md": ("02-sources", "jd-breakdown.md"),
    "11-复盘回写清单.md": ("09-publish", "retro-checklist.md"),
}

# HTML 美学规范和视图模型总是复制到 08-html/ 供参考
REFERENCE_MAP = {
    "09-可视化视图模型.md": ("08-html", "view-model-schema-ref.md"),
    "09-HTML美学规范.md": ("08-html", "html-aesthetics-spec.md"),
}

# 必须创建的空文件（discarded.md 没有模板但是必产物）
EMPTY_FILES = {
    "02-sources/discarded.md": """<!-- ros-version: v0.5 | last-updated: {date} | status: current -->

# 丢弃源清单（discarded.md）

> 本文件记录被丢弃的候选源及原因。**必产物**——不能省略。
> 每条记录包含：源名 / URL / 丢弃原因 / 丢弃日期

---

## 丢弃源列表

| 编号 | 源名 | URL | 丢弃原因 | 日期 |
|---|---|---|---|---|
| - | （待填）| | | |

## 丢弃原因分类

- **重复**：和已有源内容重复
- **低质**：来源不可信（如营销稿、未署名博客）
- **过时**：信息已过时（如 3 年前的数据）
- **付费墙**：无法访问全文
- **语言**：无法理解的语言
- **主题偏移**：和调研主题不相关
""",
    "03-evidence/conflicts.md": """<!-- ros-version: v0.5 | last-updated: {date} | status: current -->

# 冲突信息（conflicts.md）

> 本文件记录证据之间的冲突。**必产物**——不能假装没看见。
> 每条冲突包含：冲突描述 / 涉及证据 / 解决方式 / 最终判定

---

## 冲突列表

### 冲突 1
- **描述**：（待填）
- **涉及证据**：E00X vs E00Y
- **解决方式**：（待填）
- **最终判定**：（待填）

## 冲突解决原则

1. **源码优先**：A 级证据（源码/技术报告）优先于 B/C 级
2. **多源验证**：单一来源的论断标记为 partial
3. **时间 newer 优先**：新信息覆盖旧信息
4. **官方优先**：官方文档优先于社区评测
""",
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
        description="Research OS v1.0 - scaffold a new research project"
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
    """v1.0: 状态文件，schema 升级，含核心对象直采和独立审计两个子步骤。"""
    html_required = depth in ("R2", "R3")
    route = route_research(name, rtype, depth)
    return {
        "schema_version": "research-os-state-v0.5",
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
        # v1.0: 完整步骤状态（含 step_6_5 核心对象直采和 step_9_5 独立审计）
        "steps": {
            "step_0_scaffold": "done",
            "step_1_route": "pending",
            "step_1_5_direction_selection": "pending",
            "step_2_task_card": "pending",
            "step_3_research_plan": "pending",
            "step_4_candidates": "pending",
            "step_5_evidence_matrix": "pending",
            "step_6_hypothesis": "pending",
            "step_6_5_core_objects_fetch": "pending",
            "step_7_analysis": "pending",
            "step_7_5_narrative_plan": "pending",
            "step_8_red_team": "pending",
            "step_9_final_report_draft": "pending",
            "step_9_5_independent_audit": "pending",
            "step_9_6_adversarial_review": "pending",
            "step_10_reader_simulation": "pending",
            "step_10_5_write_read_rewrite": "pending",
            "step_11_trace_manifest": "pending",
            "step_12_view_model": "pending",
            "step_13_html_build": "pending",
            "step_14_validate": "pending",
            "step_15_publish": "pending",
        },
        "human_confirmation_points": {
            "step_1_5_direction_selection": True,
            "step_2_task_card": False,
            "step_3_research_plan": False,
            "step_13_html_build": False,
        },
        "html_source": "07-output/final-report.md" if html_required else "",
        "view_model_source": "07-output/view-model.json" if html_required else "",
        "trace_manifest_source": "07-output/trace-manifest.json" if html_required else "",
        "research_plan_source": "01-plan/research-plan.md",
        "candidates_source": "02-sources/candidates.md",
        "discarded_source": "02-sources/discarded.md",
        "hypothesis_ledger_source": "03-evidence/hypothesis_ledger.json",
        "conflicts_source": "03-evidence/conflicts.md",
        "intent_doc_source": "00-task/intent_doc.json",
        "goal_ledger_source": "00-task/goal_ledger.json",
        "validation_required": True,
        "next_required_action": "fill_task_card",
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
            # v0.5 新增
            "require_discarded_md": True,
            "require_conflicts_md": True,
            "require_aesthetics_compliance": html_required,
            "require_version_consistency": True,
        },
        "last_updated": date.today().isoformat(),
    }


def copy_templates(project_root: Path, depth: str, project_name: str = "") -> list:
    """v0.5: 复制全部 14 个模板（不是 v0.1 的 5 个）。"""
    copied = []
    mapping = dict(TEMPLATE_MAP)
    mapping.update(REFERENCE_MAP)
    if depth in ("R2", "R3"):
        mapping.update(SCENARIO_MAP)
    for src_name, (subdir, dest_name) in mapping.items():
        src = TEMPLATE_DIR / src_name
        if not src.exists():
            print(f"[warn] 模板缺失: {src}", file=sys.stderr)
            continue
        dest_dir = project_root / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / dest_name
        text = src.read_text(encoding="utf-8-sig")
        if project_name and "{项目名}" in text:
            text = text.replace("{项目名}", project_name)
            copied.append((src_name, str(dest) + " (替换占位符)"))
        else:
            copied.append((src_name, str(dest)))
        dest.write_text(text, encoding="utf-8")
    return copied


def create_empty_files(project_root: Path) -> list:
    """v0.5: 创建必产的空文件（discarded.md, conflicts.md）。"""
    today = date.today().isoformat()
    created = []
    for rel_path, template in EMPTY_FILES.items():
        dest = project_root / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        text = template.replace("{date}", today)
        dest.write_text(text, encoding="utf-8")
        created.append(str(dest))
    return created


def create_dirs(project_root: Path, depth: str) -> list:
    dirs = FULL_DIRS if depth in ("R2", "R3") else SIMPLE_DIRS
    created = []
    for d in dirs:
        p = project_root / d
        p.mkdir(parents=True, exist_ok=True)
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
    empty_vm = build_empty_view_model(state["project_name"], route)
    empty_vm["schema_version"] = "research-os-view-model-v0.5"
    f.write_text(
        json.dumps(empty_vm, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return f


def write_trace_manifest(project_root: Path, state: dict) -> Path | None:
    if state.get("depth") not in ("R2", "R3"):
        return None
    trace_manifest = {
        "schema_version": "research-os-trace-manifest-v0.5",
        "project_name": state["project_name"],
        "claims": [],
    }
    trace_path = project_root / "07-output" / "trace-manifest.json"
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.write_text(json.dumps(trace_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return trace_path


def write_protocol_files(project_root: Path, state: dict) -> list[Path]:
    """初始化 candidate_pool.json + hypothesis_ledger.json + goal_ledger.json

    intent_doc.json 由 intent_discovery.prepare() 创建（ros new 时自动调用），
    此处不再重复创建以避免 schema 不一致。"""
    if state.get("depth") not in ("R2", "R3"):
        return []
    today = date.today().isoformat()

    candidate_pool = {
        "schema_version": "research-os-candidate-pool-v0.5",
        "project_name": state["project_name"],
        "created_at": today,
        "items": [],
    }
    hypothesis_ledger = {
        "schema_version": "research-os-hypothesis-ledger-v0.5",
        "project_name": state["project_name"],
        "created_at": today,
        "hypotheses": [],
    }
    goal_ledger = {
        "schema_version": "research-os-goal-ledger-v0.5",
        "project_name": state["project_name"],
        "created_at": today,
        "goals": [],
        "iteration_log": [],
    }

    outputs = []
    for rel_path, data in [
        ("02-sources/candidate_pool.json", candidate_pool),
        ("03-evidence/hypothesis_ledger.json", hypothesis_ledger),
        ("00-task/goal_ledger.json", goal_ledger),
    ]:
        p = project_root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        outputs.append(p)
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
    state = build_state(name, rtype, depth)
    copied = copy_templates(project_root, depth, state["project_name"])
    empty_files = create_empty_files(project_root)
    state_file = write_state(project_root, state)
    view_model_file = write_view_model(project_root, state)
    trace_manifest_file = write_trace_manifest(project_root, state)
    protocol_files = write_protocol_files(project_root, state)

    print(f"[ok] 项目已创建: {project_root}")
    print(f"[ok] 目录数: {len(created_dirs)}")
    print(f"[ok] 模板数: {len(copied)}（v0.5 完整 14 个）")
    print(f"[ok] 空文件: {len(empty_files)}（discarded.md + conflicts.md）")
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

    # Trigger intent discovery (pre-research phase). Non-fatal.
    try:
        discover_intent(project_root)
        print(f"[ok] 意图文档已生成 (基于项目名+历史画像)")
        print(f"[hint] 填完 task-card.md 后再跑一次: ros discover \"{project_root}\"")
    except Exception as exc:
        print(f"[warn] 意图挖掘跳过: {exc}", file=sys.stderr)
        print(f"[hint] 填完 task-card.md 后可手动跑: ros discover \"{project_root}\"", file=sys.stderr)
    print()
    print("下一步（v0.5 完整 15 步）:")
    print(f"  1. 填 {project_root / '00-task' / 'task-card.md'}")
    print(f"  2. 🛑 人工确认任务卡")
    if depth in ("R2", "R3"):
        print(f'  3. 生成调研方案: ros plan "{project_root}"')
        print(f"  4. 🛑 人工确认调研方案")
        print(f"  5. 填候选池: {project_root / '02-sources' / 'candidates.md'}")
        print(f"  6. 填丢弃源: {project_root / '02-sources' / 'discarded.md'}（必产物）")
        print(f"  7. 填证据矩阵: {project_root / '03-evidence' / 'evidence_matrix.md'}")
        print(f"  8. 填假设账本: {project_root / '03-evidence' / 'hypothesis_ledger.json'}")
        print(f"  9. 填冲突信息: {project_root / '03-evidence' / 'conflicts.md'}（必产物）")
        print(f"  10. 多 Agent 分析: {project_root / '05-analysis'}")
        print(f"  11. 反方审计（至少 1 次降级）: {project_root / '06-review' / 'red_team.md'}")
        print(f"  12. 写最终报告草稿: {project_root / '07-output' / 'final-report.md'}")
        print(f"  13. 读者模拟 + 重写: ros rewrite \"{project_root}\"")
        print(f"  14. 填溯源清单: {project_root / '07-output' / 'trace-manifest.json'}")
        print(f"  15. 填视图模型: {project_root / '07-output' / 'view-model.json'}")
        print(f'  16. 生成 HTML（遵循 09-HTML美学规范.md）: ros build --project "{project_root}"')
        print(f'  17. 🛑 人工确认 HTML 美学合规')
        print(f'  18. 验证项目: ros validate "{project_root}"')
        print(f'  19. 发布到桌面: ros publish "{project_root}"')
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
