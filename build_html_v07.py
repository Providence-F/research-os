#!/usr/bin/env python3
"""Research OS v0.8 - HTML Builder

v0.8 升级（从 v0.7）：
  1. LaTeX公式渲染：引入MathJax 3 CDN，支持$...$行内公式和$$...$$块级公式
  2. inline()函数公式保护：提取$...$公式后再处理其他格式，防止*和#正则破坏LaTeX
  3. md_to_html()块级公式处理：识别$$...$$独占行，输出为math-display div
  4. CSS添加.math-display样式：居中显示、背景色区分、横向滚动

v0.7 升级（从 v0.6）：
  1. 通用化：命令行参数接收项目路径（不再硬编码特赞项目）
  2. 固化美学规范：CSS 中标注 LOCKED 区块，禁止修改关键规则
  3. 滚轮永久禁止：aside.toc overflow: hidden（LOCKED）
  4. 附录 div 闭合自动修复：用 regex 检测并修复未闭合 div
  5. 动态可视化识别：从报告内容自动识别"四层/三层架构"、"N大功能"、"工作流"、"家族"等模式
  6. 信息来源自动压缩：检测多个连续表格，自动应用紧凑样式
  7. 验证集成：构建后自动运行 HTML_FORBIDDEN_PATTERNS 检查

设计哲学：Smart Agent. Dumb Tools.
工具做机械转换，可视化组件由报告内容驱动（不硬编码产品名）。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ============================================================
# v0.7 CSS - 固化美学规范
# ============================================================

CSS = """
:root {
  --bg: #faf9f5;
  --bg-card: #ffffff;
  --bg-soft: #f5f4ee;
  --fg: #1a1a1a;
  --fg-soft: #3d3d3d;
  --muted: #6b6b6b;
  --muted-2: #8e8e8e;
  --line: #e5e3d8;
  --line-soft: #ede9dd;
  --accent: #b85b44;
  --accent-soft: #f5e8e0;
  --accent-bg: #fdf6f0;
  --note: #2c5f8d; --note-bg: #eef4fa;
  --tip: #5d4ba0; --tip-bg: #f0ecf7;
  --caution: #b8732e; --caution-bg: #fbf0e0;
  --ok: #4a7a4a; --ok-bg: #eef5ee;
  --font-serif: "Lora", "Noto Serif SC", Georgia, serif;
  --font-sans: "Inter", -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-mono: "JetBrains Mono", Consolas, monospace;
  --reader-width: 72rem;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  background: var(--bg);
  color: var(--fg);
  font-family: var(--font-serif);
  font-size: 16px;
  line-height: 1.75;
  -webkit-font-smoothing: antialiased;
}
.reading-progress {
  position: fixed; top: 0; left: 0;
  height: 2px; background: var(--accent);
  width: 0; z-index: 50;
  transition: width 0.1s ease-out;
}
.page-shell {
  max-width: 1600px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 16rem minmax(0, 1fr);
  min-height: 100vh;
}

/* ===== 目录栏样式（v1.1 修复：支持滚动） =====
 * v0.7 问题：overflow: hidden 导致长目录被截断不可见
 * v1.1 修复：overflow-y: auto + 隐藏滚动条，保留滚动功能不影响美观
 * 验证器同步更新：aside.toc 允许 overflow-y: auto
 */
aside.toc {
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  scrollbar-width: none;  /* Firefox: 隐藏滚动条 */
  -ms-overflow-style: none;  /* IE/Edge: 隐藏滚动条 */
  padding: 2rem 1.5rem;
  border-right: 1px solid var(--line);
  background: var(--bg);
}
aside.toc::-webkit-scrollbar {
  display: none;  /* Chrome/Safari: 隐藏滚动条 */
}
aside.toc .toc-title {
  font-family: var(--font-sans);
  font-size: 11.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  margin-bottom: 1rem;
}
aside.toc nav a {
  display: block;
  padding: 0.35rem 0;
  font-family: var(--font-sans);
  font-size: 13.5px;
  color: var(--fg-soft);
  text-decoration: none;
  border-left: 2px solid transparent;
  padding-left: 0.75rem;
  transition: all 0.15s;
}
aside.toc nav a:hover { color: var(--accent); border-left-color: var(--accent); }
aside.toc nav a.sub { padding-left: 1.5rem; font-size: 12.5px; color: var(--muted); }
aside.toc nav a.active { color: var(--accent); border-left-color: var(--accent); font-weight: 600; background: rgba(184, 91, 68, 0.06); }
/* ===== LOCKED END ===== */

