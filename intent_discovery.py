#!/usr/bin/env python3
"""Research OS intent discovery - pre-research phase.

Triggered after `ros new` (or manually via `ros discover`). Reads the task
card, the user profile (cross-project memory), and the recent project index.
Calls DeepSeek to surface hidden intents, unresolved seeds from past
projects, and tailored sub-questions/hypotheses.

Anti-recursion (MemOS DirectRecall analog): scope excludes the AI's own past
intent_doc outputs and revision records - intent_discovery reads only real
research signals (task card, profile, project index, cross-project insights
that were extracted from completed projects), not AI's previous reflections
on those projects.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import config
import llm_client
import profile_store
from research_router import route_research


SYSTEM_PROMPT = """你是一个长期研究教练，不是面试官，不是机械 5 why 提问机器。

你的工作：基于用户的历史调研记录、用户身份画像和这次填的任务卡，挖掘他们没说出口的真实需求，甚至帮他们意识到自己埋藏在内心深处的"问题种子"，让用户看到时有 aha moment。

## 核心原则

1. 不要机械套话术。每条假设必须配具体证据（任务卡里的原话 / 历史项目里的具体记录 / 身份画像里的具体字段）。
2. 如果你不确定，就直接说"我需要更多信息"，不要硬猜。
3. 你不是在审讯用户，是在帮他们看清自己。
4. 真需求往往是慢慢明确的——你给的 hidden_intents 是假设，不是定论。用户可以拒绝。
5. surfaced_seeds 必须来自用户画像的 unresolved_seeds，不能编造。
6. suggested_sub_questions 要基于意图定制，不能照搬通用模板（"产品解决什么问题"这种空话不算定制）。
7. open_questions 要具体到能直接回答，不要"你想深入了解什么"这种空泛追问。

## 三层深度挖掘（每个 hidden_intent 必须回答）

每条 hidden_intent 不能只写"用户可能想 X"。必须显式回答三层：

### 第 1 层：本质
- 用户在任务卡里说 X，但 X 背后的 Y 才是真问题。Y 是什么？
- 例：用户说"为 AMD 参访做准备"——本质是"判断 AMD 这条线值不值得深挖"。
- 如果本质就是表层（Y = X），说明这条意图可能不重要，考虑降级。

### 第 2 层：子问题
- 把 Y 拆成 Y1 / Y2 / Y3，看哪个是真问题。
- 例：Y = "AMD 这条线值不值得深挖" → Y1 = "技术路线是否领先" / Y2 = "市场位置是否稳固" / Y3 = "跟我个人长期价值的关系"。
- 必须明确"哪个子问题最关键"。

### 第 3 层：隐藏需求
- 用户没说但实际在乎的。基于身份画像（employment_status / current_products / track_judgments / long_term_goals）判断。
- 常见隐藏需求类型：
  - 求职故事：这次调研能不能成为面试时的"我做过 X"案例？
  - 产品启发：这次调研对用户当前产品组合有什么启发？
  - 赛道修正：这次调研是否修正了用户对某条赛道的判断？
  - 认知差：这次调研能不能让用户获得"别人不知道但我知道"的洞察？
- 如果某条 hidden_intent 找不到隐藏需求层，说明这条意图可能太表面，考虑降级。

## 身份贯穿（强制）

每条 hidden_intent 必须显式回答三个身份关系问题：
1. **跟求职状态的关系**：基于 identity.employment_status，这条意图跟用户的求职目标/求职故事有什么关系？如果无关，明确说"无关"。
2. **跟产品组合的关系**：基于 identity.current_products，这条意图跟用户当前在做的产品有什么启发？如果无关，明确说"无关"。
3. **跟赛道判断的关系**：基于 identity.track_judgments，这条意图是否修正/强化用户对某条赛道的判断？如果无关，明确说"无关"。

如果某条 hidden_intent 三个关系都"无关"，说明这条意图跟用户长期价值锚定不够，考虑降级或替换。

## 输出格式（JSON）

