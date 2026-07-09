"""build_dashboard.py - Research OS v0.5 系统看板生成器

生成一个展示 Research OS 系统本身的 HTML 看板：
- 系统怎么运作（可视化工作流）
- 产出过什么（项目卡片 + 链接到报告）
- 怎么演化（版本时间线）
- 设计哲学（为什么这样设计）

定位：作品集入口 + 系统自省工具
受众：想了解 Research OS 这个系统的人（招聘官/合作伙伴/自己）
"""

from __future__ import annotations
import json
import os
from datetime import datetime
from pathlib import Path
from html import escape


RESEARCH_OS_ROOT = Path(r"C:\Users\19932\research-os")
PROJECTS_DIR = RESEARCH_OS_ROOT / "projects"
DESKTOP_DIR = Path.home() / "Desktop"


# 用户明确点名属于 Research OS 产出的桌面 HTML 报告（白名单，不扫所有桌面 HTML）
# 历史报告不是这个系统的产出，只有这里点名的才算
NAMED_DESKTOP_REPORTS = [
    {
        "filename": "MemOS 核心记忆机制科普拆解.html",
        "title": "MemOS 核心记忆机制科普拆解",
        "category": "技术科普",
        "desc": "拆解 MemOS 记忆系统的核心机制，做技术科普。",
    },
    {
        "filename": "Mizzen Insight 产品深度拆解报告.html",
        "title": "Mizzen Insight 产品深度拆解",
        "category": "产品拆解",
        "desc": "对 Mizzen Insight 做产品层面的深度拆解。",
    },
    {
        "filename": "Kai 下一阶段 AI 产品 FDE 作品集方向优先级研究.html",
        "title": "Kai 下一阶段 AI 产品 FDE 作品集方向",
        "category": "求职",
        "desc": "研究 Kai 下一阶段作品集方向优先级，服务 FDE 岗位求职。",
    },
    {
        "filename": "物理学师范毕业论文选题与导师推荐报告.html",
        "title": "物理学师范毕业论文选题与导师推荐",
        "category": "求学",
        "desc": "为物理学师范毕业论文选题方向与导师选择做推荐。",
    },
]


# 项目目录名 → 类别 映射（research-os/projects/ 下的项目按这个分类）
PROJECT_CATEGORY_MAP = {
    "前端设计深度调研": "系统设计",
    "AMD 参访准备": "求职",
    "DeepSeek 六月岗位 JD 分析": "求职",
    "开源深度调研系统横向拆解v2": "系统设计",
    "深度调研开源项目横向拆解": "系统设计",
    "芯片行业第一性原理": "行业研究",
}


# 类别展示顺序（未列出的类别排到末尾，按字母序）
CATEGORY_ORDER = [
    "产品拆解",
    "求职",
    "求学",
    "系统设计",
    "技术科普",
    "行业研究",
]


# =====================================================================
# 1. 扫描项目（research-os/projects/ + 用户点名的桌面报告）
# =====================================================================

def scan_projects() -> list[dict]:
    """扫描 projects/ 目录，提取每个项目的元数据。"""
    projects = []
    if not PROJECTS_DIR.exists():
        return projects

    for proj_dir in sorted(PROJECTS_DIR.iterdir()):
        if not proj_dir.is_dir():
            continue
        state_path = proj_dir / "research_state.json"
        report_path = proj_dir / "07-output" / "final-report.md"
        html_path = proj_dir / "08-html" / "index.html"

        proj = {
            "name": proj_dir.name,
            "dir": str(proj_dir),
            "source": "research-os",  # 来自 research-os/projects/
            "category": PROJECT_CATEGORY_MAP.get(proj_dir.name, "其他"),
            "status": "unknown",
            "depth": "unknown",
            "mode": "unknown",
            "evidence_count": 0,
            "verdict": "",
            "has_html": html_path.exists(),
            "html_path": str(html_path) if html_path.exists() else "",
            "has_report": report_path.exists(),
        }

        if state_path.exists():
            try:
                state = json.loads(state_path.read_text(encoding="utf-8-sig"))
                proj["status"] = state.get("status", "unknown")
                proj["depth"] = state.get("depth", "unknown")
                proj["mode"] = state.get("research_mode", "unknown")
                proj["evidence_count"] = state.get("evidence_count", 0)
            except Exception:
                pass

        # 从 final-report.md 提取一句话结论（第一个 > 引用）
        if report_path.exists():
            try:
                md = report_path.read_text(encoding="utf-8-sig")
                for line in md.split("\n"):
                    line = line.strip()
                    if line.startswith("> 一句话结论："):
                        proj["verdict"] = line.replace("> 一句话结论：", "").strip()
                        break
            except Exception:
                pass

        projects.append(proj)

    return projects


