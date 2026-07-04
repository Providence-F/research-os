#!/usr/bin/env python3
"""
sync_dashboard.py - 从 research-os 真实数据同步到 dashboard

用法:
    cd research-os
    python scripts/sync_dashboard.py

功能:
    1. 扫描 projects/ 下所有项目
    2. 读取 research_state.json 和 final-report.md
    3. 生成 dashboard/src/data/projects.ts
    4. 读取 CHANGELOG.md 生成 dashboard/src/data/versions.ts
    5. 更新 dashboard/src/data/stats.ts 中的计数
"""

import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime

# 路径配置
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
PROJECTS_DIR = REPO_ROOT / "projects"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
DASHBOARD_DATA_DIR = REPO_ROOT / "dashboard" / "src" / "data"


def scan_projects():
    """扫描所有项目，返回项目列表"""
    projects = []
    if not PROJECTS_DIR.exists():
        print(f"Warning: {PROJECTS_DIR} does not exist")
        return projects

    for project_dir in sorted(PROJECTS_DIR.iterdir()):
        if not project_dir.is_dir() or project_dir.name.startswith("."):
            continue

        # 读取 research_state.json
        state_path = project_dir / "research_state.json"
        state = {}
        if state_path.exists():
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)

        # 检查是否有 HTML 产出
        html_path = project_dir / "08-html" / "index.html"
        has_html = html_path.exists()

        # 读取 final-report.md
        report_path = project_dir / "07-output" / "final-report.md"
        report_content = ""
        if report_path.exists():
            with open(report_path, "r", encoding="utf-8") as f:
                report_content = f.read()

        # 提取摘要和发现
        summary, key_findings = extract_from_report(report_content)

        # 推断分类（需要根据项目名判断，这里用简单规则）
        category = infer_category(project_dir.name)

        # 读取 delivery_status（如果 research_state.json 中有标记，使用之；否则默认 trae）
        delivery_status = state.get("delivery_status", "trae")

        # 提取 version（去掉 "research-os-state-" 前缀）
        raw_version = state.get("schema_version", "v0.5")
        version = raw_version.replace("research-os-state-", "") if isinstance(raw_version, str) else "v0.5"

        project = {
            "id": project_dir.name.replace(" ", "-").lower(),
            "name": project_dir.name,
            "category": category,
            "version": version,
            "deliveryStatus": delivery_status,
            "summary": summary or project_dir.name,
            "htmlPath": f"projects/{project_dir.name}/08-html/index.html" if has_html else None,
            "relations": [],
            "date": state.get("last_updated", ""),
            "overview": summary,
            "keyTopics": [],
            "keyFindings": key_findings,
        }
        projects.append(project)

    # 追加 Claude Code 时代产出（不在 research-os/projects/ 中的历史项目）
    projects.extend(get_extra_projects())

    return projects


