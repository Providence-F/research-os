"""reader_simulation.py - Research OS 读者模拟模块（v2.0）

LLM 不只是生产者，更要扮演读者代理。在 final-report.md 写完后、ros build 之前，
让 LLM 扮演 reader persona 读报告，反馈读懂度 + 卡点 + 改写建议，触发写-读-改闭环。

v2.0 变更：
- 双读者模拟：READER_PERSONAS 定义「领域外行人」(outsider) 和「零基础小白」(layman)
  两个画像，各自独立跑一遍诊断，两个都过才算过门禁（v1.5 单读者容易
  "自以为通俗其实不通俗"）
- reader_diagnosis.json 升级为 research-os-reader-v2.0 schema：
  readers.{outsider,layman} + overall_pass + blocking_issues
- reader_feedback.md 分两节（外行人反馈 / 小白反馈），各含复述测试原文、
  卡点清单、修改建议
- 新增纯机械函数：build_dual_reader_prompts / validate_reader_diagnosis /
  compute_overall_pass / compute_blocking_issues / assemble_diagnosis /
  write_dual_diagnosis / write_dual_feedback_markdown / dual_readability_gate
- v1 单读者函数（readability_gate / simulate_reader /
  write_reader_feedback_markdown / apply_diagnosis_to_rewrite 等）保留向后兼容
  （ros.py build 门禁、archive 工具仍在调用），内部标注 DEPRECATED

Dumb Tools 诚实标注：
- 本工具不跑模拟、不做语义判断。模拟读者、评价文本由使用系统的 AI Agent 完成。
- 工具只做机械的事：拼 prompt 骨架、校验 Agent 提交的诊断结构、
  按固定规则算门禁与共同卡点、写产物文件。
- v1 的 llm_simulate_paragraph 是历史遗留占位接口，llm_client 不可用时返回占位结果。

v1 设计原则（保留）：
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
    """通过 llm_client 调用真实 LLM，不可用时降级占位。

    DEPRECATED (v2.0)：单读者逐段模拟是 v1 路径。v2 由 Agent 直接以
    build_dual_reader_prompts 生成的整篇 prompt 跑模拟，不再走这个占位接口。
    """
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
    """加载读者画像。

    读者画像由 Agent 内化（从记忆和知识库获取），不由工具管理。
    intent_doc.json 的 v07.reader_model 仅用于"读者≠用户本人"的覆盖声明。

    - reader_model 为 None 或不存在 → 返回完整默认画像
    - reader_model 存在且非空 → 用覆盖值补全缺失字段后返回
    """
    intent_path = project / "00-task" / "intent_doc.json"
    if not intent_path.exists():
        return _default_reader_persona()
    try:
        intent = json.loads(intent_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return _default_reader_persona()
    v07 = intent.get("v07", {})
    reader = v07.get("reader_model")
    if not reader:
        # None 或 {} → Agent 用自己的画像，工具给完整默认值兜底
        return _default_reader_persona()
    # 覆盖声明：补全缺失字段
    reader.setdefault("background", "")
    reader.setdefault("role", "")
    reader.setdefault("cognitive_style", "")
    reader.setdefault("info_appetite", "")
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
    """主流程：跑一遍 reader_simulation，返回完整诊断。

    DEPRECATED (v2.0)：单读者版本，保留给旧调用方。新流程见第 7 节
    dual_readability_gate（双读者门禁）。
    """
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
    """读者门禁：通过返回 (True, diagnosis)；不通过返回 (False, diagnosis)。

    DEPRECATED (v2.0)：单读者门禁，ros.py build 仍在调用故保留签名。
    新流程用 dual_readability_gate（第 7 节）。
    """
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
    """把诊断转成给 agent 用的可读 markdown，触发重写。

    DEPRECATED (v2.0)：单读者反馈模板，ros.py build 仍在调用故保留签名。
    新流程用 write_dual_feedback_markdown（第 7 节）。
    """
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
    """agent 重写完后调这个函数再跑一遍门禁。超过 2 轮强制 fail。

    DEPRECATED (v2.0)：单读者重写循环，保留向后兼容。
    """
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


# =====================================================================
# 7. v2.0 双读者模拟（Dumb Tool：prompt 骨架 + 结构校验 + 机械门禁）
# =====================================================================

SCHEMA_VERSION_V2 = "research-os-reader-v2.0"

READER_PERSONAS: dict[str, dict[str, Any]] = {
    "outsider": {
        "name": "领域外行人",
        "description": (
            "受过高等教育但非本领域的读者。例如调研 AI 产品时，他是做外贸的本科生。"
            "能跟上逻辑链条，但所有专业术语必须解释，否则就卡住。"
        ),
        "focus_checks": ["术语解释", "类比质量", "逻辑跳跃"],
        "pass_threshold": 75,
    },
    "layman": {
        "name": "零基础小白",
        "description": (
            "物理系大三学生水平的通识读者（系统主人的画像基准），对调研领域零前置知识。"
            "阈值更低不是放水——读不懂是解释方（作者）的责任，不是读者的责任。"
        ),
        "focus_checks": [
            "能不能用自己的话复述核心结论",
            "有没有被术语劝退",
            "第一章能不能看懂",
        ],
        "pass_threshold": 65,
    },
}

READER_PROMPT_TEMPLATE_V2 = """你现在是【{name}】。

