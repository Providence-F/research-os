#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sync_dashboard.py — Research OS v2.0 看板数据链

从 projects/ 真实数据 + workflow_def.py 工作流定义，生成看板数据文件：
  dashboard/src/data/workflow.ts   工作流定义（23 步 + 12 门禁 + 5 阶段）
  dashboard/src/data/projects.ts   项目流水线状态（位置/进度/门禁/健康度）
  dashboard/src/data/versions.ts   版本时间线（从 CHANGELOG.md）
  dashboard/src/data/stats.ts      系统级统计

设计哲学：Smart Agent. Dumb Tools.
本脚本只做机械检查（文件存在、字符数、JSON 字段），不做语义判断。

用法:
    cd research-os
    python scripts/sync_dashboard.py
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from workflow_def import PHASES, STEPS, GATES, TOTAL_STEPS, SYSTEM_VERSION  # noqa: E402

PROJECTS_DIR = REPO_ROOT / "projects"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
DATA_DIR = REPO_ROOT / "dashboard" / "src" / "data"

CATEGORY_NAMES = {
    "product": "产品拆解",
    "industry": "行业赛道",
    "topic": "主题研究",
    "mixed": "混合研究",
    "user-research": "用户研究",
    "company-jd": "JD分析",
    "tech": "技术深度",
    "personal": "个人决策",
    "system": "系统自身",
}


def read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception:
        return {}


def file_ok(p: Path, min_size: int = 10) -> bool:
    """机械判定：文件存在且非空。"""
    try:
        return p.exists() and p.stat().st_size >= min_size
    except Exception:
        return False


def artifact_exists(project: Path, artifact: str) -> bool:
    """步骤产物存在性（机械）。目录型产物检查目录下有无 .md/.json。"""
    if artifact.endswith("/"):
        d = project / artifact
        if not d.is_dir():
            return False
        return any(d.glob("*.md")) or any(d.glob("*.json"))
    if "/" not in artifact:  # 特殊说明项（validation report / 桌面副本）——无法机械判定
        return False
    return file_ok(project / artifact)


def infer_steps_from_artifacts(project: Path) -> dict:
    """无 research_state.json 的遗留项目：从产物存在性机械推断步骤状态。"""
    steps = {}
    for s in STEPS:
        if s["id"] == "step_0_scaffold":
            steps[s["id"]] = "done"  # 目录存在即脚手架已搭
        elif s["id"] in ("step_14_validate", "step_15_publish"):
            # 无状态文件时：HTML 存在则机械视为已验证已发布
            steps[s["id"]] = "done" if file_ok(project / "08-html" / "index.html") else "pending"
        else:
            steps[s["id"]] = "done" if artifact_exists(project, s["artifact"]) else "pending"
    return steps


def last_activity(project: Path) -> str:
    """项目内最新文件修改时间（跳过隐藏目录）。"""
    latest = 0.0
    try:
        for p in project.rglob("*"):
            if not p.is_file() or any(part.startswith(".") for part in p.parts):
                continue
            latest = max(latest, p.stat().st_mtime)
    except Exception:
        pass
    return datetime.fromtimestamp(latest).strftime("%Y-%m-%d") if latest else ""


def project_summary(project: Path, state: dict) -> str:
    """一句话主题：优先 decision_served，否则 final-report 首个标题。"""
    ds = (state.get("decision_served") or "").strip()
    if ds:
        return ds[:80]
    report = project / "07-output" / "final-report.md"
    if file_ok(report):
        for line in report.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line.startswith("#"):
                return line.lstrip("#").strip()[:80]
    return ""


