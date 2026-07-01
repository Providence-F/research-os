#!/usr/bin/env python3
"""Build reader-first black/white HTML from Research OS final-report.md."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path
from typing import Any

from research_planner import update_state
from research_status import infer_status


APPENDIX_KEYWORDS = [
    "附录",
    "证据标准",
    "信息淘汰说明",
    "核心事实表",
    "结论溯源表",
    "反方审计摘要",
    "来源与附录",
    "最终置信度",
]

CSS = """
:root {
  --bg: #fff;
  --fg: #111;
  --muted: #666;
  --line: #d8d8d8;
  --soft: #f6f6f6;
  --soft2: #fafafa;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: 16px;
  line-height: 1.75;
}
a { color: var(--fg); text-decoration: none; border-bottom: 1px solid var(--line); }
a:hover { border-bottom-color: var(--fg); }
.layout { display: grid; grid-template-columns: 260px minmax(0, 980px); gap: 40px; max-width: 1340px; margin: 0 auto; padding: 40px 28px 88px; }
aside { position: sticky; top: 24px; align-self: start; border-right: 1px solid var(--line); padding-right: 24px; max-height: calc(100vh - 48px); overflow: auto; }
main { min-width: 0; }
.kicker { color: var(--muted); font-size: 13px; letter-spacing: 1.4px; text-transform: uppercase; margin-bottom: 10px; }
h1 { font-size: 34px; line-height: 1.2; margin: 0 0 16px; letter-spacing: -0.8px; }
.subtitle { color: var(--muted); font-size: 14px; margin-bottom: 32px; }
.toc-title { font-size: 13px; color: var(--muted); letter-spacing: 1.2px; text-transform: uppercase; margin: 0 0 12px; }
.toc { list-style: none; padding: 0; margin: 0; font-size: 14px; }
.toc li { margin: 7px 0; }
.chapter { padding: 34px 0; border-top: 1px solid var(--line); }
.chapter:first-of-type { border-top: 2px solid var(--fg); }
.chapter h2 { font-size: 24px; line-height: 1.25; margin: 0 0 20px; letter-spacing: -0.4px; }
h3 { font-size: 18px; margin: 28px 0 10px; }
h4 { font-size: 16px; margin: 20px 0 8px; }
p { margin: 12px 0; }
ul, ol { padding-left: 24px; }
li { margin: 6px 0; }
blockquote { margin: 18px 0; padding: 12px 18px; border-left: 3px solid var(--fg); background: var(--soft); color: var(--muted); }
code { font-family: "JetBrains Mono", Consolas, monospace; font-size: 13px; background: var(--soft); padding: 2px 6px; border: 1px solid var(--line); }
pre { overflow: auto; background: var(--soft); border: 1px solid var(--line); padding: 14px; }
pre code { border: 0; padding: 0; background: transparent; }
pre.mermaid { background: #fff; border: 1px solid var(--line); padding: 18px; text-align: center; margin: 22px 0; overflow: visible; }
hr { border: 0; border-top: 1px dashed var(--line); margin: 28px 0; }
.analogy-card { display: grid; grid-template-columns: 1fr auto 1fr; gap: 14px; align-items: center; margin: 18px 0; padding: 16px 20px; border: 1px solid var(--line); background: var(--soft2); }
.analogy-x { font-weight: 650; }
.analogy-arrow { color: var(--muted); font-size: 22px; }
.analogy-y { color: var(--muted); font-style: italic; }
.code-snippet-card { margin: 18px 0; border: 1px solid var(--line); }
.code-snippet-meta { background: var(--soft); padding: 8px 14px; font-size: 12px; color: var(--muted); border-bottom: 1px solid var(--line); font-family: monospace; }
.code-snippet-card pre { margin: 0; border: 0; background: #fff; }
table { border-collapse: collapse; width: 100%; margin: 18px 0; font-size: 14px; }
th, td { border: 1px solid var(--line); padding: 9px 10px; text-align: left; vertical-align: top; }
th { background: var(--soft); font-weight: 650; }
.details-wrap { margin: 22px 0; border: 1px solid var(--line); background: #fff; }
details summary { cursor: pointer; padding: 14px 18px; font-weight: 650; user-select: none; }
details summary::before { content: "+ "; color: var(--muted); font-family: monospace; }
details[open] summary::before { content: "- "; }
.details-body { padding: 0 18px 20px; border-top: 1px solid var(--line); }
.toolbar { display: flex; gap: 10px; flex-wrap: wrap; margin: 22px 0 34px; }
button, input { border: 1px solid var(--fg); background: #fff; color: var(--fg); padding: 8px 12px; font: inherit; font-size: 13px; }
button { cursor: pointer; }
button:hover, button.active { background: var(--fg); color: #fff; }
input { width: min(100%, 360px); }
footer { color: var(--muted); font-size: 12px; border-top: 1px solid var(--line); padding-top: 18px; margin-top: 36px; }
.dashboard { border-top: 2px solid var(--fg); padding: 30px 0 8px; margin-bottom: 18px; }
.vm-hero { border: 1px solid var(--fg); padding: 24px; background: var(--soft2); margin-bottom: 18px; }
.vm-hero .label { color: var(--muted); font-size: 12px; letter-spacing: 1.2px; text-transform: uppercase; }
.hero-verdict { font-size: 34px; line-height: 1.15; font-weight: 750; margin: 8px 0 10px; letter-spacing: -0.8px; }
.hero-summary { max-width: 760px; color: #222; }
.hero-meta { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
.pill { display: inline-flex; align-items: center; min-height: 26px; padding: 2px 9px; border: 1px solid var(--line); background: #fff; color: var(--muted); font-size: 12px; }
.section-label { margin: 26px 0 12px; font-size: 13px; color: var(--muted); letter-spacing: 1.2px; text-transform: uppercase; }
.summary-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 12px 0 24px; }
.summary-card { border: 1px solid var(--line); padding: 16px; min-height: 96px; background: #fff; }
.summary-card .label { color: var(--muted); font-size: 13px; margin-bottom: 8px; }
.summary-card .value { font-weight: 700; line-height: 1.45; }
.object-tools, .table-tools { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin: 10px 0 14px; }
.object-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin: 12px 0 28px; }
.object-card { border: 1px solid var(--line); background: #fff; padding: 16px; cursor: pointer; min-height: 210px; display: flex; flex-direction: column; gap: 10px; }
.object-card:hover, .object-card:focus { outline: 0; border-color: var(--fg); box-shadow: 0 0 0 1px var(--fg) inset; }
.object-card .topline { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.object-card h3 { margin: 0; font-size: 20px; line-height: 1.25; }
.rank { border: 1px solid var(--fg); min-width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; }
.card-meta { color: var(--muted); font-size: 13px; }
.card-line { font-size: 14px; color: #222; }
.card-fields { display: grid; gap: 6px; margin-top: auto; font-size: 13px; }
.card-fields div { display: grid; grid-template-columns: 74px minmax(0, 1fr); gap: 8px; }
.card-fields span:first-child { color: var(--muted); }
.strategy-tabs { border: 1px solid var(--line); margin: 12px 0 28px; }
.tab-buttons { display: flex; flex-wrap: wrap; border-bottom: 1px solid var(--line); }
.tab-buttons button { border: 0; border-right: 1px solid var(--line); }
.tab-panel { display: none; padding: 18px; }
.tab-panel.active { display: block; }
.matrix-wrap, .filterable-table-wrap { overflow: auto; margin: 12px 0 28px; }
.full-report-note { color: var(--muted); font-size: 14px; margin-bottom: 18px; }
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,.54); display: none; align-items: center; justify-content: center; padding: 24px; z-index: 20; }
.modal-backdrop.open { display: flex; }
.modal { width: min(920px, 100%); max-height: min(86vh, 920px); overflow: auto; background: #fff; border: 1px solid var(--fg); padding: 22px; box-shadow: 0 16px 60px rgba(0,0,0,.24); }
.modal-head { display: flex; justify-content: space-between; gap: 16px; border-bottom: 1px solid var(--line); padding-bottom: 12px; margin-bottom: 14px; }
.modal h2 { margin: 0; font-size: 26px; }
.modal-block { border-top: 1px solid var(--line); padding-top: 12px; margin-top: 12px; }
.modal-block h4 { margin: 0 0 8px; color: var(--muted); font-size: 13px; letter-spacing: 1px; text-transform: uppercase; }
@media (max-width: 1000px) {
  .layout { display: block; padding: 28px 18px 72px; }
  aside { position: static; border-right: 0; border-bottom: 1px solid var(--line); padding: 0 0 20px; margin-bottom: 24px; max-height: none; }
  h1, .hero-verdict { font-size: 28px; }
  .summary-grid, .object-grid { grid-template-columns: 1fr; }
}
"""


def clean_emoji(s: str) -> str:
    return re.sub(r"[\U0001F300-\U0001FAFF☀-➿]", "", s or "")


def inline_md(text: Any) -> str:
    text = html.escape(str(text or ""))
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<a href=\"\2\">\1</a>", text)
    return text


def slug(text: str) -> str:
    s = re.sub(r"<.*?>", "", text)
    s = re.sub(r"[^\w一-鿿]+", "-", s).strip("-").lower()
    return s or "section"


def split_sections(md: str):
    lines = md.splitlines()
    title = None
    intro = []
    sections = []
    current_title = None
    current_lines = []

    for line in lines:
        h1 = re.match(r"^#\s+(.+)$", line)
        h2 = re.match(r"^##\s+(.+)$", line)
        if h1 and title is None:
            title = h1.group(1).strip()
            continue
        if h2:
            if current_title is not None:
                sections.append((current_title, "\n".join(current_lines)))
            elif current_lines:
                intro.extend(current_lines)
            current_title = h2.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_title is not None:
        sections.append((current_title, "\n".join(current_lines)))
    elif current_lines:
        intro.extend(current_lines)
    return title, "\n".join(intro), sections


def md_block_to_html(md: str) -> str:
    md = clean_emoji(md or "")
    lines = md.splitlines()
    out = []
    para = []
    in_ul = False
    in_table = False
    in_code = False
    code_lines = []
    is_mermaid = False
    code_lang = ""

    def flush_para():
        nonlocal para
        if para:
            out.append("<p>" + inline_md(" ".join(para).strip()) + "</p>")
            para = []

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    def close_table():
        nonlocal in_table
        if in_table:
            out.append("</tbody></table>")
            in_table = False

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_para(); close_ul(); close_table()
            if not in_code:
                in_code = True
                code_lines = []
                code_lang = stripped[3:].strip().lower()
                is_mermaid = code_lang == "mermaid"
            else:
                if is_mermaid:
                    out.append('<pre class="mermaid">' + "\n".join(code_lines) + '</pre>')
                else:
                    out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                in_code = False
                is_mermaid = False
                code_lang = ""
            continue
        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            flush_para(); close_ul(); close_table()
            continue

        if stripped == "---":
            flush_para(); close_ul(); close_table(); out.append("<hr>"); continue

        if stripped.startswith("|") and stripped.endswith("|"):
            flush_para(); close_ul()
            cells = [inline_md(c.strip()) for c in stripped.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells):
                continue
            if not in_table:
                out.append("<table><tbody>")
                in_table = True
                out.append("<tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr>")
            else:
                out.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
            continue
        close_table()

        h = re.match(r"^(#{3,6})\s+(.+)$", stripped)
        if h:
            flush_para(); close_ul(); close_table()
            level = min(len(h.group(1)), 6)
            out.append(f"<h{level}>{inline_md(h.group(2))}</h{level}>")
            continue

        if stripped.startswith(">"):
            flush_para(); close_ul(); close_table()
            out.append("<blockquote>" + inline_md(stripped.lstrip("> ")) + "</blockquote>")
            continue

        if re.match(r"^[-*]\s+", stripped):
            flush_para(); close_table()
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append("<li>" + inline_md(re.sub(r"^[-*]\s+", "", stripped)) + "</li>")
            continue

        if re.match(r"^\d+\.\s+", stripped):
            flush_para(); close_ul(); close_table()
            out.append("<p>" + inline_md(stripped) + "</p>")
            continue

        para.append(stripped)

    flush_para(); close_ul(); close_table()
    return "\n".join(out)


def is_appendix(title: str) -> bool:
    return any(k in title for k in APPENDIX_KEYWORDS)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_state(project: Path) -> dict[str, Any]:
    try:
        return load_json(project / "research_state.json")
    except json.JSONDecodeError:
        return {}


def load_view_model(project: Path) -> dict[str, Any] | None:
    path = project / "07-output" / "view-model.json"
    if not path.exists():
        return None
    try:
        data = load_json(path)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    has_content = any(data.get(k) for k in ("hero", "summary_cards", "object_cards", "strategy_tabs", "comparison_matrix", "filterable_table"))
    return data if has_content else None


def render_list(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, list):
        return "<ul>" + "".join(f"<li>{inline_md(v)}</li>" for v in value if str(v).strip()) + "</ul>"
    if isinstance(value, dict):
        return "<ul>" + "".join(f"<li><strong>{inline_md(k)}</strong>：{inline_md(v)}</li>" for k, v in value.items() if str(v).strip()) + "</ul>"
    text = str(value)
    return md_block_to_html(text) if "\n" in text else f"<p>{inline_md(text)}</p>"


def render_hero(model: dict[str, Any]) -> str:
    hero = model.get("hero") or {}
    verdict = hero.get("verdict") or model.get("verdict") or ""
    summary = hero.get("summary") or model.get("summary") or ""
    meta = hero.get("meta") or []
    if not verdict and not summary and not meta:
        return ""
    return f"""
    <section class="vm-hero">
      <div class="label">Decision / Verdict</div>
      <div class="hero-verdict">{inline_md(verdict)}</div>
      <div class="hero-summary">{inline_md(summary)}</div>
      <div class="hero-meta">{''.join(f'<span class="pill">{inline_md(item)}</span>' for item in meta)}</div>
    </section>
    """


def render_summary_cards(cards: list[dict[str, Any]]) -> str:
    if not cards:
        return ""
    items = []
    for card in cards:
        label = card.get("label") or card.get("title") or ""
        value = card.get("value") or card.get("summary") or card.get("body") or ""
        items.append(f"<article class='summary-card'><div class='label'>{inline_md(label)}</div><div class='value'>{inline_md(value)}</div></article>")
    return f"<div class='section-label'>Key Cards</div><section class='summary-grid'>{''.join(items)}</section>"


def object_search_text(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False).lower()


def render_card_fields(obj: dict[str, Any]) -> str:
    fields = [
        ("方向", obj.get("type") or obj.get("category") or obj.get("direction")),
        ("MVP", obj.get("mvp")),
        ("升级", obj.get("upgrade")),
        ("风险", obj.get("risk")),
        ("价值", obj.get("portfolio_value") or obj.get("employment_value") or obj.get("value")),
    ]
    rows = [f"<div><span>{inline_md(label)}</span><span>{inline_md(value)}</span></div>" for label, value in fields if value]
    return "<div class='card-fields'>" + "".join(rows) + "</div>" if rows else ""


def render_object_cards(cards: list[dict[str, Any]], kind: str = "object") -> str:
    if not cards:
        return ""
    rendered = []
    for idx, obj in enumerate(cards):
        name = obj.get("name") or obj.get("title") or f"对象 {idx + 1}"
        priority = obj.get("priority") or obj.get("rank") or idx + 1
        tag = obj.get("fit") or obj.get("tier") or obj.get("type") or obj.get("category") or ""
        one_liner = obj.get("one_liner") or obj.get("summary") or obj.get("judgement") or obj.get("判断") or ""
        rendered.append(f"""
        <article class="object-card {kind}-card" tabindex="0" role="button" data-index="{idx}" data-search="{html.escape(object_search_text(obj), quote=True)}">
          <div class="topline"><h3>{inline_md(name)}</h3><span class="rank">{inline_md(priority)}</span></div>
          <div class="card-meta">{inline_md(tag)}</div>
          <div class="card-line">{inline_md(one_liner)}</div>
          {render_card_fields(obj)}
        </article>
        """)
    return f"""
    <div class="section-label">Object Cards</div>
    <div class="object-tools">
      <input id="objectSearch" type="search" placeholder="筛选卡片：导师 / 风险 / 方向 / 价值" oninput="filterCards(this.value)">
      <span class="pill" id="objectCount">{len(cards)} cards</span>
    </div>
    <section class="object-grid" id="objectGrid">{''.join(rendered)}</section>
    """


def normalize_tabs(raw_tabs: Any) -> list[dict[str, Any]]:
    tabs = raw_tabs or []
    out = []
    for item in tabs:
        if isinstance(item, str):
            out.append({"title": item, "body": ""})
        elif isinstance(item, dict):
            out.append(item)
    return out


def render_tabs(raw_tabs: Any) -> str:
    tabs = normalize_tabs(raw_tabs)
    if not tabs:
        return ""
    buttons = []
    panels = []
    for idx, tab in enumerate(tabs):
        title = tab.get("title") or tab.get("label") or f"策略 {idx + 1}"
        body = tab.get("body") or tab.get("summary") or tab.get("content") or tab.get("items") or ""
        active = " active" if idx == 0 else ""
        buttons.append(f"<button class='{active.strip()}' onclick='switchTab(" + str(idx) + f")'>{inline_md(title)}</button>")
        panels.append(f"<div class='tab-panel{active}' data-tab='{idx}'>{render_list(body)}</div>")
    return f"<div class='section-label'>Strategy Tabs</div><section class='strategy-tabs'><div class='tab-buttons'>{''.join(buttons)}</div>{''.join(panels)}</section>"


def normalize_matrix(raw: Any) -> tuple[list[str], list[Any]]:
    if isinstance(raw, dict):
        columns = raw.get("columns") or []
        rows = raw.get("rows") or []
    elif isinstance(raw, list):
        rows = raw
        columns = list(rows[0].keys()) if rows and isinstance(rows[0], dict) else []
    else:
        columns, rows = [], []
    if rows and not columns and isinstance(rows[0], dict):
        columns = list(rows[0].keys())
    return columns, rows


def render_matrix(raw_matrix: Any) -> str:
    columns, rows = normalize_matrix(raw_matrix)
    if not columns or not rows:
        return ""
    body = []
    for row in rows:
        if isinstance(row, dict):
            cells = [row.get(col, "") for col in columns]
        else:
            cells = row if isinstance(row, list) else [row]
        body.append("<tr>" + "".join(f"<td>{inline_md(cell)}</td>" for cell in cells) + "</tr>")
    return f"""
    <div class="section-label">Comparison Matrix</div>
    <div class="matrix-wrap"><table class="comparison-matrix">
      <thead><tr>{''.join(f'<th>{inline_md(col)}</th>' for col in columns)}</tr></thead>
      <tbody>{''.join(body)}</tbody>
    </table></div>
    """


def render_filterable_table(raw_table: Any) -> str:
    if not isinstance(raw_table, dict):
        return ""
    rows = raw_table.get("rows") or []
    if not rows:
        return ""
    columns = raw_table.get("columns") or list(rows[0].keys())
    body = []
    for row in rows:
        search = html.escape(json.dumps(row, ensure_ascii=False).lower(), quote=True)
        body.append("<tr data-search='" + search + "'>" + "".join(f"<td>{inline_md(row.get(col, ''))}</td>" for col in columns) + "</tr>")
    return f"""
    <div class="section-label">Filterable Table</div>
    <div class="table-tools"><input type="search" placeholder="筛选表格" oninput="filterTable(this.value)"></div>
    <div class="filterable-table-wrap"><table id="filterableTable">
      <thead><tr>{''.join(f'<th>{inline_md(col)}</th>' for col in columns)}</tr></thead>
      <tbody>{''.join(body)}</tbody>
    </table></div>
    """


def render_modal_shell() -> str:
    return """
    <div class="modal-backdrop" id="objectModal" onclick="if(event.target===this) closeObjectModal()">
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modalTitle">
        <div class="modal-head"><h2 id="modalTitle"></h2><button onclick="closeObjectModal()">关闭</button></div>
        <div id="modalBody"></div>
      </div>
    </div>
    """


def render_dashboard(model: dict[str, Any]) -> str:
    cards = model.get("object_cards") or model.get("advisor_cards") or model.get("objects") or []
    table = model.get("filterable_table") or {}
    matrix = model.get("comparison_matrix") or model.get("matrix") or {}
    parts = [
        "<section class='dashboard' id='dashboard'>",
        render_hero(model),
        render_summary_cards(model.get("summary_cards") or []),
        render_object_cards(cards, model.get("object_kind") or "object"),
        render_tabs(model.get("strategy_tabs") or model.get("tabs") or []),
        render_matrix(matrix),
        render_filterable_table(table),
        "</section>",
    ]
    return "\n".join(part for part in parts if part)


def render_sections(sections: list[tuple[str, str]]) -> tuple[list[tuple[str, str]], str]:
    toc = []
    used = set()
    section_html = []
    for idx, (section_title, body) in enumerate(sections, start=1):
        anchor = slug(section_title)
        if anchor in used:
            anchor = f"{anchor}-{idx}"
        used.add(anchor)
        toc.append((anchor, section_title))
        body_html = md_block_to_html(body)
        if is_appendix(section_title):
            section_html.append(
                f"<section class='chapter' id='{anchor}'><details class='details-wrap'>"
                f"<summary>{inline_md(section_title)}</summary><div class='details-body'>{body_html}</div>"
                f"</details></section>"
            )
        else:
            section_html.append(
                f"<section class='chapter' id='{anchor}'><h2>{inline_md(section_title)}</h2>{body_html}</section>"
            )
    return toc, "".join(section_html)


def script_for_model(model: dict[str, Any] | None) -> str:
    objects = []
    if model:
        objects = model.get("object_cards") or model.get("advisor_cards") or model.get("objects") or []
    data = json.dumps(objects, ensure_ascii=False).replace("</", "<\\/")
    return f"""
<script>
const OBJECTS = {data};
function esc(s){{return String(s ?? '').replace(/[&<>'\"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','\"':'&quot;'}}[c]));}}
function htmlOf(v){{
  if(Array.isArray(v)) return '<ul>'+v.filter(Boolean).map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>';
  if(v && typeof v==='object') return '<ul>'+Object.entries(v).filter(([k,val])=>val).map(([k,val])=>'<li><strong>'+esc(k)+'</strong>：'+esc(val)+'</li>').join('')+'</ul>';
  return '<p>'+esc(v || '')+'</p>';
}}
function filterCards(q){{
  q=String(q||'').toLowerCase();
  let shown=0;
  document.querySelectorAll('.object-card').forEach(card=>{{
    const ok=card.dataset.search.includes(q);
    card.style.display=ok?'flex':'none';
    if(ok) shown++;
  }});
  const count=document.getElementById('objectCount');
  if(count) count.textContent=shown+' cards';
}}
function openObjectModal(i){{
  const obj=OBJECTS[i]; if(!obj) return;
  document.getElementById('modalTitle').textContent=obj.name || obj.title || ('对象 '+(i+1));
  const skip=new Set(['name','title','priority','rank','one_liner','summary']);
  const blocks=Object.entries(obj).filter(([k,v])=>!skip.has(k)&&v!==''&&v!==null&&v!==undefined).map(([k,v])=>'<div class="modal-block"><h4>'+esc(k)+'</h4>'+htmlOf(v)+'</div>').join('');
  document.getElementById('modalBody').innerHTML=(obj.summary||obj.one_liner?'<p>'+esc(obj.summary||obj.one_liner)+'</p>':'')+blocks;
  document.getElementById('objectModal').classList.add('open');
}}
function closeObjectModal(){{const el=document.getElementById('objectModal'); if(el) el.classList.remove('open');}}
function switchTab(idx){{
  document.querySelectorAll('.tab-buttons button').forEach((b,i)=>b.classList.toggle('active',i===idx));
  document.querySelectorAll('.tab-panel').forEach(p=>p.classList.toggle('active',Number(p.dataset.tab)===idx));
}}
function filterTable(q){{
  q=String(q||'').toLowerCase();
  document.querySelectorAll('#filterableTable tbody tr').forEach(row=>{{row.style.display=row.dataset.search.includes(q)?'':'none';}});
}}
function appendixDetails(){{return [...document.querySelectorAll('details.details-wrap')];}}
function setAppendixStatus(text){{const el=document.getElementById('appendixStatus'); if(el) el.textContent=text;}}
function expandAppendices(){{
  const items=appendixDetails();
  items.forEach(d=>d.open=true);
  setAppendixStatus(items.length ? '已展开 '+items.length+' 个附录' : '没有可展开的附录');
  if(items[0]) items[0].scrollIntoView({{behavior:'smooth', block:'start'}});
}}
function collapseAppendices(){{
  const items=appendixDetails();
  items.forEach(d=>d.open=false);
  setAppendixStatus(items.length ? '已折叠 '+items.length+' 个附录' : '没有可折叠的附录');
}}
document.addEventListener('DOMContentLoaded',()=>{{
  document.querySelectorAll('.object-card').forEach(card=>{{
    const open=()=>openObjectModal(Number(card.dataset.index));
    card.addEventListener('click',open);
    card.addEventListener('keydown',e=>{{if(e.key==='Enter'||e.key===' '){{e.preventDefault();open();}}}});
  }});
  document.addEventListener('keydown',e=>{{if(e.key==='Escape') closeObjectModal();}});
}});
</script>
"""


def _sync_state_after_build(project: Path) -> None:
    """Sync research_state.json after HTML build.

    Without this, state.json keeps next_required_action="build_html" even after
    index.html exists. update_state() recomputes next_required_action by checking
    file existence, so it will correctly return "none" once HTML is built.

    Also upgrades status: planned/in_progress → completed (if 0 FAIL) or failed
    (if FAIL). Without this, status stays "planned" forever even after build.
    """
    state_path = project / "research_state.json"
    if not state_path.exists():
        return
    try:
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return
    outputs = state.setdefault("outputs", [])
    if "08-html/index.html" not in outputs:
        outputs.append("08-html/index.html")
    update_state(project, state)
    # update_state rewrote state.json; reload and stamp status on top.
    try:
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return
    state["status"] = infer_status(project, state)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def build(project: Path, copy_desktop: bool = False) -> Path:
    report = project / "07-output" / "final-report.md"
    if not report.exists():
        raise FileNotFoundError(f"missing {report}")
    out = project / "08-html" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)

    md = report.read_text(encoding="utf-8-sig")
    title, intro, sections = split_sections(md)
    state = load_state(project)
    view_model = load_view_model(project)
    toc, section_html = render_sections(sections)
    toc_items = [("dashboard", "可视化总览")] if view_model else []
    toc_items += [("full-report", "完整正文")] + toc if view_model else toc

    dashboard = render_dashboard(view_model) if view_model else ""
    modal = render_modal_shell() if view_model else ""
    full_report_open = "<section class='chapter' id='full-report'><h2>完整正文</h2><div class='full-report-note'>下方保留 07-output/final-report.md 的完整正文，方便存档和逐段阅读。</div>" if view_model else ""
    full_report_close = "</section>" if view_model else ""

    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(clean_emoji(title))}</title>
  <style>{CSS}</style>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
</head>
<body data-source="final-report.md" data-view-type="{html.escape(str(state.get('view_type', '')))}">
  <div class="layout">
    <aside>
      <div class="toc-title">目录</div>
      <ol class="toc">
        {''.join(f'<li><a href="#{a}">{inline_md(t)}</a></li>' for a, t in toc_items)}
      </ol>
      <div class="toolbar">
        <button type="button" onclick="expandAppendices()">展开附录</button>
        <button type="button" onclick="collapseAppendices()">折叠附录</button>
        <span class="pill" id="appendixStatus">附录默认折叠</span>
      </div>
    </aside>
    <main>
      <div class="kicker">Research OS Reader Report</div>
      <h1>{inline_md(title)}</h1>
      <div class="subtitle">由 07-output/final-report.md 生成 · 黑白极简 · 结构化视图优先 · 完整正文保留</div>
      {dashboard}
      {full_report_open}
      {md_block_to_html(intro)}
      {section_html}
      {full_report_close}
      <footer>Source: 07-output/final-report.md · View model: 07-output/view-model.json · Generated by build_research_html.py</footer>
    </main>
  </div>
  {modal}
  {script_for_model(view_model)}
  <script>mermaid.initialize({{startOnLoad: true, theme: 'neutral', securityLevel: 'loose'}});</script>
</body>
</html>
"""
    out.write_text(html_doc, encoding="utf-8")

    _sync_state_after_build(project)

    if copy_desktop:
        desktop = Path.home() / "Desktop" / f"{title}.html"
        shutil.copy2(out, desktop)
        print(f"Copied desktop HTML: {desktop}")

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Research OS reader-first HTML")
    parser.add_argument("--project", required=True, help="Path to research project directory")
    parser.add_argument("--copy-desktop", action="store_true", help="Copy output HTML to Desktop")
    args = parser.parse_args()

    out = build(Path(args.project).resolve(), args.copy_desktop)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
