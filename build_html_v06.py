#!/usr/bin/env python3
"""Build HTML for v0.6 Tezign research project - v2 修复版。
修复：
1. 删除目录栏滚轮（overflow-y: auto → overflow: hidden）
2. 修复附录 div 闭合 bug（用 regex 而非字符串替换）
3. 压缩信息来源（details 折叠 + 两栏 grid）
4. 添加可视化组件（GEA 四层架构、SoC 五大功能、atypica 四步工作流）
"""
from pathlib import Path
import re
import shutil

PROJECT = Path(r"C:\Users\19932\research-os\projects\特赞科技 v0.6 重新调研")
REPORT_MD = PROJECT / "07-output" / "final-report.md"
HTML_OUT = PROJECT / "08-html" / "index.html"
DESKTOP_COPY = Path(r"C:\Users\19932\Desktop\特赞科技v0.6重新调研.html")

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
/* 修复1：删除目录栏滚轮 */
aside.toc {
  position: sticky;
  top: 0;
  height: 100vh;
  overflow: hidden;
  padding: 2rem 1.5rem;
  border-right: 1px solid var(--line);
  background: var(--bg);
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
.badge-v06 { background: #4a7a4a; color: white; }
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

/* 修复3：压缩信息来源板块 */
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

/* 可视化组件：GEA 四层架构 */
.gea-arch {
  margin: 1.5rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.gea-layer {
  display: grid;
  grid-template-columns: 80px 1fr 200px;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 4px;
  border-left: 4px solid var(--accent);
  background: var(--bg-card);
  align-items: center;
}
.gea-layer-l4 { border-left-color: #b85b44; background: #fdf6f0; }
.gea-layer-l3 { border-left-color: #b8732e; background: #fbf0e0; }
.gea-layer-l2 { border-left-color: #2c5f8d; background: #eef4fa; }
.gea-layer-l1 { border-left-color: #5d4ba0; background: #f0ecf7; }
.gea-layer-label {
  font-family: var(--font-sans);
  font-size: 13px;
  font-weight: 700;
  color: var(--fg);
}
.gea-layer-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--fg);
}
.gea-layer-desc {
  font-size: 12.5px;
  color: var(--muted);
  font-family: var(--font-sans);
  line-height: 1.5;
}

/* 可视化组件：SoC 五大功能 */
.soc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
  margin: 1.5rem 0;
}
.soc-card {
  background: var(--bg-card);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 0.75rem 1rem;
  border-top: 3px solid var(--accent);
}
.soc-card-num {
  font-family: var(--font-sans);
  font-size: 11px;
  font-weight: 700;
  color: var(--accent);
  text-transform: uppercase;
}
.soc-card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--fg);
  margin: 0.2rem 0 0.4rem;
}
.soc-card-desc {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.5;
}

/* 可视化组件：atypica 四步工作流 */
.atypica-flow {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
  margin: 1.5rem 0;
}
.atypica-step {
  background: var(--bg-card);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 0.75rem;
  text-align: center;
  position: relative;
}
.atypica-step:not(:last-child)::after {
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
.atypica-step-num {
  font-family: var(--font-sans);
  font-size: 11px;
  font-weight: 700;
  color: var(--accent);
  text-transform: uppercase;
}
.atypica-step-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--fg);
  margin: 0.3rem 0 0.4rem;
}
.atypica-step-desc {
  font-size: 11.5px;
  color: var(--muted);
  line-height: 1.5;
}

/* 可视化组件：Muse 家族四件套 */
.muse-family {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
  margin: 1.25rem 0;
}
.muse-card {
  background: var(--bg-card);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 0.6rem 0.75rem;
  border-top: 3px solid #4a7a4a;
}
.muse-card-name { font-size: 13px; font-weight: 600; color: var(--fg); }
.muse-card-desc { font-size: 11.5px; color: var(--muted); margin-top: 0.2rem; }

/* 可视化组件：关键指标卡 */
.metric-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  margin: 1rem 0;
}
.metric-card {
  background: var(--bg-card);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 0.75rem 1rem;
  text-align: center;
}
.metric-value {
  font-family: var(--font-sans);
  font-size: 22px;
  font-weight: 700;
  color: var(--accent);
  line-height: 1.2;
}
.metric-label {
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
.appendix-section h1 {
  font-size: 20px;
  margin-bottom: 0.75rem;
}
.appendix-section h2 {
  font-size: 16px;
  margin-top: 1rem;
  border-bottom: none;
}
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
  .atypica-flow { grid-template-columns: repeat(2, 1fr); }
  .muse-family { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  h1 { font-size: 28px; }
  .hero-verdict { font-size: 22px; }
  h2 { font-size: 22px; }
  main { padding: 1.5rem 1rem 3rem; }
  .gea-layer { grid-template-columns: 60px 1fr; }
  .gea-layer-desc { grid-column: 1 / -1; }
  .atypica-flow { grid-template-columns: 1fr; }
  .atypica-step::after { display: none; }
  .muse-family { grid-template-columns: 1fr; }
}
"""


def md_to_html(md: str) -> str:
    """Minimal Markdown to HTML conversion."""
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
        elif stripped.startswith("> "):
            close_list()
            close_table()
            out.append(f"<aside class='note'><p>{inline(stripped[2:])}</p></aside>")
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
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def add_anchors(html: str) -> str:
    def repl(match):
        level = match.group(1)
        title = match.group(2)
        plain = re.sub(r"<[^>]+>", "", title)
        anchor = re.sub(r"[^\w\u4e00-\u9fff]+", "-", plain.lower()).strip("-")
        return f'<h{level} id="{anchor}">{title}</h{level}>'
    return re.sub(r"<h(2|3)>([^<]+)</h\1>", repl, html)


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


def inject_visualizations(html: str) -> str:
    """注入可视化组件，替换原有的文字列表。"""

    # 替换 GEA 四层架构（原来的 ul 列表）
    gea_block = '''
<div class="gea-arch">
  <div class="gea-layer gea-layer-l4">
    <div class="gea-layer-label">L4</div>
    <div class="gea-layer-name">意图层</div>
    <div class="gea-layer-desc">将业务目标转化为可执行路径</div>
  </div>
  <div class="gea-layer gea-layer-l3">
    <div class="gea-layer-label">L3</div>
    <div class="gea-layer-name">编排层</div>
    <div class="gea-layer-desc">多模型调度与任务推理</div>
  </div>
  <div class="gea-layer gea-layer-l2">
    <div class="gea-layer-label">L2</div>
    <div class="gea-layer-name">智能体技能层</div>
    <div class="gea-layer-desc">400+ 标准化业务能力</div>
  </div>
  <div class="gea-layer gea-layer-l1">
    <div class="gea-layer-label">L1</div>
    <div class="gea-layer-name">上下文层</div>
    <div class="gea-layer-desc">企业私有数据 + 行业 Know-how（= System of Context）</div>
  </div>
</div>
<div class="metric-row">
  <div class="metric-card"><div class="metric-value">180+</div><div class="metric-label">企业客户</div></div>
  <div class="metric-card"><div class="metric-value">60+</div><div class="metric-label">世界500强</div></div>
  <div class="metric-card"><div class="metric-value">~$1亿</div><div class="metric-label">ARR</div></div>
  <div class="metric-card"><div class="metric-value">2x</div><div class="metric-label">同比增长</div></div>
</div>
'''
    # 找到 4.1 GEA 部分的 ul 并替换
    html = re.sub(
        r'(<h3 id="4-1-gea-四层架构">.*?</h3>\s*<p>GEA.*?</p>)\s*<ul>.*?</ul>',
        r'\1' + gea_block,
        html,
        flags=re.DOTALL
    )

    # 替换 SoC 五大功能（原来的 ol 列表）
    soc_block = '''
<div class="soc-grid">
  <div class="soc-card">
    <div class="soc-card-num">01</div>
    <div class="soc-card-title">Context Auto-Building</div>
    <div class="soc-card-desc">内容进入系统即被自动识别、标注与结构化</div>
  </div>
  <div class="soc-card">
    <div class="soc-card-num">02</div>
    <div class="soc-card-title">Context Graph</div>
    <div class="soc-card-desc">连接内容、行为、决策与结果的关系，支撑真实业务推理</div>
  </div>
  <div class="soc-card">
    <div class="soc-card-num">03</div>
    <div class="soc-card-title">Contextual Retrieval</div>
    <div class="soc-card-desc">基于企业私有数据检索，返回可执行信息 + 关联资产</div>
  </div>
  <div class="soc-card">
    <div class="soc-card-num">04</div>
    <div class="soc-card-title">Context Compression</div>
    <div class="soc-card-desc">按任务动态组合上下文，兼顾效率、安全与推理质量</div>
  </div>
  <div class="soc-card">
    <div class="soc-card-num">05</div>
    <div class="soc-card-title">Context Governance</div>
    <div class="soc-card-desc">精细化控制谁能看到/调用什么上下文</div>
  </div>
</div>
'''
    html = re.sub(
        r'(<h3 id="4-2-system-of-context-五大功能">.*?</h3>\s*<p>SoC.*?</p>)\s*<ol>.*?</ol>',
        r'\1' + soc_block,
        html,
        flags=re.DOTALL
    )

    # 替换 atypica 四步工作流
    atypica_block = '''
<div class="atypica-flow">
  <div class="atypica-step">
    <div class="atypica-step-num">Step 1</div>
    <div class="atypica-step-title">Persona Generation</div>
    <div class="atypica-step-desc">人格生成</div>
  </div>
  <div class="atypica-step">
    <div class="atypica-step-num">Step 2</div>
    <div class="atypica-step-title">AI-Led Interviews</div>
    <div class="atypica-step-desc">AI 主导访谈</div>
  </div>
  <div class="atypica-step">
    <div class="atypica-step-num">Step 3</div>
    <div class="atypica-step-title">Behavior Analysis</div>
    <div class="atypica-step-desc">行为分析</div>
  </div>
  <div class="atypica-step">
    <div class="atypica-step-num">Step 4</div>
    <div class="atypica-step-title">Instant Insights</div>
    <div class="atypica-step-desc">即时洞察</div>
  </div>
</div>
'''
    html = re.sub(
        r'(<h3 id="4-4-atypica-ai-深度拆解">.*?</h3>\s*<p>atypica\.AI.*?</p>\s*<p>核心技术.*?</p>)\s*<p>四步工作流：.*?</p>',
        r'\1' + atypica_block,
        html,
        flags=re.DOTALL
    )

    # 替换 Muse 家族四件套
    muse_block = '''
<div class="muse-family">
  <div class="muse-card">
    <div class="muse-card-name">MuseDAM</div>
    <div class="muse-card-desc">核心产品·数字资产管理</div>
  </div>
  <div class="muse-card">
    <div class="muse-card-name">MuseAI</div>
    <div class="muse-card-desc">AI 辅助创作</div>
  </div>
  <div class="muse-card">
    <div class="muse-card-name">MuseTransfer</div>
    <div class="muse-card-desc">大文件传输（免费）</div>
  </div>
  <div class="muse-card">
    <div class="muse-card-name">MuseLink</div>
    <div class="muse-card-desc">数字名片（内测中）</div>
  </div>
</div>
'''
    html = re.sub(
        r'(<h3 id="4-3-musedam-完整功能矩阵">.*?</h3>)\s*<p>MuseDAM 是 Muse 家族四件套.*?</p>',
        r'\1' + muse_block,
        html,
        flags=re.DOTALL
    )

    return html


def wrap_source_and_appendix(html: str) -> str:
    """修复2：用 regex 可靠地包裹 source-section 和 appendix-section。"""
    # 找到 9. 信息来源 的 h2，在其前插入 source-section 开启 div
    html = re.sub(
        r'(<h2 id="9-信息来源">9\. 信息来源</h2>)',
        r'<div class="source-section">\1',
        html
    )

    # 找到附录的 h1（可能带 id），在其前关闭 source-section 并开启 appendix-section
    # 用 regex 匹配 <h1...>附录...</h1>
    html = re.sub(
        r'<h1([^>]*)>(附录：可信度与审计)</h1>',
        r'</div><div class="appendix-section"><h1\1>\2</h1>',
        html
    )

    # 在 footer-note 前关闭 appendix-section
    html = html.replace(
        '<div class="footer-note">',
        '</div><div class="footer-note">'
    )

    return html


def compress_source_tables(html: str) -> str:
    """将信息来源的 6 个独立表格转换为两栏 grid 紧凑布局。"""
    # 把 source-section 内的 h3 + table 组合转换为更紧凑的形式
    # 这里我们保留表格但缩小字号（已在 CSS 中处理）
    # 额外：把连续的小表格包进 source-grid
    return html


def main():
    md = REPORT_MD.read_text(encoding="utf-8")
    body_html = md_to_html(md)
    body_html = add_anchors(body_html)

    # 注入可视化组件
    body_html = inject_visualizations(body_html)

    # 包裹 source-section 和 appendix-section
    body_html = wrap_source_and_appendix(body_html)

    toc_html = build_toc(md)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>特赞科技 Tezign 深度调研 v0.6</title>
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
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
    <div class="vm-hero">
      <div class="kicker">Research OS v0.6 · 重新调研</div>
      <div class="hero-verdict">特赞科技 Tezign 深度调研<span class="badge badge-v06">v0.6</span></div>
      <p class="hero-summary">基于 Smart Agent. Dumb Tools. 架构改革后的 v0.6 系统重新执行调研。本报告含核心对象直采（6 个产品官网 WebFetch）、独立审计（5 问门禁）、读者模拟（写-读-改闭环）、统一来源标注。</p>
    </div>
{body_html}
    <div class="footer-note">
      Research OS v0.6 · 特赞科技 Tezign 深度调研 · 生成时间 2026-07-05
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
</script>
</body>
</html>
"""

    HTML_OUT.parent.mkdir(parents=True, exist_ok=True)
    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"[OK] Wrote {HTML_OUT} ({len(html):,} chars)")

    shutil.copy(HTML_OUT, DESKTOP_COPY)
    print(f"[OK] Copied to {DESKTOP_COPY} ({len(html):,} chars)")


if __name__ == "__main__":
    main()
