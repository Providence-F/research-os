"""final_report_writer.py - Research OS v0.5 模块 (原 v0.10 模块，v0.5 重构后归并版本号)

带写-读-改循环的报告生成器。替换一次成稿模式。

核心思想：人类作者写完一段会自己读一遍，感到不通顺就改。
LLM 也应该这样：写完 → reader_simulation 读 → 不通过就重写 → 再读 → 通过才交付。

5 幕叙事结构（替换 §1-§7 并列）：
1. 问题 - 读者为什么要读这份报告
2. 探索 - 你看了什么、发现了什么
3. 冲突 - 哪些你以为对的事情被推翻了
4. 决策 - 基于以上，选了什么、淘汰了什么
5. 行动 - 如果只做一件事，做什么

数据流：
    证据矩阵 + 假设账本 + 反方审计 + 意图文档
        ↓
    compose_draft()       ← 按 5 幕结构组装初稿
        ↓
    reader_simulation.readability_gate()
        ↓ pass → 写 final-report.md
        ↓ fail → rewrite_failed_sections()
            ↓
            apply_diagnosis_to_rewrite() 再读一遍
            ↓ 通过 → 写；不通过 → 最多 2 轮
"""

from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import reader_simulation as rs


# =====================================================================
# 1. 5 幕叙事模板
# =====================================================================

FIVE_ACT_TEMPLATE = """# {title}

> 一句话结论：{verdict}

## 1. 问题

{act1_problem}

## 2. 探索

{act2_explore}

## 3. 冲突

{act3_conflict}

## 4. 决策

{act4_decision}

## 5. 行动

{act5_action}

---

## 附录

{appendix}
"""


# =====================================================================
# 2. compose_draft - 从研究产物组装 5 幕初稿
# =====================================================================

def compose_draft(
    title: str,
    verdict: str,
    act1_problem: str,
    act2_explore: str,
    act3_conflict: str,
    act4_decision: str,
    act5_action: str,
    appendix: str = "",
) -> str:
    """按 5 幕结构组装初稿。

    agent 在调用这个函数前，应该已经从 evidence_matrix / hypothesis_ledger /
    red_team / intent_doc 里提炼了素材。这个函数只负责组装，不做研究判断。
    """
    return FIVE_ACT_TEMPLATE.format(
        title=title,
        verdict=verdict,
        act1_problem=act1_problem,
        act2_explore=act2_explore,
        act3_conflict=act3_conflict,
        act4_decision=act4_decision,
        act5_action=act5_action,
        appendix=appendix or "_（附录见可折叠区）_",
    )


# =====================================================================
# 3. write_read_rewrite_loop - 写-读-改闭环
# =====================================================================

@dataclass
class RewriteResult:
    """写-读-改闭环的结果。"""
    final_md: str
    rounds: int
    final_score: float
    passed: bool
    diagnosis_path: Path
    feedback_path: Path | None = None


def write_read_rewrite_loop(
    project: Path,
    draft_md: str,
    simulate_fn: Callable = rs.llm_simulate_paragraph,
    max_rounds: int = 2,
) -> RewriteResult:
    """写-读-改闭环主流程。

    1. 把 draft 写到 final-report.md
    2. 跑 reader_simulation.readability_gate
    3. 不通过 → agent 重写失败段 → 再读
    4. 通过或达到 max_rounds → 终止
    """
    report_path = project / "07-output" / "final-report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # 第 0 轮：写初稿 + 跑门禁
    report_path.write_text(draft_md, encoding="utf-8")
    passed, diag = rs.readability_gate(project, draft_md, simulate_fn)
    feedback_path = None
    rounds = 0

    if not passed:
        # 写反馈 markdown，供 agent 重写时参考
        feedback_path = rs.write_reader_feedback_markdown(diag, project)
        print(f"[reader_simulation] 第 0 轮门禁未通过")
        print(f"  - 整体读懂度：{diag.overall_score:.2f}")
        print(f"  - 通过段落：{diag.passed_paragraphs}/{diag.total_paragraphs}")
        print(f"  - 反馈文件：{feedback_path}")
        print(f"  - 请 agent 根据 reader_feedback.md 重写失败段后调用 apply_rewrite()")

    return RewriteResult(
        final_md=draft_md,
        rounds=rounds,
        final_score=diag.overall_score,
        passed=passed,
        diagnosis_path=project / "06-review" / "reader_diagnosis.json",
        feedback_path=feedback_path,
    )


