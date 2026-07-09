#!/usr/bin/env python3
"""Research OS topic router — Dumb Router.

设计原则（Smart Agent. Dumb Tools.）：
  这个工具只做一件机械的事：按 research_type 返回 preset 配置。
  不做关键词路由（Agent 显式选择 research_mode）。
  不硬编码 core_generators（Agent 用 ljg-rank 现场降秩，写入 research-plan.md）。
  不做项目名语义联想（工具不基于名称做推断）。

  core_generators 留空，由 Agent 在调研方案阶段用 ljg-rank skill 降秩产出，
  写入 research-plan.md 的 ## 核心生成器 章节，工具从该章节读取。
"""
from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path


BASE_MODULES = ["hero", "summary_cards", "full_report", "appendix_fold"]

ROUTE_PRESETS = {
    "narrative": {
        "research_mode": "evidence_intelligence",
        "view_type": "narrative_report",
        "visual_modules": ["hero", "full_report", "appendix_fold"],
    },
    "thinking_decision": {
        "research_mode": "thinking_decision",
        "view_type": "decision_board",
        "visual_modules": [
            "hero", "summary_cards", "object_cards", "strategy_tabs",
            "comparison_matrix", "full_report", "appendix_fold",
        ],
    },
    "opportunity_map": {
        "research_mode": "opportunity_map",
        "view_type": "ranked_map",
        "visual_modules": [
            "hero", "summary_cards", "object_cards", "filters", "detail_modal",
            "filterable_table", "full_report", "appendix_fold",
        ],
    },
    "product_teardown": {
        "research_mode": "product_teardown",
        "view_type": "product_teardown_view",
        "visual_modules": [
            "hero", "summary_cards", "object_cards", "focus_tabs",
            "comparison_matrix", "full_report", "appendix_fold",
        ],
    },
    "user_voice": {
        "research_mode": "user_voice",
        "view_type": "card_dashboard",
        "visual_modules": [
            "hero", "summary_cards", "object_cards", "filters",
            "comparison_matrix", "full_report", "appendix_fold",
        ],
    },
    "career_strategy": {
        "research_mode": "career_strategy",
        "view_type": "decision_board",
        "visual_modules": [
            "hero", "summary_cards", "object_cards", "strategy_tabs",
            "comparison_matrix", "full_report", "appendix_fold",
        ],
    },
}

# research_type -> preset 的机械映射（不做语义判断）
MODE_BY_TYPE = {
    "product": "product_teardown",
    "competitor": "product_teardown",
    "user-research": "user_voice",
    "portfolio": "thinking_decision",
    "company-jd": "career_strategy",
    "industry": "opportunity_map",
    "topic": "narrative",
    "mixed": "narrative",
}


def infer_route(project_name: str, research_type: str, depth: str) -> dict:
    """按 research_type 返回 preset，不做语义判断。

    core_generators 留空——由 Agent 在 research-plan.md 中用 ljg-rank 降秩产出。
    工具不硬编码生成器，不做关键词路由，不做项目名联想。
    """
    rtype = research_type or "mixed"
    preset_key = MODE_BY_TYPE.get(rtype, "narrative")
    route = deepcopy(ROUTE_PRESETS[preset_key])

    # core_generators 留空，由 Agent 降秩产出
    route["core_generators"] = []

    # R0/R1 深度简化视觉模块
    if depth in ("R0", "R1") and route["view_type"] != "narrative_report":
        route["visual_modules"] = [m for m in route["visual_modules"] if m in BASE_MODULES]
    return route


def read_core_generators_from_plan(project: Path) -> list[str]:
    """从 research-plan.md 的 ## 核心生成器 章节读取 Agent 降秩的结果。

    这是 dumb 的机械读取——不判断生成器对不对，只提取列表。
    Agent 负责降秩的质量，工具负责把结果传递给需要的地方。
    """
    plan_path = project / "01-plan" / "research-plan.md"
    if not plan_path.exists():
        return []

    text = plan_path.read_text(encoding="utf-8-sig")
    # 提取 ## 核心生成器 到下一个 ## 之间的内容
    pattern = r"^##\s+核心生成器\s*\n(.*?)(?=^##\s|\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    if not match:
        return []

    section = match.group(1)
    # 提取列表项（- 开头的行）
    generators = []
    for line in section.splitlines():
        line = line.strip()
        if line.startswith("- "):
            # 去掉前缀和可能的尾注
            item = line[2:].strip()
            # 去掉"（待填）"等占位符
            if "（待填）" not in item and item:
                generators.append(item)
    return generators


def apply_route_overrides(route: dict, overrides: dict | None = None) -> dict:
    if not overrides:
        return route
    for k, v in overrides.items():
        if k == "core_generators" and "core_generators" in route:
            # merge instead of replace
            route["core_generators"] = list(set(route["core_generators"] + v))
        else:
            route[k] = v
    return route


def route_research(
    project_name: str,
    research_type: str,
    depth: str,
    overrides: dict | None = None,
) -> dict:
    """推断路由 + 应用覆盖"""
    return apply_route_overrides(infer_route(project_name, research_type, depth), overrides)


def build_empty_view_model(project_name: str, route: dict) -> dict:
    """构建空 view-model.json 模板"""
    return {
        "schema_version": "research-os-view-model-v0.5",
        "project_name": project_name,
        "research_mode": route.get("research_mode", "evidence_intelligence"),
        "view_type": route.get("view_type", "narrative_report"),
        "visual_modules": route.get("visual_modules", []),
        "core_generators": route.get("core_generators", []),
        "hero": {
            "verdict": "",
            "summary": "",
            "meta": [],
        },
        "summary_cards": [],
        "object_cards": [],
        "strategy_tabs": [],
        "comparison_matrix": {
            "columns": [],
            "rows": [],
        },
        "concept_ladder": [],
    }
