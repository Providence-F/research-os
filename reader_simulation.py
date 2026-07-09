"""reader_simulation.py - Research OS v1.0 模块LLM 不只是生产者，更要扮演读者代理。在 final-report.md 写完后、ros build 之前，
让 LLM 扮演 reader persona 逐段读报告，反馈读懂度 + 卡点 + 改写建议，
触发写-读-改闭环。

设计原则：
1. 不直接调 LLM API，定义接口 + 默认实现（默认由 agent 模拟）
2. 输出结构化 JSON 诊断，不只是 pass/fail
3. 读者画像含具体 knowledge_blindspots
4. 重写循环最多 2 轮，第 3 轮 fail 让人接手
"""

from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# =====================================================================
# 1. 幕后信息过滤器（规则层，廉价确定）
# =====================================================================

EVIDENCE_ID_PATTERN = re.compile(r"\[E\d{3}\]")
HYPOTHESIS_ID_PATTERN = re.compile(r"\[H\d{3}\]")
SCHEMA_TERMS = [
    "v0.7 契约", "v0.9", "reader_model", "concept_ladder_seed",
    "concept_ladder", "intent_tree", "personalization_plan",
    "report_contract", "exploration_history", "stated_intent",
    "resolved_intent", "intent_evolution", "v07", "v09",
]


