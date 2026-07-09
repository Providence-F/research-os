#!/usr/bin/env python3
"""Research OS v1.0 反方审计 agent把"反方审计"从 06-review/red_team.md 空模板升级成
有 persona 的主动 agent（融入 dogfood skill 的核心方法论）。

dogfood 的核心方法论：
  - systematically explore（系统探索）
  - find bugs（主动找问题）
  - structured report with screenshots（结构化报告含截图）

有机融入方式：
  - 反方审计员有 persona（不是被动模板）
  - 主动质疑每条结论，不只是"有没有反例"
  - 至少降级一条结论（硬性要求，validator 已检查）
  - 审计产出自动写回 trace-manifest.json 的 confidence

这个模块提供审计的 prompt 模板和执行框架，
实际攻击由 LLM 完成，结果结构化存盘。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from datetime import datetime


# 反方审计员的 persona（融入 dogfood 的"主动找问题"精神）
RED_TEAMER_PERSONA = """你是 Research OS 的反方审计员（v0.9，融入 dogfood 方法论）。

你的工作不是"看看有没有问题"，而是**主动攻击**——
像 dogfood 找 web app bug 一样找报告结论的漏洞。

攻击原则：
  1. 每条结论都问"凭什么"——证据等级够不够？来源独立性怎么样？
  2. 找反例——有没有证据能推翻这个结论？
  3. 找隐含假设——结论偷偷假设了什么没说？
  4. 找过度推广——"在 A 情况成立"被推广成"普遍成立"了吗？
  5. 找成本盲区——结论忽略了什么代价？

输出格式（结构化，融入 dogfood 的结构化报告精神）：
```json
{{
  "attacks": [
    {{
      "target_conclusion_id": "CL001",
      "attack_type": "证据不足|隐含假设|过度推广|反例存在|成本盲区",
      "attack_content": "具体攻击内容",
      "evidence_cited": ["E005", "E008"],
      "severity": "high|medium|low",
      "recommended_revision": "降级为'部分成立'|增加限定|维持原状",
      "confidence_after_attack": "high|medium|low"
    }}
  ],
  "summary": "本次审计攻击了 N 条结论，成功 M 条，降级 K 条",
  "meets_requirement": true
}}
```

硬性要求：至少降级一条结论（meets_requirement=true 当且仅当至少一条
confidence_after_attack 低于原 confidence）。"""


def build_attack_targets(conclusions: list[dict]) -> str:
    """构建攻击目标清单（给 LLM 的输入）"""
    lines = []
    for c in conclusions:
        cid = c.get("conclusion_id", "?")
        stmt = c.get("结论", c.get("statement", "?"))
        conf = c.get("置信度", c.get("confidence", "?"))
        evid = c.get("supported_by", [])
        lines.append(f"- {cid} [置信度:{conf}] {stmt} | 证据:{evid}")
    return "\n".join(lines)


def run_audit(project_dir: Path | str, conclusions: list[dict]) -> dict:
    """执行反方审计（产出结构化结果，实际攻击由 LLM 完成）

    Returns:
        dict: 审计结果，含 attacks 列表和 meets_requirement 标志
    """
    project = Path(project_dir)
    review_dir = project / "06-review"
    review_dir.mkdir(parents=True, exist_ok=True)

    # 写入 red_team.md（带 persona 的结构化模板）
    red_team_md = f"""# 反方审计报告（v0.9，融入 dogfood 方法论）

> 审计时间：{datetime.now().isoformat()}
> 审计员 persona：主动攻击者（不是被动检查）

## 攻击目标清单

{build_attack_targets(conclusions)}

## 审计结果

（由 LLM 执行攻击后填入，格式见 persona 说明）

## 硬性要求

至少降级一条结论。如果所有结论都维持原状，说明审得不够用力——
重新审计，找更深的攻击角度。

## 审计产出

- attacks 数组：每条攻击的详细记录
- 至少一条 confidence_after_attack 低于原 confidence
- 修订建议自动写回 trace-manifest.json
"""
    (review_dir / "06-review/red_team.md").write_text(red_team_md, encoding="utf-8")

    # 保存审计框架（供 LLM 执行）
    audit_framework = {
        "persona": RED_TEAMER_PERSONA,
        "targets": conclusions,
        "timestamp": datetime.now().isoformat(),
        "schema_version": "red-team-v0.9",
        "requirement": "至少降级一条结论",
    }
    (review_dir / "red_team_framework.json").write_text(
        json.dumps(audit_framework, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return audit_framework


def apply_audit_results(project_dir: Path | str, audit_results: dict) -> None:
    """把审计结果写回 trace-manifest.json（自动降级 confidence）

    有机融入：审计结果不只是写到 red_team.md，
    还自动写回 trace-manifest.json 的 confidence 字段。
    """
    project = Path(project_dir)
    manifest_path = project / "07-output" / "trace-manifest.json"

    if not manifest_path.exists():
        print(f"[warn] no trace-manifest.json at {manifest_path}", file=sys.stderr)
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    conclusions = manifest.get("conclusions", [])

    # 应用降级
    attacks = audit_results.get("attacks", [])
    for attack in attacks:
        cid = attack.get("target_conclusion_id")
        new_conf = attack.get("confidence_after_attack")
        for c in conclusions:
            if c.get("conclusion_id") == cid and new_conf:
                old_conf = c.get("confidence", "high")
                c["confidence"] = new_conf
                c["revision_log"] = c.get("revision_log", [])
                c["revision_log"].append({
                    "from": old_conf,
                    "to": new_conf,
                    "reason": attack.get("attack_content", ""),
                    "attack_type": attack.get("attack_type", ""),
                    "timestamp": datetime.now().isoformat(),
                })

    manifest["conclusions"] = conclusions
    manifest["last_red_team_audit"] = datetime.now().isoformat()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] trace-manifest.json updated with red_team audit results")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: red_team_agent.py <project_dir> --conclusions <json>")
        sys.exit(1)
    project = Path(sys.argv[1])
    # 简化：从 trace-manifest.json 读 conclusions
    manifest = project / "07-output" / "trace-manifest.json"
    if manifest.exists():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        conclusions = data.get("conclusions", [])
        framework = run_audit(project, conclusions)
        print(json.dumps(framework, ensure_ascii=False, indent=2))
    else:
        print(f"[error] no trace-manifest.json", file=sys.stderr)
        sys.exit(1)
