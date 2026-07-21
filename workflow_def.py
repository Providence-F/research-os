# -*- coding: utf-8 -*-
"""Research OS v2.0 - 工作流定义（机器可读单一真相源）

供 scripts/sync_dashboard.py 生成看板数据。
步骤/门禁语义以 templates/14-研究执行状态机.md 为规范原文；
本文件是其机器可读投影——改状态机时必须同步改这里。

设计哲学：Smart Agent. Dumb Tools.
本文件只做数据声明，不做任何判断。

v2.0 变更（从 v1.5）：
  - SYSTEM_VERSION: v1.5 -> v2.0
  - 门禁数: 9 -> 12（新增 gate_10 意图树 / gate_11 洞察账本 / gate_12 跨产物一致性）
  - 新增 step_1_2_intent_discovery（意图探索，介于 step_1 与 step_1.5 之间）
  - step_7_analysis 新增 insight_ledger.json r2_r3_required 产物（深度档位感知）
  - step_8_red_team 触发 gate_11（洞察账本验证）
  - step_11_trace_manifest 触发 gate_12（跨产物一致性）
  - step_3_research_plan 新增 intent_doc.json artifact
"""

SYSTEM_VERSION = "v2.0"

# 5 个阶段（流水线视觉分组）
PHASES = [
    {"id": "define",  "name": "定义", "color": "#8a6d3b"},
    {"id": "collect", "name": "采集", "color": "#4a7a6f"},
    {"id": "analyze", "name": "分析", "color": "#7a5a8a"},
    {"id": "review",  "name": "审核", "color": "#b85b44"},
    {"id": "deliver", "name": "交付", "color": "#3d6b8e"},
]

# 23 个步骤（与状态机 v2.0 一致；顺序即流水线顺序）
# gate_after: 该步骤完成后触发的门禁 id
STEPS = [
    {"id": "step_0_scaffold",              "num": "0",    "label": "脚手架",       "phase": "define",  "artifact": "research_state.json"},
    {"id": "step_1_route",                 "num": "1",    "label": "主题路由",     "phase": "define",  "artifact": "01-plan/route_result.json"},
    {"id": "step_1_2_intent_discovery",   "num": "1.2",  "label": "意图探索",     "phase": "define",  "artifact": "00-task/intent_doc.json",                "gate_after": "gate_10"},
    {"id": "step_1_5_direction_selection", "num": "1.5",  "label": "方向选择",     "phase": "define",  "artifact": "00-task/direction_selection.json",       "gate_after": "gate_4"},
    {"id": "step_2_task_card",             "num": "2",    "label": "任务卡",       "phase": "define",  "artifact": "00-task/task-card.md"},
    {"id": "step_3_research_plan",         "num": "3",    "label": "调研方案",     "phase": "define",  "artifact": "01-plan/research-plan.md",
     "extra_artifacts": ["00-task/intent_doc.json"]},
    {"id": "step_4_candidates",            "num": "4",    "label": "候选源采集",   "phase": "collect", "artifact": "02-sources/candidates.md"},
    {"id": "step_5_evidence_matrix",       "num": "5",    "label": "证据矩阵",     "phase": "collect", "artifact": "03-evidence/evidence_matrix.md"},
    {"id": "step_6_hypothesis",            "num": "6",    "label": "假设账本",     "phase": "collect", "artifact": "03-evidence/hypothesis_ledger.json"},
    {"id": "step_6_5_core_objects_fetch",  "num": "6.5",  "label": "核心对象直采", "phase": "collect", "artifact": "04-captures/core_objects_fetch_log.md",  "gate_after": "gate_1"},
    {"id": "step_7_analysis",              "num": "7",    "label": "多Agent分析",  "phase": "analyze", "artifact": "05-analysis/",
     "r2_r3_required": ["05-analysis/insight_ledger.json"]},
    {"id": "step_7_5_narrative_plan",      "num": "7.5",  "label": "行文思路规划", "phase": "analyze", "artifact": "05-analysis/narrative-plan.md",          "gate_after": "gate_7"},
    {"id": "step_8_red_team",              "num": "8",    "label": "反方审计",     "phase": "analyze", "artifact": "06-review/red_team.md",                "gate_after": "gate_11"},
    {"id": "step_9_final_report_draft",    "num": "9",    "label": "报告初稿",     "phase": "review",  "artifact": "07-output/final-report.md"},
    {"id": "step_9_5_independent_audit",   "num": "9.5",  "label": "独立审计",     "phase": "review",  "artifact": "06-review/audit_report.md",              "gate_after": "gate_2"},
    {"id": "step_9_6_adversarial_review",  "num": "9.6",  "label": "对抗式审核",   "phase": "review",  "artifact": "06-review/adversarial_review.json",      "gate_after": "gate_5"},
    {"id": "step_10_reader_simulation",    "num": "10",   "label": "读者模拟",     "phase": "review",  "artifact": "06-review/reader_diagnosis.json",        "gate_after": "gate_3"},
    {"id": "step_10_5_write_read_rewrite", "num": "10.5", "label": "写-读-改闭环", "phase": "review",  "artifact": "06-review/iteration_state.json",         "gate_after": "gate_8"},
    {"id": "step_11_trace_manifest",       "num": "11",   "label": "溯源清单",     "phase": "deliver", "artifact": "07-output/trace-manifest.json",          "gate_after": "gate_12"},
    {"id": "step_12_view_model",           "num": "12",   "label": "视图模型",     "phase": "deliver", "artifact": "07-output/view-model.json"},
    {"id": "step_13_html_build",           "num": "13",   "label": "HTML构建",     "phase": "deliver", "artifact": "08-html/index.html",                    "gate_after": "gate_9"},
    {"id": "step_14_validate",             "num": "14",   "label": "验证",         "phase": "deliver", "artifact": "validation report"},
    {"id": "step_15_publish",              "num": "15",   "label": "发布",         "phase": "deliver", "artifact": "桌面副本"},
]

