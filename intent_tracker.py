#!/usr/bin/env python3
"""Research OS intent tracker - mid-research phase.

Triggered via `ros reflect <project>`. Extracts behavior signals from project
files (no LLM needed for signal extraction), then calls DeepSeek to interpret
those signals and propose intent revisions.

This is the layer that elevates "dynamic" from state-machine progression to
target correction. The state machine knows you have N candidates; this module
notices you keep revising H002 and the largest section of your draft is about
Dream mechanism - and asks whether your real question has shifted.

Anti-recursion: scope excludes intent_doc.md and prior intent_revisions/*.
The LLM reads only real research artifacts (evidence, hypotheses, candidates,
report draft, task card) - not its own previous reflections.
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


SYSTEM_PROMPT = """你是一个研究教练，不是审讯员。

你的工作：基于用户在调研过程中的真实行为信号（不是他们说的，是他们做的），识别他们真正在纠结什么，主动修正调研意图。

原则：
1. 基于行为信号推断，不是基于用户原话。原话可能停留在表层，行为更接近真需求。
2. 如果信号不够明确，直接说"需要更多调研才能判断"，不要硬猜。
3. revised_intent 必须跟原 stated_intent 形成对比或修正关系，不能照搬。
4. 如果发现新意图跟原意图正交（不是修正，是新方向），建议拉子调研而不是覆盖原意图。
5. new_questions 要基于行为信号具体生成，不要套话术。看到证据模糊就问"你这里说『有意思』，是想拿来用还是纯粹好奇？"这种。
6. suggested_pivot 只在证据足够强时才设 should_pivot=true，否则保守。
"""


USER_PROMPT_TEMPLATE = """## 项目信息
- 项目名：{project_name}
- research_mode：{research_mode}

## 原意图文档（调研前生成的，作为对照基准）
{intent_doc_summary}

## 调研中观察到的行为信号
{signals_summary}

## 当前调研内容摘录（前 2000 字）
{content_excerpt}

---

请基于以上信息生成意图修正建议，输出严格 JSON：