def strip_metadata(text: str) -> str:
    """删除不该出现在读者视图的幕后信息。"""
    text = EVIDENCE_ID_PATTERN.sub("", text)
    text = HYPOTHESIS_ID_PATTERN.sub("", text)
    for term in SCHEMA_TERMS:
        text = text.replace(f"({term})", "")
        text = text.replace(f"（{term}）", "")
        text = re.sub(rf"(?<![\w]){re.escape(term)}(?![\w])", "", text)
    text = re.sub(r"  +", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# =====================================================================
# 2. 报告切分
# =====================================================================

def split_into_sections(md: str) -> list[dict[str, Any]]:
    """把 markdown 切成 [{title, paragraphs: [str]}]。"""
    sections: list[dict[str, Any]] = []
    current_title: str | None = None
    current_paras: list[str] = []
    buffer: list[str] = []

    def flush_para():
        if buffer:
            para = "\n".join(buffer).strip()
            if para:
                current_paras.append(para)
            buffer.clear()

    def flush_section():
        flush_para()
        if current_title is not None:
            sections.append({"title": current_title, "paragraphs": current_paras[:]})
        current_paras.clear()

    for line in md.split("\n"):
        if line.startswith("## "):
            flush_section()
            current_title = line[3:].strip()
        elif line.startswith("# ") or line.startswith("### "):
            flush_para()
            if current_title is not None:
                current_paras.append(line.strip())
            else:
                buffer.append(line)
        elif line.strip() == "":
            flush_para()
        else:
            buffer.append(line)
    flush_section()
    return sections


# =====================================================================
# 3. 读者诊断数据结构
# =====================================================================

@dataclass
class ParagraphDiagnosis:
    section_title: str
    paragraph_index: int
    paragraph_preview: str
    comprehension_score: float
    understood_summary: str
    stuck_points: list[dict[str, str]] = field(default_factory=list)
    term_gaps: list[dict[str, str]] = field(default_factory=list)
    rewrite_suggestion: str = ""


@dataclass
class ReaderDiagnosis:
    reader_persona_summary: str
    total_paragraphs: int
    passed_paragraphs: int
    failed_paragraphs: list[ParagraphDiagnosis]
    overall_score: float
    passed: bool
    rewrite_round: int = 0


# =====================================================================
# 4. LLM 调用接口
# =====================================================================

READER_SIMULATION_PROMPT = """你是这个读者：

背景：{background}
角色：{role}
认知风格：{cognitive_style}
信息偏好：{info_appetite}
知识盲区（你不知道这些，看到必须在语境里建立）：
{knowledge_blindspots}

反模式（如果作者这样写，你会读不懂）：
{anti_patterns}

读下面这段话（来自研究报告的一节），作为这个读者告诉我：
1. comprehension_score (0.0-1.0)：你读懂了多少
2. understood_summary：用一句话复述你读懂了什么
3. stuck_points：你没读懂的地方 [{"quote": "...", "reason": "..."}]
4. term_gaps：你没理解的术语 [{"term": "...", "context_needed": "..."}]
5. rewrite_suggestion：要让你懂，这段该怎么改

评分扣分：统计描述当结论扣 0.3；流程记录当叙事扣 0.3；
schema 名词在正文扣 0.2；术语当标签没建语境扣 0.2；缺承接扣 0.2。

节标题：{section_title}
段落内容：
---
{paragraph}
---
"""


def llm_simulate_paragraph(paragraph, section_title, reader_persona):
    """通过 llm_client 调用真实 LLM，不可用时降级占位。"""
    try:
        import llm_client
        prompt = READER_SIMULATION_PROMPT.format(
            background=reader_persona.get("background", ""),
            role=reader_persona.get("role", ""),
            cognitive_style=reader_persona.get("cognitive_style", ""),
            info_appetite=reader_persona.get("info_appetite", ""),
            knowledge_blindspots="\n".join(f"- {x}" for x in reader_persona.get("knowledge_blindspots", [])),
            anti_patterns="\n".join(f"- {x}" for x in reader_persona.get("anti_patterns", [])),
            section_title=section_title,
            paragraph=paragraph,
        )
        return llm_client.chat_json(
            system="你是 reader_simulation 模块，扮演读者逐段诊断报告可读性。",
            user=prompt,
        )
    except Exception:
        return {
            "comprehension_score": 0.0,
            "understood_summary": "[default: 需要 agent 调 LLM]",
            "stuck_points": [],
            "term_gaps": [],
            "rewrite_suggestion": "[default: 需要 agent 调 LLM]",
        }


# =====================================================================
# 5. 读者模拟主流程
# =====================================================================

def load_reader_persona(project: Path) -> dict[str, Any]:
    """从 intent_doc.json 的 v07.reader_model 加载读者画像。"""
    intent_path = project / "00-task" / "intent_doc.json"
    if not intent_path.exists():
        return _default_reader_persona()
    try:
        intent = json.loads(intent_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return _default_reader_persona()
    v07 = intent.get("v07", {})
    reader = v07.get("reader_model", {})
    reader.setdefault("knowledge_blindspots", [])
    reader.setdefault("anti_patterns", [])
    reader.setdefault("comprehension_target", 0.75)
    return reader


def _default_reader_persona():
    return {
        "background": "通用读者",
        "role": "调研报告读者",
        "cognitive_style": "线性阅读，需要因果链",
        "info_appetite": "需要洞察，不需要元描述",
        "knowledge_blindspots": [],
        "anti_patterns": [],
        "comprehension_target": 0.75,
    }


def simulate_reader(report_md, reader_persona, simulate_fn=llm_simulate_paragraph):
    """主流程：跑一遍 reader_simulation，返回完整诊断。"""
    threshold = reader_persona.get("comprehension_target", 0.75)
    cleaned = strip_metadata(report_md)
    sections = split_into_sections(cleaned)

    all_diagnoses = []
    failed = []
    total = 0
    passed = 0
    scores = []

    for sec in sections:
        for i, para in enumerate(sec["paragraphs"]):
            total += 1
            result = simulate_fn(para, sec["title"], reader_persona)
            score = float(result.get("comprehension_score", 0.0))
            scores.append(score)
            diag = ParagraphDiagnosis(
                section_title=sec["title"],
                paragraph_index=i,
                paragraph_preview=para[:80],
                comprehension_score=score,
                understood_summary=result.get("understood_summary", ""),
                stuck_points=result.get("stuck_points", []),
                term_gaps=result.get("term_gaps", []),
                rewrite_suggestion=result.get("rewrite_suggestion", ""),
            )
            all_diagnoses.append(diag)
            if score >= threshold:
                passed += 1
            else:
                failed.append(diag)

    overall = sum(scores) / len(scores) if scores else 0.0
    passed_gate = (passed / total >= 0.8) if total > 0 else False
    return ReaderDiagnosis(
        reader_persona_summary=f"{reader_persona.get('background', '')} / {reader_persona.get('role', '')}",
        total_paragraphs=total,
        passed_paragraphs=passed,
        failed_paragraphs=failed,
        overall_score=overall,
        passed=passed_gate,
    )


# =====================================================================
# 6. 读者门禁 + 重写循环
# =====================================================================

def readability_gate(project, report_md=None, simulate_fn=llm_simulate_paragraph):
    """读者门禁：通过返回 (True, diagnosis)；不通过返回 (False, diagnosis)。"""
    if report_md is None:
        report_path = project / "07-output" / "final-report.md"
        if not report_path.exists():
            return False, ReaderDiagnosis(
                reader_persona_summary="[missing report]",
                total_paragraphs=0, passed_paragraphs=0,
                failed_paragraphs=[], overall_score=0.0, passed=False,
            )
        report_md = report_path.read_text(encoding="utf-8-sig")

    reader = load_reader_persona(project)
    diag = simulate_reader(report_md, reader, simulate_fn)

    diag_path = project / "06-review" / "reader_diagnosis.json"
    diag_path.parent.mkdir(parents=True, exist_ok=True)
    diag_data = {
        "schema_version": "research-os-reader-diagnosis-v1.0",
        "reader_persona_summary": diag.reader_persona_summary,
        "total_paragraphs": diag.total_paragraphs,
        "passed_paragraphs": diag.passed_paragraphs,
        "overall_score": round(diag.overall_score, 3),
        "passed": diag.passed,
        "comprehension_target": reader.get("comprehension_target", 0.75),
        "failed_paragraphs": [
            {
                "section": d.section_title,
                "paragraph_index": d.paragraph_index,
                "preview": d.paragraph_preview,
                "score": d.comprehension_score,
                "understood_summary": d.understood_summary,
                "stuck_points": d.stuck_points,
                "term_gaps": d.term_gaps,
                "rewrite_suggestion": d.rewrite_suggestion,
            }
            for d in diag.failed_paragraphs
        ],
    }
    diag_path.write_text(json.dumps(diag_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return diag.passed, diag


def write_reader_feedback_markdown(diag, project: Path) -> Path:
    """把诊断转成给 agent 用的可读 markdown，触发重写。"""
    out = project / "06-review" / "reader_feedback.md"
    lines = [
        "# Reader Simulation Feedback",
        "",
        f"- 总段落：{diag.total_paragraphs}",
        f"- 通过段落：{diag.passed_paragraphs}",
        f"- 整体读懂度：{diag.overall_score:.2f}",
        f"- 门禁结果：{'PASSED' if diag.passed else 'FAILED'}",
        "",
        "## 失败段落（需要重写）",
        "",
    ]
    for d in diag.failed_paragraphs:
        lines.append(f"### §{d.section_title} · 第 {d.paragraph_index + 1} 段")
        lines.append(f"- 读懂度：{d.comprehension_score:.2f}")
        lines.append(f"- 预览：{d.paragraph_preview}...")
        lines.append(f"- 读懂的：{d.understood_summary}")
        if d.stuck_points:
            lines.append("- 卡点：")
            for sp in d.stuck_points:
                lines.append(f"  - 「{sp.get('quote', '')}」→ {sp.get('reason', '')}")
        if d.term_gaps:
            lines.append("- 术语缺口：")
            for tg in d.term_gaps:
                lines.append(f"  - {tg.get('term', '')} → 需要：{tg.get('context_needed', '')}")
        lines.append(f"- 改写建议：{d.rewrite_suggestion}")
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def apply_diagnosis_to_rewrite(project, rewritten_report_md, round_num, simulate_fn=llm_simulate_paragraph):
    """agent 重写完后调这个函数再跑一遍门禁。超过 2 轮强制 fail。"""
    if round_num > 2:
        return False, ReaderDiagnosis(
            reader_persona_summary="[rewrite limit exceeded]",
            total_paragraphs=0, passed_paragraphs=0,
            failed_paragraphs=[], overall_score=0.0,
            passed=False, rewrite_round=round_num,
        )
    passed, diag = readability_gate(project, rewritten_report_md, simulate_fn)
    diag.rewrite_round = round_num
    return passed, diag