# 12 个门禁（编号与 templates/14-研究执行状态机.md 的「门禁 N」一致）
# artifacts: Dumb 判定——文件存在即视为该门禁已过（机械检查，不做语义判断）
GATES = [
    {"id": "gate_1", "number": 1, "name": "核心对象直采", "after_step": "step_6_5_core_objects_fetch",
     "requirement": "直采日志存在且达标",
     "artifacts": ["04-captures/core_objects_fetch_log.md"]},
    {"id": "gate_2", "number": 2, "name": "独立审计", "after_step": "step_9_5_independent_audit",
     "requirement": "audit_report.md 5 问全 PASS",
     "artifacts": ["06-review/audit_report.md"]},
    {"id": "gate_3", "number": 3, "name": "读者模拟", "after_step": "step_10_reader_simulation",
     "requirement": "reader_diagnosis.json + reader_feedback.md",
     "artifacts": ["06-review/reader_diagnosis.json", "06-review/reader_feedback.md"]},
    {"id": "gate_4", "number": 4, "name": "方向选择", "after_step": "step_1_5_direction_selection",
     "requirement": "≥2 边界问题 + 用户回答",
     "artifacts": ["00-task/direction_selection.json"]},
    {"id": "gate_5", "number": 5, "name": "对抗式审核", "after_step": "step_9_6_adversarial_review",
     "requirement": "≥3 攻击 + 每个攻击有回应",
     "artifacts": ["06-review/adversarial_review.json"]},
    {"id": "gate_6", "number": 6, "name": "第一性原理", "after_step": "step_9_final_report_draft",
     "requirement": "意图层/任务层/报告层三层齐备",
     "artifacts": ["00-task/intent_doc.json"]},
    {"id": "gate_7", "number": 7, "name": "行文思路规划", "after_step": "step_7_5_narrative_plan",
     "requirement": "narrative-plan.md ≥500 字符 + 4 关键词",
     "artifacts": ["05-analysis/narrative-plan.md"]},
    {"id": "gate_8", "number": 8, "name": "写-读-改闭环", "after_step": "step_10_5_write_read_rewrite",
     "requirement": "rewrite_instructions.json + 执行重写（≤2 轮）",
     "artifacts": ["06-review/rewrite_instructions.json", "06-review/iteration_state.json"]},
    {"id": "gate_9", "number": 9, "name": "美学合规验证", "after_step": "step_13_html_build",
     "requirement": "禁止模式 + 必须结构 + 视觉量化",
     "artifacts": ["08-html/index.html"]},
    {"id": "gate_10", "number": 10, "name": "意图树验证", "after_step": "step_1_2_intent_discovery",
     "requirement": "5轮探索 + intent_tree分层结构 + candidate_paths + success_criteria",
     "artifacts": ["00-task/intent_doc.json"]},
    {"id": "gate_11", "number": 11, "name": "洞察账本验证", "after_step": "step_8_red_team",
     "requirement": "verified洞察数R2>=3/R3>=5 + >=1 contrarian + evidence_ids>=2 + report_anchor约束",
     "artifacts": ["05-analysis/insight_ledger.json"]},
    {"id": "gate_12", "number": 12, "name": "跨产物一致性", "after_step": "step_11_trace_manifest",
     "requirement": "intent_tree answer_pointer + insight report_anchor + trace链路id全部存在",
     "artifacts": ["07-output/trace-manifest.json", "07-output/final-report.md"]},
]

STEP_INDEX = {s["id"]: i for i, s in enumerate(STEPS)}
TOTAL_STEPS = len(STEPS)
