#!/usr/bin/env python3
"""Research OS profile updater - post-research phase.

Triggered after `ros build` completes with validator 0 FAIL. Reads the full
project (evidence / hypotheses / red team / final report / intent doc +
revisions), calls DeepSeek to extract what the user actually resolved, what
judgment patterns surfaced, what unresolved seeds they left behind, and
what cross-project insights are worth keeping.

Writes back to ~/.research-os/:
- user_profile.json: judgment_patterns, unresolved_seeds, domain_preferences
- project_index.json: this project's resolved_intent + completion date
- insight_memory.json: cross-project reusable insights (capped at 50)

This is the layer that makes the next `ros new` smarter - unresolved seeds
from this project will surface in the next project's intent_discovery.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import config
import llm_client
import profile_store


SYSTEM_PROMPT = """你是一个研究教练 + 长期记忆管理者。

你的工作：基于一次调研的完整产出（不只是任务卡，而是真正写完的证据/假设/反方/最终报告），总结这次调研真正解决了什么问题，用户展现了什么稳定的判断倾向，留下了什么未解的种子值得下次继续挖。

## 核心原则

1. resolved_intent 必须基于真实调研产出，不是基于任务卡里写的"想解决什么"。用户往往在调研中才发现自己真正想问的是什么。
2. judgment_patterns 是用户做判断的稳定倾向（不是这次的具体结论）。例如"倾向把'感兴趣'转成'能不能用在自己系统上'"。
3. unresolved_seeds 是这次没解决、但下次可以继续挖的问题。不要写已经解决的。
4. cross_project_insights 是跨项目可复用的方法论或模式（不是这次的具体事实）。例如"Placeholder 注释识别规则可跨产品复用"。
5. 如果信息不足，可以输出空数组，不要硬编。

## 意图演化记录（v0.2 新增）

你必须显式记录 stated_intent vs resolved_intent 的差距：
- stated_intent：调研前用户说的想做什么（来自 intent_doc）
- resolved_intent：调研后真正解决了什么
- gap：两者之间的差距描述。如果一致，写"无显著差距"。如果不一致，描述用户原以为要 X，实际要 Y。
- implication_for_next：基于这个差距，下次类似调研应该怎么做。例如"用户原以为要参访攻略，实际要的是方向判断 → 下次类似调研先 L1 草稿"。

这个 intent_evolution 字段会被下次 ros new 时的 intent_discovery 读取，用来提议"要不要先 L1 草稿"。

## 身份贯穿（v0.2 新增）

总结时必须显式回答：这次调研对用户的长期价值锚定（基于身份画像）：
- 求职故事：这次调研能不能成为面试时的"我做过 X"案例？
- 产品启发：这次调研对用户当前产品组合有什么启发？
- 赛道修正：这次调研是否修正了用户对某条赛道的判断？
- 如果某项无关，明确说"无关"。不要硬编。
"""


USER_PROMPT_TEMPLATE = """## 项目信息
- 项目名：{project_name}
- 调研类型：{research_type}
- 深度档位：{depth}
- research_mode：{research_mode}

## 调研前的意图文档（作为对照基准）
{intent_doc_summary}

## 调研中的意图修正记录
{revisions_summary}

## 最终报告全文
{final_report}

## 证据矩阵 + 假设账本 + 反方审计（摘录）
{evidence_summary}

## 当前用户身份画像（求职/产品/赛道判断/长期目标）
{identity_summary}

## 当前用户行为画像（已有的判断模式和未解种子，避免重复）
{existing_profile_summary}

---

请基于以上信息生成调研后画像回写。**必须显式记录 stated_intent vs resolved_intent 的差距（intent_evolution 字段）**，并显式回答这次调研对用户长期价值锚定（求职故事/产品启发/赛道修正）。

输出严格 JSON：