def get_extra_projects():
    """返回 Claude Code 时代产出（不在 research-os/projects/ 中的历史项目）"""
    return [
        {
            "id": "memtensor-memos-产品深度拆解",
            "name": "MemTensor 与 MemOS 产品深度拆解",
            "category": "product",
            "version": "v0.4",
            "deliveryStatus": "claude-code",
            "summary": "对 MemTensor 公司及其核心产品 MemOS 做架构、记忆机制、技术栈、商业模式的深度拆解。",
            "htmlPath": None,
            "relations": [],
            "date": "2026-06-26",
            "overview": "对 MemTensor 公司及其核心产品 MemOS 做架构、记忆机制、技术栈、商业模式的深度拆解。覆盖核心记忆机制、产品边界、技术选型和对个人 AI 产品的启发。",
            "keyTopics": ["记忆机制", "产品架构", "技术栈拆解", "商业模式"],
            "keyFindings": [
                "MemOS 采用三层记忆架构：短期/工作记忆 + 长期记忆 + 核心记忆",
                "核心记忆机制是 MemTensor 区别于其他记忆产品的关键",
                "技术栈以 Python + 向量数据库为主，无重前端依赖",
            ],
        },
        {
            "id": "memos-核心记忆机制科普拆解",
            "name": "MemOS 核心记忆机制科普拆解",
            "category": "product",
            "version": "v0.4",
            "deliveryStatus": "claude-code",
            "summary": "对 MemOS 核心记忆机制做科普拆解，用物理学语言翻译记忆机制原理。",
            "htmlPath": None,
            "relations": [],
            "date": "2026-06-26",
            "overview": "对 MemOS 核心记忆机制做科普拆解，用物理学语言翻译记忆机制原理，让非技术背景读者也能理解。",
            "keyTopics": ["核心记忆", "记忆编码", "记忆检索", "记忆衰减"],
            "keyFindings": [
                "MemOS 的核心记忆借鉴海马体机制，区分情景记忆和语义记忆",
                "记忆编码采用多模态融合 + 时间戳锚定",
                "记忆检索用注意力机制做相关性排序",
            ],
        },
        {
            "id": "physics-thesis-topic-advisor",
            "name": "物理学师范毕业论文选题与导师推荐报告",
            "category": "personal",
            "version": "v0.4",
            "deliveryStatus": "claude-code",
            "summary": "为物理学师范本科生做毕业论文选题推荐和潜在导师匹配报告。",
            "htmlPath": None,
            "relations": [],
            "date": "2026-06-26",
            "overview": "为物理学师范本科生做毕业论文选题推荐和潜在导师匹配报告。基于用户背景画像（物理教育 + AI 产品方向）做选题优先级排序和导师方向匹配。",
            "keyTopics": ["选题方向", "导师匹配", "物理学教育", "AI 与物理交叉"],
            "keyFindings": [
                "选题方向 1：AI 辅助物理教学（与用户兴趣强匹配）",
                "选题方向 2：物理直觉在 AI 模型中的应用（与用户长期目标强匹配）",
                "导师匹配基于研究方向重叠度 + 学术影响力 + 招生意向",
            ],
        },
        {
            "id": "kai-fde-portfolio-priority",
            "name": "Kai 下一阶段 AI 产品 FDE 作品集方向优先级研究",
            "category": "personal",
            "version": "v0.4",
            "deliveryStatus": "claude-code",
            "summary": "为用户 Kai 做 AI 产品方向、FDE 作品集方向的优先级排序研究。",
            "htmlPath": None,
            "relations": [],
            "date": "2026-06-26",
            "overview": "为用户 Kai 做 AI 产品方向、FDE（Field Deployment Engineer）作品集方向的优先级排序研究。基于用户兴趣、市场机会、技能匹配做综合排序。",
            "keyTopics": ["FDE 方向", "作品集方向", "AI 产品方向", "优先级排序"],
            "keyFindings": [
                "推荐方向 1：AI Developer Tools FDE（与用户技术栈强匹配）",
                "推荐方向 2：AI Education 产品 FDE（与用户物理教育背景匹配）",
                "作品集应该突出技术深度 + 用户洞察双能力",
            ],
        },
    ]


def extract_from_report(content):
    """从 final-report.md 提取摘要和核心发现"""
    if not content:
        return "", []

    # 提取第一段非标题文本作为摘要
    lines = content.split("\n")
    summary_lines = []
    for line in lines[1:]:  # 跳过第一个标题
        line = line.strip()
        if line and not line.startswith("#"):
            summary_lines.append(line)
            if len(summary_lines) >= 3:
                break
    summary = " ".join(summary_lines)[:200]

    # 提取核心发现（查找"发现""结论"等关键词附近的列表项）
    findings = []
    in_findings = False
    for line in lines:
        if any(kw in line for kw in ["发现", "结论", "关键", "核心"]):
            in_findings = True
            continue
        if in_findings and line.strip().startswith("-"):
            findings.append(line.strip().lstrip("- ").strip())
            if len(findings) >= 4:
                break
        elif in_findings and line.strip() and not line.strip().startswith("-"):
            in_findings = False

    return summary, findings


def infer_category(project_name):
    """根据项目名推断分类"""
    name_lower = project_name.lower()

    # 个人决策（优先匹配，避免"参访"等被误归类）
    personal_keywords = ["amd", "参访", "论文", "毕业", "kai", "作品集", "fde", "导师"]
    if any(kw in name_lower for kw in personal_keywords):
        return "personal"

    # 产品拆解（公司/产品名）
    product_keywords = ["dealism", "tezign", "特赞", "mizzenai", "memtensor", "memos", "产品"]
    if any(kw in name_lower for kw in product_keywords):
        return "product"

    # 行业赛道
    industry_keywords = ["deepseek", "芯片", "行业", "岗位", "jd"]
    if any(kw in name_lower for kw in industry_keywords):
        return "industry"

    # 技术深度（注意：开源深度调研系统归为产品，不是 tech）
    tech_keywords = ["agent", "llm", "opencode", "源码"]
    if any(kw in name_lower for kw in tech_keywords):
        # 但 "开源深度调研系统" 归为产品
        if "深度调研系统" in project_name or "横向拆解" in project_name:
            return "product"
        return "tech"

    # 横向拆解深度调研系统的归为产品
    if "深度调研系统" in project_name or "开源深度调研" in project_name:
        return "product"

    # 系统自身
    system_keywords = ["前端", "设计", "dashboard", "看板"]
    if any(kw in name_lower for kw in system_keywords):
        return "system"

    return "system"  # 默认


