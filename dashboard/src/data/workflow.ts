// src/data/workflow.ts
// 调研工作流 v1.4 - 16 步 + 8 门禁

import type { WorkflowPhase } from "./types";

export const workflowPhases: WorkflowPhase[] = [
  {
    id: "intent",
    number: "1.0",
    name: "意图挖掘 + 方向选择",
    purpose: "从用户描述中反推真实问题，通过 Kimi 式边界追问锁定调研方向",
    keySteps: [
      "解析用户原始请求，区分表面诉求与真实目的",
      "Agent 提出 2 个边界问题（范围/深度/时间/决策），用户回答",
      "生成 direction_selection.json 记录方向确认结果",
    ],
    output: "intent_doc.json + direction_selection.json",
    isCore: true,
  },
  {
    id: "planning",
    number: "2.0",
    name: "调研规划",
    purpose: "将调研意图拆解为可执行的步骤清单，Agent 自主完成（无人工确认）",
    keySteps: [
      "生成 task-card.md 作为本次调研的契约",
      "规划调研路径：先扫什么、后深什么、如何交叉验证",
      "确定调研深度（R0/R1/R2/R3）和证据标准",
    ],
    output: "task-card.md + research-plan.md",
  },
  {
    id: "execution",
    number: "3.0",
    name: "深度执行 + 核心对象直采",
    purpose: "按规划执行调研，多源采集并结构化信息，强制核心对象直采",
    keySteps: [
      "多源采集：官网 / 源码 / 论文 / 财报 / JD",
      "核心对象直采（门禁1）：≥3 个对象 + ≥3 个 URL，不能只靠二手资料",
      "交叉验证：至少 2 个独立来源确认关键事实",
    ],
    output: "candidates.md + evidence_matrix.md + core_objects_fetch_log.md",
    isCore: true,
  },
  {
    id: "analysis",
    number: "4.0",
    name: "多 Agent 分析 + 行文思路规划",
    purpose: "多 Agent 并行分析（产品/技术/团队/岗位），然后规划报告行文思路",
    keySteps: [
      "4 个 Agent 并行产出分析文件",
      "行文思路规划（v1.4 新增，门禁7）：判断认知类型，设计三级节点结构",
      "产出 narrative-plan.md 决定章节顺序和第一性原理位置",
    ],
    output: "05-analysis/*.md + narrative-plan.md",
    isCore: true,
  },
  {
    id: "audit",
    number: "5.0",
    name: "反方审计 + 独立审计 + 对抗式审核",
    purpose: "三层质量把关：反方攻击、独立审计、对抗式审核",
    keySteps: [
      "反方 Agent 攻击结论，触发降级",
      "独立审计 Agent（独立会话）5 问全 PASS（门禁2）",
      "对抗式审核 subagent 执行再分测试（门禁5），≥3 攻击 + 回应",
    ],
    output: "red_team.md + audit_report.md + adversarial_review.json",
  },
  {
    id: "reader",
    number: "6.0",
    name: "读者模拟 + 写-读-改闭环",
    purpose: "AI 写完后换角色当读者自检，模拟真实读者的理解过程",
    keySteps: [
      "切换为读者视角，逐段检查理解盲区（门禁3）",
      "对每段打分：0.91+ 通过 / 0.7-0.9 需要重写 / <0.7 推倒重来",
      "写-读-改闭环（门禁8）：最多 2 轮迭代，第 3 轮 fail 转人工",
    ],
    output: "reader_diagnosis.json + rewrite_instructions.json",
    isCore: true,
  },
  {
    id: "delivery",
    number: "7.0",
    name: "交付与发布",
    purpose: "产出可交付的 HTML 报告，验证后发布",
    keySteps: [
      "构建 HTML 报告（Anthropic 美学，工具自动生成）",
      "验证器全量检查（v1.4：含 narrative-plan + 第一性原理位置检查）",
      "发布到桌面 + 同步 Obsidian 知识库 + 推送 GitHub 看板",
    ],
    output: "index.html + validation_report + 桌面副本",
  },
];