```json
{{
  "resolved_intent": "这次调研真正解决的问题（一句话，可能跟初判意图不同）",
  "aha_moment": "用户可能在调研中经历的 aha moment（如果有，描述这个瞬间；如果没有，留空字符串）",
  "judgment_patterns": [
    {{
      "pattern": "用户做判断的稳定倾向（一句话）",
      "evidence_in_this_project": "这次调研里的具体证据"
    }}
  ],
  "unresolved_seeds": [
    {{
      "seed": "这次没解决、下次可以继续挖的问题（一句话）",
      "why_unresolved": "为什么这次没解决"
    }}
  ],
  "cross_project_insights": [
    {{
      "insight": "跨项目可复用的方法论或模式",
      "applicable_domains": ["适用的调研类型"]
    }}
  ],
  "domain_preference": {{
    "domain": "这次调研触及的领域（如 AI 基础设施 / 产品拆解 / 职业选择）",
    "depth_tendency": "用户在这个领域倾向的深度（R0/R1/R2/R3）"
  }},
  "intent_evolution": {{
    "stated_intent": "调研前用户说的想做什么（来自 intent_doc）",
    "resolved_intent": "调研后真正解决了什么（同上 resolved_intent）",
    "gap": "两者差距。如果一致写'无显著差距'。如果不一致描述用户原以为要 X，实际要 Y",
    "implication_for_next": "基于这个差距下次类似调研应该怎么做"
  }},
  "long_term_value_anchors": {{
    "employment_story": "这次调研对用户求职故事的关系（无关则写'无关'）",
    "product_inspiration": "这次调研对用户当前产品组合的启发（无关则写'无关'）",
    "track_revision": "这次调研对用户赛道判断的修正（无关则写'无关'）"
  }}
}}
```

只输出 JSON。"""


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def _read_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    try:
        return path.read_text(encoding="utf-8-sig")
    except OSError:
        return default


def _summarize_intent_doc(project: Path) -> str:
    intent_doc = _read_json(project / "00-task" / "intent_doc.json", {})
    if not intent_doc:
        return "(没有意图文档 - 调研前未运行 intent_discovery)"
    lines = [f"表层意图: {intent_doc.get('stated_intent', '(空)')}"]
    hidden = intent_doc.get("hidden_intents", [])
    if hidden:
        lines.append("隐藏意图假设（含三层深度挖掘）:")
        for i, h in enumerate(hidden, 1):
            lines.append(f"  {i}. {h.get('intent', '')}")
            essence = h.get("essence", "")
            if essence:
                lines.append(f"     本质: {essence}")
            hidden_need = h.get("hidden_need", "")
            if hidden_need:
                lines.append(f"     隐藏需求: {hidden_need}")
            rel = h.get("identity_relations", {})
            if rel:
                emp = rel.get("employment", "")
                if emp and emp != "无关":
                    lines.append(f"     求职关系: {emp}")
                prod = rel.get("products", "")
                if prod and prod != "无关":
                    lines.append(f"     产品关系: {prod}")
                tracks = rel.get("tracks", "")
                if tracks and tracks != "无关":
                    lines.append(f"     赛道关系: {tracks}")
    return "\n".join(lines)


def _summarize_identity_for_updater() -> str:
    """Read identity.json and render summary for LLM context."""
    identity = profile_store.read_identity()
    if not identity:
        return "(身份画像为空 - 用户尚未跑 ros discover-identity 并 accept)"
    lines = []
    emp = identity.get("employment_status", {})
    if emp:
        lines.append(f"求职状态: {emp.get('current', '?')} → {emp.get('target', '?')} (时间线: {emp.get('timeline', '?')})")
        intentions = emp.get("intentions", [])
        if intentions:
            lines.append(f"  意向: {', '.join(intentions[:5])}")

    products = identity.get("current_products", [])
    if products:
        lines.append(f"当前产品组合 ({len(products)} 个):")
        for p in products:
            lines.append(f"  - {p.get('name', '?')} [{p.get('status', '?')}]")

    tracks = identity.get("track_judgments", [])
    if tracks:
        lines.append(f"赛道判断 ({len(tracks)} 条):")
        for t in tracks:
            lines.append(f"  - {t.get('track', '?')}: {t.get('judgment', '?')}")

    goals = identity.get("long_term_goals", [])
    if goals:
        lines.append("长期目标:")
        for g in goals[:5]:
            lines.append(f"  - {g}")

    return "\n".join(lines) if lines else "(身份画像字段为空)"


def _summarize_revisions(project: Path) -> str:
    revisions_dir = project / "00-task" / "intent_revisions"
    if not revisions_dir.exists():
        return "(没有调研中意图修正记录)"
    files = sorted(revisions_dir.iterdir())
    if not files:
        return "(没有调研中意图修正记录)"
    lines = []
    for f in files[-3:]:  # last 3 revisions
        text = _read_text(f)
        if not text:
            continue
        # Extract the revised_intent section
        match = _extract_section(text, "修正后的意图")
        if match:
            lines.append(f"- {f.name}: {match[:200]}")
    return "\n".join(lines) if lines else "(修订记录为空)"


def _extract_section(md: str, heading: str) -> str:
    """Extract the body of a ## heading section."""
    pattern = rf"^##\s+{re.escape(heading)}\s*$((?:.|\n)*?)(?=^##\s|\Z)"
    match = re.search(pattern, md, re.M)
    return match.group(1).strip() if match else ""


