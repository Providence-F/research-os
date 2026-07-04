#!/usr/bin/env python3
"""Research OS intent discovery (v0.5 重构后归并版本号，原 v0.9 模块).

v0.9 升级：融入 brainstorming skill 的结构化探索方法论。
discover 从"LLM 一次性 prompt 生成 intent_doc"升级成
"多轮结构化探索"——

Round 1: 宽泛探索（用户嘴上说什么）
Round 2: 挖差距（嘴上说 vs 实际要的）
Round 3: 固化（写成 agent 可解的问题说明书，融入 ljg-good-question）

每轮的探索记录都存到 intent_doc.json 的 exploration_history 字段，
让意图形成过程可审计——不是黑盒一次性输出。

用法：
  python intent_discovery.py discover <project_dir>
  → 读 task-card.md
  → 3 轮结构化探索
  → 输出 intent_doc.json（含 exploration_history）
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from datetime import datetime


# v0.9 新增：3 轮探索的 prompt 模板
EXPLORATION_ROUNDS = [
    {
        "round": 1,
        "name": "宽泛探索",
        "purpose": "把用户嘴上说的需求记下来，不做判断",
        "prompt": """你是意图探索员 Round 1。读 task-card.md，回答：
1. 用户字面上说要调研什么？
2. 服务什么决策？
3. 目标读者是谁？
4. 期望的最终行动是什么？

只记录，不评判。输出 JSON：
{{
  "stated_need": "...",
  "stated_decision": "...",
  "stated_reader": "...",
  "stated_action": "...",
  "round1_notes": "探索记录"
}}""",
    },
    {
        "round": 2,
        "name": "挖差距",
        "purpose": "找出嘴上说 vs 实际要的差距（这是 brainstorming 的核心）",
        "prompt": """你是意图探索员 Round 2。基于 Round 1 的记录，挖掘差距：

1. 用户嘴上说要 X，但实际可能要 Y——为什么？
   （参考 user_profile.json 的判断模式）
2. 有没有"嘴上说要 X，实际 X 本身就是目的"的情况？
   （参考过去调研的 intent_discovery 记录）
3. 这个调研的真实成本——如果不做会损失什么？

输出 JSON：
{{
  "stated_vs_real_gap": "...",
  "real_problem_hypothesis": "...",
  "cost_of_not_solving": "...",
  "round2_notes": "差距分析"
}}""",
    },
    {
        "round": 3,
        "name": "固化成问题说明书",
        "purpose": "把探索结果固化成 agent 可解、可验证、可批评的问题说明书",
        "prompt": """你是意图探索员 Round 3。基于 Round 1+2 的探索，固化成问题说明书：

1. 核心问题（一句话，agent 可解）
2. 可验证性：完成后怎么检查被答了？
3. 可批评性：什么证据能推翻问题前提？
4. agent 可解性：AI 拿到能独立推理吗？需要什么前置知识？
5. concept_ladder_seed：需要解释的 5-10 个术语
6. clarifying_questions：还需要澄清的问题（若有）

输出完整的 intent_doc.json（v0.9 schema）。""",
    },
]


def discover(project_dir: str | Path) -> Path:
    """v0.9 多轮结构化意图探索。

    流程：
      1. 读 task-card.md
      2. 跑 3 轮探索（实际由 LLM 执行，这里只准备结构）
      3. 输出 intent_doc.json（含 exploration_history）
    """
    project = Path(project_dir)
    task_card = project / "00-task" / "task-card.md"

    # v0.9: 记录探索历史（可审计）
    exploration_history = []
    for r in EXPLORATION_ROUNDS:
        exploration_history.append({
            "round": r["round"],
            "name": r["name"],
            "purpose": r["purpose"],
            "prompt_template": r["prompt"],
            "timestamp": datetime.now().isoformat(),
            "result": None,  # LLM 执行后填入
        })

    intent_doc = {
        "schema_version": "research-os-intent-v0.9",
        "project_name": project.name,
        "exploration_method": "brainstorming_integrated_3rounds",
        "exploration_history": exploration_history,
        "stated_intent": "",
        "confidence": "medium",
        "v09_features": {
            "core_generators_aware": True,
            "drill_down_required": True,
            "task_card_is_problem_spec": True,
        },
        "v07": {
            # 保留 v0.7 兼容字段
            "reader_model": {},
            "intent_tree": [],
            "concept_ladder_needed": True,
            "concept_ladder_seed": [],
            "clarifying_questions": [],
            "personalization_plan": {},
            "report_contract": {},
        },
    }

    out_path = project / "00-task" / "intent_doc.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(intent_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "discover":
        print("usage: intent_discovery.py discover <project_dir>", file=sys.stderr)
        sys.exit(1)
    out = discover(sys.argv[2])
    print(f"Wrote {out}")


# =====================================================================
# v0.10 反确认偏误：防止过度拟合历史 pattern
# =====================================================================
#
# intent_discovery 的第 2 轮（挖差距）默认找 gap，但不是每个任务都有 gap。
# 过度拟合历史 pattern 会导致：
# - 强行套用"嘴上要 X 实际要 Y"模板
# - 把字面意思就是真实意图的任务也框进 gap 模板
#
# 修复原则：
# 1. user_profile 的 intent_evolution 是参考，不是模板
# 2. 第 2 轮允许输出"无显著 gap"
# 3. gap 必须由本次任务的具体内容验证，不能直接套历史 pattern
# 4. intent_doc 的 gap 字段允许为 null

ALLOW_NO_GAP = True  # v0.10: 允许无 gap

def should_question_gap(gap_result: dict) -> bool:
    """如果 gap 跟历史 pattern 高度相似，质疑是否在套模板。"""
    if not gap_result.get("stated_vs_real_gap"):
        return False  # 已经是"无 gap"
    # 检查是否在套"广度覆盖 vs 单一决策"pattern
    gap_text = gap_result.get("stated_vs_real_gap", "")
    pattern_keywords = ["广度", "单一", "嘴上", "实际要"]
    matches = sum(1 for kw in pattern_keywords if kw in gap_text)
    return matches >= 3  # 命中 3+ 关键词，可能是套模板
