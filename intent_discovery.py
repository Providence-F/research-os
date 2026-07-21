#!/usr/bin/env python3
"""Research OS intent_discovery — 意图探索骨架准备器（Dumb Tool，v2.0）。

设计原则（Smart Agent. Dumb Tools.）：
  这个工具只做机械的、可验证的事：
    1. 创建 intent_doc.json 骨架（v2.0 schema，含 5 轮探索的 prompt 模板）
    2. 提供 commit_exploration_result() 供 Agent 逐轮写回探索结果
    3. finalize_exploration() 做硬校验（轮次齐/意图树结构/候选路径/澄清上限/成功标准）
    4. revise_intent_tree() 支撑反僵化修订（旧树快照追加 revision_history，禁原地改）

  v2.0 变更：
    - 探索轮次 3 → 5：R3 意图树构建、R4 路径生成为新增；原 R3 演进为 R5 问题说明书
    - schema_version 升级为 research-os-intent-v2.0
    - v07 新增 candidate_paths / success_criteria / revision_history
    - finalize_exploration() 硬校验升级：意图树分层结构（≥1 个 L1_meta、≥3 个
      L2_mechanism）、parent_id 引用完整性、候选路径 ≥2 且恰 1 选中、未选中必有
      pruned_reason、blocks_plan 澄清问题 ≤3、success_criteria 非空
    - finalize_exploration() 签名扩展：intent_tree / candidate_paths /
      success_criteria 写入 v07
    - 新增 revise_intent_tree()：意图树是活的，修订留痕；major_change=True 时返回
      requires_direction_reselection 标记，提示 Agent 需重过 step_1.5 方向选择
      （工具只标记不强制）
    - 意图产出从"用户要什么"的记录升级为"调研该怎么打"的作战地图
      （协议见 templates/24-意图拆解协议.md）

  工具不做的事（交给 Agent）：
    - 不调 LLM 跑探索（探索是语义动作，由 Agent 做）
    - 不判断意图树内容是否合理（只校验结构完整性，语义判断归 Agent）
    - 不强制方向重选（major_change 只做标记，重过 step_1.5 是 Agent 的责任）
    - 不声称用了什么探索方法（避免伪信任）

  诚实标注：骨架创建后 status="skeleton_pending_agent"，
  exploration_history 为空列表。任何人看到此文件都知道探索尚未开始。

用法：
  # 工具创建骨架（ros new 时自动调用，或手动）
  python intent_discovery.py prepare <project_dir>

  # Agent 跑完某轮探索后提交结果（Agent 代码调用）
  from intent_discovery import commit_exploration_result
  commit_exploration_result(project_dir, round_num=1, result={...})

  # 标记探索完成（Agent 全部 5 轮跑完后调用，硬校验通过才生效）
  from intent_discovery import finalize_exploration
  finalize_exploration(project_dir, stated_intent="...", intent_tree=[...],
                       candidate_paths=[...], success_criteria="...")

  # 调研中途修订意图树（反僵化条款）
  from intent_discovery import revise_intent_tree
  revise_intent_tree(project_dir, new_tree=[...], revision_reason="...",
                     triggering_evidence="...", major_change=False)
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# ============================================================
# 5 轮探索的 prompt 模板（供 Agent 使用，工具不执行）
# ============================================================

EXPLORATION_ROUNDS = [
    {
        "round": 1,
        "name": "字面记录",
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
        "name": "差距挖掘",
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
        "name": "意图树构建",
        "purpose": "把意图拆解成问题树——本次调研的作战地图",
        "prompt": """你是意图探索员 Round 3。基于 Round 1+2 的记录，把意图拆解成一棵问题树（intent_tree）——这是本次调研的作战地图。

树的分层（对应认知深度）：
- L0 根问题：这次调研到底要回答什么（1 个节点，id=Q0，parent_id=null）
- L1 元问题：这个问题问对了吗、该投入多少（≥1 个节点）
- L2 机制问题：对象怎么运作（≥3 个节点）
- L3 证据问题：支撑机制判断的事实
- L4 反问题：什么证据会推翻当前框架

示例（拆解 Manus）：
- L0: Manus 的产品机制是什么、值不值得学
- L1: 真问题是"Agent 产品如何做任务编排"，不是"Manus 是不是噱头"
- L2: 任务如何被拆解、执行、验收
- L3: 官方文档怎么说、实测表现如何、用户怎么评价
- L4: 如果 Manus 只是包装，哪些观察能证伪"自研编排"