def _summarize_evidence(project: Path) -> str:
    parts = []
    evidence_text = _read_text(project / "03-evidence" / "evidence_matrix.md")
    if evidence_text:
        parts.append("## evidence_matrix.md (前 1500 字)")
        parts.append(evidence_text[:1500])

    ledger = _read_json(project / "03-evidence" / "hypothesis_ledger.json", {})
    hypotheses = ledger.get("hypotheses", []) if isinstance(ledger, dict) else []
    if hypotheses:
        parts.append("\n## hypothesis_ledger.json (假设状态)")
        for h in hypotheses[:10]:
            if not isinstance(h, dict):
                continue
            parts.append(
                f"- {h.get('id', '?')}: {str(h.get('hypothesis', ''))[:100]} "
                f"[status={h.get('status', '?')}, revisions={len(h.get('revision_history') or [])}]"
            )

    red_team_text = _read_text(project / "06-review" / "red_team.md")
    if red_team_text:
        parts.append("\n## red_team.md (前 800 字)")
        parts.append(red_team_text[:800])

    return "\n".join(parts) if parts else "(没有证据/假设/反方审计内容)"


def _summarize_existing_profile(profile: dict[str, Any]) -> str:
    if not profile:
        return "(画像为空 - 这是第一次调研)"
    lines = []
    patterns = profile.get("judgment_patterns", [])
    if patterns:
        lines.append("已有判断模式:")
        for p in patterns[:5]:
            lines.append(f"  - {p.get('pattern', '')}")
    seeds = [s for s in profile.get("unresolved_seeds", []) if s.get("status") == "open"]
    if seeds:
        lines.append(f"\n已有未解种子 ({len(seeds)} 个 open):")
        for s in seeds[:5]:
            lines.append(f"  - {s.get('seed', '')}")
    return "\n".join(lines) if lines else "(画像字段为空)"


def _build_aha_summary(result: dict[str, Any], project_name: str) -> str:
    """Human-readable summary printed to terminal after write-back."""
    lines = [f"\n=== 调研后画像回写 — {project_name} ===", ""]
    lines.append(f"resolved_intent: {result.get('resolved_intent', '(空)')}")
    aha = result.get("aha_moment", "")
    if aha:
        lines.append(f"\naha moment: {aha}")

    # intent_evolution (v0.2)
    evo = result.get("intent_evolution", {})
    if evo and evo.get("gap"):
        lines.append("\n意图演化记录:")
        lines.append(f"  stated: {evo.get('stated_intent', '?')}")
        lines.append(f"  resolved: {evo.get('resolved_intent', '?')}")
        lines.append(f"  gap: {evo.get('gap', '?')}")
        lines.append(f"  下次启示: {evo.get('implication_for_next', '?')}")

    # long_term_value_anchors (v0.2)
    anchors = result.get("long_term_value_anchors", {})
    if anchors:
        lines.append("\n长期价值锚定:")
        for key, label in [
            ("employment_story", "求职故事"),
            ("product_inspiration", "产品启发"),
            ("track_revision", "赛道修正"),
        ]:
            val = anchors.get(key, "")
            if val and val != "无关":
                lines.append(f"  {label}: {val}")

    patterns = result.get("judgment_patterns", [])
    if patterns:
        lines.append(f"\n新增/更新判断模式 ({len(patterns)} 条):")
        for p in patterns:
            lines.append(f"  - {p.get('pattern', '')}")
    seeds = result.get("unresolved_seeds", [])
    if seeds:
        lines.append(f"\n留下未解种子 ({len(seeds)} 个):")
        for s in seeds:
            lines.append(f"  - {s.get('seed', '')}")
    insights = result.get("cross_project_insights", [])
    if insights:
        lines.append(f"\n跨项目洞察 ({len(insights)} 条):")
        for i in insights:
            lines.append(f"  - {i.get('insight', '')}")
    return "\n".join(lines)