```json
{
  "stated_intent": "表层意图（用户说的）",
  "hidden_intents": [
    {
      "intent": "隐藏意图的一句话总结",
      "essence": "本质层：X 背后的 Y 是什么",
      "sub_questions": ["Y1", "Y2", "Y3"],
      "key_sub_question": "最关键的子问题",
      "hidden_need": "隐藏需求层（求职故事/产品启发/赛道修正/认知差）",
      "identity_relations": {
        "employment": "跟求职状态的关系（无关则写'无关'）",
        "products": "跟产品组合的关系（无关则写'无关'）",
        "tracks": "跟赛道判断的关系（无关则写'无关'）"
      },
      "evidence": ["任务卡原话1", "身份画像字段1", "历史项目记录1"],
      "if_true_implication": "如果是真，对调研方向的影响"
    }
  ],
  "surfaced_seeds": [
    {
      "seed": "过去调研留下的开放问题",
      "origin_project_id": "原项目ID",
      "why_relevant": "为什么这次调研可能正面解决"
    }
  ],
  "suggested_sub_questions": ["基于意图定制的5个子问题"],
  "suggested_hypotheses": ["基于意图定制的3个初始假设"],
  "open_questions": [
    {
      "question": "需要追问用户的具体问题",
      "why": "为什么问这个（基于任务卡里哪句模糊的话）"
    }
  ]
}
```

只输出 JSON，不要加任何前后说明文字。"""


USER_PROMPT_TEMPLATE = """## 本次调研基础信息
- 项目名：{project_name}
- 调研类型：{research_type}
- 深度档位：{depth}
- 推断的 research_mode：{research_mode}

## 任务卡内容（用户填写的）
{task_card}

## 用户身份画像（就业状态 / 产品组合 / 赛道判断 / 长期目标）
{identity_summary}

## 用户行为画像（判断模式 + 未解种子 + 领域偏好）
{user_profile_summary}

## 最近 5 个历史项目
{project_history}

## 跨项目洞察（来自已完成项目，非 AI 反思）
{insight_memory_summary}

## 上次调研的意图演化（stated vs resolved 差异）
{intent_evolution_summary}

---

请基于以上输入生成意图文档。**每个 hidden_intent 必须显式回答三层（本质/子问题/隐藏需求）+ 三个身份关系（就业/产品/赛道）**。

输出严格 JSON 格式：

```json
{{
  "stated_intent": "用户表面说他想要的（一句话总结）",
  "hidden_intents": [
    {{
      "intent": "可能真正想问的是 X（一句话）",
      "essence": "本质层：X 背后的 Y 是什么",
      "sub_questions": ["Y1", "Y2", "Y3"],
      "key_sub_question": "最关键的子问题",
      "hidden_need": "隐藏需求层（求职故事/产品启发/赛道修正/认知差）",
      "identity_relations": {{
        "employment": "跟求职状态的关系（无关则写'无关'）",
        "products": "跟产品组合的关系（无关则写'无关'）",
        "tracks": "跟赛道判断的关系（无关则写'无关'）"
      }},
      "evidence": ["证据1：任务卡里写了 Y", "证据2：身份画像字段 Z", "证据3：历史项目记录 W"],
      "if_true_implication": "如果是真，调研该往 V 方向走（具体说）"
    }}
  ],
  "surfaced_seeds": [
    {{
      "seed": "未解种子的原文（必须来自用户画像的 unresolved_seeds）",
      "origin_project_id": "种子来源项目 id",
      "why_relevant": "为什么这次调研可能正面解决这个种子"
    }}
  ],
  "suggested_sub_questions": [
    "基于意图定制的子问题1（不是通用模板，要具体到这次调研对象）",
    "子问题2",
    "子问题3",
    "子问题4",
    "子问题5"
  ],
  "suggested_hypotheses": [
    "基于意图定制的初始假设1（可被证据证伪的）",
    "假设2",
    "假设3"
  ],
  "open_questions": [
    {{
      "question": "具体追问（用户能直接回答的）",
      "why": "为什么问这个（基于任务卡里哪句模糊的话）"
    }}
  ]
}}
```