def scan_named_desktop_reports() -> list[dict]:
    """扫描用户明确点名的桌面 HTML 报告。

    历史报告不是这个系统的产出，只有用户点名提到的报告才是。
    所以这里用白名单，不扫所有桌面 HTML。
    """
    reports = []
    for entry in NAMED_DESKTOP_REPORTS:
        html_path = DESKTOP_DIR / entry["filename"]
        reports.append({
            "name": entry["title"],
            "dir": "",
            "source": "desktop-named",  # 用户点名的桌面报告
            "category": entry["category"],
            "status": "done",  # 桌面报告默认已完成
            "depth": "—",  # 没有元数据
            "mode": "—",
            "evidence_count": 0,
            "verdict": entry["desc"],  # 用简短描述代替一句话结论
            "has_html": html_path.exists(),
            "html_path": str(html_path) if html_path.exists() else "",
            "has_report": False,
        })
    return reports


# =====================================================================
# 2. 系统演化轨迹
# =====================================================================

SYSTEM_EVOLUTION = [
    {
        "version": "v0.1-v0.5",
        "date": "2026 Q1",
        "title": "基础工作台",
        "changes": [
            "命令行工具（ros new/plan/run/build）",
            "10 步调研流程",
            "JSON 配置 + Markdown 模板",
            "HTML 报告生成器",
        ],
        "why": "解决调研过程中来源不可验证、结论断裂、过程与交付混杂的问题",
    },
    {
        "version": "v0.9",
        "date": "2026 Q2",
        "title": "意图挖掘 + 反方审计",
        "changes": [
            "意图挖掘模块（3 轮结构化探索）",
            "反方审计（11 维度攻击）",
            "读者优先报告模式",
            "证据分级（A/B/C/D）",
            "假设账本（含置信度追踪）",
        ],
        "why": "用户嘴上说的需求跟真实需求常有差距，需要系统挖掘；每条结论需要被反方审计才能交付",
    },
    {
        "version": "v0.5",
        "date": "2026-07",
        "title": "读者代理 + 看板",
        "changes": [
            "reader_simulation 模块（LLM 扮演读者逐段验证可读性）",
            "写-读-改闭环（最多 2 轮重写）",
            "用户确认门禁（ros confirm，输入端防方向错）",
            "AI 味检测（detect_ai_tell）",
            "意图挖掘反确认偏误（允许无 gap）",
            "系统看板（本文件）",
        ],
        "why": "报告读起来像 XML（幕后信息泄漏正文）；LLM 只当生产者不当读者；意图挖掘过度拟合历史 pattern；缺少系统级的展示和自省入口",
    },
]


# =====================================================================
# 3. 调研流程可视化
# =====================================================================

WORKFLOW_STEPS = [
    {"step": 1, "name": "创建项目", "cmd": "ros new", "desc": "起一个调研任务，设定深度和模式"},
    {"step": 2, "name": "挖掘意图", "cmd": "ros discover", "desc": "3 轮探索：你嘴上要什么 vs 实际要什么"},
    {"step": 3, "name": "确认意图", "cmd": "ros confirm", "desc": "你确认 agent 的理解对不对，防止方向错"},
    {"step": 4, "name": "制定计划", "cmd": "ros plan", "desc": "拆子问题、列假设、定证据来源"},
    {"step": 5, "name": "收集证据", "cmd": "ros collect", "desc": "从候选池筛选证据，分级（A/B/C/D）"},
    {"step": 6, "name": "形成假设", "cmd": "ros hypothesize", "desc": "证据支持哪些假设，置信度多少"},
    {"step": 7, "name": "反方审计", "cmd": "ros redteam", "desc": "主动攻击自己的结论，至少降级 1 个"},
    {"step": 8, "name": "写报告", "cmd": "ros report", "desc": "5 幕结构：问题-探索-冲突-决策-行动"},
    {"step": 9, "name": "读者验证", "cmd": "ros rewrite", "desc": "LLM 扮演读者逐段读，读懂了才交付"},
    {"step": 10, "name": "生成 HTML", "cmd": "ros build", "desc": "渲染成可分享的 HTML 报告"},
]


