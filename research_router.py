#!/usr/bin/env python3
"""Research OS topic router (v0.9).

v0.9 升级：融入 ljg-rank"降秩"方法论。
不再只看关键词决定 research_mode，而是分析
"撑着这个调研对象的几根独立的力"（core_generators）。

router 现在输出两部分：
  1. research_mode / view_type（沿用 v0.8）
  2. core_generators: 这个调研对象背后的核心生成器列表
     （借鉴 ljg-rank：把现象砍到不可再少的生成器，
      砍完能把现象一个个生回来才算数）

core_generators 决定：
  - concept_ladder_seed（概念阶梯种子）
  - comparison_matrix 的维度
  - 报告的核心章节
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

# v0.9 新增：每种 research_mode 的默认 core_generators
# 借鉴 ljg-rank：把领域砍到不可再少的生成器
# 这些是"撑着这个调研类型的核心维度"——不是关键词，是结构
DEFAULT_CORE_GENERATORS = {
    "evidence_intelligence": ["事实可靠性", "来源独立性", "时间新鲜度"],
    "thinking_decision": ["价值大小", "成本风险", "时间窗口", "可逆性"],
    "opportunity_map": ["机会规模", "门槛高度", "增长趋势", "竞争密度"],
    "product_teardown": ["架构哲学", "执行引擎", "差异化机制", "工程成熟度"],
    "user_voice": ["核心痛点", "使用场景", "满意度信号", "未满足需求"],
    "career_strategy": ["背景匹配度", "赛道增长", "技能可迁移性", "时机窗口"],
}

# 关键词仍保留作为 fallback（v0.8 兼容）
DECISION_KEYWORDS = ["选题", "导师", "毕业论文", "论文", "职业", "求职", "转行",
                     "作品集", "策略", "要不要", "是否值得"]
OPPORTUNITY_KEYWORDS = ["地图", "榜单", "候选池", "展商", "公司清单", "秋招", "投递", "岗位"]
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
    """v0.9: 推断路由 + core_generators。

    流程：
      1. 先按 research_type 给默认 preset（v0.8 兼容）
      2. 关键词 override（v0.8 兼容）
      3. v0.9 新增：根据 research_mode 取默认 core_generators
      4. v0.9 新增：如果 project_name 含特定信号，调整 generators
    """
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

    # v0.9 新增：注入 core_generators
    research_mode = route["research_mode"]
    generators = list(DEFAULT_CORE_GENERATORS.get(research_mode, []))

    # v0.9 新增：项目名含特定信号时调整 generators
    if "开源" in name or "github" in name.lower():
        # 开源项目拆解：加"社区活跃度""复现可行性"
        if "社区活跃度" not in generators:
            generators.append("社区活跃度")
        if "复现可行性" not in generators:
            generators.append("复现可行性")
    if "深度调研" in name or "调研系统" in name:
        # 调研系统拆解：加"引用溯源""证据留存"
        if "引用溯源" not in generators:
            generators.append("引用溯源")
        if "证据留存" not in generators:
            generators.append("证据留存")

    route["core_generators"] = generators

    if depth in ("R0", "R1") and route["view_type"] != "narrative_report":
        route["visual_modules"] = [m for m in route["visual_modules"] if m in BASE_MODULES]
    return route


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
    """v0.9: 推断路由 + 应用覆盖"""
    return apply_route_overrides(infer_route(project_name, research_type, depth), overrides)


def build_empty_view_model(project_name: str, route: dict) -> dict:
    """v0.9: 构建空 view-model.json 模板（含 core_generators）"""
    return {
        "schema_version": "research-os-view-model-v0.5",
        "project_name": project_name,
        "research_mode": route.get("research_mode", "evidence_intelligence"),
        "view_type": route.get("view_type", "narrative_report"),
        "visual_modules": route.get("visual_modules", []),
        "core_generators": route.get("core_generators", []),  # v0.9 新增
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
        "concept_ladder": [],  # v0.9: 由 concept_ladder_helper.py 填充
    }