def generate_projects_ts(projects):
    """生成 projects.ts 文件"""
    content = """// AUTO-GENERATED by scripts/sync_dashboard.py
// Do not edit manually - run sync script to update

import type { Project, CategoryMeta, ProjectCategory, DeliveryStatus } from "./types";

// 5 类主体元信息
export const categoryMeta: Record<ProjectCategory, CategoryMeta> = {
  product: {
    id: "product",
    name: "产品拆解",
    color: "#6a9bcc",
    description: "对单一产品做架构、技术栈、商业模式的深度拆解",
  },
  industry: {
    id: "industry",
    name: "行业赛道",
    color: "#c97a4a",
    description: "对行业趋势、岗位需求、产业链的横向调研",
  },
  tech: {
    id: "tech",
    name: "技术深度",
    color: "#5b8c7e",
    description: "对开源框架、LLM、源码的技术原理拆解",
  },
  personal: {
    id: "personal",
    name: "个人决策",
    color: "#7a5cb0",
    description: "辅助个人重大决策：选题、求职、参访",
  },
  system: {
    id: "system",
    name: "系统自身",
    color: "#b0aea5",
    description: "对 Research OS 自身的设计决策和迭代",
  },
};

export const categoryOrder: ProjectCategory[] = [
  "product", "industry", "personal", "tech", "system",
];

export const projects: Project[] = [
"""

    for p in projects:
        content += "  {\n"
        content += f'    id: "{p["id"]}",\n'
        content += f'    name: "{p["name"]}",\n'
        content += f'    category: "{p["category"]}",\n'
        content += f'    version: "{p["version"]}",\n'
        content += f'    deliveryStatus: "{p["deliveryStatus"]}",\n'
        # 转义字符串中的特殊字符
        summary = p["summary"].replace('"', '\\"').replace("\n", " ")
        content += f'    summary: "{summary}",\n'
        if p.get("htmlPath"):
            content += f'    htmlPath: "{p["htmlPath"]}",\n'
        content += f'    relations: {json.dumps(p["relations"])},\n'
        if p.get("date"):
            content += f'    date: "{p["date"]}",\n'
        if p.get("overview"):
            overview = p["overview"].replace('"', '\\"').replace("\n", " ")
            content += f'    overview: "{overview}",\n'
        if p.get("keyTopics"):
            content += f'    keyTopics: {json.dumps(p["keyTopics"], ensure_ascii=False)},\n'
        if p.get("keyFindings"):
            findings = [f.replace('"', '\\"').replace("\n", " ") for f in p["keyFindings"]]
            content += f'    keyFindings: {json.dumps(findings, ensure_ascii=False)},\n'
        content += "  },\n"

    content += """];

// 工具：按分类分组
export function groupByCategory(list: Project[]): Record<ProjectCategory, Project[]> {
  const groups: Record<string, Project[]> = {};
  for (const cat of categoryOrder) {
    groups[cat] = list.filter((p) => p.category === cat);
  }
  return groups as Record<ProjectCategory, Project[]>;
}

// 工具：按 id 查找
export function findById(id: string, list: Project[] = projects): Project | undefined {
  return list.find((p) => p.id === id);
}

// 工具：获取关联项目
export function getRelated(project: Project, list: Project[] = projects): Project[] {
  return project.relations
    .map((id) => findById(id, list))
    .filter((p): p is Project => p !== undefined);
}

// 交付状态中文标签
export const deliveryStatusLabel: Record<DeliveryStatus, string> = {
  trae: "Trae",
  "claude-code": "Claude Code",
};
"""

    return content