每个节点字段（机器可验证）：
{{
  "id": "Q0 / Q1.1 / Q2.1 格式，不得重复",
  "layer": "L0_root | L1_meta | L2_mechanism | L3_evidence | L4_counter",
  "question": "...",
  "parent_id": "必须指向已存在节点；Q0 的 parent_id 为 null",
  "status": "open",
  "research_mode": "该节点适合的调研方式",
  "priority": "must | should | could"
}}

输出 JSON：
{{
  "intent_tree": [ ...节点列表... ],
  "round3_notes": "树构建思路"
}}""",
    },
    {
        "round": 4,
        "name": "路径生成",
        "purpose": "生成候选调研路径并显式剪枝——方向选择是显式的，不是默认的",
        "prompt": """你是意图探索员 Round 4。基于 Round 3 的意图树，生成 ≥2 条候选调研路径（candidate_paths），并做出初步选择。

意图树不只是一棵树，还包含被放弃的路径——这保证方向选择是显式的，不是默认的。

每条路径字段：
{{
  "path_id": "P1 / P2 ...",
  "name": "路径名",
  "description": "这条路径怎么打",
  "expected_yield": "预期产出",
  "cost": "成本估计",
  "selected": true/false,
  "pruned_reason": "未选中时必填——为什么剪掉这条"
}}

硬规则：
- ≥2 条候选路径，每条有 expected_yield 和 cost
- 恰有 1 条 selected=true
- 未选中的必须有非空 pruned_reason

示例（Manus）：
- P1 机制拆解路径（selected=true）：把 Manus 当工程对象拆，yield=知道它怎么工作、壁垒在哪，cost=高（需实测+源码级分析）
- P2 商业叙事路径（selected=false）：把 Manus 当营销案例拆，yield=知道它怎么讲故事，cost=低，pruned_reason=用户已读过营销分析，边际收益低

输出 JSON：
{{
  "candidate_paths": [ ... ],
  "round4_notes": "初步选择理由"
}}""",
    },
    {
        "round": 5,
        "name": "固化成问题说明书",
        "purpose": "把探索结果固化成 agent 可解、可验证、可批评的问题说明书",
        "prompt": """你是意图探索员 Round 5。基于 Round 1-4 的探索，固化成问题说明书：

1. 核心问题（一句话，agent 可解）
2. 可验证性：完成后怎么检查被答了？
3. 可批评性：什么证据能推翻问题前提？
4. agent 可解性：AI 拿到能独立推理吗？需要什么前置知识？
5. concept_ladder_seed：需要解释的 5-10 个术语
6. clarifying_questions：还需澄清的问题，每个标注 blocks_plan_if_unanswered
   - true 表示不定案就无法规划，≤3 个；超出的降级为开放问题（false）
7. success_criteria：成功标准（非空——什么叫这次调研打赢了）
8. **first_principles_decomposition（保留 v1.3 要求）**：这个问题的第一性原理拆解
   - 列出 ≥3 条不可再分的底层逻辑
   - 每条说明"为什么不可再分"（irreducibility_argument）
   - 每条说明证据基础（evidence_basis）
   - 示例：如果问题是"是否出海"，原理可以是"出海=用中国成本+赚海外收入+拿海外估值（三重套利，不可再分）"