# =====================================================================
# 4. 设计哲学
# =====================================================================

DESIGN_PHILOSOPHY = [
    {
        "title": "可溯源",
        "desc": "每条结论都能追溯到证据。不是'我觉得'，是'证据显示'。",
    },
    {
        "title": "读者优先",
        "desc": "报告写给读者看，不是写给研究者自己看。幕后信息不进正文。",
    },
    {
        "title": "反方审计",
        "desc": "每条核心结论必须经过反方攻击。R2 深度要求至少降级 1 个结论。",
    },
    {
        "title": "写-读-改闭环",
        "desc": "写完不是结束，读者读懂了才是结束。LLM 既当作者又当读者。",
    },
    {
        "title": "输入端确认",
        "desc": "意图挖掘后必须用户确认，防止整个调研方向错。",
    },
]


# =====================================================================
# 5. HTML 生成
# =====================================================================

def _sort_by_category(projects: list[dict]) -> list[dict]:
    """按 CATEGORY_ORDER 排序，未列出的排到末尾按字母序。"""
    def sort_key(p: dict) -> tuple:
        cat = p.get("category", "其他")
        if cat in CATEGORY_ORDER:
            return (0, CATEGORY_ORDER.index(cat), p["name"])
        return (1, 0, p["name"])
    return sorted(projects, key=sort_key)


def _group_by_category(projects: list[dict]) -> list[tuple[str, list[dict]]]:
    """按类别分组，保持 CATEGORY_ORDER 顺序。"""
    groups: dict[str, list[dict]] = {}
    for p in projects:
        cat = p.get("category", "其他")
        groups.setdefault(cat, []).append(p)
    ordered = []
    for cat in CATEGORY_ORDER:
        if cat in groups:
            ordered.append((cat, groups[cat]))
    # 其他未列出的类别按字母序追加
    for cat in sorted(groups.keys()):
        if cat not in CATEGORY_ORDER:
            ordered.append((cat, groups[cat]))
    return ordered


