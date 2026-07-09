#!/usr/bin/env python3
"""Research OS intent_discovery — 意图探索骨架准备器（Dumb Tool）。

设计原则（Smart Agent. Dumb Tools.）：
  这个工具只做两件机械的事：
    1. 创建 intent_doc.json 骨架，含 3 轮探索的 prompt 模板
    2. 提供 commit_exploration_result() 供 Agent 写回探索结果

  工具不做的事（交给 Agent）：
    - 不调 LLM 跑探索（探索是语义动作，由 Agent 做）
    - 不判断意图是否"完成"（由 Agent 的实际调用驱动 status）
    - 不声称用了什么探索方法（避免伪信任）

  诚实标注：骨架创建后 status="skeleton_pending_agent"，
  exploration_history 为空列表。任何人看到此文件都知道探索尚未开始。

用法：
  # 工具创建骨架（ros new 时自动调用，或手动）
  python intent_discovery.py prepare <project_dir>

  # Agent 跑完某轮探索后提交结果（Agent 代码调用）
  from intent_discovery import commit_exploration_result
  commit_exploration_result(project_dir, round_num=1, result={...})

  # 标记探索完成（Agent 全部跑完后调用）
  from intent_discovery import finalize_exploration
  finalize_exploration(project_dir, stated_intent="...")
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# ============================================================
# 3 轮探索的 prompt 模板（供 Agent 使用，工具不执行）
# ============================================================

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
        "purpose": "找出嘴上说 vs 实际要的差距",
        "prompt": """你是意图探索员 Round 2。基于 Round 1 的记录，挖掘差距：

1. 用户嘴上说要 X，但实际可能要 Y——为什么？
2. 有没有"嘴上说要 X，实际 X 本身就是目的"的情况？
3. 这个调研的真实成本——如果不做会损失什么？

