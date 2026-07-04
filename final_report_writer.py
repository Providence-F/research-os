#!/usr/bin/env python3
"""Research OS v0.7 - Final Report Writer

写-读-改闭环的"改"那一半。
接收 reader_diagnosis.json，输出结构化重写指令给 Agent。

v0.7 升级（从 v0.6）：
  1. 输出格式从纯文本改为结构化 JSON（rewrite_instructions.json）
  2. 增加段落定位（章节 + 段落索引 + 预览）
  3. 增加重写优先级排序（按 score 升序）
  4. 增加"卡点"和"术语缺口"分类
  5. 增加迭代状态追踪（iteration_state.json）
  6. 增加门禁检查（达到 max_iterations 时 fail）

v0.7.1 修复（Dumb Tools 合规）：
  - 删除 action 分类（rewrite/expand/delete）
    原来用 score 阈值决定 action 是轻度语义判断，违反 Dumb Tools
    工具只输出 score + stuck_points + term_gaps，由 Agent 决定 action
  - 工具只做数据整理和排序，不做语义判断

设计原则（不变）：
- 不直接调 LLM API，定义接口 + 默认实现
- 重写循环最多 2 轮，第 3 轮 fail 让人接手
- 重写后的报告必须保留原文结构，只修改有问题的段落
- 工具只准备结构化输入，由 Agent 执行实际重写

用法：
    python final_report_writer.py <project_path> [--max-iterations 2]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def load_diagnosis(project: Path) -> dict:
    """加载读者诊断结果。"""
    diag_path = project / "06-review" / "reader_diagnosis.json"
    if not diag_path.exists():
        return {}
    try:
        return json.loads(diag_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_report(project: Path) -> str:
    """加载最终报告。"""
    report_path = project / "07-output" / "final-report.md"
    if not report_path.exists():
        return ""
    return report_path.read_text(encoding="utf-8")


def save_report(project: Path, content: str) -> None:
    """保存重写后的报告。"""
    report_path = project / "07-output" / "final-report.md"
    report_path.write_text(content, encoding="utf-8")


def build_rewrite_instructions(diagnosis: dict) -> dict:
    """v0.7.1: 构建结构化重写指令。

    Dumb Tools 合规修复：
    - 删除 action 分类（原来用 score 阈值决定 rewrite/expand 是语义判断）
    - 工具只做数据整理和排序，不做语义判断
    - Agent 根据这些数据自行决定 action

    输出格式：
    {
        "generated_at": "ISO时间",
        "total_failed": int,
        "instructions": [
            {
                "priority": 1,  # 1=最紧急（score 最低）
                "section": "章节名",
                "preview": "段落预览（前 100 字）",
                "score": float,
                "stuck_points": [...],
                "term_gaps": [...],
                "rewrite_suggestion": "...",
                "data_for_agent": {
                    "stuck_point_count": int,
                    "term_gap_count": int,
                    "score_below_03": bool,
                    "score_below_05": bool
                }
            }
        ],
        "note": "工具只提供数据，action 由 Agent 决定"
    }
    """
    failed_paragraphs = diagnosis.get("failed_paragraphs", [])
    if not failed_paragraphs:
        return {
            "generated_at": datetime.now().isoformat(),
            "total_failed": 0,
            "instructions": [],
            "status": "no_action_needed"
        }

    # 按 score 升序排序（分数最低的优先重写）
    sorted_paras = sorted(failed_paragraphs, key=lambda p: p.get("score", 0))

    instructions = []
    for i, para in enumerate(sorted_paras, 1):
        score = para.get("score", 0)
        stuck_points = para.get("stuck_points", [])
        term_gaps = para.get("term_gaps", [])

        # v0.7.1: 只提供客观数据，不决定 action
        # Agent 根据这些数据自行决定是 rewrite / expand / delete
        data_for_agent = {
            "stuck_point_count": len(stuck_points),
            "term_gap_count": len(term_gaps),
            "score_below_03": score < 0.3,
            "score_below_05": score < 0.5,
            "more_term_gaps_than_stuck_points": len(term_gaps) > len(stuck_points),
        }

        instructions.append({
            "priority": i,
            "section": para.get("section", ""),
            "preview": para.get("preview", "")[:100],
            "score": score,
            "stuck_points": stuck_points,
            "term_gaps": term_gaps,
            "rewrite_suggestion": para.get("rewrite_suggestion", ""),
            "data_for_agent": data_for_agent,
        })

    return {
        "generated_at": datetime.now().isoformat(),
        "total_failed": len(failed_paragraphs),
        "instructions": instructions,
        "status": "action_required",
        "note": "v0.7.1 Dumb Tools 合规：工具只提供客观数据，action 由 Agent 决定"
    }


def save_rewrite_instructions(project: Path, instructions: dict) -> Path:
    """v0.7: 保存重写指令到文件，供 Agent 读取。"""
    out_path = project / "06-review" / "rewrite_instructions.json"
    out_path.write_text(
        json.dumps(instructions, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    return out_path


def load_iteration_state(project: Path) -> dict:
    """v0.7: 加载迭代状态。"""
    state_path = project / "06-review" / "iteration_state.json"
    if not state_path.exists():
        return {"iterations": 0, "history": []}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {"iterations": 0, "history": []}


def save_iteration_state(project: Path, state: dict) -> None:
    """v0.7: 保存迭代状态。"""
    state_path = project / "06-review" / "iteration_state.json"
    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def write_read_rewrite_loop(project: Path, max_iterations: int = 2) -> dict:
    """v0.7 写-读-改闭环。

    流程：
    1. 加载 reader_diagnosis.json
    2. 构建结构化重写指令（rewrite_instructions.json）
    3. 输出指令路径，Agent 读取并执行重写
    4. Agent 重写后，重新运行 reader_simulation.py
    5. 重复直到通过或达到最大迭代次数

    返回：
        {
            "iterations": int,
            "final_passed": bool,
            "final_score": float,
            "rewrite_instructions_path": str,
        }
    """
    results = {
        "iterations": 0,
        "final_passed": False,
        "final_score": 0.0,
        "rewrite_instructions_path": "",
    }

    iter_state = load_iteration_state(project)
    current_iteration = iter_state.get("iterations", 0) + 1

    if current_iteration > max_iterations:
        print(f"[FAIL] 已达到最大迭代次数 {max_iterations}，仍未通过")
        print("[ACTION] 第 3 轮 fail，让人接手")
        results["iterations"] = max_iterations
        return results

    print(f"\n[iteration {current_iteration}/{max_iterations}] 写-读-改闭环")

    diagnosis = load_diagnosis(project)
    if not diagnosis:
        print("[WARN] 无诊断结果，请先运行 reader_simulation.py")
        return results

    passed = diagnosis.get("passed", False)
    overall_score = diagnosis.get("overall_score", 0.0)

    if passed:
        print(f"[OK] 读者模拟通过！overall_score={overall_score}")
        results["final_passed"] = True
        results["final_score"] = overall_score
        # 更新迭代状态
        iter_state["iterations"] = current_iteration
        iter_state["history"].append({
            "iteration": current_iteration,
            "passed": True,
            "score": overall_score,
            "timestamp": datetime.now().isoformat()
        })
        save_iteration_state(project, iter_state)
        return results

    print(f"[INFO] 读者模拟未通过，overall_score={overall_score}")

    report = load_report(project)
    if not report:
        print("[ERROR] 无 final-report.md")
        return results

    # v0.7.1: 构建结构化重写指令（Dumb Tools 合规，不含 action 分类）
    instructions = build_rewrite_instructions(diagnosis)
    instructions_path = save_rewrite_instructions(project, instructions)

    print(f"\n[INFO] 重写指令已生成: {instructions_path}")
    print(f"[INFO] 共 {instructions['total_failed']} 个段落需要重写")
    print("=" * 60)

    # 打印摘要（便于 Agent 快速理解）
    for inst in instructions["instructions"]:
        print(f"\n--- 优先级 {inst['priority']} ---")
        print(f"章节: {inst['section']}")
        print(f"理解分: {inst['score']}")
        print(f"预览: {inst['preview']}...")
        if inst["stuck_points"]:
            print(f"卡点 ({inst['data_for_agent']['stuck_point_count']} 个):")
            for sp in inst["stuck_points"]:
                quote = sp.get("quote", "") if isinstance(sp, dict) else str(sp)
                reason = sp.get("reason", "") if isinstance(sp, dict) else ""
                print(f"  - {quote}: {reason}")
        if inst["term_gaps"]:
            print(f"术语缺口 ({inst['data_for_agent']['term_gap_count']} 个):")
            for tg in inst["term_gaps"]:
                term = tg.get("term", "") if isinstance(tg, dict) else str(tg)
                context = tg.get("context_needed", "") if isinstance(tg, dict) else ""
                print(f"  - {term}: 需要 {context}")
        if inst["rewrite_suggestion"]:
            print(f"重写建议: {inst['rewrite_suggestion']}")
        # v0.7.1: 不打印 action，由 Agent 决定
        print(f"[数据] score={inst['score']}, 卡点={inst['data_for_agent']['stuck_point_count']}, 术语缺口={inst['data_for_agent']['term_gap_count']}")

    print("\n" + "=" * 60)
    print(f"[ACTION] Agent 应根据 {instructions_path} 重写 final-report.md")
    print(f"[ACTION] 重写后请重新运行 reader_simulation.py")
    print(f"[ACTION] 然后再次运行此脚本完成第 {current_iteration + 1} 轮迭代")
    print(f"[NOTE] 工具不直接调 LLM，由 Agent 执行实际重写")
    print(f"[NOTE] v0.7.1 Dumb Tools 合规：工具只提供客观数据，action 由 Agent 决定")
    print("=" * 60)

    # 更新迭代状态
    iter_state["iterations"] = current_iteration
    iter_state["history"].append({
        "iteration": current_iteration,
        "passed": False,
        "score": overall_score,
        "timestamp": datetime.now().isoformat(),
        "failed_count": instructions["total_failed"]
    })
    save_iteration_state(project, iter_state)

    results["iterations"] = current_iteration
    results["final_score"] = overall_score
    results["rewrite_instructions_path"] = str(instructions_path)

    return results


def main():
    parser = argparse.ArgumentParser(description="Research OS v0.7 写-读-改闭环：根据读者反馈重写报告")
    parser.add_argument("project", help="项目路径")
    parser.add_argument("--max-iterations", type=int, default=2, help="最大迭代次数")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    if not project.exists():
        print(f"[ERROR] Project not found: {project}", file=sys.stderr)
        return 1

    results = write_read_rewrite_loop(project, args.max_iterations)

    print(f"\n{'=' * 60}")
    print(f"写-读-改闭环结果:")
    print(f"  迭代次数: {results['iterations']}")
    print(f"  最终通过: {results['final_passed']}")
    print(f"  最终分数: {results['final_score']}")
    if results["rewrite_instructions_path"]:
        print(f"  重写指令: {results['rewrite_instructions_path']}")
    print(f"{'=' * 60}")

    return 0 if results["final_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
