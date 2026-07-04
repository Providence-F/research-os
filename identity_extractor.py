#!/usr/bin/env python3
"""Identity extractor for Research OS v0.5 (原 v0.2 模块，v0.5 重构后归并版本号).

Dual-source extraction of user identity:
1. Claude memory (~/.claude/CLAUDE.md + ~/.claude/projects/.../memory/*.md)
2. Obsidian vault (E:/obsidian/AI革命生存指南/, focus on 01-身份 / 04-项目 / 09-收件箱)

Each extracted field is tagged with source + freshness to handle time drift
(older project notes may describe an outdated identity).

Output: ~/.research-os/identity.draft.json — NOT identity.json.
User must run `ros accept-identity` to promote draft to identity.json.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

import config
import llm_client


SYSTEM_PROMPT = """你是一个用户身份画像抽取器。你的工作：从两个来源（Claude 记忆 + Obsidian 知识库）通读用户的笔记和指令，抽取用户的身份画像，输出结构化 JSON。

抽取维度：
1. employment_status（求职状态）
   - current: 当前身份（学生/在岗/转型中）
   - target: 目标身份
   - timeline: 关键时间节点（秋招/入职/转型截止）
   - intentions: 意向公司列表（如果知识库里有）

2. current_products（当前产品组合）
   - name: 产品名
   - status: 已上线/开发中/已完成/已搁置
   - role: 用户在产品中的角色
   - tech_stack: 技术栈（如果有）
   - link: 生产地址或仓库（如果有）

3. track_judgments（赛道判断）
   - track: 赛道名（如"AI 记忆系统"/"AI 算力基础设施"/"AI 硬件"）
   - judgment: 关注中/待评估/已放弃/已投入
   - evidence: 判断依据（哪个调研/哪个项目）
   - note: 可能过时的标注（如果信息较旧）

4. long_term_goals（长期目标）
   - 具体的目标描述（不是"成功""自由"这种空话）

5. collaboration_patterns（协作偏好，可选）
   - 用户希望 AI 怎么跟 ta 协作（基于 CLAUDE.md 指令和过往复盘）

时间偏差处理原则：
- 每条信息必须标注 source（来源文件路径）和 freshness（年-月或具体日期）
- 更近的信息权重更高
- 如果某条信息可能过时（比如 3 个月前的求职状态，可能已变化），在 note 字段标注"可能已过时，需重新评估"
- 如果两个来源冲突，优先取更新的那个，但都保留并在 note 字段说明冲突

输出 JSON 格式：
```json
{
  "schema_version": "research-os-identity-v0.1",
  "extracted_at": "2026-07-02",
  "sources_read": [
    {"type": "claude_memory", "path": "~/.claude/CLAUDE.md", "read_at": "..."},
    {"type": "obsidian_vault", "path": "E:/obsidian/AI革命生存指南/", "files_read": N}
  ],
  "employment_status": {
    "current": "...",
    "target": "...",
    "timeline": "...",
    "intentions": ["..."],
    "source": "...",
    "freshness": "2026-07",
    "confidence": "high/medium/low",
    "note": ""
  },
  "current_products": [
    {"name": "...", "status": "...", "role": "...", "tech_stack": "...", "link": "...", "source": "...", "freshness": "..."}
  ],
  "track_judgments": [
    {"track": "...", "judgment": "...", "evidence": "...", "source": "...", "freshness": "...", "note": ""}
  ],
  "long_term_goals": ["..."],
  "collaboration_patterns": ["..."],
  "extraction_notes": "抽取过程中发现的冲突/疑点/需用户确认的事项"
}
```

只输出 JSON，不要加任何前后说明文字。"""


USER_PROMPT_TEMPLATE = """## 来源 1：Claude 记忆（CLAUDE.md + memory 文件）

{claude_memory_content}

## 来源 2：Obsidian 矩阵关键文件

{obsidian_content}

## 抽取任务

基于以上两个来源，抽取用户身份画像。注意：
1. 标注每条信息的 source（具体文件路径）和 freshness（年-月）
2. 可能过时的信息在 note 字段标注
3. 两个来源冲突时都保留，在 note 字段说明
4. long_term_goals 要具体（"一人公司终局"可以，"成功"不行）
5. 如果某条维度信息不足，就标 confidence: low，不要硬编