只输出 JSON，不要加任何前后说明文字。"""


def _read_task_card(project: Path) -> str:
    path = project / "00-task" / "task-card.md"
    if not path.exists():
        return "(task-card.md 不存在或为空)"
    text = path.read_text(encoding="utf-8-sig").strip()
    return text if text else "(task-card.md 内容为空 - 用户还没填)"


def _summarize_user_profile(profile: dict[str, Any]) -> str:
    if not profile:
        return "(用户画像为空 - 这是第一次调研)"
    lines = []
    patterns = profile.get("judgment_patterns", [])
    if patterns:
        lines.append("判断模式（用户做判断的稳定倾向）:")
        for p in patterns[:5]:
            lines.append(f"  - {p.get('pattern', '')}（首次发现: {p.get('first_seen', '')}）")
    seeds = profile.get("unresolved_seeds", [])
    open_seeds = [s for s in seeds if s.get("status") == "open"]
    if open_seeds:
        lines.append(f"\n未解种子（{len(open_seeds)} 个开放种子，可能跟这次调研相关）:")
        for s in open_seeds[:5]:
            lines.append(f"  - {s.get('seed', '')}")
            lines.append(f"    来源: {s.get('origin_project_id', '')}")
            touched = s.get("touched_again", [])
            if touched:
                lines.append(f"    再次触及: {', '.join(touched)}")
    prefs = profile.get("domain_preferences", [])
    if prefs:
        lines.append(f"\n领域偏好:")
        for p in prefs[:5]:
            lines.append(f"  - {p.get('domain', '')}: 倾向 {p.get('depth_tendency', '')}, 频率 {p.get('frequency', 0)}")
    return "\n".join(lines) if lines else "(画像字段都为空)"


def _summarize_project_history() -> str:
    idx = profile_store.read_project_index()
    if not idx:
        return "(没有历史项目)"
    lines = []
    for entry in idx[:5]:
        lines.append(f"- [{entry.get('project_id', '?')}] {entry.get('title', '')}")
        if entry.get("resolved_intent"):
            lines.append(f"    真正解决: {entry.get('resolved_intent', '')}")
        lines.append(f"    完成: {entry.get('completed_at', '?')}")
    return "\n".join(lines)


def _summarize_insight_memory() -> str:
    items = profile_store.read_insight_memory()
    if not items:
        return "(没有跨项目洞察)"
    lines = []
    for item in items[:5]:
        lines.append(f"- {item.get('insight', '')}")
        lines.append(f"    来源: {item.get('origin_project_id', '?')}")
        if item.get("applicable_domains"):
            lines.append(f"    适用: {', '.join(item.get('applicable_domains', []))}")
    return "\n".join(lines)


def _summarize_identity() -> str:
    """Read identity.json and render as summary for LLM context."""
    identity = profile_store.read_identity()
    if not identity:
        return "(身份画像为空 - 用户尚未跑 ros discover-identity 并 accept)"
    lines = []
    emp = identity.get("employment_status", {})
    if emp:
        lines.append("【求职状态】")
        lines.append(f"  当前: {emp.get('current', '?')}")
        lines.append(f"  目标: {emp.get('target', '?')}")
        lines.append(f"  时间线: {emp.get('timeline', '?')}")
        intentions = emp.get("intentions", [])
        if intentions:
            lines.append(f"  意向公司: {', '.join(intentions[:5])}")
        if emp.get("note"):
            lines.append(f"  注: {emp['note']}")

    products = identity.get("current_products", [])
    if products:
        lines.append(f"\n【当前产品组合】({len(products)} 个)")
        for p in products:
            lines.append(f"  - {p.get('name', '?')} [{p.get('status', '?')}] — {p.get('role', '')} ({p.get('freshness', '?')})")

    tracks = identity.get("track_judgments", [])
    if tracks:
        lines.append(f"\n【赛道判断】({len(tracks)} 条)")
        for t in tracks:
            line = f"  - {t.get('track', '?')}: {t.get('judgment', '?')} ({t.get('freshness', '?')})"
            if t.get("evidence"):
                line += f" — {t['evidence']}"
            if t.get("note"):
                line += f" ⚠️ {t['note']}"
            lines.append(line)

    goals = identity.get("long_term_goals", [])
    if goals:
        lines.append("\n【长期目标】")
        for g in goals:
            lines.append(f"  - {g}")

    return "\n".join(lines) if lines else "(身份画像字段都为空)"


def _summarize_intent_evolution() -> str:
    """Read intent_evolution list and render last 3 for LLM context."""
    evo = profile_store.read_intent_evolution()
    if not evo:
        return "(没有意图演化记录 - 这是第一次调研)"
    lines = []
    for entry in evo[-3:]:  # last 3
        lines.append(f"- 项目: {entry.get('project_id', '?')}")
        lines.append(f"  声称意图: {entry.get('stated_intent', '?')}")
        lines.append(f"  实际意图: {entry.get('resolved_intent', '?')}")
        lines.append(f"  差距: {entry.get('gap', '?')}")
        lines.append(f"  对下次启示: {entry.get('implication_for_next', '?')}")
        lines.append("")
    return "\n".join(lines)


def _build_intent_doc_md(result: dict[str, Any], project_name: str) -> str:
    """Render the LLM JSON output as human-readable markdown."""
    lines = [f"# 意图文档 — {project_name}", ""]
    lines.append(f"_生成日期: {date.today().isoformat()}_")
    lines.append("")
    lines.append("## 表层意图")
    lines.append("")
    lines.append(result.get("stated_intent", "(空)"))
    lines.append("")

    hidden = result.get("hidden_intents", [])
    if hidden:
        lines.append("## 隐藏意图假设（三层深度挖掘）")
        lines.append("")
        lines.append("_这些是 AI 基于你的身份画像、历史和任务卡做的推断。每条意图都回答了三层：本质 / 子问题 / 隐藏需求，并显式标注跟身份的关系。你可以拒绝任何一个。_")
        lines.append("")
        for i, h in enumerate(hidden, 1):
            lines.append(f"### 假设 {i}: {h.get('intent', '')}")
            lines.append("")

            essence = h.get("essence", "")
            if essence:
                lines.append(f"**本质层:** {essence}")
                lines.append("")

            sub_qs = h.get("sub_questions", [])
            if sub_qs:
                lines.append("**子问题拆解:**")
                for sq in sub_qs:
                    lines.append(f"  - {sq}")
                key_sq = h.get("key_sub_question", "")
                if key_sq:
                    lines.append("")
                    lines.append(f"**最关键子问题:** {key_sq}")
                lines.append("")

            hidden_need = h.get("hidden_need", "")
            if hidden_need:
                lines.append(f"**隐藏需求:** {hidden_need}")
                lines.append("")

            rel = h.get("identity_relations", {})
            if rel:
                lines.append("**跟身份的关系:**")
                emp_rel = rel.get("employment", "")
                if emp_rel:
                    lines.append(f"  - 求职: {emp_rel}")
                prod_rel = rel.get("products", "")
                if prod_rel:
                    lines.append(f"  - 产品: {prod_rel}")
                track_rel = rel.get("tracks", "")
                if track_rel:
                    lines.append(f"  - 赛道: {track_rel}")
                lines.append("")

            evidence = h.get("evidence", [])
            if evidence:
                lines.append("**证据:**")
                for e in evidence:
                    lines.append(f"- {e}")
                lines.append("")
            implication = h.get("if_true_implication", "")
            if implication:
                lines.append(f"**如果是真:** {implication}")
                lines.append("")

    seeds = result.get("surfaced_seeds", [])
    if seeds:
        lines.append("## 浮现的未解种子")
        lines.append("")
        lines.append("_这些是你过去调研留下的开放问题，这次可能正面解决。_")
        lines.append("")
        for s in seeds:
            lines.append(f"- **{s.get('seed', '')}**")
            lines.append(f"  - 来源: {s.get('origin_project_id', '?')}")
            why = s.get("why_relevant", "")
            if why:
                lines.append(f"  - 为什么相关: {why}")
        lines.append("")

    questions = result.get("suggested_sub_questions", [])
    if questions:
        lines.append("## 建议子问题")
        lines.append("")
        lines.append("_这些子问题替换了通用 MODE_PLANS 模板，基于你的意图定制。_")
        lines.append("")
        for i, q in enumerate(questions, 1):
            lines.append(f"{i}. {q}")
        lines.append("")

    hyps = result.get("suggested_hypotheses", [])
    if hyps:
        lines.append("## 建议初始假设")
        lines.append("")
        for i, h in enumerate(hyps, 1):
            lines.append(f"{i}. {h}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_此文档由 intent_discovery 生成，会随调研演化（ros reflect 会追加修订）。_")
    return "\n".join(lines)


def _build_open_questions_md(result: dict[str, Any]) -> str:
    questions = result.get("open_questions", [])
    if not questions:
        return "# AI 反问的问题\n\n_本次没有需要追问的，可以直接开始调研。_\n"
    lines = ["# AI 反问你的问题", ""]
    lines.append("_回答这些问题能帮 AI 更准确理解你的意图。可以全跳过，但建议至少看一眼。_")
    lines.append("")
    for i, q in enumerate(questions, 1):
        lines.append(f"## Q{i}. {q.get('question', '')}")
        why = q.get("why", "")
        if why:
            lines.append("")
            lines.append(f"_为什么问: {why}_")
        lines.append("")
        lines.append("**你的回答:**")
        lines.append("")
        lines.append("")
    return "\n".join(lines)


def discover(project: Path) -> dict[str, Any]:
    """Run intent discovery on a project. Writes intent_doc.md/json and
    open_questions.md. Returns the parsed LLM result."""
    config.ensure_runtime_dirs()

    state_path = project / "research_state.json"
    if not state_path.exists():
        raise FileNotFoundError(f"missing {state_path}")

    try:
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid {state_path}: {exc}") from exc

    project_name = state.get("project_name", project.name)
    research_type = state.get("research_type", "mixed")
    depth = state.get("depth", "R1")
    route = route_research(project_name, research_type, depth)
    research_mode = route.get("research_mode", "evidence_intelligence")

    task_card = _read_task_card(project)
    profile = profile_store.read_user_profile()
    profile_summary = _summarize_user_profile(profile)
    project_history = _summarize_project_history()
    insight_summary = _summarize_insight_memory()
    identity_summary = _summarize_identity()
    intent_evolution_summary = _summarize_intent_evolution()

    user_prompt = USER_PROMPT_TEMPLATE.format(
        project_name=project_name,
        research_type=research_type,
        depth=depth,
        research_mode=research_mode,
        task_card=task_card,
        identity_summary=identity_summary,
        user_profile_summary=profile_summary,
        project_history=project_history,
        insight_memory_summary=insight_summary,
        intent_evolution_summary=intent_evolution_summary,
    )

    result = llm_client.chat_json(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=4000,
    )

    # Defensive: ensure required keys exist
    result.setdefault("stated_intent", "")
    result.setdefault("hidden_intents", [])
    result.setdefault("surfaced_seeds", [])
    result.setdefault("suggested_sub_questions", [])
    result.setdefault("suggested_hypotheses", [])
    result.setdefault("open_questions", [])

    task_dir = project / "00-task"
    task_dir.mkdir(parents=True, exist_ok=True)

    # Machine-readable version for research_planner to consume
    (task_dir / "intent_doc.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # Human-readable version
    (task_dir / "intent_doc.md").write_text(
        _build_intent_doc_md(result, project_name), encoding="utf-8"
    )
    # AI's questions for the user
    (task_dir / "open_questions.md").write_text(
        _build_open_questions_md(result), encoding="utf-8"
    )

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run intent discovery on a Research OS project"
    )
    parser.add_argument("project", help="Path to research project directory")
    args = parser.parse_args()
    project = Path(args.project).resolve()
    if not project.exists():
        print(f"[error] project not found: {project}", file=sys.stderr)
        return 1
    try:
        result = discover(project)
    except Exception as exc:
        print(f"[error] intent discovery failed: {exc}", file=sys.stderr)
        return 1
    print(f"[ok] intent_doc written to {project / '00-task' / 'intent_doc.md'}")
    print(f"[ok] open_questions written to {project / '00-task' / 'open_questions.md'}")
    print(f"[ok] stated_intent: {result.get('stated_intent', '')[:80]}")
    hidden = result.get("hidden_intents", [])
    print(f"[ok] hidden_intents: {len(hidden)}")
    seeds = result.get("surfaced_seeds", [])
    print(f"[ok] surfaced_seeds: {len(seeds)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