def parse_changelog():
    """解析 CHANGELOG.md，返回版本列表"""
    if not CHANGELOG_PATH.exists():
        return []

    with open(CHANGELOG_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    versions = []
    # 匹配 ## [vX.X] 或 ## vX.X 格式
    pattern = r"^##\s*\[?(v[\d.]+)\]?\s*(.*)$"
    current_version = None
    current_date = ""
    current_changes = []

    for line in content.split("\n"):
        match = re.match(pattern, line)
        if match:
            if current_version:
                versions.append({
                    "id": current_version,
                    "date": current_date,
                    "summary": current_changes[0] if current_changes else "",
                    "changes": current_changes[1:] if len(current_changes) > 1 else [],
                })
            current_version = match.group(1)
            current_date = match.group(2).strip() or ""
            current_changes = []
        elif current_version and line.strip():
            if line.strip().startswith("-"):
                current_changes.append(line.strip().lstrip("- ").strip())

    if current_version:
        versions.append({
            "id": current_version,
            "date": current_date,
            "summary": current_changes[0] if current_changes else "",
            "changes": current_changes[1:] if len(current_changes) > 1 else [],
        })

    return versions


def generate_versions_ts(versions):
    """生成 versions.ts 文件"""
    content = """// AUTO-GENERATED by scripts/sync_dashboard.py

import type { Version } from "./types";

export const versions: Version[] = [
"""

    # 第一个版本（最新）自动标记为 isCurrent
    for idx, v in enumerate(versions):
        content += "  {\n"
        content += f'    id: "{v["id"]}",\n'
        content += f'    date: "{v["date"]}",\n'
        summary = v["summary"].replace('"', '\\"')
        content += f'    summary: "{summary}",\n'
        content += f'    changes: {json.dumps(v["changes"], ensure_ascii=False)},\n'
        if idx == 0:
            content += "    isCurrent: true,\n"
        if v["id"] == "v0.5":
            content += "    isRollback: true,\n"
        content += "  },\n"

    content += "];\n"
    return content


def generate_stats_ts(project_count, version_count, current_version="v0.7.1"):
    """生成 stats.ts 文件"""
    content = f"""// AUTO-GENERATED by scripts/sync_dashboard.py

import type {{ Stats }} from "./types";

export const stats: Stats = {{
  hero: {{
    versions: {version_count},
    outputs: {project_count},
    categories: 5,
    currentVersion: "{current_version}",
  }},
}};

export const kpiBlocks = [
  {{ label: "调研产出", value: {project_count}, suffix: "个" }},
  {{ label: "版本迭代", value: {version_count}, suffix: "个" }},
  {{ label: "主体分类", value: 5, suffix: "类" }},
  {{ label: "当前版本", value: "{current_version}", suffix: "" }},
] as const;

export const systemFeatures = [
  {{
    title: "多步骤工作流",
    description: "13 个源码模块化的调研流程，从意图挖掘到读者模拟的完整链路",
  }},
  {{
    title: "意图挖掘",
    description: "从用户描述中反推真实问题，不是直接回答表面问题",
  }},
  {{
    title: "读者模拟",
    description: "AI 写完后换角色当读者自检，模拟真实读者的理解过程",
  }},
  {{
    title: "版本回退",
    description: "从 v0.10 过度工程化回退到 v0.5 做减法，保留核心流程",
  }},
];

export const systemDefinition =
  "一套个人调研系统，用多步骤工作流替代单次对话，让 AI 同时当作者和读者，产出可交付的 HTML 报告。";
"""
    return content


def main():
    print("=" * 60)
    print("Research OS Dashboard Sync")
    print("=" * 60)

    # 1. 扫描项目
    print("\n[1/4] Scanning projects...")
    projects = scan_projects()
    print(f"  Found {len(projects)} projects")

    # 2. 解析 CHANGELOG
    print("\n[2/4] Parsing CHANGELOG...")
    versions = parse_changelog()
    print(f"  Found {len(versions)} versions")

    # 3. 生成 TypeScript 文件
    print("\n[3/4] Generating TypeScript files...")

    # 确保目录存在
    DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)

    projects_ts = generate_projects_ts(projects)
    (DASHBOARD_DATA_DIR / "projects.ts").write_text(projects_ts, encoding="utf-8")
    print(f"  Generated projects.ts ({len(projects)} projects)")

    versions_ts = generate_versions_ts(versions)
    (DASHBOARD_DATA_DIR / "versions.ts").write_text(versions_ts, encoding="utf-8")
    print(f"  Generated versions.ts ({len(versions)} versions)")

    # 取最新版本号（versions 列表第一个）作为当前版本
    current_version = versions[0]["id"] if versions else "v0.7.1"
    stats_ts = generate_stats_ts(len(projects), len(versions), current_version)
    (DASHBOARD_DATA_DIR / "stats.ts").write_text(stats_ts, encoding="utf-8")
    print(f"  Generated stats.ts (current: {current_version})")

    # 4. 完成
    print("\n[4/4] Done!")
    print(f"\nDashboard data synced successfully.")
    print(f"  Projects: {len(projects)}")
    print(f"  Versions: {len(versions)}")
    print(f"\nNext step: cd dashboard && npm run build")


if __name__ == "__main__":
    main()
