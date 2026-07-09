"""Research OS v1.0: chart_selector.py有机融入 chart-visualization skill 的核心能力——
"按信息类型智能选择最合适的图表类型"。

不调外部 skill，而是把"选图逻辑"内化成 Research OS 自己的能力。
chart-visualization 有 26 种图表，我们针对深度调研场景精选 8 种，
每种配 mermaid/SVG/HTML 实现，让 build_research_html.py 能直接渲染。
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import math


class InfoType(Enum):
    """信息的本质类型——决定用什么图表"""
    FLOW = "flow"
    COMPARISON = "comparison"
    STAT_RELATION = "stat_relation"
    TRADEOFF = "tradeoff"
    HIERARCHY = "hierarchy"
    CLASSIFICATION = "classification"
    DISTRIBUTION = "distribution"
    TABLE = "table"


@dataclass
class ChartSpec:
    info_type: InfoType
    chart_type: str
    renderer: str
    title: str
    note: Optional[str] = None
    data: Optional[dict] = None


SELECTOR_RULES = {
    InfoType.FLOW: ("flowchart", "mermaid"),
    InfoType.COMPARISON: ("radar", "svg"),
    InfoType.STAT_RELATION: ("scatter", "svg"),
    InfoType.TRADEOFF: ("quadrant", "svg"),
    InfoType.HIERARCHY: ("onion", "svg"),
    InfoType.CLASSIFICATION: ("grouped_cards", "html_css"),
    InfoType.DISTRIBUTION: ("matrix", "html_css"),
    InfoType.TABLE: ("table", "html_css"),
}


PALETTE = {
    "bg_card": "#fafaf7",
    "line": "#e5e2d8",
    "accent": "#8b5a3c",
    "fg": "#2a2a2a",
    "fg_soft": "#5a5a5a",
    "muted": "#8a8a8a",
    "series_1": "#8b5a3c",
    "series_2": "#5a7a6a",
    "series_3": "#7a6a8a",
    "series_4": "#a8855a",
    "warn": "#b87a4a",
    "danger": "#a85a5a",
    "ok": "#5a8a6a",
}


def select_chart(info_type: InfoType, title: str, data: dict,
                 note: Optional[str] = None) -> ChartSpec:
    chart_type, renderer = SELECTOR_RULES.get(info_type, ("table", "html_css"))
    return ChartSpec(info_type, chart_type, renderer, title, note, data)


def render_quadrant_svg(spec: ChartSpec) -> str:
    d = spec.data or {}
    x_axis = d.get("x_axis", "X 轴")
    y_axis = d.get("y_axis", "Y 轴")
    points = d.get("points", [])

    svg_width = 560
    svg_height = 420
    margin = 60
    plot_w = svg_width - 2 * margin
    plot_h = svg_height - 2 * margin

    parts = [f'<svg viewBox="0 0 {svg_width} {svg_height}" xmlns="http://www.w3.org/2000/svg" class="chart-svg">']
    parts.append(f'<rect x="{margin}" y="{margin}" width="{plot_w/2}" height="{plot_h/2}" fill="{PALETTE["bg_card"]}" opacity="0.5"/>')
    parts.append(f'<rect x="{margin+plot_w/2}" y="{margin}" width="{plot_w/2}" height="{plot_h/2}" fill="{PALETTE["bg_card"]}" opacity="0.3"/>')
    parts.append(f'<rect x="{margin}" y="{margin+plot_h/2}" width="{plot_w/2}" height="{plot_h/2}" fill="{PALETTE["bg_card"]}" opacity="0.3"/>')
    parts.append(f'<rect x="{margin+plot_w/2}" y="{margin+plot_h/2}" width="{plot_w/2}" height="{plot_h/2}" fill="{PALETTE["bg_card"]}" opacity="0.5"/>')
    parts.append(f'<line x1="{margin}" y1="{margin+plot_h}" x2="{margin+plot_w}" y2="{margin+plot_h}" stroke="{PALETTE["fg"]}" stroke-width="1.5"/>')
    parts.append(f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{margin+plot_h}" stroke="{PALETTE["fg"]}" stroke-width="1.5"/>')
    parts.append(f'<text x="{margin+plot_w/2}" y="{svg_height-15}" text-anchor="middle" font-size="13" fill="{PALETTE["fg_soft"]}" font-family="serif">{x_axis}</text>')
    parts.append(f'<text x="20" y="{margin+plot_h/2}" text-anchor="middle" font-size="13" fill="{PALETTE["fg_soft"]}" font-family="serif" transform="rotate(-90 20 {margin+plot_h/2})">{y_axis}</text>')
    parts.append(f'<line x1="{margin+plot_w/2}" y1="{margin}" x2="{margin+plot_w/2}" y2="{margin+plot_h}" stroke="{PALETTE["line"]}" stroke-dasharray="3,3"/>')
    parts.append(f'<line x1="{margin}" y1="{margin+plot_h/2}" x2="{margin+plot_w}" y2="{margin+plot_h/2}" stroke="{PALETTE["line"]}" stroke-dasharray="3,3"/>')
    parts.append(f'<text x="{margin+plot_w*0.25}" y="{margin+18}" text-anchor="middle" font-size="11" fill="{PALETTE["muted"]}" font-style="italic">高通用 · 低可控</text>')
    parts.append(f'<text x="{margin+plot_w*0.75}" y="{margin+18}" text-anchor="middle" font-size="11" fill="{PALETTE["muted"]}" font-style="italic">高通用 · 高可控</text>')
    parts.append(f'<text x="{margin+plot_w*0.25}" y="{margin+plot_h-8}" text-anchor="middle" font-size="11" fill="{PALETTE["muted"]}" font-style="italic">低通用 · 低可控</text>')
    parts.append(f'<text x="{margin+plot_w*0.75}" y="{margin+plot_h-8}" text-anchor="middle" font-size="11" fill="{PALETTE["muted"]}" font-style="italic">低通用 · 高可控</text>')

    for p in points:
        px = margin + (p.get("x", 0.5)) * plot_w
        py = margin + (1 - p.get("y", 0.5)) * plot_h
        color = p.get("color", PALETTE["accent"])
        parts.append(f'<circle cx="{px}" cy="{py}" r="8" fill="{color}" opacity="0.85"/>')
        parts.append(f'<circle cx="{px}" cy="{py}" r="8" fill="none" stroke="{color}" stroke-width="1.5"/>')
        label_offset_y = -14 if p.get("y", 0.5) > 0.5 else 22
        parts.append(f'<text x="{px}" y="{py+label_offset_y}" text-anchor="middle" font-size="12" fill="{PALETTE["fg"]}" font-family="serif" font-weight="600">{p["label"]}</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def render_radar_svg(spec: ChartSpec) -> str:
    d = spec.data or {}
    axes = d.get("axes", ["维度1", "维度2", "维度3", "维度4", "维度5", "维度6"])
    series = d.get("series", [])

    n = len(axes)
    cx, cy = 280, 230
    r = 160

    parts = [f'<svg viewBox="0 0 560 460" xmlns="http://www.w3.org/2000/svg" class="chart-svg">']

    for layer in range(1, 6):
        lr = r * layer / 5
        pts = []
        for i in range(n):
            angle = 2 * math.pi * i / n - math.pi / 2
            px = cx + lr * math.cos(angle)
            py = cy + lr * math.sin(angle)
            pts.append(f"{px:.1f},{py:.1f}")
        parts.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="{PALETTE["line"]}" stroke-width="1"/>')

    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{px:.1f}" y2="{py:.1f}" stroke="{PALETTE["line"]}" stroke-width="1"/>')
        lx = cx + (r + 25) * math.cos(angle)
        ly = cy + (r + 25) * math.sin(angle)
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" font-size="11" fill="{PALETTE["fg_soft"]}" font-family="serif">{axes[i]}</text>')

    for s in series:
        values = s.get("values", [])
        color = s.get("color", PALETTE["accent"])
        pts = []
        for i, v in enumerate(values):
            angle = 2 * math.pi * i / n - math.pi / 2
            vr = r * max(0, min(1, v))
            px = cx + vr * math.cos(angle)
            py = cy + vr * math.sin(angle)
            pts.append(f"{px:.1f},{py:.1f}")
        parts.append(f'<polygon points="{" ".join(pts)}" fill="{color}" fill-opacity="0.12" stroke="{color}" stroke-width="2"/>')

    legend_y = 440
    legend_x = 40
    for i, s in enumerate(series):
        color = s.get("color", PALETTE["accent"])
        name = s.get("name", f"系列{i+1}")
        parts.append(f'<rect x="{legend_x + i*120}" y="{legend_y}" width="12" height="12" fill="{color}" opacity="0.7"/>')
        parts.append(f'<text x="{legend_x + i*120 + 18}" y="{legend_y+10}" font-size="11" fill="{PALETTE["fg_soft"]}" font-family="serif">{name}</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def render_onion_svg(spec: ChartSpec) -> str:
    d = spec.data or {}
    layers = d.get("layers", [])

    cx, cy = 280, 220
    parts = [f'<svg viewBox="0 0 560 440" xmlns="http://www.w3.org/2000/svg" class="chart-svg">']

    max_r = 180
    n = len(layers)
    for i, layer in enumerate(layers):
        r = max_r * (n - i) / n
        color = layer.get("color", PALETTE["series_" + str((i % 4) + 1)])
        opacity = 0.15 + 0.2 * (i / n)
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.0f}" fill="{color}" fill-opacity="{opacity}" stroke="{color}" stroke-width="1.5"/>')
        label_y = cy - r + 15 if i < n / 2 else cy + r - 5
        parts.append(f'<text x="{cx}" y="{label_y:.0f}" text-anchor="middle" font-size="12" fill="{PALETTE["fg"]}" font-family="serif" font-weight="600">{layer["label"]}</text>')

    parts.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="{PALETTE["accent"]}"/>')

    desc_x = 480
    desc_y = 80
    for i, layer in enumerate(layers):
        color = layer.get("color", PALETTE["series_" + str((i % 4) + 1)])
        desc = layer.get("desc", "")
        parts.append(f'<rect x="{desc_x}" y="{desc_y + i*55}" width="10" height="10" fill="{color}"/>')
        parts.append(f'<text x="{desc_x + 18}" y="{desc_y + i*55 + 9}" font-size="11" fill="{PALETTE["fg"]}" font-family="serif" font-weight="600">{layer["label"]}</text>')
        parts.append(f'<text x="{desc_x + 18}" y="{desc_y + i*55 + 24}" font-size="10" fill="{PALETTE["fg_soft"]}" font-family="serif">{desc}</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def render_grouped_cards_html(spec: ChartSpec) -> str:
    d = spec.data or {}
    groups = d.get("groups", [])

    parts = ['<div class="grouped-cards">']
    for g in groups:
        color = g.get("color", PALETTE["accent"])
        items = g.get("items", [])
        parts.append(f'<div class="card-group" style="border-top: 3px solid {color};">')
        parts.append(f'<div class="card-group-title" style="color: {color};">{g["title"]}</div>')
        parts.append(f'<div class="card-group-desc">{g.get("desc", "")}</div>')
        parts.append('<div class="card-items">')
        for item in items:
            parts.append(f'<div class="card-item">{item}</div>')
        parts.append('</div></div>')
    parts.append('</div>')
    return "\n".join(parts)


def render_chart(spec: ChartSpec) -> str:
    if spec.renderer == "svg":
        if spec.chart_type == "quadrant":
            return render_quadrant_svg(spec)
        elif spec.chart_type == "radar":
            return render_radar_svg(spec)
        elif spec.chart_type == "onion":
            return render_onion_svg(spec)
    elif spec.renderer == "html_css":
        if spec.chart_type == "grouped_cards":
            return render_grouped_cards_html(spec)
    return ""


def wrap_as_figure(svg_or_html: str, spec: ChartSpec, fig_num: int) -> str:
    parts = [f'<figure class="flowchart-block" id="fig-{fig_num}">']
    parts.append(f'<figcaption><span class="fig-num">图 {fig_num}</span> · {spec.title}</figcaption>')
    parts.append(f'<div class="flowchart-canvas">{svg_or_html}</div>')
    if spec.note:
        parts.append(f'<p class="flowchart-note">{spec.note}</p>')
    parts.append('</figure>')
    return "\n".join(parts)


def get_preset_charts() -> dict:
    return {
        "hero_quadrant": select_chart(
            InfoType.TRADEOFF,
            "4 个项目在「可控性 vs 通用性」象限的定位",
            data={
                "x_axis": "← 可控性（流程可预测）        通用性（处理意外）→",
                "y_axis": "← 工程派        学术派 →",
                "points": [
                    {"label": "GPT Researcher", "x": 0.75, "y": 0.25, "color": PALETTE["series_1"]},
                    {"label": "STORM", "x": 0.65, "y": 0.80, "color": PALETTE["series_2"]},
                    {"label": "HF Open Deep Research", "x": 0.30, "y": 0.30, "color": PALETTE["series_3"]},
                    {"label": "Owl", "x": 0.20, "y": 0.85, "color": PALETTE["series_4"]},
                ],
            },
            note="GPT Researcher 和 STORM 在右侧（流程可控），HF 和 Owl 在左侧（LLM 自主）。"
        ),
        "capability_radar": select_chart(
            InfoType.COMPARISON,
            "6 维度能力雷达图",
            data={
                "axes": ["执行引擎", "引用溯源", "JS渲染", "MCP生态", "复现可行性", "中文支持"],
                "series": [
                    {"name": "GPT Researcher", "values": [0.85, 0.40, 0.70, 0.80, 0.50, 0.60], "color": PALETTE["series_1"]},
                    {"name": "STORM", "values": [0.75, 0.95, 0.30, 0.20, 0.60, 0.20], "color": PALETTE["series_2"]},
                    {"name": "HF Open Deep Research", "values": [0.60, 0.10, 0.10, 0.20, 0.70, 0.50], "color": PALETTE["series_3"]},
                    {"name": "Owl", "values": [0.80, 0.30, 0.90, 0.85, 0.30, 0.60], "color": PALETTE["series_4"]},
                ],
            },
            note="STORM 引用溯源最强（0.95），Owl JS 渲染最强（0.90），但两者复现可行性都不高。"
        ),
        "philosophy_groups": select_chart(
            InfoType.CLASSIFICATION,
            "两派架构哲学",
            data={
                "groups": [
                    {
                        "title": "流水线派",
                        "desc": "把调研拆成固定阶段（问→搜→筛→写），用编排保证稳定性",
                        "color": PALETTE["series_1"],
                        "items": ["GPT Researcher — planner-execution 双 agent", "STORM — 4 模块+persona 对话"],
                    },
                    {
                        "title": "Agent 派",
                        "desc": "不做固定阶段，让 LLM 在 ReAct loop 里自己决定下一步",
                        "color": PALETTE["series_3"],
                        "items": ["HF Open Deep Research — CodeAgent 两层", "Owl — Workforce/RolePlaying"],
                    },
                ]
            },
            note=None
        ),
        "methodology_onion": select_chart(
            InfoType.HIERARCHY,
            "Research OS 方法论分层",
            data={
                "layers": [
                    {"label": "读者优先", "desc": "最外层：内部工作区 vs 最终交付分离", "color": PALETTE["series_1"]},
                    {"label": "反方审计", "desc": "中间层：主动攻击每条结论", "color": PALETTE["series_2"]},
                    {"label": "证据分级", "desc": "中间层：A/B/C/D + 来源独立性", "color": PALETTE["series_3"]},
                    {"label": "假设驱动", "desc": "核心层：先假设再验证", "color": PALETTE["series_4"]},
                ]
            },
            note="Research OS 独特的 4 层方法论——四个开源项目都没有显式实现，但有隐式替代。"
        ),
    }


if __name__ == "__main__":
    charts = get_preset_charts()
    print("Available preset charts:")
    for k, spec in charts.items():
        print(f"  - {k}: {spec.chart_type} ({spec.renderer}) — {spec.title}")
