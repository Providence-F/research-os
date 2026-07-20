// 本文件由 scripts/sync_dashboard.py 自动生成，请勿手改
import type { WorkflowDef } from './types';

export const workflow: WorkflowDef = {
  "phases": [
    {
      "id": "define",
      "name": "定义",
      "color": "#8a6d3b"
    },
    {
      "id": "collect",
      "name": "采集",
      "color": "#4a7a6f"
    },
    {
      "id": "analyze",
      "name": "分析",
      "color": "#7a5a8a"
    },
    {
      "id": "review",
      "name": "审核",
      "color": "#b85b44"
    },
    {
      "id": "deliver",
      "name": "交付",
      "color": "#3d6b8e"
    }
  ],
  "steps": [
    {
      "id": "step_0_scaffold",
      "num": "0",
      "label": "脚手架",
      "phase": "define",
      "artifact": "research_state.json",
      "gateAfter": null
    },
    {
      "id": "step_1_route",
      "num": "1",
      "label": "主题路由",
      "phase": "define",
      "artifact": "01-plan/route_result.json",
      "gateAfter": null
    },
    {
      "id": "step_1_5_direction_selection",
      "num": "1.5",
      "label": "方向选择",
      "phase": "define",
      "artifact": "00-task/direction_selection.json",
      "gateAfter": "gate_4"
    },
    {
      "id": "step_2_task_card",
      "num": "2",
      "label": "任务卡",
      "phase": "define",
      "artifact": "00-task/task-card.md",
      "gateAfter": null
    },
    {
      "id": "step_3_research_plan",
      "num": "3",
      "label": "调研方案",
      "phase": "define",
      "artifact": "01-plan/research-plan.md",
      "gateAfter": null
    },
    {
      "id": "step_4_candidates",
      "num": "4",
      "label": "候选源采集",
      "phase": "collect",
      "artifact": "02-sources/candidates.md",
      "gateAfter": null
    },
    {
      "id": "step_5_evidence_matrix",
      "num": "5",
      "label": "证据矩阵",
      "phase": "collect",
      "artifact": "03-evidence/evidence_matrix.md",
      "gateAfter": null
    },
    {
      "id": "step_6_hypothesis",
      "num": "6",
      "label": "假设账本",
      "phase": "collect",
      "artifact": "03-evidence/hypothesis_ledger.json",
      "gateAfter": null
    },
    {
      "id": "step_6_5_core_objects_fetch",
      "num": "6.5",
      "label": "核心对象直采",
      "phase": "collect",
      "artifact": "04-captures/core_objects_fetch_log.md",
      "gateAfter": "gate_1"
    },
    {
      "id": "step_7_analysis",
      "num": "7",
      "label": "多Agent分析",
      "phase": "analyze",
      "artifact": "05-analysis/",
      "gateAfter": null
    },
    {
      "id": "step_7_5_narrative_plan",
      "num": "7.5",
      "label": "行文思路规划",
      "phase": "analyze",
      "artifact": "05-analysis/narrative-plan.md",
      "gateAfter": "gate_7"
    },
    {
      "id": "step_8_red_team",
      "num": "8",
      "label": "反方审计",
      "phase": "analyze",
      "artifact": "06-review/red_team.md",
      "gateAfter": null
    },
    {
      "id": "step_9_final_report_draft",
      "num": "9",
      "label": "报告初稿",
      "phase": "review",
      "artifact": "07-output/final-report.md",
      "gateAfter": null
    },
    {
      "id": "step_9_5_independent_audit",
      "num": "9.5",
      "label": "独立审计",
      "phase": "review",
      "artifact": "06-review/audit_report.md",
      "gateAfter": "gate_2"
    },
    {
      "id": "step_9_6_adversarial_review",
      "num": "9.6",
      "label": "对抗式审核",
      "phase": "review",
      "artifact": "06-review/adversarial_review.json",
      "gateAfter": "gate_5"
    },
    {
      "id": "step_10_reader_simulation",
      "num": "10",
      "label": "读者模拟",
      "phase": "review",
      "artifact": "06-review/reader_diagnosis.json",
      "gateAfter": "gate_3"
    },
    {
      "id": "step_10_5_write_read_rewrite",
      "num": "10.5",
      "label": "写-读-改闭环",
      "phase": "review",
      "artifact": "06-review/iteration_state.json",
      "gateAfter": "gate_8"
    },
    {
      "id": "step_11_trace_manifest",
      "num": "11",
      "label": "溯源清单",
      "phase": "deliver",
      "artifact": "07-output/trace-manifest.json",
      "gateAfter": null
    },
    {
      "id": "step_12_view_model",
      "num": "12",
      "label": "视图模型",
      "phase": "deliver",
      "artifact": "07-output/view-model.json",
      "gateAfter": null
    },
    {
      "id": "step_13_html_build",
      "num": "13",
      "label": "HTML构建",
      "phase": "deliver",
      "artifact": "08-html/index.html",
      "gateAfter": "gate_9"
    },
    {
      "id": "step_14_validate",
      "num": "14",
      "label": "验证",
      "phase": "deliver",
      "artifact": "validation report",
      "gateAfter": null
    },
    {
      "id": "step_15_publish",
      "num": "15",
      "label": "发布",
      "phase": "deliver",
      "artifact": "桌面副本",
      "gateAfter": null
    }
  ],
  "gates": [
    {
      "id": "gate_1",
      "number": 1,
      "name": "核心对象直采",
      "afterStep": "step_6_5_core_objects_fetch",
      "requirement": "直采日志存在且达标"
    },
    {
      "id": "gate_2",
      "number": 2,
      "name": "独立审计",
      "afterStep": "step_9_5_independent_audit",
      "requirement": "audit_report.md 5 问全 PASS"
    },
    {
      "id": "gate_3",
      "number": 3,
      "name": "读者模拟",
      "afterStep": "step_10_reader_simulation",
      "requirement": "reader_diagnosis.json + reader_feedback.md"
    },
    {
      "id": "gate_4",
      "number": 4,
      "name": "方向选择",
      "afterStep": "step_1_5_direction_selection",
      "requirement": "≥2 边界问题 + 用户回答"
    },
    {
      "id": "gate_5",
      "number": 5,
      "name": "对抗式审核",
      "afterStep": "step_9_6_adversarial_review",
      "requirement": "≥3 攻击 + 每个攻击有回应"
    },
    {
      "id": "gate_6",
      "number": 6,
      "name": "第一性原理",
      "afterStep": "step_9_final_report_draft",
      "requirement": "意图层/任务层/报告层三层齐备"
    },
    {
      "id": "gate_7",
      "number": 7,
      "name": "行文思路规划",
      "afterStep": "step_7_5_narrative_plan",
      "requirement": "narrative-plan.md ≥500 字符 + 4 关键词"
    },
    {
      "id": "gate_8",
      "number": 8,
      "name": "写-读-改闭环",
      "afterStep": "step_10_5_write_read_rewrite",
      "requirement": "rewrite_instructions.json + 执行重写（≤2 轮）"
    },
    {
      "id": "gate_9",
      "number": 9,
      "name": "美学合规验证",
      "afterStep": "step_13_html_build",
      "requirement": "禁止模式 + 必须结构 + 视觉量化"
    }
  ]
};