def scan_projects() -> list:
    projects = []
    if not PROJECTS_DIR.exists():
        return projects

    for d in sorted(PROJECTS_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue

        state = read_json(d / "research_state.json")
        tracked = bool(state)

        steps_status = state.get("steps", {}) if tracked else {}
        # 归一化：只认 done，其余（pending/缺失）都算未完成；无状态项目走产物推断
        if tracked:
            steps = {s["id"]: ("done" if steps_status.get(s["id"]) == "done" else "pending") for s in STEPS}
        else:
            steps = infer_steps_from_artifacts(d)

        done_count = sum(1 for v in steps.values() if v == "done")
        current_index = next((i for i, s in enumerate(STEPS) if steps[s["id"]] != "done"), TOTAL_STEPS)
        progress = round(done_count / TOTAL_STEPS, 3)

        # 门禁：产物文件存在即过（Dumb 判定）
        gates = []
        for g in GATES:
            passed = all(file_ok(d / a) for a in g["artifacts"])
            gates.append({"id": g["id"], "passed": passed})

        # 卡点：流水线顺序上，项目当前位置之前首个「触发步骤已达但门禁产物缺失」的门禁
        step_index = {s["id"]: i for i, s in enumerate(STEPS)}
        blocked_gate = None
        for g in GATES:
            gate_passed = next(x["passed"] for x in gates if x["id"] == g["id"])
            if gate_passed:
                continue
            after_idx = step_index[g["after_step"]]
            if after_idx < current_index:
                blocked_gate = g["id"]
                break

        has_html = file_ok(d / "08-html" / "index.html")
        report = d / "07-output" / "final-report.md"
        report_chars = len(report.read_text(encoding="utf-8", errors="ignore")) if file_ok(report) else 0

        raw_status = (state.get("status") or "").strip()
        if not raw_status:
            raw_status = "published" if has_html else ("in_progress" if done_count > 1 else "untracked")

        rtype = state.get("research_type") or ""
        category = CATEGORY_NAMES.get(rtype, rtype or "未分类")

        projects.append({
            "id": d.name,
            "name": d.name,
            "category": category,
            "depth": state.get("depth") or "—",
            "status": raw_status,
            "tracked": tracked,
            "currentStepIndex": current_index,
            "progress": progress,
            "doneSteps": done_count,
            "steps": steps,
            "gates": gates,
            "gatesPassed": sum(1 for x in gates if x["passed"]),
            "blockedGate": blocked_gate,
            "hasHtml": has_html,
            "reportChars": report_chars,
            "evidenceCount": int(state.get("evidence_count") or 0),
            "lastActivity": last_activity(d),
            "summary": project_summary(d, state),
        })

    # 默认按最后活动排序（新→旧）
    projects.sort(key=lambda p: p["lastActivity"] or "", reverse=True)
    return projects


def parse_changelog() -> list:
    """从 CHANGELOG.md 机械解析版本块。"""
    if not CHANGELOG_PATH.exists():
        return []
    text = CHANGELOG_PATH.read_text(encoding="utf-8")
    versions = []
    blocks = re.split(r"^## \[", text, flags=re.MULTILINE)[1:]
    for b in blocks:
        header, _, body = b.partition("\n")
        m = re.match(r"(v[\d.]+)\]\s*-\s*([\d-]+)", header)
        if not m:
            continue
        vid, date = m.group(1), m.group(2)
        # 摘要：第一个 ### 小节标题
        sm = re.search(r"^###\s+(.+)$", body, flags=re.MULTILINE)
        summary = sm.group(1).strip() if sm else ""
        # 变更：前 5 条 bullet
        changes = [ln.strip("- ").strip() for ln in body.splitlines() if ln.strip().startswith("- ")][:5]
        versions.append({"id": vid, "date": date, "summary": summary, "changes": changes})
    if versions:
        versions[0]["isCurrent"] = True
    return versions


def build_stats(projects: list) -> dict:
    published = [p for p in projects if p["currentStepIndex"] >= TOTAL_STEPS or p["status"] in ("published", "completed", "validated")]
    blocked = [p for p in projects if p["blockedGate"]]
    in_pipeline = [p for p in projects if p not in published and p["tracked"]]
    untracked = [p for p in projects if not p["tracked"]]
    return {
        "totalProjects": len(projects),
        "published": len(published),
        "inPipeline": len(in_pipeline),
        "blocked": len(blocked),
        "untracked": len(untracked),
        "totalEvidence": sum(p["evidenceCount"] for p in projects),
        "totalReportChars": sum(p["reportChars"] for p in projects),
        "currentVersion": SYSTEM_VERSION,
        "syncedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def ts(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def write_data_files(projects: list, versions: list, stats: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    workflow = {
        "phases": PHASES,
        "steps": [
            {
                "id": s["id"], "num": s["num"], "label": s["label"],
                "phase": s["phase"], "artifact": s["artifact"],
                "gateAfter": s.get("gate_after"),
            }
            for s in STEPS
        ],
        "gates": [
            {
                "id": g["id"], "number": g["number"], "name": g["name"],
                "afterStep": g["after_step"], "requirement": g["requirement"],
            }
            for g in GATES
        ],
    }

    header = "// 本文件由 scripts/sync_dashboard.py 自动生成，请勿手改\n"

    (DATA_DIR / "workflow.ts").write_text(
        header
        + "import type { WorkflowDef } from './types';\n\nexport const workflow: WorkflowDef = "
        + ts(workflow) + ";\n",
        encoding="utf-8",
    )
    (DATA_DIR / "projects.ts").write_text(
        header
        + "import type { ProjectPipeline } from './types';\n\nexport const projects: ProjectPipeline[] = "
        + ts(projects) + ";\n",
        encoding="utf-8",
    )
    (DATA_DIR / "versions.ts").write_text(
        header
        + "import type { VersionInfo } from './types';\n\nexport const versions: VersionInfo[] = "
        + ts(versions) + ";\n",
        encoding="utf-8",
    )
    (DATA_DIR / "stats.ts").write_text(
        header
        + "import type { SystemStats } from './types';\n\nexport const stats: SystemStats = "
        + ts(stats) + ";\n",
        encoding="utf-8",
    )


def main():
    projects = scan_projects()
    versions = parse_changelog()
    stats = build_stats(projects)
    write_data_files(projects, versions, stats)
    print(f"[ok] projects: {len(projects)} (tracked {sum(1 for p in projects if p['tracked'])}, "
          f"published {stats['published']}, blocked {stats['blocked']})")
    print(f"[ok] versions: {len(versions)} (current {stats['currentVersion']})")
    print(f"[ok] data written to {DATA_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