```json
{{
  "signals_observed": [
    {{
      "signal": "观察到的具体信号（引用真实数据）",
      "interpretation": "这个信号说明什么"
    }}
  ],
  "revised_intent": "修正后的意图（一句话，跟原 stated_intent 形成对比或推进关系）",
  "revision_rationale": "为什么这样修正（基于哪些信号）",
  "new_questions": [
    {{
      "question": "基于行为信号的具体追问",
      "why": "为什么问这个（哪个信号触发的）"
    }}
  ],
  "suggested_pivot": {{
    "should_pivot": false,
    "rationale": "如果 should_pivot=true，说明为什么要拉子调研；如果 false，解释为什么保持原方向",
    "sub_research_topic": "如果 pivot，子调研的主题（should_pivot=false 时为空字符串）"
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


def extract_behavior_signals(project: Path) -> dict[str, Any]:
    """Extract signals from project files. Pure Python, no LLM."""
    signals: dict[str, Any] = {}

    # 1. Hypothesis revision depth - which hypotheses are being fought over
    ledger = _read_json(project / "03-evidence" / "hypothesis_ledger.json", {})
    hypotheses = ledger.get("hypotheses") or []
    revised = []
    for h in hypotheses:
        if not isinstance(h, dict):
            continue
        rev_history = h.get("revision_history") or []
        rev_count = len(rev_history) if isinstance(rev_history, list) else 0
        status = h.get("status", "")
        if rev_count > 0 or status in {"downgraded", "rejected"}:
            revised.append({
                "id": h.get("id", "?"),
                "hypothesis": str(h.get("hypothesis", ""))[:120],
                "status": status,
                "revision_count": rev_count,
                "supporting_evidence_count": len(h.get("supporting_evidence") or []),
                "contradicting_evidence_count": len(h.get("contradicting_evidence") or []),
            })
    revised.sort(key=lambda x: (x["revision_count"], x["contradicting_evidence_count"]), reverse=True)
    signals["most_contested_hypotheses"] = revised[:3]

    # 2. Candidate discard pattern - what kinds of sources are being filtered out
    pool = _read_json(project / "02-sources" / "candidate_pool.json", {})
    items = pool.get("items") or []
    candidates = [i for i in items if isinstance(i, dict)]
    discarded = [i for i in candidates if i.get("status") == "discarded"]
    signals["candidate_total"] = len(candidates)
    signals["discarded_count"] = len(discarded)
    signals["discard_reasons"] = [
        str(i.get("discard_reason", ""))[:150] for i in discarded[:5]
    ]

    # 3. Final report section emphasis (if draft exists)
    report_text = _read_text(project / "07-output" / "final-report.md")
    if report_text:
        sections = re.split(r"^##\s+", report_text, flags=re.M)
        section_sizes = []
        for s in sections[1:]:
            title = s.split("\n", 1)[0].strip()
            body = s[len(title):].strip() if "\n" in s else ""
            section_sizes.append({"title": title, "char_count": len(body)})
        section_sizes.sort(key=lambda x: x["char_count"], reverse=True)
        signals["largest_report_sections"] = section_sizes[:3]
        signals["report_total_chars"] = len(report_text)

    # 4. Evidence matrix scale
    evidence_text = _read_text(project / "03-evidence" / "evidence_matrix.md")
    if evidence_text:
        evidence_ids = set(re.findall(r"\bE\d{2,4}\b", evidence_text))
        signals["evidence_count"] = len(evidence_ids)
        signals["evidence_matrix_chars"] = len(evidence_text)

    # 5. Red team pressure (if exists)
    red_team_text = _read_text(project / "06-review" / "red_team.md")
    if red_team_text:
        # Look for downgrade signals
        downgraded = re.findall(r"降级|reject|downgrade", red_team_text, re.I)
        signals["red_team_downgrade_mentions"] = len(downgraded)
        signals["red_team_chars"] = len(red_team_text)

    # 6. Recently edited files (mtime signal - what's being touched right now)
    files_by_mtime = []
    for sub in ["00-task", "01-plan", "02-sources", "03-evidence", "06-review", "07-output"]:
        d = project / sub
        if not d.exists():
            continue
        for f in d.iterdir():
            if f.is_file() and f.suffix in {".md", ".json"}:
                try:
                    stat = f.stat()
                    files_by_mtime.append({
                        "path": str(f.relative_to(project)).replace("\\", "/"),
                        "mtime": int(stat.st_mtime),
                        "size": stat.st_size,
                    })
                except OSError:
                    continue
    files_by_mtime.sort(key=lambda x: x["mtime"], reverse=True)
    signals["recently_edited_files"] = files_by_mtime[:5]

    return signals


def _summarize_intent_doc(project: Path) -> str:
    """Summarize the pre-research intent_doc for the LLM. Excludes revision
    records (anti-recursion)."""
    intent_doc = _read_json(project / "00-task" / "intent_doc.json", {})
    if not intent_doc:
        return "(没有意图文档 - 调研前未运行 intent_discovery)"
    lines = [f"表层意图: {intent_doc.get('stated_intent', '(空)')}"]
    hidden = intent_doc.get("hidden_intents", [])
    if hidden:
        lines.append("隐藏意图假设:")
        for i, h in enumerate(hidden, 1):
            lines.append(f"  {i}. {h.get('intent', '')}")
    questions = intent_doc.get("suggested_sub_questions", [])
    if questions:
        lines.append("建议子问题:")
        for i, q in enumerate(questions, 1):
            lines.append(f"  Q{i}. {q}")
    return "\n".join(lines)


def _format_signals(signals: dict[str, Any]) -> str:
    lines = []
    contested = signals.get("most_contested_hypotheses", [])
    if contested:
        lines.append("最受争议的假设（按修订次数+反证数量排序）:")
        for h in contested:
            lines.append(
                f"  - {h['id']}: {h['hypothesis']} (修订 {h['revision_count']} 次, "
                f"支持证据 {h['supporting_evidence_count']}, 反证 {h['contradicting_evidence_count']}, "
                f"状态: {h['status']})"
            )
    discarded = signals.get("discard_reasons", [])
    if discarded:
        lines.append(f"\n丢弃的来源理由（共 {signals.get('discarded_count', 0)} 个）:")
        for r in discarded:
            lines.append(f"  - {r}")
    largest = signals.get("largest_report_sections", [])
    if largest:
        lines.append("\n最终报告里字数最多的章节:")
        for s in largest:
            lines.append(f"  - {s['title']}: {s['char_count']} 字")
    if signals.get("evidence_count"):
        lines.append(f"\n证据矩阵: {signals['evidence_count']} 个 evidence_id, "
                     f"{signals['evidence_matrix_chars']} 字")
    if signals.get("red_team_downgrade_mentions") is not None:
        lines.append(f"\n反方审计: {signals['red_team_downgrade_mentions']} 处降级信号, "
                     f"{signals.get('red_team_chars', 0)} 字")
    recent = signals.get("recently_edited_files", [])
    if recent:
        lines.append("\n最近编辑的文件:")
        for f in recent:
            lines.append(f"  - {f['path']} ({f['size']} bytes)")
    return "\n".join(lines) if lines else "(没有可提取的行为信号 - 项目可能还没开始填)"


def _extract_content_excerpt(project: Path, max_chars: int = 2000) -> str:
    """Pull a representative excerpt of current research content."""
    parts = []
    evidence_text = _read_text(project / "03-evidence" / "evidence_matrix.md")
    if evidence_text:
        parts.append("## evidence_matrix.md 摘录")
        parts.append(evidence_text[:800])
    report_text = _read_text(project / "07-output" / "final-report.md")
    if report_text:
        parts.append("\n## final-report.md 摘录")
        parts.append(report_text[:1200])
    if not parts:
        return "(项目内容还很少)"
    excerpt = "\n".join(parts)
    return excerpt[:max_chars]


def _build_revision_md(result: dict[str, Any], project_name: str, signals: dict[str, Any]) -> str:
    lines = [f"# 意图修正记录 — {project_name}", ""]
    lines.append(f"_生成日期: {date.today().isoformat()}_")
    lines.append("")

    lines.append("## 观察到的行为信号（原始数据）")
    lines.append("")
    lines.append(_format_signals(signals))
    lines.append("")

    lines.append("## AI 解读的信号")
    lines.append("")
    for s in result.get("signals_observed", []):
        lines.append(f"- **{s.get('signal', '')}**")
        lines.append(f"  - 解读: {s.get('interpretation', '')}")
    lines.append("")

    lines.append("## 修正后的意图")
    lines.append("")
    lines.append(f"**{result.get('revised_intent', '(未修正)')}**")
    lines.append("")
    rationale = result.get("revision_rationale", "")
    if rationale:
        lines.append(f"_理由: {rationale}_")
        lines.append("")

    new_q = result.get("new_questions", [])
    if new_q:
        lines.append("## 新的追问")
        lines.append("")
        for i, q in enumerate(new_q, 1):
            lines.append(f"### Q{i}. {q.get('question', '')}")
            why = q.get("why", "")
            if why:
                lines.append(f"_为什么问: {why}_")
            lines.append("")
            lines.append("**你的回答:**")
            lines.append("")
            lines.append("")

    pivot = result.get("suggested_pivot", {})
    if pivot:
        lines.append("## 子调研建议")
        lines.append("")
        should = pivot.get("should_pivot", False)
        lines.append(f"**建议拉子调研: {'是' if should else '否'}**")
        lines.append("")
        rationale = pivot.get("rationale", "")
        if rationale:
            lines.append(f"_理由: {rationale}_")
            lines.append("")
        topic = pivot.get("sub_research_topic", "")
        if should and topic:
            lines.append(f"**子调研主题: {topic}**")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_此记录由 intent_tracker 生成，不自动覆盖 intent_doc.md。如需采纳修正，"
                 "手动把 revised_intent 写回 intent_doc.md 或重新跑 ros discover。_")
    return "\n".join(lines)


def reflect(project: Path) -> dict[str, Any]:
    """Run mid-research intent reflection. Writes revision record to
    00-task/intent_revisions/<date>.md. Does NOT overwrite intent_doc.md -
    revisions are advisory until the user explicitly adopts them.
    """
    config.ensure_runtime_dirs()

    state_path = project / "research_state.json"
    if not state_path.exists():
        raise FileNotFoundError(f"missing {state_path}")
    state = _read_json(state_path, {})
    project_name = state.get("project_name", project.name)
    research_mode = state.get("research_mode", "evidence_intelligence")

    signals = extract_behavior_signals(project)
    intent_doc_summary = _summarize_intent_doc(project)
    signals_summary = _format_signals(signals)
    content_excerpt = _extract_content_excerpt(project)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        project_name=project_name,
        research_mode=research_mode,
        intent_doc_summary=intent_doc_summary,
        signals_summary=signals_summary,
        content_excerpt=content_excerpt,
    )

    result = llm_client.chat_json(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=2000,
    )

    result.setdefault("signals_observed", [])
    result.setdefault("revised_intent", "")
    result.setdefault("revision_rationale", "")
    result.setdefault("new_questions", [])
    result.setdefault("suggested_pivot", {"should_pivot": False, "rationale": "", "sub_research_topic": ""})

    revisions_dir = project / "00-task" / "intent_revisions"
    revisions_dir.mkdir(parents=True, exist_ok=True)
    revision_path = revisions_dir / f"{date.today().isoformat()}.md"
    # Avoid overwriting if run multiple times in a day
    counter = 1
    while revision_path.exists():
        revision_path = revisions_dir / f"{date.today().isoformat()}-{counter}.md"
        counter += 1

    revision_path.write_text(
        _build_revision_md(result, project_name, signals), encoding="utf-8"
    )

    return {
        "revision_path": str(revision_path),
        "revised_intent": result.get("revised_intent", ""),
        "signals_count": len(result.get("signals_observed", [])),
        "should_pivot": bool(result.get("suggested_pivot", {}).get("should_pivot")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run mid-research intent reflection on a Research OS project"
    )
    parser.add_argument("project", help="Path to research project directory")
    args = parser.parse_args()
    project = Path(args.project).resolve()
    if not project.exists():
        print(f"[error] project not found: {project}", file=sys.stderr)
        return 1
    try:
        result = reflect(project)
    except Exception as exc:
        print(f"[error] intent reflection failed: {exc}", file=sys.stderr)
        return 1
    print(f"[ok] revision written to {result['revision_path']}")
    print(f"[ok] revised_intent: {result['revised_intent'][:80]}")
    print(f"[ok] signals_count: {result['signals_count']}")
    if result["should_pivot"]:
        print(f"[hint] AI 建议拉子调研 - 检查 revision 文件里的 suggested_pivot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