def build_dashboard_html(projects: list[dict], output: Path) -> Path:
    """生成看板 HTML。"""
    # 统计数字
    total_projects = len(projects)
    done_projects = sum(1 for p in projects if p["status"] in ("done", "completed"))
    total_evidence = sum(p["evidence_count"] for p in projects)
    # 模块数
    py_files = list(RESEARCH_OS_ROOT.glob("*.py"))
    module_count = len(py_files)

    # 按类别分组
    sorted_projects = _sort_by_category(projects)
    grouped = _group_by_category(sorted_projects)

    # ===== HTML 头部 =====
    html_parts = ["""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Research OS — 深度调研工作台</title>
<style>
:root {
  --bg: #FAF9F5;
  --surface: #FFFFFF;
  --text: #1A1A1A;
  --text-secondary: #5C5C5C;
  --accent: #C96442;
  --accent-light: #F4E4DE;
  --border: #E5E2D9;
  --green: #4A7C59;
  --shadow: 0 2px 8px rgba(0,0,0,0.06);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, "Segoe UI", "Noto Sans SC", sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.7;
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px 24px 80px;
}

/* ===== Hero ===== */
.hero {
  text-align: center;
  padding: 60px 20px 40px;
}
.hero h1 {
  font-size: 2.8em;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-bottom: 12px;
}
.hero .tagline {
  font-size: 1.2em;
  color: var(--text-secondary);
  margin-bottom: 32px;
}
.hero .stats {
  display: flex;
  justify-content: center;
  gap: 40px;
  flex-wrap: wrap;
}
.hero .stat {
  text-align: center;
}
.hero .stat-num {
  font-size: 2.2em;
  font-weight: 700;
  color: var(--accent);
}
.hero .stat-label {
  font-size: 0.9em;
  color: var(--text-secondary);
}
.hero .version-badge {
  display: inline-block;
  margin-top: 20px;
  padding: 6px 16px;
  background: var(--accent-light);
  color: var(--accent);
  border-radius: 20px;
  font-size: 0.85em;
  font-weight: 600;
}

/* ===== Section ===== */
.section {
  margin-top: 60px;
}
.section h2 {
  font-size: 1.6em;
  font-weight: 700;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--border);
}
.section .section-desc {
  color: var(--text-secondary);
  font-size: 0.95em;
  margin-bottom: 24px;
}

/* ===== 工作流 ===== */
.workflow {
  background: var(--surface);
  border-radius: 12px;
  padding: 32px;
  box-shadow: var(--shadow);
}
.workflow-steps {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 16px;
}
.workflow-step {
  border-left: 3px solid var(--accent);
  padding: 12px 16px;
  background: var(--bg);
  border-radius: 0 8px 8px 0;
  transition: transform 0.2s, box-shadow 0.2s;
}
.workflow-step:hover {
  transform: translateX(4px);
  box-shadow: var(--shadow);
}
.workflow-step .step-num {
  font-size: 0.75em;
  color: var(--accent);
  font-weight: 700;
  text-transform: uppercase;
}
.workflow-step .step-name {
  font-weight: 600;
  margin: 4px 0;
}
.workflow-step .step-cmd {
  font-family: "Cascadia Code", "Consolas", monospace;
  font-size: 0.8em;
  color: var(--text-secondary);
  background: var(--border);
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  margin-bottom: 6px;
}
.workflow-step .step-desc {
  font-size: 0.85em;
  color: var(--text-secondary);
}

/* ===== 项目卡片 ===== */
.category-group {
  margin-bottom: 32px;
}
.category-group .cat-title {
  font-size: 1.15em;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 16px;
  padding-bottom: 6px;
  border-bottom: 1px dashed var(--border);
  display: flex;
  align-items: center;
  gap: 12px;
}
.category-group .cat-count {
  font-size: 0.8em;
  color: var(--text-secondary);
  font-weight: 500;
  background: var(--accent-light);
  padding: 2px 10px;
  border-radius: 12px;
}
.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}
.project-card {
  background: var(--surface);
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
}
.project-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}
.project-card .proj-name {
  font-size: 1.15em;
  font-weight: 700;
  margin-bottom: 8px;
}
.project-card .proj-verdict {
  color: var(--text-secondary);
  font-size: 0.9em;
  margin-bottom: 16px;
  flex-grow: 1;
  line-height: 1.6;
}
.project-card .proj-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.project-card .badge {
  font-size: 0.75em;
  padding: 3px 10px;
  border-radius: 12px;
  font-weight: 600;
}
.badge-depth { background: var(--accent-light); color: var(--accent); }
.badge-status-done { background: #E8F5E9; color: var(--green); }
.badge-status-failed { background: #FFEBEE; color: #C62828; }
.badge-status-unknown { background: var(--border); color: var(--text-secondary); }
.badge-evidence { background: #E3F2FD; color: #1565C0; }
.badge-source {
  background: #F3E5F5;
  color: #6A1B9A;
}
.project-card .proj-link {
  display: inline-block;
  margin-top: 8px;
  color: var(--accent);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9em;
}
.project-card .proj-link:hover {
  text-decoration: underline;
}

/* ===== 时间线 ===== */
.timeline {
  position: relative;
  padding-left: 32px;
}
.timeline::before {
  content: "";
  position: absolute;
  left: 8px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--border);
}
.timeline-item {
  position: relative;
  margin-bottom: 32px;
  padding: 20px;
  background: var(--surface);
  border-radius: 12px;
  box-shadow: var(--shadow);
}
.timeline-item::before {
  content: "";
  position: absolute;
  left: -28px;
  top: 24px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--accent);
  border: 3px solid var(--bg);
}
.timeline-item .tl-version {
  font-size: 0.8em;
  color: var(--accent);
  font-weight: 700;
  text-transform: uppercase;
}
.timeline-item .tl-title {
  font-size: 1.2em;
  font-weight: 700;
  margin: 4px 0 8px;
}
.timeline-item .tl-date {
  font-size: 0.8em;
  color: var(--text-secondary);
  margin-bottom: 12px;
}
.timeline-item .tl-why {
  font-size: 0.9em;
  color: var(--text-secondary);
  margin-bottom: 12px;
  font-style: italic;
}
.timeline-item .tl-changes {
  list-style: none;
  padding: 0;
}
.timeline-item .tl-changes li {
  padding: 4px 0 4px 20px;
  position: relative;
  font-size: 0.9em;
}
.timeline-item .tl-changes li::before {
  content: "+";
  position: absolute;
  left: 0;
  color: var(--green);
  font-weight: 700;
}

/* ===== 设计哲学 ===== */
.philosophy-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}
.philosophy-card {
  background: var(--surface);
  border-radius: 12px;
  padding: 20px;
  box-shadow: var(--shadow);
  border-top: 3px solid var(--accent);
}
.philosophy-card .ph-title {
  font-weight: 700;
  margin-bottom: 8px;
  font-size: 1.05em;
}
.philosophy-card .ph-desc {
  font-size: 0.9em;
  color: var(--text-secondary);
}

/* ===== Footer ===== */
.footer {
  text-align: center;
  margin-top: 60px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
  color: var(--text-secondary);
  font-size: 0.85em;
}
</style>
</head>
<body>
"""]

    # ===== Hero =====
    html_parts.append(f"""
<div class="hero">
  <h1>Research OS</h1>
  <p class="tagline">深度调研工作台 — 让每条结论可溯源、可验证、可理解</p>
  <div class="stats">
    <div class="stat">
      <div class="stat-num">{total_projects}</div>
      <div class="stat-label">调研项目</div>
    </div>
    <div class="stat">
      <div class="stat-num">{module_count}</div>
      <div class="stat-label">系统模块</div>
    </div>
    <div class="stat">
      <div class="stat-num">{total_evidence}</div>
      <div class="stat-label">证据条数</div>
    </div>
    <div class="stat">
      <div class="stat-num">{done_projects}</div>
      <div class="stat-label">已完成</div>
    </div>
  </div>
  <div class="version-badge">v0.5 · 系统看板（v0.5 重构后归并版本号）</div>
</div>
""")

    # ===== 调研流程 =====
    html_parts.append("""
<div class="section">
  <h2>这个系统怎么运作</h2>
  <p class="section-desc">每个调研任务走 10 步流程。前 3 步防止方向错，中间 4 步收集和验证证据，最后 3 步确保报告能被读者读懂。</p>
  <div class="workflow">
    <div class="workflow-steps">
""")
    for step in WORKFLOW_STEPS:
        html_parts.append(f"""
      <div class="workflow-step">
        <div class="step-num">第 {step['step']} 步</div>
        <div class="step-name">{escape(step['name'])}</div>
        <div class="step-cmd">{escape(step['cmd'])}</div>
        <div class="step-desc">{escape(step['desc'])}</div>
      </div>
""")
    html_parts.append("""
    </div>
  </div>
</div>
""")

    # ===== 项目展示（按类别分组） =====
    html_parts.append("""
<div class="section">
  <h2>调研产出</h2>
  <p class="section-desc">每个项目是一份独立的深度调研。点击卡片打开完整报告。按类别分组，方便按场景查找。</p>
""")
    if not grouped:
        html_parts.append('<p style="color:var(--text-secondary)">还没有项目。</p>')
    for cat, items in grouped:
        html_parts.append(f"""
  <div class="category-group">
    <div class="cat-title">
      <span>{escape(cat)}</span>
      <span class="cat-count">{len(items)} 份</span>
    </div>
    <div class="projects-grid">
""")
        for p in items:
            status_class = "badge-status-unknown"
            status_text = p["status"]
            if p["status"] in ("done", "completed"):
                status_class = "badge-status-done"
                status_text = "已完成"
            elif p["status"] == "failed":
                status_class = "badge-status-failed"
                status_text = "进行中"

            # 来源标签
            source_text = "本地项目" if p.get("source") == "research-os" else "桌面报告"

            link_html = ""
            if p["has_html"]:
                html_path = p["html_path"].replace("\\", "/")
                link_html = f'<a class="proj-link" href="file:///{html_path}" target="_blank">查看报告 →</a>'

            # 桌面报告没有 evidence_count，不显示证据条数 badge
            evidence_badge = ""
            if p.get("source") == "research-os" and p["evidence_count"] > 0:
                evidence_badge = f'<span class="badge badge-evidence">{p["evidence_count"]} 条证据</span>'

            html_parts.append(f"""
      <div class="project-card">
        <div class="proj-name">{escape(p['name'])}</div>
        <div class="proj-verdict">{escape(p['verdict'] or '（结论待提取）')}</div>
        <div class="proj-meta">
          <span class="badge badge-source">{escape(source_text)}</span>
          <span class="badge badge-depth">{escape(str(p['depth']))}</span>
          <span class="badge {status_class}">{escape(str(status_text))}</span>
          {evidence_badge}
        </div>
        {link_html}
      </div>
""")
        html_parts.append("""
    </div>
  </div>
""")
    html_parts.append("</div>")

    # ===== 系统演化 =====
    html_parts.append("""
<div class="section">
  <h2>系统怎么长大的</h2>
  <p class="section-desc">每个版本解决一个具体问题，不是预先设计出来的。</p>
  <div class="timeline">
""")
    for ev in SYSTEM_EVOLUTION:
        changes_html = "".join(f"<li>{escape(c)}</li>" for c in ev["changes"])
        html_parts.append(f"""
    <div class="timeline-item">
      <div class="tl-version">{escape(ev['version'])}</div>
      <div class="tl-title">{escape(ev['title'])}</div>
      <div class="tl-date">{escape(ev['date'])}</div>
      <div class="tl-why">{escape(ev['why'])}</div>
      <ul class="tl-changes">
        {changes_html}
      </ul>
    </div>
""")
    html_parts.append("""
  </div>
</div>
""")

    # ===== 设计哲学 =====
    html_parts.append("""
<div class="section">
  <h2>为什么这样设计</h2>
  <p class="section-desc">5 条核心原则，每条都来自实际踩过的坑。</p>
  <div class="philosophy-grid">
""")
    for ph in DESIGN_PHILOSOPHY:
        html_parts.append(f"""
    <div class="philosophy-card">
      <div class="ph-title">{escape(ph['title'])}</div>
      <div class="ph-desc">{escape(ph['desc'])}</div>
    </div>
""")
    html_parts.append("""
  </div>
</div>
""")

    # ===== Footer =====
    html_parts.append(f"""
<div class="footer">
  Research OS v0.5 · 生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}<br>
  深度调研工作台 · 让每条结论可溯源、可验证、可理解
</div>

</body>
</html>
""")

    # 写入
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(html_parts), encoding="utf-8")
    return output


# =====================================================================
# 6. CLI 入口
# =====================================================================

def build_dashboard(output_path: Path | None = None, copy_desktop: bool = False) -> Path:
    """生成看板 HTML。

    合并两个来源的项目：
    - research-os/projects/ 下的所有项目（带元数据）
    - 用户明确点名的桌面 HTML 报告（白名单，不扫所有桌面 HTML）
    """
    projects = scan_projects() + scan_named_desktop_reports()
    if output_path is None:
        output_path = RESEARCH_OS_ROOT / "dashboard.html"
    build_dashboard_html(projects, output_path)

    if copy_desktop:
        import shutil
        desktop = Path.home() / "Desktop"
        desktop_copy = desktop / "Research OS 看板.html"
        shutil.copy2(output_path, desktop_copy)
        print(f"已拷贝到桌面：{desktop_copy}")

    return output_path


if __name__ == "__main__":
    out = build_dashboard(copy_desktop=True)
    print(f"看板已生成：{out}")