## 你的画像
{description}

## 你重点检查
{focus_checks}

## 任务
以这个读者身份，从头到尾通读这份调研报告（项目内路径：07-output/final-report.md）。
完整读，不要跳读。读的时候诚实一点：你不是专家，看不懂就是看不懂，
不要脑补、不要替作者找补。

读完后只输出一份 JSON（不要输出任何其他文字），结构如下：

{{
  "comprehension_score": 0-100 的整数，你整体读懂了多少,
  "terms_not_understood": [
    {{"term": "卡住的术语", "section": "在第几节", "reason": "为什么卡住"}}
  ],
  "analogy_gaps": [
    {{"concept": "缺类比的概念", "section": "在第几节", "why_needed": "为什么没有类比就想不明白"}}
  ],
  "retell_test": "合上书，用你自己的话复述这篇报告的核心结论（3-5 句，你怎么跟朋友讲就怎么写）",
  "abandonment_points": [
    {{"section": "在第几节", "quote": "读到哪里会想放弃", "reason": "为什么想放弃"}}
  ],
  "verdict": "pass 或 fail，后接一句话理由"
}}

## 判定规则
- comprehension_score >= {pass_threshold} 且没有让你彻底读不下去的卡点 → verdict 为 "pass"
- 否则 verdict 为 "fail"
- retell_test 必须真的写出来；写不出来本身就是 fail 的信号
"""


def build_reader_prompt(persona_key: str) -> str:
    """生成指定读者画像的诊断 prompt 骨架（只拼模板，不跑模拟）。"""
    if persona_key not in READER_PERSONAS:
        raise KeyError(f"unknown reader persona: {persona_key} (可选: {list(READER_PERSONAS)})")
    p = READER_PERSONAS[persona_key]
    return READER_PROMPT_TEMPLATE_V2.format(
        name=p["name"],
        description=p["description"],
        focus_checks="\n".join(f"- {c}" for c in p["focus_checks"]),
        pass_threshold=p["pass_threshold"],
    )


def build_dual_reader_prompts() -> dict[str, str]:
    """为两个读者各生成一份独立 prompt。Agent 用同一报告分别跑两遍模拟。"""
    return {key: build_reader_prompt(key) for key in READER_PERSONAS}


READER_DIAGNOSIS_REQUIRED_FIELDS: dict[str, Any] = {
    "comprehension_score": (int, float),
    "terms_not_understood": list,
    "analogy_gaps": list,
    "retell_test": str,
    "abandonment_points": list,
    "verdict": str,
}


def validate_reader_diagnosis(data: Any, persona_key: str) -> list[str]:
    """机械校验 Agent 提交的单读者诊断结构。返回问题列表（空列表 = 合格）。"""
    problems: list[str] = []
    if not isinstance(data, dict):
        return [f"{persona_key}: 诊断结果不是 JSON object"]
    for fname, ftype in READER_DIAGNOSIS_REQUIRED_FIELDS.items():
        if fname not in data:
            problems.append(f"{persona_key}: 缺字段 {fname}")
        elif not isinstance(data[fname], ftype):
            problems.append(f"{persona_key}: 字段 {fname} 类型应为 {ftype}")
    score = data.get("comprehension_score")
    if isinstance(score, (int, float)) and not isinstance(score, bool) and not (0 <= score <= 100):
        problems.append(f"{persona_key}: comprehension_score 应在 0-100，实际 {score}")
    return problems


def _verdict_is_pass(verdict: Any) -> bool:
    """verdict 允许 "pass" 或 "pass：一句话理由" 形式，机械取前缀判断。"""
    return str(verdict).strip().lower().startswith("pass")


def compute_overall_pass(diagnosis: dict) -> bool:
    """机械门禁：两个读者的 verdict 都是 pass 且 comprehension_score 都达各自阈值。"""
    readers = diagnosis.get("readers", {}) if isinstance(diagnosis, dict) else {}
    for key, persona in READER_PERSONAS.items():
        r = readers.get(key)
        if not isinstance(r, dict):
            return False
        if not _verdict_is_pass(r.get("verdict", "")):
            return False
        score = r.get("comprehension_score")
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            return False
        if score < persona["pass_threshold"]:
            return False
    return True


def compute_blocking_issues(diagnosis: dict) -> list[str]:
    """机械找跨读者共同卡点：两个读者都没看懂的术语 / 都想放弃的章节取交集。"""
    readers = diagnosis.get("readers", {}) if isinstance(diagnosis, dict) else {}
    issues: list[str] = []

    def _terms(key: str) -> set:
        r = readers.get(key) or {}
        return {
            str(t.get("term", "")).strip().lower()
            for t in (r.get("terms_not_understood") or [])
            if isinstance(t, dict) and t.get("term")
        }

    def _quit_sections(key: str) -> set:
        r = readers.get(key) or {}
        return {
            str(a.get("section", "")).strip()
            for a in (r.get("abandonment_points") or [])
            if isinstance(a, dict) and a.get("section")
        }

    for term in sorted(_terms("outsider") & _terms("layman")):
        issues.append(f"术语「{term}」两个读者都没看懂")
    for sec in sorted(_quit_sections("outsider") & _quit_sections("layman")):
        issues.append(f"「{sec}」两个读者都读到想放弃")
    return issues


def assemble_diagnosis(readers_results: dict) -> dict:
    """把 Agent 提交的两份单读者诊断组装成 v2.0 结构（机械算 overall_pass / blocking_issues）。"""
    diagnosis = {
        "schema_version": SCHEMA_VERSION_V2,
        "readers": {key: readers_results.get(key, {}) for key in READER_PERSONAS},
    }
    diagnosis["overall_pass"] = compute_overall_pass(diagnosis)
    diagnosis["blocking_issues"] = compute_blocking_issues(diagnosis)
    return diagnosis


def write_dual_diagnosis(project, readers_results: dict) -> Path:
    """结构校验 + 组装 + 写 06-review/reader_diagnosis.json（v2.0 schema）。"""
    project = Path(project)
    problems: list[str] = []
    for key in READER_PERSONAS:
        problems.extend(validate_reader_diagnosis(readers_results.get(key, {}), key))
    if problems:
        raise ValueError("reader diagnosis 结构不合格：\n" + "\n".join(f"- {p}" for p in problems))
    diagnosis = assemble_diagnosis(readers_results)
    out = project / "06-review" / "reader_diagnosis.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(diagnosis, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def _suggest_fixes(reader: dict) -> list[str]:
    """从结构化卡点机械生成修改建议（逐条映射，不做语义判断）。"""
    suggestions: list[str] = []
    for t in reader.get("terms_not_understood") or []:
        if isinstance(t, dict):
            suggestions.append(
                f"在「{t.get('section', '?')}」为术语「{t.get('term', '?')}」"
                f"补一句白话解释（{t.get('reason', '')}）"
            )
    for g in reader.get("analogy_gaps") or []:
        if isinstance(g, dict):
            suggestions.append(
                f"为「{g.get('concept', '?')}」（{g.get('section', '?')}）补一个生活化类比"
            )
    for a in reader.get("abandonment_points") or []:
        if isinstance(a, dict):
            suggestions.append(
                f"重写或精简「{a.get('section', '?')}」："
                f"读者在「{a.get('quote', '')}」处想放弃（{a.get('reason', '')}）"
            )
    return suggestions


def write_dual_feedback_markdown(diagnosis: dict, project) -> Path:
    """把 v2.0 诊断转成给 Agent 用的 markdown，分两节（外行人反馈 / 小白反馈）。"""
    project = Path(project)
    readers = diagnosis.get("readers", {})
    lines = [
        "# 双读者模拟反馈（v2.0）",
        "",
        f"- 总体门禁：{'PASSED' if diagnosis.get('overall_pass') else 'FAILED'}",
    ]
    blocking = diagnosis.get("blocking_issues") or []
    if blocking:
        lines.append("- 跨读者共同卡点：")
        lines.extend(f"  - {b}" for b in blocking)
    lines.append("")

    for key, persona in READER_PERSONAS.items():
        r = readers.get(key) or {}
        lines.append(f"## {persona['name']}反馈（{key}）")
        lines.append("")
        lines.append(f"- 读懂度：{r.get('comprehension_score', '?')}/100（阈值 {persona['pass_threshold']}）")
        lines.append(f"- 判定：{r.get('verdict', '?')}")
        lines.append("")
        lines.append("### 复述测试（读者原话）")
        lines.append("")
        lines.append(f"> {r.get('retell_test', '') or '（未提交）'}")
        lines.append("")
        lines.append("### 卡点清单")
        lines.append("")
        terms = [t for t in (r.get("terms_not_understood") or []) if isinstance(t, dict)]
        gaps = [g for g in (r.get("analogy_gaps") or []) if isinstance(g, dict)]
        quits = [a for a in (r.get("abandonment_points") or []) if isinstance(a, dict)]
        if terms:
            lines.append("- 没看懂的术语：")
            for t in terms:
                lines.append(f"  - 「{t.get('term', '?')}」（{t.get('section', '?')}）→ {t.get('reason', '')}")
        if gaps:
            lines.append("- 缺类比的概念：")
            for g in gaps:
                lines.append(f"  - 「{g.get('concept', '?')}」（{g.get('section', '?')}）→ {g.get('why_needed', '')}")
        if quits:
            lines.append("- 想放弃的位置：")
            for a in quits:
                lines.append(f"  - 「{a.get('section', '?')}」{a.get('quote', '')} → {a.get('reason', '')}")
        if not (terms or gaps or quits):
            lines.append("- 无")
        lines.append("")
        lines.append("### 修改建议")
        lines.append("")
        suggestions = _suggest_fixes(r)
        if suggestions:
            lines.extend(f"- {s}" for s in suggestions)
        else:
            lines.append("- 无")
        lines.append("")

    out = project / "06-review" / "reader_feedback.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def dual_readability_gate(project, readers_results: dict) -> tuple:
    """v2.0 双读者门禁：写入 reader_diagnosis.json + reader_feedback.md，
    返回 (overall_pass, diagnosis)。

    readers_results 是 Agent 跑完两遍模拟后提交的结构：
    {"outsider": {...诊断...}, "layman": {...诊断...}}
    """
    diag_path = write_dual_diagnosis(project, readers_results)
    diagnosis = json.loads(diag_path.read_text(encoding="utf-8"))
    write_dual_feedback_markdown(diagnosis, project)
    return diagnosis["overall_pass"], diagnosis
