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
/* ===== v0.8 visual system: Anthropic cream + Lora serif + Starlight asides =====
   Design tokens borrowed from:
   - Anthropic claude.ai (cream bg #faf9f5, Lora serif body, clay accent #d97757)
   - Astro Starlight (content-width 45rem, line-height 1.75, asides pattern)
   - Stripe Press (serif body, narrow column, generous leading)
   First-principles: reader opens HTML with decision to make + cognitive gap +
   limited attention budget. Visualization restores structural information lost
   by linearization. Long-form argument + structured blocks 穿插, not dashboard.
*/
:root {
  /* color */
  --bg: #faf9f5;
  --bg-card: #ffffff;
  --bg-soft: #f5f4ee;
  --bg-softer: #f0eee5;
  --fg: #1a1a1a;
  --fg-soft: #3d3d3d;
  --muted: #6b6b6b;
  --muted-2: #8e8e8e;
  --line: #e5e3d8;
  --line-soft: #ede9dd;
  --accent: #b85b44;          /* warm brick (Anthropic clay sibling) */
  --accent-soft: #f5e8e0;
  --accent-bg: #fdf6f0;
  --note: #2c5f8d;
  --note-bg: #eef4fa;
  --note-border: #b8d3eb;
  --tip: #5d4ba0;
  --tip-bg: #f0ecf7;
  --tip-border: #c7b8e0;
  --caution: #b8732e;
  --caution-bg: #fbf0e0;
  --caution-border: #e8c890;
  --danger: #b85b44;
  --danger-bg: #fceeea;
  --danger-border: #e8b8a8;
  --ok: #4a7a4a;
  --ok-bg: #eef5ee;
  /* type */
  --font-serif: "Lora", "Noto Serif SC", "Source Han Serif SC", Georgia, "Times New Roman", serif;
  --font-sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-mono: "JetBrains Mono", "Geist Mono", Consolas, monospace;
  /* size */
  --sidebar-width: 15rem;
  --reader-width: 56rem;
  --shell-max-width: 1480px;
  --radius: 6px;
  --radius-sm: 4px;
  /* spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.5rem;
  --space-6: 2rem;
  --space-7: 3rem;
  --space-8: 4rem;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font-family: var(--font-serif);
  font-size: 16px;
  line-height: 1.75;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}
a { color: var(--accent); text-decoration: none; border-bottom: 1px solid rgba(184, 91, 68, 0.3); transition: border-color 0.15s; }
a:hover { border-bottom-color: var(--accent); }
.page-shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  gap: var(--space-7);
  max-width: var(--shell-max-width);
  margin: 0 auto;
  padding: var(--space-7) 28px var(--space-8);
}
aside {
  position: sticky;
  top: var(--space-6);
  align-self: start;
  padding-right: var(--space-5);
  max-height: calc(100vh - 48px);
  overflow: auto;
  font-family: var(--font-sans);
  font-size: 13.5px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
aside::-webkit-scrollbar { display: none; }
main { min-width: 0; overflow-wrap: anywhere; word-break: normal; }
.toc a.active { color: var(--accent); font-weight: 600; padding-left: 8px; border-left: 2px solid var(--accent); }
.reading-progress {
  position: fixed;
  top: 0;
  left: 0;
  height: 2px;
  background: var(--accent);
  width: 0;
  z-index: 50;
  transition: width 0.1s ease-out;
}

/* ===== Header / Title ===== */
.kicker {
  color: var(--accent);
  font-family: var(--font-sans);
  font-size: 11.5px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  margin-bottom: var(--space-3);
  font-weight: 600;
}
h1 {
  font-family: var(--font-serif);
  font-size: 38px;
  line-height: 1.15;
  margin: 0 0 var(--space-4);
  letter-spacing: -0.02em;
  font-weight: 600;
  color: var(--fg);
}
.subtitle {
  color: var(--muted);
  font-family: var(--font-sans);
  font-size: 14.5px;
  line-height: 1.6;
  margin-bottom: var(--space-7);
  max-width: 38rem;
}
.toc-title {
  font-family: var(--font-sans);
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 0.16em;
  text-transform: uppercase;
  margin: 0 0 var(--space-4);
  font-weight: 600;
}
.toc { list-style: none; padding: 0; margin: 0; }
.toc li { margin: 6px 0; }
.toc a { color: var(--fg-soft); border-bottom: 0; display: block; padding: 2px 0; transition: color 0.15s; }
.toc a:hover { color: var(--accent); }

/* ===== Chapter / Body ===== */
.chapter {
  padding: var(--space-7) 0;
  border-top: 1px solid var(--line);
}
.chapter:first-of-type { border-top: 0; padding-top: 0; }
.chapter h2 {
  font-family: var(--font-serif);
  font-size: 26px;
  line-height: 1.25;
  margin: 0 0 var(--space-5);
  letter-spacing: -0.015em;
  font-weight: 600;
  color: var(--fg);
}
h3 {
  font-family: var(--font-serif);
  font-size: 19px;
  margin: var(--space-6) 0 var(--space-3);
  font-weight: 600;
  color: var(--fg);
}
h4 {
  font-family: var(--font-sans);
  font-size: 14px;
  margin: var(--space-5) 0 var(--space-2);
  font-weight: 600;
  color: var(--fg-soft);
  letter-spacing: 0.02em;
}
p { margin: var(--space-3) 0; }
p, li { font-family: var(--font-serif); font-size: 16px; line-height: 1.75; }
ul, ol { padding-left: var(--space-6); }
li { margin: var(--space-2) 0; }
strong { font-weight: 600; color: var(--fg); }
em { font-style: italic; }

/* ===== Blockquote →Aside pattern (Starlight style) ===== */
blockquote {
  margin: var(--space-5) 0;
  padding: var(--space-3) var(--space-4) var(--space-3) var(--space-5);
  border-inline-start: 3px solid var(--line);
  background: transparent;
  color: var(--fg-soft);
  font-style: italic;
}

/* ===== Code ===== */
code {
  font-family: var(--font-mono);
  font-size: 13.5px;
  background: var(--bg-soft);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--line-soft);
  color: var(--accent);
}
pre {
  overflow: auto;
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: var(--space-4);
  font-family: var(--font-mono);
  font-size: 13.5px;
  line-height: 1.6;
  margin: var(--space-5) 0;
}
pre code { border: 0; padding: 0; background: transparent; color: var(--fg); }
pre.mermaid {
  background: var(--bg-card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: var(--space-5);
  text-align: center;
  margin: var(--space-6) 0;
  overflow: visible;
  max-height: none;
}
pre.mermaid svg { max-width: 100%; height: auto; display: block; margin: 0 auto; }
pre.mermaid svg.flowchart { background: var(--bg-card); }

/* v0.9.1: 图示组件（融入 ljg-card 设计语言） */
figure.flowchart-block {
  margin: var(--space-6) 0;
  padding: var(--space-5) var(--space-5) var(--space-4);
  background: var(--bg-card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
}
figure.flowchart-block figcaption {
  font-family: var(--font-sans);
  font-size: 12px;
  color: var(--muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: var(--space-3);
  font-weight: 600;
}
figure.flowchart-block figcaption .fig-num {
  color: var(--accent);
  font-weight: 700;
}
.flowchart-canvas {
  overflow: visible;
  max-height: none;
  display: flex;
  justify-content: center;
  align-items: center;
}
.flowchart-canvas svg { max-width: 100%; height: auto; display: block; }
.flowchart-canvas .chart-svg { max-width: 100%; height: auto; }
p.flowchart-note {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--line-soft);
  font-size: 13.5px;
  color: var(--fg-soft);
  font-style: italic;
  font-family: var(--font-serif);
}

/* v0.9.1: 分组卡片（chart_selector 的 grouped_cards 用） */
.grouped-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-4);
  margin: var(--space-5) 0;
}
.card-group {
  padding: var(--space-4);
  background: var(--bg-card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
}
.card-group-title {
  font-family: var(--font-sans);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.02em;
  margin-bottom: var(--space-2);
}
.card-group-desc {
  font-size: 13px;
  color: var(--fg-soft);
  font-style: italic;
  margin-bottom: var(--space-3);
  line-height: 1.55;
}
.card-items { display: flex; flex-direction: column; gap: var(--space-2); }
.card-item {
  padding: var(--space-2) var(--space-3);
  background: var(--bg-soft);
  border-left: 2px solid var(--line);
  font-size: 13.5px;
  border-radius: var(--radius-sm);
}

/* v0.9.1: 附录证据等级徽章（融入 stop-slop 风格的颜色编码） */
.evidence-grade {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.evidence-grade-a { background: #e8f5e9; color: #2e7d32; border: 1px solid #c8e6c9; }
.evidence-grade-b { background: #e3f2fd; color: #1565c0; border: 1px solid #bbdefb; }
.evidence-grade-c { background: #fff8e1; color: #ef6c00; border: 1px solid #ffe082; }
.evidence-grade-d { background: #ffebee; color: #c62828; border: 1px solid #ffcdd2; }

/* v0.9.1: 结论状态徽章 */
.conclusion-status {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.status-confirmed { background: #eceff1; color: #455a64; border: 1px solid #cfd8dc; }
.status-partial { background: #fff3e0; color: #e65100; border: 1px solid #ffe0b2; }
.status-rejected { background: #ffebee; color: #c62828; border: 1px solid #ffcdd2; }

hr { border: 0; border-top: 1px solid var(--line); margin: var(--space-6) 0; }

/* ===== Analogy card (physics analogy / pattern mapping) ===== */
.analogy-card {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: var(--space-4);
  align-items: center;
  margin: var(--space-5) 0;
  padding: var(--space-4) var(--space-5);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--bg-card);
}
.analogy-x { font-weight: 600; font-family: var(--font-serif); }
.analogy-arrow { color: var(--muted-2); font-size: 22px; font-family: var(--font-sans); }
.analogy-y { color: var(--muted); font-style: italic; font-family: var(--font-serif); }

/* ===== Code snippet card ===== */
.code-snippet-card {
  margin: var(--space-5) 0;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  overflow: hidden;
}
.code-snippet-meta {
  background: var(--bg-soft);
  padding: var(--space-2) var(--space-4);
  font-size: 12px;
  color: var(--muted);
  border-bottom: 1px solid var(--line);
  font-family: var(--font-sans);
}
.code-snippet-card pre { margin: 0; border: 0; background: var(--bg-card); border-radius: 0; }

/* ===== Tables (Stripe Press style: clean lines, no heavy borders) ===== */
table {
  border-collapse: collapse;
  width: 100%;
  table-layout: fixed;
  margin: var(--space-5) 0;
  font-size: 14.5px;
  font-family: var(--font-sans);
}
th, td {
  border: 0;
  border-bottom: 1px solid var(--line);
  padding: 10px 12px;
  text-align: left;
  vertical-align: top;
  line-height: 1.6;
}
th {
  background: transparent;
  font-weight: 600;
  color: var(--fg);
  border-bottom: 2px solid var(--fg);
  font-size: 13px;
  letter-spacing: 0.02em;
}
td { color: var(--fg-soft); }
tbody tr:hover { background: var(--bg-soft); }

/* ===== Collapsible details ===== */
.details-wrap {
  margin: var(--space-6) 0;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--bg-card);
  overflow: hidden;
}
details summary {
  cursor: pointer;
  padding: var(--space-4) var(--space-5);
  font-weight: 600;
  font-family: var(--font-sans);
  font-size: 14.5px;
  user-select: none;
  list-style: none;
  color: var(--fg);
}
details summary::-webkit-details-marker { display: none; }
details summary::before { content: "▸ "; color: var(--muted-2); font-family: var(--font-sans); margin-right: var(--space-2); transition: transform 0.15s; display: inline-block; }
details[open] summary::before { transform: rotate(90deg); }
.details-body { padding: 0 var(--space-5) var(--space-5); border-top: 1px solid var(--line-soft); }
.details-body > *:first-child { margin-top: var(--space-4); }

/* ===== Toolbar (search/filter, kept for legacy) ===== */
.toolbar { display: flex; gap: var(--space-3); flex-wrap: wrap; margin: var(--space-5) 0 var(--space-6); }
button, input {
  border: 1px solid var(--line);
  background: var(--bg-card);
  color: var(--fg);
  padding: 7px 12px;
  font: inherit;
  font-family: var(--font-sans);
  font-size: 13px;
  border-radius: var(--radius-sm);
}
button { cursor: pointer; transition: all 0.15s; }
button:hover, button.active { background: var(--fg); color: var(--bg); border-color: var(--fg); }
input { width: min(100%, 360px); }

footer {
  color: var(--muted);
  font-size: 12.5px;
  font-family: var(--font-sans);
  border-top: 1px solid var(--line);
  padding-top: var(--space-5);
  margin-top: var(--space-7);
  line-height: 1.7;
}

/* ===== v0.8 visual_layout blocks ===== */
.visual-layout { border-top: 0; padding: 0; margin-bottom: var(--space-5); }
.visual-layout[data-layout-theme="narrative"] { border-top: 0; padding-top: 0; }
.visual-layout[data-layout-theme="narrative"] .vm-hero { border: 0; padding: 0; background: transparent; }
.visual-layout[data-layout-theme="narrative"] .vm-hero .hero-verdict { font-size: 30px; }

/* ===== Hero (核心判断) ===== */
.vm-hero {
  border: 0;
  border-left: 3px solid var(--accent);
  padding: var(--space-2) 0 var(--space-2) var(--space-5);
  background: transparent;
  margin-bottom: var(--space-7);
}
.vm-hero .label, .hero-label {
  color: var(--accent);
  font-family: var(--font-sans);
  font-size: 11.5px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  margin-bottom: var(--space-3);
  font-weight: 600;
}
.hero-verdict {
  font-family: var(--font-serif);
  font-size: 30px;
  line-height: 1.25;
  font-weight: 600;
  margin: var(--space-2) 0 var(--space-3);
  letter-spacing: -0.02em;
  color: var(--fg);
}
.hero-summary {
  max-width: 38rem;
  color: var(--fg-soft);
  font-size: 16px;
  line-height: 1.7;
  margin-top: var(--space-3);
}
.hero-meta {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-top: var(--space-5);
  padding-top: var(--space-4);
  border-top: 1px solid var(--line-soft);
}
.hero-meta-row {
  display: grid;
  grid-template-columns: 8rem minmax(0, 1fr);
  gap: var(--space-3);
  font-family: var(--font-sans);
  font-size: 13.5px;
  align-items: baseline;
}
.hero-meta-label { color: var(--muted); font-weight: 500; }
.hero-meta-value { color: var(--fg-soft); }
.pill {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 2px 9px;
  border: 1px solid var(--line);
  background: var(--bg-card);
  color: var(--muted);
  font-family: var(--font-sans);
  font-size: 12px;
  border-radius: 999px;
}

/* ===== Concept Ladder (核心：术语阶梯) ===== */
.concept-ladder {
  margin: var(--space-7) 0;
  padding: 0;
  border: 0;
  background: transparent;
}
.concept-ladder h2 {
  font-family: var(--font-serif);
  font-size: 22px;
  margin: 0 0 var(--space-2);
  font-weight: 600;
  color: var(--fg);
}
.ladder-note {
  color: var(--muted);
  font-family: var(--font-sans);
  font-size: 13.5px;
  margin: 0 0 var(--space-5);
  line-height: 1.65;
  max-width: 38rem;
}
.ladder-entry {
  margin: var(--space-5) 0;
  padding: var(--space-5) 0 var(--space-5) var(--space-5);
  border-left: 2px solid var(--line);
  position: relative;
}
.ladder-entry:hover { border-left-color: var(--accent); }
.ladder-head {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}
.ladder-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  background: var(--accent);
  color: var(--bg);
  font-family: var(--font-sans);
  font-size: 12px;
  font-weight: 700;
  border-radius: 50%;
  flex-shrink: 0;
}
.ladder-term {
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: var(--fg);
  letter-spacing: -0.01em;
}
.ladder-row {
  display: grid;
  grid-template-columns: 5rem minmax(0, 1fr);
  gap: var(--space-4);
  margin: var(--space-3) 0;
  align-items: baseline;
}
.ladder-field {
  font-family: var(--font-sans);
  font-size: 11.5px;
  color: var(--accent);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-weight: 600;
}
.ladder-value {
  font-family: var(--font-serif);
  font-size: 15.5px;
  line-height: 1.7;
  color: var(--fg-soft);
}
.ladder-intuition .ladder-value { font-style: italic; color: var(--muted); }
.ladder-anchor .ladder-value { color: var(--accent); font-weight: 500; }

/* ===== Decision Path (vertical timeline) ===== */
.decision-path {
  margin: var(--space-7) 0;
  padding: var(--space-6) var(--space-6) var(--space-4);
  background: var(--bg-card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
}
.decision-path h2 {
  font-family: var(--font-serif);
  font-size: 22px;
  margin: 0 0 var(--space-5);
  font-weight: 600;
}
.decision-table { font-size: 14.5px; font-family: var(--font-sans); }
.decision-table td:first-child {
  font-weight: 700;
  text-align: center;
  color: var(--accent);
  font-family: var(--font-serif);
  font-size: 18px;
  width: 2.5rem;
}

/* ===== Question Bank (面试问题清单) ===== */
.question-bank {
  margin: var(--space-7) 0;
  padding: 0;
  border: 0;
  background: transparent;
}
.question-bank h2 {
  font-family: var(--font-serif);
  font-size: 22px;
  margin: 0 0 var(--space-2);
  font-weight: 600;
}
.qb-note {
  color: var(--muted);
  font-family: var(--font-sans);
  font-size: 13.5px;
  margin: 0 0 var(--space-5);
  line-height: 1.65;
  max-width: 38rem;
}
.qb-category {
  margin: var(--space-5) 0;
  padding-left: var(--space-5);
  border-left: 2px solid var(--line);
}
.qb-category-title {
  font-family: var(--font-sans);
  font-size: 13px;
  color: var(--accent);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin: 0 0 var(--space-3);
  font-weight: 600;
}
.question-list { padding-left: var(--space-5); }
.question-list li { margin: var(--space-3) 0; }
.qb-question {
  font-family: var(--font-serif);
  font-size: 15.5px;
  font-weight: 500;
  color: var(--fg);
  line-height: 1.6;
}
.question-context {
  color: var(--muted);
  font-family: var(--font-sans);
  font-size: 12.5px;
  margin-top: var(--space-1);
  font-style: normal;
  line-height: 1.55;
}

/* ===== Causal Chain ===== */
.causal-chain { margin: var(--space-7) 0; }
.causal-chain h2 {
  font-family: var(--font-serif);
  font-size: 22px;
  margin: 0 0 var(--space-5);
  font-weight: 600;
}
.chain-flow {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  align-items: stretch;
}
.chain-step {
  flex: 1;
  min-width: 160px;
  padding: var(--space-4) var(--space-4);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--bg-card);
}
.step-label {
  font-family: var(--font-sans);
  font-weight: 600;
  margin-bottom: var(--space-2);
  font-size: 13px;
  color: var(--accent);
  letter-spacing: 0.04em;
}
.step-detail {
  font-family: var(--font-serif);
  font-size: 14px;
  color: var(--fg-soft);
  line-height: 1.6;
}
.chain-arrow {
  display: flex;
  align-items: center;
  color: var(--muted-2);
  font-family: var(--font-sans);
  font-size: 22px;
}

/* ===== Timeline ===== */
.timeline-block { margin: var(--space-7) 0; }
.timeline-block h2 {
  font-family: var(--font-serif);
  font-size: 22px;
  margin: 0 0 var(--space-5);
  font-weight: 600;
}
.timeline {
  list-style: none;
  padding: 0;
  margin: 0;
  border-left: 2px solid var(--line);
  padding-left: var(--space-5);
}
.timeline li {
  padding: var(--space-3) 0 var(--space-3) var(--space-3);
  position: relative;
}
.timeline li::before {
  content: "";
  position: absolute;
  left: calc(-1 * var(--space-5) - 6px);
  top: var(--space-4);
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--accent);
  border: 2px solid var(--bg);
}
.tl-date {
  font-family: var(--font-sans);
  font-weight: 600;
  font-size: 13px;
  color: var(--accent);
}
.tl-event {
  font-family: var(--font-serif);
  font-size: 15px;
  color: var(--fg-soft);
  margin-top: var(--space-1);
}

/* ===== Evidence Table ===== */
.evidence-table-block { margin: var(--space-7) 0; }
.evidence-table-block h2 {
  font-family: var(--font-serif);
  font-size: 22px;
  margin: 0 0 var(--space-5);
  font-weight: 600;
}

/* ===== Legacy dashboard (kept as fallback, but de-emphasized) ===== */
.dashboard { border-top: 1px solid var(--line); padding: var(--space-7) 0 var(--space-2); margin-bottom: var(--space-5); }
.section-label {
  margin: var(--space-6) 0 var(--space-3);
  font-family: var(--font-sans);
  font-size: 11.5px;
  color: var(--muted);
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-weight: 600;
}
.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-3);
  margin: var(--space-3) 0 var(--space-6);
}
.summary-card {
  border: 1px solid var(--line);
  padding: var(--space-4);
  min-height: 96px;
  background: var(--bg-card);
  border-radius: var(--radius);
}
.summary-card .label {
  color: var(--muted);
  font-family: var(--font-sans);
  font-size: 12.5px;
  margin-bottom: var(--space-2);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.summary-card .value {
  font-weight: 600;
  font-family: var(--font-serif);
  font-size: 15px;
  line-height: 1.5;
  color: var(--fg);
}
.object-tools, .table-tools {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  margin: var(--space-3) 0 var(--space-4);
}
.object-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
  margin: var(--space-3) 0 var(--space-7);
}
.object-card {
  border: 1px solid var(--line);
  background: var(--bg-card);
  padding: var(--space-4);
  cursor: pointer;
  min-height: 210px;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  border-radius: var(--radius);
  transition: border-color 0.15s, box-shadow 0.15s;
}
.object-card:hover, .object-card:focus {
  outline: 0;
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent) inset;
}
.object-card .topline {
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
  align-items: flex-start;
}
.object-card h3 {
  margin: 0;
  font-family: var(--font-serif);
  font-size: 19px;
  line-height: 1.3;
  font-weight: 600;
}
.rank {
  border: 1px solid var(--fg);
  min-width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-sans);
  font-size: 12px;
  font-weight: 700;
  border-radius: 50%;
}
.card-meta {
  color: var(--muted);
  font-family: var(--font-sans);
  font-size: 13px;
}
.card-line {
  font-family: var(--font-serif);
  font-size: 14.5px;
  color: var(--fg-soft);
  line-height: 1.6;
}
.card-fields {
  display: grid;
  gap: var(--space-2);
  margin-top: auto;
  font-family: var(--font-sans);
  font-size: 13px;
}
.card-fields div {
  display: grid;
  grid-template-columns: 74px minmax(0, 1fr);
  gap: var(--space-3);
}
.card-fields span:first-child { color: var(--muted); }
.strategy-tabs {
  border: 1px solid var(--line);
  margin: var(--space-3) 0 var(--space-7);
  border-radius: var(--radius);
  overflow: hidden;
}
.tab-buttons {
  display: flex;
  flex-wrap: wrap;
  border-bottom: 1px solid var(--line);
  background: var(--bg-soft);
}
.tab-buttons button { border: 0; border-right: 1px solid var(--line); border-radius: 0; background: transparent; }
.tab-buttons button.active { background: var(--bg-card); border-bottom: 2px solid var(--accent); }
.tab-panel {
  display: none;
  padding: var(--space-5);
  background: var(--bg-card);
}
.tab-panel.active { display: block; }
.matrix-wrap, .filterable-table-wrap {
  overflow: auto;
  margin: var(--space-3) 0 var(--space-7);
  border: 1px solid var(--line);
  border-radius: var(--radius);
}
.full-report-note {
  color: var(--muted);
  font-family: var(--font-sans);
  font-size: 14px;
  margin-bottom: var(--space-5);
}
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(26, 26, 26, 0.54);
  display: none;
  align-items: center;
  justify-content: center;
  padding: var(--space-6);
  z-index: 20;
}
.modal-backdrop.open { display: flex; }
.modal {
  width: min(920px, 100%);
  max-height: min(86vh, 920px);
  overflow: auto;
  background: var(--bg-card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: var(--space-6);
  box-shadow: 0 16px 60px rgba(0, 0, 0, 0.18);
}
.modal-head {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
  border-bottom: 1px solid var(--line);
  padding-bottom: var(--space-3);
  margin-bottom: var(--space-4);
}
.modal h2 {
  margin: 0;
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 600;
}
.modal-block {
  border-top: 1px solid var(--line);
  padding-top: var(--space-3);
  margin-top: var(--space-3);
}
.modal-block h4 {
  margin: 0 0 var(--space-2);
  color: var(--muted);
  font-family: var(--font-sans);
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
@media (max-width: 1000px) {
  /* Desktop-first report: keep the reading shell stable instead of switching to a mobile layout. */
  .page-shell { min-width: 1040px; }
}
"""


def clean_emoji(s: str) -> str:
    return re.sub(r"[\U0001F300-\U0001FAFF☀-➿]", "", s or "")


def inline_md(text: Any) -> str:
    s = str(text or "")
    # v0.9.2: 表格内联 HTML 标签 pass-through（解决徽章被转义成 &lt;span&gt; 的问题）
    # 命中证据等级/结论状态徽章等已知 span 标签时，跳过 html.escape
    if re.search(r'<span class="(?:evidence-grade|conclusion-status)', s) or s.startswith("<span"):
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        return s
    text = html.escape(s)
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
            joined = " ".join(para).strip()
            # v0.9.1 fix: if paragraph contains raw HTML (figure/svg/div/span etc), pass through without escape
            if joined.startswith("<") and (">" in joined):
                # Contains HTML tags - pass through raw, only process inline md on text between tags
                out.append(joined)
            else:
                out.append("<p>" + inline_md(joined) + "</p>")
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

    in_html_block = False
    html_block_lines = []
    html_block_tag = ""

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        # v0.9.1: detect HTML block start (line starts with <tag)
        if not in_code and not in_table and not in_html_block:
            if stripped.startswith("<figure") or stripped.startswith("<svg") or stripped.startswith('<div class="grouped-cards"'):
                flush_para(); close_ul(); close_table()
                in_html_block = True
                html_block_lines = [line]
                html_block_tag = "figure" if "<figure" in stripped else ("svg" if "<svg" in stripped else "div")
                continue

        # v0.9.1: inside HTML block - collect lines until closing tag
        if in_html_block:
            html_block_lines.append(line)
            # Check for closing tag
            if html_block_tag == "figure" and stripped == "</figure>":
                out.append("\n".join(html_block_lines))
                in_html_block = False
                html_block_lines = []
                continue
            elif html_block_tag == "svg" and stripped == "</svg>":
                # svg might be wrapped in figure, check if next is </figure>
                # Actually svg is always inside figure in our case, so let figure handle closing
                # But if standalone svg, output now
                if not any("<figure" in l for l in html_block_lines):
                    out.append("\n".join(html_block_lines))
                    in_html_block = False
                    html_block_lines = []
                continue
            elif html_block_tag == "div" and stripped == "</div>":
                out.append("\n".join(html_block_lines))
                in_html_block = False
                html_block_lines = []
                continue
            else:
                continue  # keep collecting

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
    meta_html = []
    for item in meta:
        if isinstance(item, dict):
            label = item.get("label", "")
            value = item.get("value", "")
            meta_html.append(f"<div class='hero-meta-row'><span class='hero-meta-label'>{inline_md(label)}</span><span class='hero-meta-value'>{inline_md(value)}</span></div>")
        else:
            meta_html.append(f"<div class='hero-meta-row'><span class='hero-meta-value'>{inline_md(str(item))}</span></div>")
    return f"""
    <section class="vm-hero">
      <div class="hero-label">核心判断</div>
      <div class="hero-verdict">{inline_md(verdict)}</div>
      {f'<div class="hero-summary">{inline_md(summary)}</div>' if summary else ''}
      {f'<div class="hero-meta">{''.join(meta_html)}</div>' if meta_html else ''}
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
    return f"<div class='section-label'>关键卡片</div><section class='summary-grid'>{''.join(items)}</section>"


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
    <div class="section-label">岗位卡片</div>
    <div class="object-tools">
      <input id="objectSearch" type="search" placeholder="筛选岗位 / 风险 / 方向 / 价值" oninput="filterCards(this.value)">
      <span class="pill" id="objectCount">{len(cards)} 张卡片</span>
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


# ===== v0.7 layout_spec-driven rendering =====
# Borrowed pattern: assafelovic/gpt-researcher VisualizerAgent — each skill
# returns None when no suitable data, and the orchestrator skips None blocks.

def render_concept_ladder_block(intent_doc: dict[str, Any], view_model: dict[str, Any] | None = None) -> str | None:
    """Render concept ladder. Prefers view_model.concept_ladder (rich dict with
    intuition/definition/mechanism/etc.) over intent_doc.concept_ladder_seed
    (bare string list). Returns None if no ladder data."""
    rich_ladder = []
    if view_model:
        rich_ladder = view_model.get("concept_ladder") or []
    v07 = intent_doc.get("v07") or intent_doc
    needed = v07.get("concept_ladder_needed") or rich_ladder
    if not needed and not rich_ladder:
        return None
    seed = v07.get("concept_ladder_seed") or []
    # Build unified ladder: prefer rich dicts, fall back to seed strings
    items = []
    if rich_ladder:
        for entry in rich_ladder:
            if isinstance(entry, dict):
                items.append({
                    "term": entry.get("term", ""),
                    "intuition": entry.get("intuition", ""),
                    "definition": entry.get("definition", ""),
                    "mechanism": entry.get("mechanism", ""),
                    "industry_context": entry.get("industry_context", ""),
                    "user_concern": entry.get("user_concern", ""),
                    "project_anchor": entry.get("project_anchor", ""),
                })
            elif isinstance(entry, str):
                items.append({"term": entry, "intuition": "", "definition": "", "mechanism": "", "industry_context": "", "user_concern": "", "project_anchor": ""})
    else:
        for term in seed:
            items.append({"term": term, "intuition": "", "definition": "", "mechanism": "", "industry_context": "", "user_concern": "", "project_anchor": ""})
    if not items:
        return None
    parts = [
        "<section class='concept-ladder' id='concept-ladder'>",
        "<h2>概念阶梯</h2>",
        "<p class='ladder-note'>陌生领域先建概念阶梯，再展开事实。每个术语：直觉比喻 → 基础定义 → 工作机制 → 行业语境 → 用户关心点 → 项目锚点。</p>",
    ]
    for i, item in enumerate(items, 1):
        term = html.escape(str(item.get("term", "")))
        intuition = item.get("intuition", "")
        definition = item.get("definition", "")
        mechanism = item.get("mechanism", "")
        industry = item.get("industry_context", "")
        user = item.get("user_concern", "")
        anchor = item.get("project_anchor", "")
        parts.append(f"<article class='ladder-entry' id='ladder-{i}'>")
        parts.append(f"<header class='ladder-head'><span class='ladder-num'>{i}</span><h3 class='ladder-term'>{term}</h3></header>")
        if intuition:
            parts.append(f"<div class='ladder-row ladder-intuition'><span class='ladder-field'>直觉</span><div class='ladder-value'>{inline_md(intuition)}</div></div>")
        if definition:
            parts.append(f"<div class='ladder-row ladder-definition'><span class='ladder-field'>定义</span><div class='ladder-value'>{inline_md(definition)}</div></div>")
        if mechanism:
            parts.append(f"<div class='ladder-row ladder-mechanism'><span class='ladder-field'>机制</span><div class='ladder-value'>{inline_md(mechanism)}</div></div>")
        if industry:
            parts.append(f"<div class='ladder-row ladder-industry'><span class='ladder-field'>行业</span><div class='ladder-value'>{inline_md(industry)}</div></div>")
        if user:
            parts.append(f"<div class='ladder-row ladder-user'><span class='ladder-field'>用户</span><div class='ladder-value'>{inline_md(user)}</div></div>")
        if anchor:
            parts.append(f"<div class='ladder-row ladder-anchor'><span class='ladder-field'>锚点</span><div class='ladder-value'>{inline_md(anchor)}</div></div>")
        parts.append("</article>")
    parts.append("</section>")
    return "\n".join(parts)


def render_decision_path_block(view_model: dict[str, Any], intent_doc: dict[str, Any]) -> str | None:
    """Render a decision path / priority ranking block. Returns None if no
    decision_path data in view_model."""
    dp = view_model.get("decision_path") or view_model.get("decision_matrix") or {}
    if not dp:
        return None
    rows = dp.get("rows") or []
    if not rows:
        return None
    parts = [
        "<section class='decision-path' id='decision-path'>",
        "<h2>决策路径</h2>",
        "<table class='decision-table'>",
        "<thead><tr><th>优先级</th><th>选项</th><th>匹配度</th><th>理由</th></tr></thead>",
        "<tbody>",
    ]
    for i, row in enumerate(rows, 1):
        parts.append(
            f"<tr><td>{i}</td><td>{html.escape(str(row.get('option', '')))}</td>"
            f"<td>{html.escape(str(row.get('match_score', '')))}</td>"
            f"<td>{html.escape(str(row.get('rationale', '')))}</td></tr>"
        )
    parts.append("</tbody></table>")
    parts.append("</section>")
    return "\n".join(parts)


def render_question_bank_block(view_model: dict[str, Any], intent_doc: dict[str, Any]) -> str | None:
    """Render a question bank block for field-guide style reports.

    Supports two structures:
    1. Nested (preferred): {title, categories: [{category, questions:[...]}]}
    2. Flat (legacy): [{question, context}]
    """
    qb = view_model.get("question_bank")
    if not qb:
        # Try to derive from intent_doc.open_questions + clarifying_questions
        oq = intent_doc.get("open_questions") or []
        cq = (intent_doc.get("v07") or {}).get("clarifying_questions") or []
        if not oq and not cq:
            return None
        qb = []
        for q in oq:
            qb.append({"question": q.get("question", ""), "context": q.get("why", "")})
        for q in cq:
            qb.append({"question": q.get("question", ""), "context": q.get("why", "")})

    # Nested structure: {title, categories: [...]}
    if isinstance(qb, dict) and qb.get("categories"):
        title = qb.get("title", "问题清单")
        categories = qb.get("categories") or []
        parts = [
            "<section class='question-bank' id='question-bank'>",
            f"<h2>{inline_md(title)}</h2>",
            "<p class='qb-note'>把这些问题当作面试或自检脚手架。每个分类下的题目不只是答案，更是你证明'我想清楚了'的方式。</p>",
        ]
        for cat in categories:
            cat_name = cat.get("category", "") if isinstance(cat, dict) else str(cat)
            questions = cat.get("questions", []) if isinstance(cat, dict) else []
            if not questions:
                continue
            parts.append(f"<div class='qb-category'>")
            parts.append(f"<h3 class='qb-category-title'>{inline_md(cat_name)}</h3>")
            parts.append("<ol class='question-list'>")
            for q in questions:
                question = q if isinstance(q, str) else (q.get("question", "") if isinstance(q, dict) else str(q))
                context = q.get("context", "") if isinstance(q, dict) else ""
                parts.append(f"<li><div class='qb-question'>{inline_md(question)}</div>")
                if context:
                    parts.append(f"<div class='question-context'>{inline_md(context)}</div>")
                parts.append("</li>")
            parts.append("</ol>")
            parts.append("</div>")
        parts.append("</section>")
        return "\n".join(parts)

    # Flat legacy structure: list of {question, context}
    if isinstance(qb, list) and qb:
        parts = [
            "<section class='question-bank' id='question-bank'>",
            "<h2>问题清单</h2>",
            "<ol class='question-list'>",
        ]
        for q in qb:
            question = q.get("question", "") if isinstance(q, dict) else str(q)
            context = q.get("context", "") if isinstance(q, dict) else ""
            parts.append(f"<li><strong>{inline_md(question)}</strong>")
            if context:
                parts.append(f"<div class='question-context'>{inline_md(context)}</div>")
            parts.append("</li>")
        parts.append("</ol>")
        parts.append("</section>")
        return "\n".join(parts)

    return None


def render_causal_chain_block(view_model: dict[str, Any]) -> str | None:
    """Render a causal chain block (A → B → C)."""
    cc = view_model.get("causal_chain") or []
    if not cc:
        return None
    parts = [
        "<section class='causal-chain' id='causal-chain'>",
        "<h2>因果链</h2>",
        "<div class='chain-flow'>",
    ]
    for i, step in enumerate(cc):
        if i > 0:
            parts.append("<span class='chain-arrow'>→</span>")
        parts.append(f"<div class='chain-step'><div class='step-label'>{html.escape(str(step.get('label', '')))}</div><div class='step-detail'>{html.escape(str(step.get('detail', '')))}</div></div>")
    parts.append("</div>")
    parts.append("</section>")
    return "\n".join(parts)


def render_narrative_section_block(view_model: dict[str, Any]) -> str | None:
    """The full narrative is rendered from final-report.md below the visual blocks."""
    return None


def render_evidence_table_block(view_model: dict[str, Any]) -> str | None:
    """Evidence table — summary table of evidence IDs and grades."""
    et = view_model.get("evidence_table") or {}
    rows = et.get("rows") or []
    if not rows:
        return None
    parts = [
        "<section class='evidence-table-block' id='evidence-table'>",
        "<h2>证据摘要表</h2>",
        "<table><thead><tr><th>ID</th><th>主张</th><th>等级</th><th>来源</th></tr></thead><tbody>",
    ]
    for r in rows:
        parts.append(
            f"<tr><td>{html.escape(str(r.get('id', '')))}</td>"
            f"<td>{html.escape(str(r.get('claim', '')))}</td>"
            f"<td>{html.escape(str(r.get('grade', '')))}</td>"
            f"<td>{html.escape(str(r.get('source', '')))}</td></tr>"
        )
    parts.append("</tbody></table></section>")
    return "\n".join(parts)


def render_timeline_block(view_model: dict[str, Any]) -> str | None:
    """Timeline block — vertical list of dated events."""
    tl = view_model.get("timeline") or []
    if not tl:
        return None
    parts = [
        "<section class='timeline-block' id='timeline'>",
        "<h2>时间线</h2>",
        "<ul class='timeline'>",
    ]
    for item in tl:
        parts.append(
            f"<li><div class='tl-date'>{html.escape(str(item.get('date', '')))}</div>"
            f"<div class='tl-event'>{html.escape(str(item.get('event', '')))}</div></li>"
        )
    parts.append("</ul></section>")
    return "\n".join(parts)


# v0.7 visual skill registry: block name → render function.
# Each function returns str (HTML) or None (skip).
# Borrowed from gpt-researcher VisualizerAgent pattern: return None when
# no suitable data for the block.
VISUAL_SKILL_REGISTRY: dict[str, Any] = {
    "hero": lambda vm, idoc: render_hero(vm) if vm.get("hero") else None,
    "summary_cards": lambda vm, idoc: render_summary_cards(vm.get("summary_cards") or []),
    "object_cards": lambda vm, idoc: render_object_cards(
        vm.get("object_cards") or vm.get("advisor_cards") or vm.get("objects") or [],
        vm.get("object_kind") or "object",
    ),
    "strategy_tabs": lambda vm, idoc: render_tabs(vm.get("strategy_tabs") or vm.get("tabs") or []),
    "comparison_matrix": lambda vm, idoc: render_matrix(
        vm.get("comparison_matrix") or vm.get("matrix") or {}
    ),
    "filterable_table": lambda vm, idoc: render_filterable_table(vm.get("filterable_table") or {}),
    "concept_ladder": lambda vm, idoc: render_concept_ladder_block(idoc, vm),
    "decision_path": lambda vm, idoc: render_decision_path_block(vm, idoc),
    "question_bank": lambda vm, idoc: render_question_bank_block(vm, idoc),
    "causal_chain": lambda vm, idoc: render_causal_chain_block(vm),
    "timeline": lambda vm, idoc: render_timeline_block(vm),
    "evidence_table": lambda vm, idoc: render_evidence_table_block(vm),
    "narrative_section": lambda vm, idoc: render_narrative_section_block(vm),
}


def render_layout(layout_spec: dict[str, Any], view_model: dict[str, Any], intent_doc: dict[str, Any]) -> str:
    """v0.7: render blocks in order declared by layout_spec.blocks.
    Each block's render() can return None — skipped silently (gpt-researcher
    VisualizerAgent pattern). Falls back to render_dashboard if no blocks."""
    blocks = layout_spec.get("blocks") or []
    if not blocks:
        return render_dashboard(view_model) if view_model else ""

    skip_blocks = layout_spec.get("skip_blocks") or []
    skip_names = {s.get("block") if isinstance(s, dict) else s for s in skip_blocks}

    parts = [f"<section class='visual-layout' data-layout-theme='{html.escape(str(layout_spec.get('theme', '')))}' id='layout'>"]
    rendered_any = False
    for block_name in blocks:
        if block_name in skip_names:
            continue
        renderer = VISUAL_SKILL_REGISTRY.get(block_name)
        if not renderer:
            continue
        try:
            block_html = renderer(view_model, intent_doc)
        except Exception:
            block_html = None
        if block_html:
            parts.append(block_html)
            rendered_any = True
    parts.append("</section>")
    if not rendered_any:
        # Fallback to dashboard if no blocks rendered (avoid empty page)
        return render_dashboard(view_model) if view_model else ""
    return "\n".join(parts)


def load_intent_doc(project: Path) -> dict[str, Any]:
    """Load intent_doc.json for layout_spec-driven rendering."""
    path = project / "00-task" / "intent_doc.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


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
  // 高亮当前章节对应的目录项（目录不滚动时的位置补偿）
  const tocLinks=document.querySelectorAll('.toc a');
  const chapters=document.querySelectorAll('main .chapter');
  if(tocLinks.length && chapters.length){{
    const setActive=(anchor)=>{{
      tocLinks.forEach(a=>a.classList.toggle('active', a.getAttribute('href')==='#'+anchor));
    }};
    const observer=new IntersectionObserver((entries)=>{{
      entries.forEach(en=>{{ if(en.isIntersecting) setActive(en.target.id); }});
    }}, {{rootMargin: '-20% 0px -70% 0px', threshold: 0}});
    chapters.forEach(ch=>observer.observe(ch));
  }}
  // 顶部阅读进度条：补偿目录不滚动后的位置感
  const bar=document.getElementById('readingProgress');
  if(bar){{
    const upd=()=>{{
      const h=document.documentElement;
      const scrolled=h.scrollTop;
      const max=h.scrollHeight-h.clientHeight;
      bar.style.width=(max>0?(scrolled/max*100):0)+'%';
    }};
    window.addEventListener('scroll',upd,{{passive:true}});
    upd();
  }}
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


def build(project: Path, copy_desktop: bool = True) -> Path:
    report = project / "07-output" / "final-report.md"
    if not report.exists():
        raise FileNotFoundError(f"missing {report}")
    out = project / "08-html" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)

    md = report.read_text(encoding="utf-8-sig")
    # v0.10: 从 reader_simulation 引入 strip_metadata，
    # 在渲染前过滤掉证据编号、假设编号、schema 名词等幕后信息
    try:
        import reader_simulation as rs
        md = rs.strip_metadata(md)
    except ImportError:
        pass  # reader_simulation 不可用时退化为不过滤
    title, intro, sections = split_sections(md)
    state = load_state(project)
    view_model = load_view_model(project)
    intent_doc = load_intent_doc(project)
    # v0.7: prefer layout_spec from intent_doc if present
    v07 = intent_doc.get("v07") or {}
    layout_spec = v07.get("layout_spec") or {}
    has_layout_spec = bool(layout_spec.get("blocks"))
    toc, section_html = render_sections(sections)
    toc_items = [("layout", "结构化总览")] if view_model else []
    toc_items += [("full-report", "完整正文")] + toc if view_model else toc

    # v0.7: use render_layout if layout_spec exists, else legacy render_dashboard
    if has_layout_spec:
        dashboard = render_layout(layout_spec, view_model or {}, intent_doc)
    else:
        dashboard = render_dashboard(view_model) if view_model else ""
    modal = render_modal_shell() if view_model else ""
    full_report_open = "<section class='chapter' id='full-report'><h2>完整正文</h2><div class='full-report-note'>下方保留 07-output/final-report.md 的完整正文，方便存档和逐段阅读。</div>" if view_model else ""
    full_report_close = "</section>" if view_model else ""

    # Detect mermaid blocks: only load CDN script if report actually uses them.
    # Avoids 5-30s jsdelivr timeout on mainland when report has 0 mermaid blocks.
    combined_html = section_html + (intro or "")
    has_mermaid = "pre class='mermaid'" in combined_html or '<pre class="mermaid">' in combined_html or 'class="mermaid"' in combined_html
    mermaid_script_tag = '<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>' if has_mermaid else '<!-- mermaid CDN skipped: no mermaid blocks in report -->'
    mermaid_init_script = "<script>mermaid.initialize({{startOnLoad: true, theme: 'neutral', securityLevel: 'loose', flowchart: {{useMaxWidth: false, htmlLabels: true, curve: 'basis'}}, themeVariables: {{fontSize: '15px', fontFamily: 'inherit'}}}});</script>" if has_mermaid else '<!-- mermaid init skipped: no mermaid blocks -->'

    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=1180">
  <title>{html.escape(clean_emoji(title))}</title>
  <style>{CSS}</style>
  {mermaid_script_tag}
</head>
<body data-source="final-report.md" data-view-type="{html.escape(str(state.get('view_type', '')))}" data-theme="{html.escape(str(layout_spec.get('theme', '')))}" data-layout-v07="{'true' if has_layout_spec else 'false'}">
  <div class="reading-progress" id="readingProgress"></div>
  <div class="page-shell">
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
      <div class="subtitle">由 07-output/final-report.md 生成 · 桌面端长文阅读 · 左侧目录 + 45rem 正文 · 结构化块穿插</div>
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
  {mermaid_init_script}
</body>
</html>
"""
    out.write_text(html_doc, encoding="utf-8")

    _sync_state_after_build(project)

    # Post-research profile write-back: if validator passed (status=completed),
    # capture what the user actually resolved, judgment patterns, and
    # unresolved seeds for future projects. Non-fatal - failure here doesn't
    # break the build. Lazy import to avoid loading LLM client at module
    # import time.
    try:
        state_after = json.loads(
            (project / "research_state.json").read_text(encoding="utf-8-sig")
        )
        if state_after.get("status") == "completed":
            from profile_updater import write_back as write_back_profile
            profile_result = write_back_profile(project)
            print(profile_result["aha_summary"])
    except Exception as exc:
        # Profile write-back is best-effort. Don't fail the build.
        print(f"[warn] profile write-back skipped: {exc}", file=sys.stderr)

    if copy_desktop:
        desktop = Path.home() / "Desktop" / f"{title}.html"
        shutil.copy2(out, desktop)
        print(f"Copied desktop HTML: {desktop}")

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Research OS reader-first HTML")
    parser.add_argument("--project", required=True, help="Path to research project directory")
    parser.add_argument("--no-copy-desktop", action="store_true", help="不拷贝到桌面（默认拷贝）")
    args = parser.parse_args()
    copy_desktop = not args.no_copy_desktop
    args = parser.parse_args()

    out = build(Path(args.project).resolve(), copy_desktop)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