输出完整的 intent_doc 补充字段。""",
    },
]


# ============================================================
# 阶段 1：创建骨架（工具做）
# ============================================================

def prepare(project_dir: str | Path) -> Path:
    """创建 intent_doc.json 骨架（v2.0 schema）。

    骨架特征（诚实标注）：
      - status = "skeleton_pending_agent"（探索尚未开始）
      - exploration_history = []（空列表，等 Agent 填）
      - stated_intent = ""（空，等 Agent 填）
      - prompt_templates = EXPLORATION_ROUNDS（5 轮 prompt，供 Agent 使用）
      - v07.intent_tree / candidate_paths / revision_history = []，
        success_criteria = ""（等 finalize 固化）

    工具不调 LLM，不做探索。骨架只是准备好了结构，等 Agent 来填。

    Args:
        project_dir: 项目目录路径

    Returns:
        intent_doc.json 的路径
    """
    project = Path(project_dir)

    intent_doc = {
        "schema_version": "research-os-intent-v2.0",
        "project_name": project.name,
        "status": "skeleton_pending_agent",
        "created_at": datetime.now().isoformat(),
        "stated_intent": "",
        "prompt_templates": EXPLORATION_ROUNDS,
        "exploration_history": [],
        "v07": {
            # reader_model 不由工具初始化——读者画像是 Agent 的内置能力
            # Agent 从记忆和知识库获取读者信息，不需要工具管理
            # 仅当读者≠用户本人时，Agent 手动在此声明 reader_model
            "reader_model": None,
            "intent_tree": [],
            "candidate_paths": [],
            "success_criteria": "",
            "revision_history": [],
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
        round_num: 第几轮（1/2/3/4/5）
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


# ============================================================
# 阶段 3：finalize 硬校验（工具机械执行，不做语义判断）
# ============================================================

def _validate_intent_tree(tree: list) -> list[str]:
    """校验意图树结构完整性。返回错误列表（空=通过）。"""
    errors: list[str] = []
    if not tree:
        return ["intent_tree 为空——R3 必须产出意图树"]

    ids = [n.get("id") for n in tree]
    seen: set = set()
    dups: list = []
    for i in ids:
        if i in seen and i not in dups:
            dups.append(i)
        seen.add(i)
    if dups:
        errors.append(f"intent_tree 存在重复 id: {dups}")

    id_set = set(ids)
    for n in tree:
        nid = n.get("id")
        pid = n.get("parent_id")
        if nid == "Q0":
            if pid is not None:
                errors.append("根节点 Q0 的 parent_id 必须为 null")
        elif pid not in id_set:
            errors.append(f"节点 {nid!r} 的 parent_id={pid!r} 未指向已存在节点")

    l1_count = sum(1 for n in tree if n.get("layer") == "L1_meta")
    if l1_count < 1:
        errors.append(f"intent_tree 需含 ≥1 个 L1_meta 元问题节点（当前 {l1_count} 个）")

    l2_count = sum(1 for n in tree if n.get("layer") == "L2_mechanism")
    if l2_count < 3:
        errors.append(f"intent_tree 需含 ≥3 个 L2_mechanism 机制问题节点（当前 {l2_count} 个）")

    return errors


def _validate_candidate_paths(paths: list) -> list[str]:
    """校验候选路径与剪枝规则。返回错误列表（空=通过）。"""
    errors: list[str] = []
    if len(paths) < 2:
        return [f"candidate_paths 需 ≥2 条（当前 {len(paths)} 条）——方向选择必须显式"]

    selected = [p for p in paths if p.get("selected") is True]
    if len(selected) != 1:
        errors.append(f"candidate_paths 恰需 1 条 selected=true（当前 {len(selected)} 条）")

    for p in paths:
        if not p.get("selected") and not str(p.get("pruned_reason", "") or "").strip():
            errors.append(f"路径 {p.get('path_id', '?')} 未选中但缺少非空 pruned_reason")

    return errors


def finalize_exploration(
    project_dir: str | Path,
    stated_intent: str,
    intent_tree: list | None = None,
    candidate_paths: list | None = None,
    success_criteria: str = "",
    concept_ladder_seed: list[str] | None = None,
    clarifying_questions: list | None = None,
    first_principles_decomposition: list | None = None,
) -> None:
    """Agent 全部 5 轮探索完成后，硬校验通过才标记探索完成并固化最终意图。

    硬校验（机械检查，任一不满足抛 ValueError 并说明哪条不满足）：
      - 5 轮全部 commit
      - intent_tree 非空、≥1 个 L1_meta 节点、≥3 个 L2_mechanism 节点、
        parent_id 指向已存在节点（Q0 为 null）、无重复 id
      - candidate_paths ≥2 且恰 1 个 selected=true，未选中的必须有非空 pruned_reason
      - blocks_plan_if_unanswered=true 的澄清问题 ≤3
      - success_criteria 非空

    Args:
        project_dir: 项目目录路径
        stated_intent: 一句话核心意图（Agent 从 Round 5 固化的）
        intent_tree: R3 产出的意图树节点列表，写入 v07.intent_tree
        candidate_paths: R4 产出的候选路径列表，写入 v07.candidate_paths
        success_criteria: 成功标准，写入 v07.success_criteria
        concept_ladder_seed: 需要解释的术语列表
        clarifying_questions: 还需澄清的问题（dict 含 blocks_plan_if_unanswered 标注）
        first_principles_decomposition: 第一性原理拆解（≥3 条）
    """
    project = Path(project_dir)
    intent_path = project / "00-task" / "intent_doc.json"

    if not intent_path.exists():
        raise FileNotFoundError(
            f"intent_doc.json 不存在于 {intent_path}。请先运行 prepare() 创建骨架。"
        )

    intent_doc = json.loads(intent_path.read_text(encoding="utf-8-sig"))

    # 硬校验 1：5 轮全部 commit 才允许 finalize
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
            f"请先用 commit_exploration_result() 提交所有 5 轮的结果。"
        )

    # 硬校验 2-5：结构检查，收集全部错误一次性报告
    tree = intent_tree if intent_tree is not None else []
    paths = candidate_paths if candidate_paths is not None else []

    errors: list[str] = []
    errors.extend(_validate_intent_tree(tree))
    errors.extend(_validate_candidate_paths(paths))

    blocking = sum(
        1 for q in (clarifying_questions or [])
        if isinstance(q, dict) and q.get("blocks_plan_if_unanswered") is True
    )
    if blocking > 3:
        errors.append(
            f"blocks_plan_if_unanswered=true 的澄清问题需 ≤3 个（当前 {blocking} 个），"
            f"超出请降级为开放问题"
        )

    if not str(success_criteria or "").strip():
        errors.append("success_criteria 不能为空——必须定义什么叫这次调研打赢了")

    if errors:
        raise ValueError("finalize 硬校验失败：\n- " + "\n- ".join(errors))

    intent_doc["status"] = "exploration_complete"
    intent_doc["stated_intent"] = stated_intent
    intent_doc["first_principles_decomposition"] = (
        first_principles_decomposition if first_principles_decomposition else []
    )

    v07 = intent_doc.setdefault("v07", {})
    v07["intent_tree"] = tree
    v07["candidate_paths"] = paths
    v07["success_criteria"] = success_criteria
    if concept_ladder_seed is not None:
        v07["concept_ladder_seed"] = concept_ladder_seed
    if clarifying_questions is not None:
        v07["clarifying_questions"] = clarifying_questions

    intent_path.write_text(json.dumps(intent_doc, ensure_ascii=False, indent=2), encoding="utf-8")


# ============================================================
# 反僵化条款：意图树修订留痕（协议第 6 节）
# ============================================================

def revise_intent_tree(
    project_dir: str | Path,
    new_tree: list,
    revision_reason: str,
    triggering_evidence: str,
    major_change: bool = False,
) -> dict[str, Any]:
    """调研中途修订意图树。工具只做机械留痕，不做语义判断。

    行为：
      1. 把当前 intent_tree 快照 + 修订理由 + 触发证据 + 时间戳追加进
         v07.revision_history（禁止原地改，旧树必须留痕）
      2. 把 new_tree 写入 v07.intent_tree
      3. major_change=True（如修订了 L1 元问题）时，在返回值里标记
         requires_direction_reselection=True，提示 Agent 需重过 step_1.5
         方向选择——工具只标记不强制

    Args:
        project_dir: 项目目录路径
        new_tree: 修订后的完整意图树
        revision_reason: 修订理由
        triggering_evidence: 触发修订的证据（如发现推翻了元问题）
        major_change: 是否重大方向变更（修订 L1 元问题=True）

    Returns:
        dict: {"status": "revised", "revision_count": n, "major_change": bool,
               可选 "requires_direction_reselection": True}
    """
    project = Path(project_dir)
    intent_path = project / "00-task" / "intent_doc.json"

    if not intent_path.exists():
        raise FileNotFoundError(
            f"intent_doc.json 不存在于 {intent_path}。请先运行 prepare() 创建骨架。"
        )

    intent_doc = json.loads(intent_path.read_text(encoding="utf-8-sig"))
    v07 = intent_doc.setdefault("v07", {})
    history = v07.setdefault("revision_history", [])

    history.append({
        "revised_at": datetime.now().isoformat(),
        "previous_tree_snapshot": v07.get("intent_tree", []),
        "revision_reason": revision_reason,
        "triggering_evidence": triggering_evidence,
        "major_change": bool(major_change),
    })

    v07["intent_tree"] = new_tree
    intent_path.write_text(json.dumps(intent_doc, ensure_ascii=False, indent=2), encoding="utf-8")

    result: dict[str, Any] = {
        "status": "revised",
        "revision_count": len(history),
        "major_change": bool(major_change),
    }
    if major_change:
        result["requires_direction_reselection"] = True
    return result


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
        print(f"[hint] Agent 应使用 prompt_templates 中的 prompt 跑 5 轮探索")
        print(f"[hint] 每轮完成后调用 commit_exploration_result() 写回结果")
        print(f"[hint] 全部完成后调用 finalize_exploration() 硬校验并标记完成")
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
