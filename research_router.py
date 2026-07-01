#!/usr/bin/env python3
"""Research OS topic router.

The router keeps templates from multiplying by deciding the research mode,
view type, and visual modules before project execution starts.
"""

from __future__ import annotations

from copy import deepcopy


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
            "hero",
            "summary_cards",
            "object_cards",
            "strategy_tabs",
            "comparison_matrix",
            "full_report",
            "appendix_fold",
        ],
    },
    "opportunity_map": {
        "research_mode": "opportunity_map",
        "view_type": "ranked_map",
        "visual_modules": [
            "hero",
            "summary_cards",
            "object_cards",
            "filters",
            "detail_modal",
            "filterable_table",
            "full_report",
            "appendix_fold",
        ],
    },
    "product_teardown": {
        "research_mode": "product_teardown",
        "view_type": "product_teardown_view",
        "visual_modules": [
            "hero",
            "summary_cards",
            "object_cards",
            "focus_tabs",
            "comparison_matrix",
            "full_report",
            "appendix_fold",
        ],
    },
    "user_voice": {
        "research_mode": "user_voice",
        "view_type": "card_dashboard",
        "visual_modules": [
            "hero",
            "summary_cards",
            "object_cards",
            "filters",
            "comparison_matrix",
            "full_report",
            "appendix_fold",
        ],
    },
    "career_strategy": {
        "research_mode": "career_strategy",
        "view_type": "decision_board",
        "visual_modules": [
            "hero",
            "summary_cards",
            "object_cards",
            "strategy_tabs",
            "comparison_matrix",
            "full_report",
            "appendix_fold",
        ],
    },
}

DECISION_KEYWORDS = [
    "选题",
    "导师",
    "毕业论文",
    "论文",
    "职业",
    "求职",
    "转行",
    "作品集",
    "策略",
    "要不要",
    "是否值得",
]

OPPORTUNITY_KEYWORDS = [
    "地图",
    "榜单",
    "候选池",
    "展商",
    "公司清单",
    "秋招",
    "投递",
    "岗位",
]

PRODUCT_KEYWORDS = ["产品", "机制", "拆解", "竞品", "体验", "增长", "商业模式"]

USER_VOICE_KEYWORDS = ["用户", "访谈", "评论", "需求", "痛点", "原声"]


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


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


def infer_route(project_name: str, research_type: str, depth: str) -> dict:
    name = project_name or ""
    text = f"{name} {research_type or ''}".lower()
    rtype = research_type or "mixed"

    preset_key = MODE_BY_TYPE.get(rtype, "narrative")

    if _contains_any(text, DECISION_KEYWORDS):
        preset_key = "thinking_decision"
    elif _contains_any(text, OPPORTUNITY_KEYWORDS):
        preset_key = "opportunity_map"
    elif _contains_any(text, PRODUCT_KEYWORDS):
        preset_key = "product_teardown"
    elif _contains_any(text, USER_VOICE_KEYWORDS):
        preset_key = "user_voice"

    route = deepcopy(ROUTE_PRESETS[preset_key])
    if depth in ("R0", "R1") and route["view_type"] != "narrative_report":
        route["visual_modules"] = [m for m in route["visual_modules"] if m in BASE_MODULES]
    return route


def apply_route_overrides(route: dict, overrides: dict | None = None) -> dict:
    if not overrides:
        return route
    out = deepcopy(route)
    for key in ("research_mode", "view_type", "visual_modules"):
        value = overrides.get(key)
        if value:
            out[key] = value
    return out


def route_research(
    project_name: str,
    research_type: str,
    depth: str,
    overrides: dict | None = None,
) -> dict:
    return apply_route_overrides(infer_route(project_name, research_type, depth), overrides)


def build_empty_view_model(project_name: str, route: dict) -> dict:
    return {
        "schema_version": "research-os-view-model-v0.2",
        "project_name": project_name,
        "research_mode": route.get("research_mode", "evidence_intelligence"),
        "view_type": route.get("view_type", "narrative_report"),
        "visual_modules": route.get("visual_modules", []),
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
        "filterable_table": {
            "filters": [],
            "rows": [],
        },
    }