今天是 {today}。"""


def _read_claude_memory() -> str:
    """Read CLAUDE.md + ~/.claude/projects/.../memory/*.md"""
    lines = []

    # CLAUDE.md (global)
    claude_md = Path.home() / ".claude" / "CLAUDE.md"
    if claude_md.exists():
        lines.append(f"### 文件: {claude_md}")
        lines.append("```")
        lines.append(claude_md.read_text(encoding="utf-8-sig"))
        lines.append("```")
        lines.append("")

    # Memory files
    memory_dir = Path.home() / ".claude" / "projects" / "C--Users-19932" / "memory"
    if memory_dir.exists():
        for md in sorted(memory_dir.glob("*.md")):
            lines.append(f"### 文件: {md.name}")
            lines.append("```")
            content = md.read_text(encoding="utf-8-sig")
            # Cap each file to 2000 chars to keep total context manageable
            if len(content) > 2000:
                content = content[:2000] + "\n... (截断)"
            lines.append(content)
            lines.append("```")
            lines.append("")

    return "\n".join(lines) if lines else "(Claude 记忆为空或不可读)"


def _read_obsidian_vault() -> tuple[str, int]:
    """Read key Obsidian files. Returns (content, files_read_count)."""
    vault = Path("E:/obsidian/AI革命生存指南")
    if not vault.exists():
        return "(Obsidian 知识库路径不存在或不可访问)", 0

    # Priority files to read (curated based on structure survey)
    priority_files = [
        "01-身份/01-人格分析/自我画像.md",
        "01-身份/身份地图.md",
        "04-项目/项目地图.md",
        "04-项目/00-管理/当前项目总览.md",
        "04-项目/01-秋招/项目-暑期实习求职.md",
        "04-项目/02-一人公司/项目-一人公司备选计划.md",
    ]

    lines = []
    files_read = 0
    for rel in priority_files:
        path = vault / rel
        if not path.exists():
            continue
        lines.append(f"### 文件: {rel}")
        lines.append("```")
        content = path.read_text(encoding="utf-8-sig")
        # Cap each file to 3000 chars
        if len(content) > 3000:
            content = content[:3000] + "\n... (截断)"
        lines.append(content)
        lines.append("```")
        lines.append("")
        files_read += 1

    # Also scan 09-收件箱 for recent thinking (last modified, top 5)
    inbox = vault / "09-收件箱"
    if inbox.exists():
        recent = sorted(inbox.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
        for md in recent:
            lines.append(f"### 文件: 09-收件箱/{md.name}")
            lines.append("```")
            content = md.read_text(encoding="utf-8-sig")
            if len(content) > 1500:
                content = content[:1500] + "\n... (截断)"
            lines.append(content)
            lines.append("```")
            lines.append("")
            files_read += 1

    return ("\n".join(lines) if lines else "(Obsidian 关键文件为空)", files_read)


def extract_identity() -> dict[str, Any]:
    """Run identity extraction. Writes draft to ~/.research-os/identity.draft.json.
    Does NOT write identity.json — user must run accept_identity() to promote."""
    config.ensure_runtime_dirs()

    claude_memory = _read_claude_memory()
    obsidian_content, files_read = _read_obsidian_vault()

    user_prompt = USER_PROMPT_TEMPLATE.format(
        claude_memory_content=claude_memory,
        obsidian_content=obsidian_content,
        today=date.today().isoformat(),
    )

    result = llm_client.chat_json(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,  # low temp for factual extraction
        max_tokens=6000,
    )

    # Ensure required fields
    result.setdefault("schema_version", "research-os-identity-v0.1")
    result.setdefault("extracted_at", date.today().isoformat())
    result.setdefault("sources_read", [
        {"type": "claude_memory", "path": "~/.claude/CLAUDE.md + memory/", "read_at": date.today().isoformat()},
        {"type": "obsidian_vault", "path": "E:/obsidian/AI革命生存指南/", "read_at": date.today().isoformat(), "files_read": files_read},
    ])
    result.setdefault("employment_status", {})
    result.setdefault("current_products", [])
    result.setdefault("track_judgments", [])
    result.setdefault("long_term_goals", [])
    result.setdefault("collaboration_patterns", [])
    result.setdefault("extraction_notes", "")

    # Write draft (not identity.json — user must accept)
    draft_path = config.PROFILE_DIR / "identity.draft.json"
    draft_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return result


def accept_identity() -> bool:
    """Promote identity.draft.json to identity.json. Returns True if promoted."""
    config.ensure_runtime_dirs()
    draft_path = config.PROFILE_DIR / "identity.draft.json"
    identity_path = config.PROFILE_DIR / "identity.json"

    if not draft_path.exists():
        print("[FAIL] 没有 identity.draft.json。请先跑 `ros discover-identity`。", file=sys.stderr)
        return False

    # Read draft, update accepted_at, write identity.json
    draft = json.loads(draft_path.read_text(encoding="utf-8-sig"))
    draft["accepted_at"] = date.today().isoformat()
    identity_path.write_text(
        json.dumps(draft, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return True


def read_identity() -> dict[str, Any]:
    """Read accepted identity.json. Returns empty dict if not present."""
    config.ensure_runtime_dirs()
    identity_path = config.PROFILE_DIR / "identity.json"
    if not identity_path.exists():
        return {}
    try:
        return json.loads(identity_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def render_identity_summary(identity: dict[str, Any]) -> str:
    """Render identity as human-readable summary for terminal display."""
    lines = ["=" * 60, "用户身份画像（草稿，待审核）", "=" * 60, ""]

    emp = identity.get("employment_status", {})
    if emp:
        lines.append("【求职状态】")
        lines.append(f"  当前: {emp.get('current', '?')}")
        lines.append(f"  目标: {emp.get('target', '?')}")
        lines.append(f"  时间线: {emp.get('timeline', '?')}")
        intentions = emp.get("intentions", [])
        if intentions:
            lines.append(f"  意向: {', '.join(intentions[:5])}")
        lines.append(f"  来源: {emp.get('source', '?')}")
        lines.append(f"  新鲜度: {emp.get('freshness', '?')}")
        if emp.get("note"):
            lines.append(f"  注: {emp['note']}")
        lines.append("")

    products = identity.get("current_products", [])
    if products:
        lines.append(f"【当前产品组合】({len(products)} 个)")
        for p in products:
            status = p.get("status", "?")
            name = p.get("name", "?")
            role = p.get("role", "")
            freshness = p.get("freshness", "?")
            lines.append(f"  - {name} [{status}] — {role} ({freshness})")
        lines.append("")

    tracks = identity.get("track_judgments", [])
    if tracks:
        lines.append(f"【赛道判断】({len(tracks)} 条)")
        for t in tracks:
            track = t.get("track", "?")
            judgment = t.get("judgment", "?")
            evidence = t.get("evidence", "")
            freshness = t.get("freshness", "?")
            note = t.get("note", "")
            line = f"  - {track}: {judgment} ({freshness})"
            if evidence:
                line += f" — {evidence}"
            if note:
                line += f" ⚠️ {note}"
            lines.append(line)
        lines.append("")

    goals = identity.get("long_term_goals", [])
    if goals:
        lines.append("【长期目标】")
        for g in goals:
            lines.append(f"  - {g}")
        lines.append("")

    patterns = identity.get("collaboration_patterns", [])
    if patterns:
        lines.append("【协作偏好】")
        for p in patterns:
            lines.append(f"  - {p}")
        lines.append("")

    notes = identity.get("extraction_notes", "")
    if notes:
        lines.append("【抽取笔记（冲突/疑点）】")
        lines.append(f"  {notes}")
        lines.append("")

    lines.append("=" * 60)
    lines.append("如果以上画像准确，跑 `ros accept-identity` 确认。")
    lines.append("如果需要修订，手动编辑 ~/.research-os/identity.draft.json 后再 accept。")
    lines.append("=" * 60)

    return "\n".join(lines)


if __name__ == "__main__":
    result = extract_identity()
    print(render_identity_summary(result))