def apply_rewrite(
    project: Path,
    rewritten_md: str,
    round_num: int,
    simulate_fn: Callable = rs.llm_simulate_paragraph,
) -> RewriteResult:
    """agent 重写完失败段后调用，把新版本写到 final-report.md 并再跑门禁。"""
    report_path = project / "07-output" / "final-report.md"
    report_path.write_text(rewritten_md, encoding="utf-8")

    passed, diag = rs.apply_diagnosis_to_rewrite(
        project, rewritten_md, round_num, simulate_fn
    )
    feedback_path = None
    if not passed:
        feedback_path = rs.write_reader_feedback_markdown(diag, project)
        print(f"[reader_simulation] 第 {round_num} 轮重写后门禁仍未通过")
        print(f"  - 整体读懂度：{diag.overall_score:.2f}")
        print(f"  - 通过段落：{diag.passed_paragraphs}/{diag.total_paragraphs}")
        if round_num >= 2:
            print(f"  - 已达到最大重写轮数，需要人工介入")
        else:
            print(f"  - 反馈文件：{feedback_path}")
    else:
        print(f"[reader_simulation] 第 {round_num} 轮重写后门禁通过")
        print(f"  - 整体读懂度：{diag.overall_score:.2f}")
        print(f"  - 通过段落：{diag.passed_paragraphs}/{diag.total_paragraphs}")

    return RewriteResult(
        final_md=rewritten_md,
        rounds=round_num,
        final_score=diag.overall_score,
        passed=passed,
        diagnosis_path=project / "06-review" / "reader_diagnosis.json",
        feedback_path=feedback_path,
    )


# =====================================================================
# 4. agent_simulate_fn - agent 模式下的 LLM 模拟
# =====================================================================

def agent_simulate_paragraph(
    paragraph: str,
    section_title: str,
    reader_persona: dict[str, Any],
) -> dict[str, Any]:
    """agent 模式：直接调 LLM（通过 agent 的对话能力），返回结构化诊断。

    agent 在调 write_read_rewrite_loop 时，应把这个函数作为 simulate_fn 传入。
    但因为 agent 本身就是 LLM，更常见的模式是：
    1. agent 调 write_read_rewrite_loop 触发首轮门禁
    2. 如果未通过，agent 自己读 reader_feedback.md
    3. agent 根据反馈重写失败段
    4. agent 调 apply_rewrite 把新版本写回并再跑门禁
    """
    # 默认实现：返回占位诊断，agent 应替换成真实 LLM 调用
    # 但在 reader_simulation 的 llm_simulate_paragraph 已有降级逻辑
    return rs.llm_simulate_paragraph(paragraph, section_title, reader_persona)


# =====================================================================
# 5. 辅助：从研究产物提取 5 幕素材
# =====================================================================

def load_research_artifacts(project: Path) -> dict[str, Any]:
    """加载所有研究产物，供 agent 提炼 5 幕素材。"""
    artifacts: dict[str, Any] = {}

    # 意图文档
    intent_path = project / "00-task" / "intent_doc.json"
    if intent_path.exists():
        artifacts["intent"] = json.loads(intent_path.read_text(encoding="utf-8-sig"))

    # 证据矩阵
    evidence_path = project / "03-evidence" / "evidence_matrix.md"
    if evidence_path.exists():
        artifacts["evidence_matrix"] = evidence_path.read_text(encoding="utf-8-sig")

    # 假设账本
    hyp_path = project / "03-evidence" / "hypothesis_ledger.json"
    if hyp_path.exists():
        artifacts["hypothesis_ledger"] = json.loads(hyp_path.read_text(encoding="utf-8-sig"))

    # 反方审计
    red_path = project / "06-review" / "red_team.md"
    if red_path.exists():
        artifacts["red_team"] = red_path.read_text(encoding="utf-8-sig")

    return artifacts


# =====================================================================
# 6. CLI 入口
# =====================================================================

def build_report(project: Path) -> int:
    """供 ros rewrite 调用的入口。

    注意：这个函数不真正调 LLM 写报告。
    它做的事是：
    1. 加载研究产物
    2. 提示 agent 需要根据这些产物按 5 幕结构写初稿
    3. agent 写完初稿后，调 write_read_rewrite_loop 触发门禁
    """
    artifacts = load_research_artifacts(project)
    if not artifacts:
        print(f"[FAIL] 项目 {project} 没有研究产物")
        return 1

    print(f"\n=== Research Artifacts Loaded ===")
    for k, v in artifacts.items():
        if isinstance(v, str):
            print(f"  - {k}: {len(v)} chars")
        elif isinstance(v, dict):
            print(f"  - {k}: {len(v)} keys")
        else:
            print(f"  - {k}: loaded")

    print(f"\n=== Next Step ===")
    print(f"agent 需要根据以上研究产物，按 5 幕叙事结构写 final-report.md 初稿：")
    print(f"  1. 问题 - 读者为什么要读这份报告")
    print(f"  2. 探索 - 你看了什么、发现了什么")
    print(f"  3. 冲突 - 哪些你以为对的事情被推翻了")
    print(f"  4. 决策 - 基于以上，选了什么、淘汰了什么")
    print(f"  5. 行动 - 如果只做一件事，做什么")
    print(f"\n写完后调用 write_read_rewrite_loop(project, draft_md) 触发读者门禁。")
    return 0