def write_back(project: Path) -> dict[str, Any]:
    """Run post-research profile write-back. Updates user_profile.json,
    project_index.json, insight_memory.json. Returns the LLM result + aha
    summary for terminal display."""
    config.ensure_runtime_dirs()

    state_path = project / "research_state.json"
    if not state_path.exists():
        raise FileNotFoundError(f"missing {state_path}")
    state = _read_json(state_path, {})
    project_name = state.get("project_name", project.name)
    research_type = state.get("research_type", "mixed")
    depth = state.get("depth", "R1")
    research_mode = state.get("research_mode", "evidence_intelligence")

    intent_doc_summary = _summarize_intent_doc(project)
    revisions_summary = _summarize_revisions(project)
    final_report = _read_text(project / "07-output" / "final-report.md")
    if not final_report:
        final_report = "(final-report.md 不存在)"
    elif len(final_report) > 4000:
        final_report = final_report[:4000] + "\n... (truncated)"
    evidence_summary = _summarize_evidence(project)
    existing_profile = profile_store.read_user_profile()
    existing_profile_summary = _summarize_existing_profile(existing_profile)
    identity_summary = _summarize_identity_for_updater()

    user_prompt = USER_PROMPT_TEMPLATE.format(
        project_name=project_name,
        research_type=research_type,
        depth=depth,
        research_mode=research_mode,
        intent_doc_summary=intent_doc_summary,
        revisions_summary=revisions_summary,
        final_report=final_report,
        evidence_summary=evidence_summary,
        identity_summary=identity_summary,
        existing_profile_summary=existing_profile_summary,
    )

    result = llm_client.chat_json(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=3500,
    )

    result.setdefault("resolved_intent", "")
    result.setdefault("aha_moment", "")
    result.setdefault("judgment_patterns", [])
    result.setdefault("unresolved_seeds", [])
    result.setdefault("cross_project_insights", [])
    result.setdefault("domain_preference", {})
    result.setdefault("intent_evolution", {})
    result.setdefault("long_term_value_anchors", {})

    project_id = project.name

    # Write back to user_profile.json
    for p in result["judgment_patterns"]:
        pattern_text = p.get("pattern", "").strip()
        if pattern_text:
            profile_store.add_judgment_pattern(pattern_text, project_id)

    for s in result["unresolved_seeds"]:
        seed_text = s.get("seed", "").strip()
        if seed_text:
            profile_store.add_unresolved_seed(seed_text, project_id)

    domain_pref = result.get("domain_preference") or {}
    domain = domain_pref.get("domain", "").strip()
    if domain:
        profile_store.add_domain_preference(
            domain, domain_pref.get("depth_tendency", depth), project_id
        )

    # Write back to insight_memory.json (separate from user_profile.insight_memory
    # to avoid AI reflecting on its own previous reflections)
    for i in result["cross_project_insights"]:
        insight_text = i.get("insight", "").strip()
        if insight_text:
            profile_store.append_insight({
                "insight": insight_text,
                "origin_project_id": project_id,
                "applicable_domains": i.get("applicable_domains", []),
                "captured_at": date.today().isoformat(),
            })

    # Update project_index.json
    profile_store.append_project_to_index({
        "project_id": project_id,
        "title": project_name,
        "research_type": research_type,
        "depth": depth,
        "resolved_intent": result["resolved_intent"],
        "completed_at": date.today().isoformat(),
    })

    # Write back intent_evolution (v0.2): records stated vs resolved gap
    evo = result.get("intent_evolution", {})
    if evo and evo.get("gap") and evo.get("gap") != "无显著差距":
        profile_store.add_intent_evolution(
            project_id=project_id,
            stated_intent=evo.get("stated_intent", result.get("resolved_intent", "")),
            resolved_intent=evo.get("resolved_intent", result.get("resolved_intent", "")),
            gap=evo.get("gap", ""),
            implication_for_next=evo.get("implication_for_next", ""),
        )

    aha_summary = _build_aha_summary(result, project_name)
    return {"result": result, "aha_summary": aha_summary}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run post-research profile write-back on a Research OS project"
    )
    parser.add_argument("project", help="Path to research project directory")
    args = parser.parse_args()
    project = Path(args.project).resolve()
    if not project.exists():
        print(f"[error] project not found: {project}", file=sys.stderr)
        return 1
    try:
        out = write_back(project)
    except Exception as exc:
        print(f"[error] profile write-back failed: {exc}", file=sys.stderr)
        return 1
    print(out["aha_summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