main {
  padding: 2.5rem 4rem 6rem;
  max-width: var(--reader-width);
}
h1 { font-size: 38px; line-height: 1.15; font-weight: 700; margin-bottom: 1.5rem; color: var(--fg); }
h2 {
  font-size: 26px; line-height: 1.25; font-weight: 600;
  margin-top: 3rem; margin-bottom: 1rem;
  color: var(--fg);
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--line);
}
h3 { font-size: 19px; font-weight: 600; margin-top: 2rem; margin-bottom: 0.75rem; color: var(--fg); }
h4 {
  font-size: 14px; font-weight: 600;
  margin-top: 1rem; margin-bottom: 0.5rem;
  color: var(--fg-soft);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
p { margin-bottom: 1rem; color: var(--fg); }
ul, ol { margin: 0.5rem 0 1rem 1.5rem; }
li { margin-bottom: 0.3rem; }
strong { color: var(--accent); font-weight: 600; }
em { color: var(--fg-soft); }
.vm-hero {
  border-left: 3px solid var(--accent);
  padding: 0.5rem 0 0.5rem 1.5rem;
  margin-bottom: 3rem;
}
.kicker {
  font-family: var(--font-sans);
  font-size: 11.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--accent);
  margin-bottom: 0.75rem;
}
.hero-verdict { font-size: 30px; font-weight: 600; line-height: 1.25; margin-bottom: 1rem; color: var(--fg); }
.hero-summary { font-size: 16px; color: var(--fg-soft); margin-bottom: 1rem; max-width: 60rem; }
.badge {
  display: inline-block;
  font-family: var(--font-sans);
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--accent-soft);
  color: var(--accent);
  margin-left: 0.5rem;
  vertical-align: middle;
}
.badge-v07 { background: #4a7a4a; color: white; }
table {
  border-collapse: collapse;
  width: 100%;
  font-size: 14.5px;
  margin: 1rem 0;
  font-family: var(--font-sans);
}
th {
  border-bottom: 2px solid var(--fg);
  font-weight: 600;
  text-align: left;
  padding: 0.75rem 0.5rem;
  color: var(--fg);
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
td {
  border-bottom: 1px solid var(--line);
  padding: 0.65rem 0.5rem;
  color: var(--fg-soft);
  vertical-align: top;
}
tbody tr:hover { background: var(--bg-soft); }
pre {
  background: var(--bg-soft);
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  margin: 1rem 0;
  border: 1px solid var(--line);
}
code {
  font-family: var(--font-mono);
  font-size: 13.5px;
  color: var(--accent);
}
pre code { color: var(--fg); background: none; padding: 0; }
aside.note, aside.tip, aside.caution, aside.ok {
  padding: 1rem 1.5rem;
  border-radius: 6px;
  margin: 1rem 0;
  border-left: 3px solid;
  font-size: 15px;
}
aside.note { background: var(--note-bg); border-color: var(--note); color: var(--note); }
aside.tip { background: var(--tip-bg); border-color: var(--tip); color: var(--tip); }
aside.caution { background: var(--caution-bg); border-color: var(--caution); color: var(--caution); }
aside.ok { background: var(--ok-bg); border-color: var(--ok); color: var(--ok); }
aside.note p, aside.tip p, aside.caution p, aside.ok p { color: var(--fg); margin-bottom: 0; }

/* ===== v1.1: blockquote 样式 ===== */
blockquote {
  margin: 1.5rem 0;
  padding: 1rem 1.5rem;
  border-left: 3px solid var(--accent);
  background: var(--accent-bg);
  border-radius: 0 6px 6px 0;
  font-size: 15px;
  color: var(--fg-soft);
  font-style: italic;
  line-height: 1.7;
}
blockquote strong { color: var(--accent); font-style: normal; }

/* ===== LOCKED: 信息来源板块压缩（禁止放大字号） =====
 * 历史问题：6 个表格无折叠，占用 1/3 版面
 * v0.7 固化：source-section 内字号 12.5px，间距压缩
 */
.source-section {
  margin-top: 2rem;
  padding: 1rem 1.25rem;
  background: var(--bg-soft);
  border-radius: 6px;
  border-left: 3px solid var(--accent);
}
.source-section h2 { margin-top: 0; font-size: 20px; border-bottom: none; padding-bottom: 0; }
.source-section h3 {
  font-size: 14px;
  margin-top: 0.75rem;
  margin-bottom: 0.4rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.source-section table {
  font-size: 12.5px;
  margin: 0.25rem 0 0.5rem;
}
.source-section th { padding: 0.4rem 0.4rem; font-size: 11px; }
.source-section td { padding: 0.35rem 0.4rem; }
.source-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  margin-top: 0.5rem;
}
.source-grid > div {
  background: var(--bg-card);
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  border: 1px solid var(--line-soft);
}
.source-grid h4 {
  font-size: 11px;
  margin: 0 0 0.3rem;
  color: var(--accent);
  text-transform: uppercase;
}
.source-grid p { font-size: 12px; margin: 0; color: var(--fg-soft); line-height: 1.5; }
/* ===== LOCKED END ===== */

/* ===== 动态可视化组件（v0.7 通用） ===== */
.viz-layer-stack {
  margin: 1.5rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.viz-layer {
  display: grid;
  grid-template-columns: 80px 1fr 200px;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 4px;
  border-left: 4px solid var(--accent);
  background: var(--bg-card);
  align-items: center;
}
.viz-layer-l4 { border-left-color: #b85b44; background: #fdf6f0; }
.viz-layer-l3 { border-left-color: #b8732e; background: #fbf0e0; }
.viz-layer-l2 { border-left-color: #2c5f8d; background: #eef4fa; }
.viz-layer-l1 { border-left-color: #5d4ba0; background: #f0ecf7; }
.viz-layer-label {
  font-family: var(--font-sans);
  font-size: 13px;
  font-weight: 700;
  color: var(--fg);
}
.viz-layer-name { font-size: 15px; font-weight: 600; color: var(--fg); }
.viz-layer-desc {
  font-size: 12.5px;
  color: var(--muted);
  font-family: var(--font-sans);
  line-height: 1.5;
}

.viz-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
  margin: 1.5rem 0;
}
.viz-card {
  background: var(--bg-card);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 0.75rem 1rem;
  border-top: 3px solid var(--accent);
}
.viz-card-num {
  font-family: var(--font-sans);
  font-size: 11px;
  font-weight: 700;
  color: var(--accent);
  text-transform: uppercase;
}
.viz-card-title { font-size: 14px; font-weight: 600; color: var(--fg); margin: 0.2rem 0 0.4rem; }
.viz-card-desc { font-size: 12px; color: var(--muted); line-height: 1.5; }

.viz-flow {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.5rem;
  margin: 1.5rem 0;
}
.viz-step {
  background: var(--bg-card);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 0.75rem;
  text-align: center;
  position: relative;
}
.viz-step:not(:last-child)::after {
  content: "→";
  position: absolute;
  right: -0.65rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--accent);
  font-weight: 700;
  font-size: 18px;
  z-index: 1;
}
.viz-step-num {
  font-family: var(--font-sans);
  font-size: 11px;
  font-weight: 700;
  color: var(--accent);
  text-transform: uppercase;
}
.viz-step-title { font-size: 13px; font-weight: 600; color: var(--fg); margin: 0.3rem 0 0.4rem; }
.viz-step-desc { font-size: 11.5px; color: var(--muted); line-height: 1.5; }

.viz-metric-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  margin: 1rem 0;
}
.viz-metric-card {
  background: var(--bg-card);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 0.75rem 1rem;
  text-align: center;
}
.viz-metric-value {
  font-family: var(--font-sans);
  font-size: 22px;
  font-weight: 700;
  color: var(--accent);
  line-height: 1.2;
}
.viz-metric-label {
  font-size: 11.5px;
  color: var(--muted);
  margin-top: 0.2rem;
  font-family: var(--font-sans);
}

/* 附录区域 */
.appendix-section {
  margin-top: 2rem;
  padding: 1rem 1.25rem;
  background: var(--bg-soft);
  border-radius: 6px;
  border-left: 3px solid var(--muted-2);
}
.appendix-section h1 { font-size: 20px; margin-bottom: 0.75rem; }
.appendix-section h2 { font-size: 16px; margin-top: 1rem; border-bottom: none; }
.appendix-section ul { font-size: 13px; }

.footer-note {
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--line);
  font-family: var(--font-sans);
  font-size: 12px;
  color: var(--muted);
  text-align: center;
}
@media (max-width: 1100px) {
  .page-shell { grid-template-columns: 1fr; }
  aside.toc { display: none; }
  main { padding: 2rem 1.5rem 4rem; max-width: 100%; }
  .source-grid { grid-template-columns: 1fr; }
  .viz-flow { grid-template-columns: repeat(2, 1fr); }
  .viz-card-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  h1 { font-size: 28px; }
  .hero-verdict { font-size: 22px; }
  h2 { font-size: 22px; }
  main { padding: 1.5rem 1rem 3rem; }
  .viz-layer { grid-template-columns: 60px 1fr; }
  .viz-layer-desc { grid-column: 1 / -1; }
  .viz-flow { grid-template-columns: 1fr; }
  .viz-step::after { display: none; }
  .viz-card-grid { grid-template-columns: 1fr; }
}

/* ===== v0.8: 数学公式样式 ===== */
.math-display {
  margin: 1.5em 0;
  padding: 1.2em 1.5em;
  background: var(--bg-soft);
  border-radius: 6px;
  border-left: 3px solid var(--accent);
  overflow-x: auto;
  text-align: center;
  font-size: 1.05em;
}
.math-display mjx-container {
  overflow-x: auto;
  overflow-y: hidden;
  max-width: 100%;
}
"""


# ============================================================
# v0.7 HTML 禁止模式（与 validator 同步）
# ============================================================

HTML_FORBIDDEN_PATTERNS = {
    # v1.1: aside.toc 允许 overflow-y: auto（长目录需要滚动），此检查已废弃
    "unclosed_div": r"<div class=\"source-section\">[^<]*<h1",
}


def check_forbidden_patterns(html: str) -> list:
    """v0.7: 构建后自检禁止模式。"""
    violations = []
    for name, pattern in HTML_FORBIDDEN_PATTERNS.items():
        if re.search(pattern, html, re.DOTALL):
            violations.append(name)
    return violations


# ============================================================
# Markdown 转换（v0.6 保留）
# ============================================================

def md_to_html(md: str) -> str:
    lines = md.split("\n")
    out = []
    in_table = False
    in_list = False
    list_type = None

    def close_list():
        nonlocal in_list, list_type
        if in_list:
            out.append(f"</{list_type}>")
            in_list = False

    def close_table():
        nonlocal in_table
        if in_table:
            out.append("</tbody></table>")
            in_table = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            close_list()
            close_table()
            i += 1
            continue

        if stripped.startswith("# "):
            close_list()
            close_table()
            out.append(f"<h1>{inline(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            close_list()
            close_table()
            out.append(f"<h2>{inline(stripped[3:])}</h2>")
        elif stripped.startswith("### "):
            close_list()
            close_table()
            out.append(f"<h3>{inline(stripped[4:])}</h3>")
        elif stripped.startswith("#### "):
            close_list()
            close_table()
            out.append(f"<h4>{inline(stripped[5:])}</h4>")
        elif stripped.startswith("$$"):
            close_list()
            close_table()
            # v0.8: 块级公式处理
            if stripped.endswith("$$") and len(stripped) > 4:
                # 单行块级公式：$$ formula $$
                formula = stripped[2:-2].strip()
                out.append(f'<div class="math-display">$${formula}$$</div>')
            else:
                # 多行块级公式：收集到下一个 $$
                formula_parts = []
                if len(stripped) > 2:
                    formula_parts.append(stripped[2:].strip())
                i += 1
                while i < len(lines):
                    line_stripped = lines[i].strip()
                    if line_stripped.endswith("$$"):
                        remaining = line_stripped[:-2].strip()
                        if remaining:
                            formula_parts.append(remaining)
                        break
                    formula_parts.append(line_stripped)
                    i += 1
                formula = " ".join(formula_parts)
                out.append(f'<div class="math-display">$${formula}$$</div>')
        elif stripped.startswith("> "):
            close_list()
            close_table()
            # v1.1: 合并连续 > 行为单个 <blockquote>，符合标准 markdown 转换
            bq_lines = [stripped[2:]]
            i += 1
            while i < len(lines):
                bq_stripped = lines[i].strip()
                if bq_stripped.startswith("> "):
                    bq_lines.append(bq_stripped[2:])
                    i += 1
                elif bq_stripped == ">":
                    bq_lines.append("")
                    i += 1
                else:
                    break
            bq_content = "<br>".join(inline(l) for l in bq_lines)
            out.append(f"<blockquote>{bq_content}</blockquote>")
            continue
        elif "|" in stripped and stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s\-:|]+\|$", lines[i + 1].strip()):
            close_list()
            close_table()
            headers = [c.strip() for c in stripped.strip("|").split("|")]
            out.append("<table><thead><tr>")
            for h in headers:
                out.append(f"<th>{inline(h)}</th>")
            out.append("</tr></thead><tbody>")
            in_table = True
            i += 2
            continue
        elif in_table and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            out.append("<tr>")
            for c in cells:
                out.append(f"<td>{inline(c)}</td>")
            out.append("</tr>")
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list or list_type != "ul":
                close_list()
                out.append("<ul>")
                in_list = True
                list_type = "ul"
            out.append(f"<li>{inline(stripped[2:])}</li>")
        elif re.match(r"^\d+\.\s", stripped):
            if not in_list or list_type != "ol":
                close_list()
                out.append("<ol>")
                in_list = True
                list_type = "ol"
            content = re.sub(r"^\d+\.\s", "", stripped)
            out.append(f"<li>{inline(content)}</li>")
        else:
            close_list()
            close_table()
            out.append(f"<p>{inline(stripped)}</p>")
        i += 1

    close_list()
    close_table()
    return "\n".join(out)


def inline(text: str) -> str:
    # v0.8: 先提取行内公式 $...$，避免被后续正则破坏LaTeX中的*和[]符号
    formulas = []
    def _save_formula(m):
        formulas.append(m.group(0))
        return f"\x00FORMULA{len(formulas)-1}\x00"
    text = re.sub(r"\$([^\$\n]+)\$", _save_formula, text)

    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

    # v0.8: 恢复公式
    for i, formula in enumerate(formulas):
        text = text.replace(f"\x00FORMULA{i}\x00", formula)
    return text


def add_anchors(html: str) -> str:
    def repl(match):
        level = match.group(1)
        title = match.group(2)
        plain = re.sub(r"<[^>]+>", "", title)
        anchor = re.sub(r"[^\w\u4e00-\u9fff]+", "-", plain.lower()).strip("-")
        return f'<h{level} id="{anchor}">{title}</h{level}>'
    return re.sub(r"<h(1|2|3|4)>([^<]+)</h\1>", repl, html)


def build_toc(md: str) -> str:
    toc = []
    for line in md.split("\n"):
        m = re.match(r"^(##+)\s+(.+)$", line.strip())
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            anchor = re.sub(r"[^\w\u4e00-\u9fff]+", "-", title.lower()).strip("-")
            cls = "sub" if level >= 3 else ""
            toc.append(f'<a href="#{anchor}" class="{cls}">{title}</a>')
    return "\n".join(toc)


# ============================================================
# v0.7 动态可视化识别
# ============================================================

def extract_list_items(html_chunk: str) -> list:
    """从 <ul>...</ul> 或 <ol>...</ol> 中提取 <li> 文本。"""
    items = re.findall(r"<li>(.*?)</li>", html_chunk, re.DOTALL)
    return [re.sub(r"<[^>]+>", "", item).strip() for item in items]


def try_build_layer_stack(h3_match: str, list_html: str, layer_count: int) -> str:
    """尝试构建分层架构图（L1-L4）。返回 HTML 或空字符串。"""
    items = extract_list_items(list_html)
    if len(items) < layer_count:
        return ""

    # 取前 N 个作为分层
    layers_html = []
    for i, item in enumerate(items[:layer_count], 1):
        layer_num = layer_count - i + 1  # 倒序：第一个是 L4
        layer_class = f"viz-layer viz-layer-l{layer_num}"

        # 尝试解析 "名称：描述" 或 "名称 - 描述" 格式
        parts = re.split(r"[：:\-—]+", item, maxsplit=1)
        if len(parts) == 2:
            name, desc = parts[0].strip(), parts[1].strip()
        else:
            name, desc = item, ""

        layers_html.append(f'''<div class="{layer_class}">
  <div class="viz-layer-label">L{layer_num}</div>
  <div class="viz-layer-name">{name}</div>
  <div class="viz-layer-desc">{desc}</div>
</div>''')

    return f'<div class="viz-layer-stack">{"".join(layers_html)}</div>'


def try_build_card_grid(h3_match: str, list_html: str) -> str:
    """尝试构建功能卡片网格。返回 HTML 或空字符串。"""
    items = extract_list_items(list_html)
    if len(items) < 3:
        return ""

    cards_html = []
    for i, item in enumerate(items, 1):
        parts = re.split(r"[：:\-—]+", item, maxsplit=1)
        if len(parts) == 2:
            title, desc = parts[0].strip(), parts[1].strip()
        else:
            title, desc = item, ""

        cards_html.append(f'''<div class="viz-card">
  <div class="viz-card-num">{i:02d}</div>
  <div class="viz-card-title">{title}</div>
  <div class="viz-card-desc">{desc}</div>
</div>''')

    return f'<div class="viz-card-grid">{"".join(cards_html)}</div>'


def try_build_flow(h3_match: str, list_html: str) -> str:
    """尝试构建工作流图。返回 HTML 或空字符串。"""
    items = extract_list_items(list_html)
    if len(items) < 3:
        return ""

    steps_html = []
    for i, item in enumerate(items, 1):
        parts = re.split(r"[：:\-—]+", item, maxsplit=1)
        if len(parts) == 2:
            title, desc = parts[0].strip(), parts[1].strip()
        else:
            title, desc = item, ""

        steps_html.append(f'''<div class="viz-step">
  <div class="viz-step-num">Step {i}</div>
  <div class="viz-step-title">{title}</div>
  <div class="viz-step-desc">{desc}</div>
</div>''')

    return f'<div class="viz-flow">{"".join(steps_html)}</div>'


def inject_dynamic_visualizations(html: str) -> str:
    """v0.7: 动态识别报告内容中的可视化机会。

    识别模式：
    1. "N层架构" + ul/ol 列表 → 分层架构图
    2. "N大功能" / "功能矩阵" + ul/ol 列表 → 卡片网格
    3. "工作流" / "流程" + ol 列表 → 流程图
    4. "家族" / "矩阵" + ul 列表 → 卡片网格
    """

    # 模式 1：N层架构
    for n in [4, 3, 5]:
        pattern = rf'(<h3 id="[^"]*"[^>]*>[^<]*{n}层架构[^<]*</h3>)\s*<p>[^<]*</p>\s*(<ul>.*?</ul>)'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            h3, list_html = match.group(1), match.group(2)
            viz = try_build_layer_stack(h3, list_html, n)
            if viz:
                html = html[:match.start()] + h3 + viz + html[match.end():]

    # 模式 2：N大功能 / 功能矩阵
    for keyword in ["大功能", "功能矩阵", "完整功能"]:
        pattern = rf'(<h3 id="[^"]*"[^>]*>[^<]*{keyword}[^<]*</h3>)\s*<p>[^<]*</p>\s*(<ul>.*?</ul>)'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            h3, list_html = match.group(1), match.group(2)
            viz = try_build_card_grid(h3, list_html)
            if viz:
                html = html[:match.start()] + h3 + viz + html[match.end():]

    # 模式 3：工作流 / 流程（ol 列表）
    for keyword in ["工作流", "流程图", "四步", "三步", "五步"]:
        pattern = rf'(<h3 id="[^"]*"[^>]*>[^<]*{keyword}[^<]*</h3>)\s*<p>[^<]*</p>\s*(<ol>.*?</ol>)'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            h3, list_html = match.group(1), match.group(2)
            viz = try_build_flow(h3, list_html)
            if viz:
                html = html[:match.start()] + h3 + viz + html[match.end():]

    # 模式 4：家族 / 四件套
    for keyword in ["家族", "四件套", "产品矩阵"]:
        pattern = rf'(<h3 id="[^"]*"[^>]*>[^<]*{keyword}[^<]*</h3>)\s*<p>[^<]*</p>\s*(<ul>.*?</ul>)'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            h3, list_html = match.group(1), match.group(2)
            viz = try_build_card_grid(h3, list_html)
            if viz:
                html = html[:match.start()] + h3 + viz + html[match.end():]

    return html


def wrap_source_and_appendix(html: str) -> str:
    """v0.7: 用 regex 可靠地包裹 source-section 和 appendix-section。

    修复历史问题：附录 div 闭合 bug（字符串替换匹配失败导致 div 延伸到 main 结尾）
    """
    # 在 9. 信息来源 的 h2 前插入 source-section 开启 div
    html = re.sub(
        r'(<h2 id="[^"]*">[\d.]*\s*信息来源</h2>)',
        r'<div class="source-section">\1',
        html
    )

    # 在附录的 h1（可能带 id）前关闭 source-section 并开启 appendix-section
    # 用 regex 匹配 <h1...>附录...</h1>
    html = re.sub(
        r'<h1([^>]*)>(附录[：:][^<]*)</h1>',
        r'</div><div class="appendix-section"><h1\1>\2</h1>',
        html
    )

    # 在 footer-note 前关闭 appendix-section（如果存在）
    html = html.replace(
        '<div class="footer-note">',
        '</div><div class="footer-note">'
    )

    return html


def wrap_chapters(html: str) -> str:
    """v1.1: 把正文中每个 h2 章节包裹在 <section class="chapter"> 中。

    规范要求 section.chapter 结构。这个函数在 vm-hero 之后、source-section 之前
    把所有 h2 及其内容包成 section.chapter。
    """
    # 找到 vm-hero 结束位置和 source-section/appendix-section 开始位置
    hero_end = html.find('</div>', html.find('class="vm-hero"'))
    if hero_end == -1:
        hero_end = 0
    else:
        # 找到 vm-hero 的闭合 </div>（向上找包含 vm-hero 的 div 的闭合）
        hero_start = html.find('class="vm-hero"')
        # 简单策略：从 vm-hero 开始找下一个 <h2
        hero_end = html.find('<h2', hero_start)
        if hero_end == -1:
            return html

    # 找到 source-section 或 appendix-section 或 footer-note 的开始
    section_end = html.find('<div class="source-section"')
    if section_end == -1:
        section_end = html.find('<div class="appendix-section"')
    if section_end == -1:
        section_end = html.find('<div class="footer-note"')
    if section_end == -1:
        section_end = len(html)

    # 提取正文部分
    body = html[hero_end:section_end]

    # 按 <h2 分割（保留 h2 在每段开头）
    parts = body.split('<h2')
    if len(parts) <= 1:
        return html

    # 第一部分是 h2 之前的内容（可能为空或换行）
    before_chapters = parts[0]
    chapter_sections = []
    for part in parts[1:]:
        chapter_sections.append('<section class="chapter"><h2' + part + '</section>')

    new_body = before_chapters + '\n'.join(chapter_sections)
    return html[:hero_end] + new_body + html[section_end:]


def build_hero(project_name: str, version: str = "v0.7") -> str:
    """构建 hero 区域。"""
    return f'''    <div class="vm-hero">
      <div class="kicker">Research OS {version} · 深度调研</div>
      <div class="hero-verdict">{project_name}<span class="badge badge-v07">{version}</span></div>
      <p class="hero-summary">基于 Smart Agent. Dumb Tools. 架构。含核心对象直采、独立审计、读者模拟写-读-改闭环、统一来源标注、动态可视化。</p>
    </div>'''


def build_html(project: Path, project_name: str = None) -> str:
    """v0.7: 构建 HTML。支持任意项目。"""
    report_md = project / "07-output" / "final-report.md"
    if not report_md.exists():
        raise FileNotFoundError(f"final-report.md not found: {report_md}")

    md = report_md.read_text(encoding="utf-8")
    body_html = md_to_html(md)
    body_html = add_anchors(body_html)

    # v0.7 动态可视化
    body_html = inject_dynamic_visualizations(body_html)

    # 包裹 source-section 和 appendix-section
    body_html = wrap_source_and_appendix(body_html)

    # v1.1: 把正文章节包裹在 section.chapter 中
    body_html = wrap_chapters(body_html)

    toc_html = build_toc(md)

    # 项目名（从目录名推断）
    if project_name is None:
        project_name = project.name

    hero = build_hero(project_name)
    footer = f"Research OS v0.8 · {project_name} · 生成时间 2026-07-10"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{project_name} 深度调研 v0.7</title>
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
<script>
  MathJax = {{
    tex: {{
      inlineMath: [['$', '$'], ['\\(', '\\)']],
      displayMath: [['$$', '$$'], ['\\[', '\\]']]
    }},
    svg: {{ fontCache: 'global' }},
    options: {{
      skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
    }}
  }};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js" id="MathJax-script" async></script>
</head>
<body>
<div class="reading-progress" id="progress"></div>
<div class="page-shell">
  <aside class="toc">
    <div class="toc-title">目录</div>
    <nav>
{toc_html}
    </nav>
  </aside>
  <main>
{hero}
{body_html}
    <div class="footer-note">
      {footer}
    </div>
  </main>
</div>
<script>
window.addEventListener('scroll', function() {{
  var h = document.documentElement;
  var b = document.body;
  var st = 'scrollTop';
  var sh = 'scrollHeight';
  var progress = (h[st] || b[st]) / ((h[sh] || b[sh]) - h.clientHeight) * 100;
  document.getElementById('progress').style.width = progress + '%';
}});

// v1.1: TOC 滚动联动 + active 高亮 + 点击平滑跳转
(function() {{
  var tocLinks = document.querySelectorAll('aside.toc nav a');
  var sections = [];
  var i;

  // 收集所有章节元素（h2 有 id 的）
  for (i = 0; i < tocLinks.length; i++) {{
    var href = tocLinks[i].getAttribute('href');
    if (href && href.startsWith('#')) {{
      var target = document.getElementById(href.slice(1));
      if (target) {{
        sections.push({{link: tocLinks[i], el: target}});
      }}
    }}
  }}

  // 点击平滑跳转
  for (i = 0; i < tocLinks.length; i++) {{
    tocLinks[i].addEventListener('click', function(e) {{
      var href = this.getAttribute('href');
      if (href && href.startsWith('#')) {{
        e.preventDefault();
        var target = document.getElementById(href.slice(1));
        if (target) {{
          target.scrollIntoView({{behavior: 'smooth', block: 'start'}});
        }}
      }}
    }});
  }}

  // 滚动时高亮当前章节
  function updateActive() {{
    var scrollPos = window.scrollY + 150;  // offset 让当前章节提前高亮
    var current = null;
    for (i = 0; i < sections.length; i++) {{
      // 用 getBoundingClientRect 获取相对于视口的绝对位置
      var rect = sections[i].el.getBoundingClientRect();
      var absTop = rect.top + window.scrollY;
      if (absTop <= scrollPos) {{
        current = sections[i];
      }}
    }}
    // 清除所有 active
    for (i = 0; i < tocLinks.length; i++) {{
      tocLinks[i].classList.remove('active');
    }}
    // 设置当前 active
    if (current) {{
      current.link.classList.add('active');
      // 让 active 的 TOC 链接在 TOC 视野内
      var tocContainer = document.querySelector('aside.toc');
      var linkRect = current.link.getBoundingClientRect();
      var tocRect = tocContainer.getBoundingClientRect();
      if (linkRect.top < tocRect.top || linkRect.bottom > tocRect.bottom) {{
        current.link.scrollIntoView({{block: 'nearest', behavior: 'smooth'}});
      }}
    }}
  }}

  window.addEventListener('scroll', updateActive);
  updateActive();  // 初始化
}})();
</script>
</body>
</html>
"""

    # v0.7 自检禁止模式
    violations = check_forbidden_patterns(html)
    if violations:
        print(f"[WARN] HTML 包含禁止模式: {violations}")
        print("[WARN] 这些模式应该在构建过程中被修复，但当前仍存在")
        print("[WARN] 请检查 wrap_source_and_appendix() 和 CSS 中的 aside.toc 规则")

    # v1.1 工具自检：验证关键JS功能存在（不依赖人工验证）
    required_js = {
        "toc_scroll_sync": ("updateActive", "TOC滚动联动"),
        "toc_smooth_scroll": ("scrollIntoView", "TOC平滑跳转"),
        "toc_active_class": ("classList.add('active')", "TOC active高亮"),
    }
    js_failures = []
    for check_id, (pattern, desc) in required_js.items():
        if pattern not in html:
            js_failures.append(f"{desc}({pattern}未找到)")
    if js_failures:
        print(f"[FAIL] 工具自检: 关键JS功能缺失: {', '.join(js_failures)}")
        print("[FAIL] build_html_v07.py 生成的HTML缺少交互JS，请检查工具源码")
        return html  # 仍然输出HTML，但标记问题
    else:
        print("[OK] 工具自检: 3项关键JS功能全部存在")

    return html


def main():
    parser = argparse.ArgumentParser(description="Research OS v1.1 HTML Builder")
    parser.add_argument("project", help="项目路径")
    parser.add_argument("--name", help="项目显示名（默认从目录名推断）", default=None)
    parser.add_argument("--output", help="输出 HTML 路径（默认 08-html/index.html）", default=None)
    args = parser.parse_args()

    project = Path(args.project).resolve()
    if not project.exists():
        print(f"[ERROR] Project not found: {project}", file=sys.stderr)
        return 1

    html = build_html(project, args.name)

    output_path = Path(args.output) if args.output else project / "08-html" / "index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"[OK] Wrote {output_path} ({len(html):,} chars)")

    # 复制到桌面
    desktop_copy = Path.home() / "Desktop" / f"{project.name}.html"
    try:
        import shutil
        shutil.copy(output_path, desktop_copy)
        print(f"[OK] Copied to {desktop_copy} ({len(html):,} chars)")
    except Exception as e:
        print(f"[WARN] Failed to copy to desktop: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