注意：不是每个任务都有 gap。如果字面意思就是真实意图，输出"无显著 gap"。
输出 JSON：
{{
  "stated_vs_real_gap": "...（可为'无显著 gap'）",
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

输出完整的 intent_doc 补充字段。""",
    },
]


# ============================================================
# 阶段 1：创建骨架（工具做）
# ============================================================

def prepare(project_dir: str | Path) -> Path:
    """创建 intent_doc.json 骨架。

    骨架特征（诚实标注）：
      - status = "skeleton_pending_agent"（探索尚未开始）
      - exploration_history = []（空列表，等 Agent 填）
      - stated_intent = ""（空，等 Agent 填）
      - prompt_templates = EXPLORATION_ROUNDS（供 Agent 使用的 prompt）

    工具不调 LLM，不做探索。骨架只是准备好了结构，等 Agent 来填。

    Args:
        project_dir: 项目目录路径

    Returns:
        intent_doc.json 的路径
    """
    project = Path(project_dir)

    intent_doc = {
        "schema_version": "research-os-intent-v1.0",
        "project_name": project.name,
        "status": "skeleton_pending_agent",
        "created_at": datetime.now().isoformat(),
        "stated_intent": "",
        "prompt_templates": EXPLORATION_ROUNDS,
        "exploration_history": [],
        "v07": {
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


# ============================================================
# 阶段 2：Agent 提交探索结果（Agent 调用）
# ============================================================

def commit_exploration_result(
    project_dir: str | Path,
    round_num: int,
    result: dict[str, Any],
) -> None:
    """Agent 跑完某轮探索后，把结果写回 intent_doc.json。

    工具只做"写入"，不做"探索"。Agent 必须显式调用此函数。

    Args:
        project_dir: 项目目录路径
        round_num: 第几轮（1/2/3）
        result: 探索结果（LLM 输出的 JSON）
    """
    project = Path(project_dir)
    intent_path = project / "00-task" / "intent_doc.json"

    if not intent_path.exists():
        raise FileNotFoundError(
            f"intent_doc.json 不存在于 {intent_path}。请先运行 prepare() 创建骨架。"
        )

    intent_doc = json.loads(intent_path.read_text(encoding="utf-8-sig"))

    # 更新 status
    intent_doc["status"] = "exploration_in_progress"

    # 找到对应轮次的 history 条目，填入 result
    history = intent_doc.get("exploration_history", [])
    found = False
    for entry in history:
        if entry.get("round") == round_num:
            entry["result"] = result
            entry["committed_at"] = datetime.now().isoformat()
            found = True
            break

    # 如果没找到（可能是新轮次），追加
    if not found:
        round_template = next(
            (r for r in EXPLORATION_ROUNDS if r["round"] == round_num),
            {"round": round_num, "name": f"Round {round_num}", "purpose": ""}
        )
        history.append({
            "round": round_num,
            "name": round_template["name"],
            "purpose": round_template["purpose"],
            "prompt_template": round_template.get("prompt", ""),
            "timestamp": datetime.now().isoformat(),
            "result": result,
            "committed_at": datetime.now().isoformat(),
        })

    intent_doc["exploration_history"] = history
    intent_path.write_text(json.dumps(intent_doc, ensure_ascii=False, indent=2), encoding="utf-8")


def finalize_exploration(
    project_dir: str | Path,
    stated_intent: str,
    concept_ladder_seed: list[str] | None = None,
    clarifying_questions: list[str] | None = None,
) -> None:
    """Agent 全部探索完成后，标记探索为已完成并固化最终意图。

    Args:
        project_dir: 项目目录路径
        stated_intent: 一句话核心意图（Agent 从 Round 3 固化的）
        concept_ladder_seed: 需要解释的术语列表
        clarifying_questions: 还需澄清的问题
    """
    project = Path(project_dir)
    intent_path = project / "00-task" / "intent_doc.json"

    if not intent_path.exists():
        raise FileNotFoundError(
            f"intent_doc.json 不存在于 {intent_path}。请先运行 prepare() 创建骨架。"
        )

    intent_doc = json.loads(intent_path.read_text(encoding="utf-8-sig"))

    # 验证所有轮次都有结果
    history = intent_doc.get("exploration_history", [])
    missing_rounds = []
    for r in EXPLORATION_ROUNDS:
        round_num = r["round"]
        entry = next((e for e in history if e.get("round") == round_num), None)
        if not entry or not entry.get("result"):
            missing_rounds.append(round_num)

    if missing_rounds:
        raise ValueError(
            f"无法标记探索完成——轮次 {missing_rounds} 尚无结果。"
            f"请先用 commit_exploration_result() 提交所有轮次的结果。"
        )

    intent_doc["status"] = "exploration_complete"
    intent_doc["stated_intent"] = stated_intent

    if concept_ladder_seed is not None:
        intent_doc.setdefault("v07", {})["concept_ladder_seed"] = concept_ladder_seed
    if clarifying_questions is not None:
        intent_doc.setdefault("v07", {})["clarifying_questions"] = clarifying_questions

    intent_path.write_text(json.dumps(intent_doc, ensure_ascii=False, indent=2), encoding="utf-8")


# ============================================================
# 向后兼容：discover() 保留为 prepare() 的别名
# ============================================================

def discover(project_dir: str | Path) -> Path:
    """向后兼容别名——等同于 prepare()。

    旧代码中 create_research_project.py 调用 discover()，
    保留此函数避免破坏现有调用。
    """
    return prepare(project_dir)


# ============================================================
# CLI 入口
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage:", file=sys.stderr)
        print("  intent_discovery.py prepare <project_dir>    # 创建骨架", file=sys.stderr)
        print("  intent_discovery.py discover <project_dir>   # 向后兼容别名", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    project_dir = sys.argv[2]

    if cmd in ("prepare", "discover"):
        out = prepare(project_dir)
        print(f"[ok] intent_doc.json 骨架已创建: {out}")
        print(f"[hint] status=skeleton_pending_agent，exploration_history 为空")
        print(f"[hint] Agent 应使用 prompt_templates 中的 prompt 跑 3 轮探索")
        print(f"[hint] 每轮完成后调用 commit_exploration_result() 写回结果")
        print(f"[hint] 全部完成后调用 finalize_exploration() 标记完成")
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
