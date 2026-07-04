// src/data/workflow.ts
// 调研工作流 5 阶段

import type { WorkflowPhase } from "./types";

export const workflowPhases: WorkflowPhase[] = [
  {
    id: "intent",
    number: "1.0",
    name: "意图挖掘",
    purpose: "从用户描述中反推真实问题，不是直接回答表面问题",
    keySteps: [
      "解析用户原始请求，区分表面诉求与真实目的",
      "通过反例对照锁定调研边界",
      "生成 intent_revisions 记录意图迭代过程",
    ],
    output: "明确的调研意图 + 调研边界文档",
  },
  {
    id: "planning",
    number: "2.0",
    name: "调研规划",
    purpose: "将调研意图拆解为可执行的步骤清单",
    keySteps: [
      "确定调研深度（R0 快速判断 / R1 标准 / R2 深度）",
      "规划调研路径：先扫什么、后深什么、如何交叉验证",
      "生成 task-card.md 作为本次调研的契约",
    ],
    output: "task-card.md + 9 阶段目录结构",
  },
  {
    id: "execution",
    number: "3.0",
    name: "深度执行",
    purpose: "按规划执行调研，收集并结构化信息",
    keySteps: [
      "多源采集：官网 / 源码 / 论文 / 财报 / JD",
      "结构化写入：每条信息进对应阶段目录",
      "交叉验证：至少 2 个独立来源确认关键事实",
    ],
    output: "结构化调研素材（05-analysis / 06-evidence）",
  },
  {
    id: "reader",
    number: "4.0",
    name: "读者模拟",
    purpose: "AI 写完后换角色当读者自检，模拟真实读者的理解过程",
    keySteps: [
      "切换为读者视角，逐段检查理解盲区",
      "对每段打分：0.91+ 通过 / 0.7-0.9 需要重写 / <0.7 推倒重来",
      "生成 reader_simulation.json 记录得分与改进建议",
    ],
    output: "reader_simulation.json + 重写后的稿件",
  },
  {
    id: "delivery",
    number: "5.0",
    name: "交付与迭代",
    purpose: "产出可交付的 HTML 报告，并记录系统改进点",
    keySteps: [
      "渲染 HTML 报告（Anthropic 美学，v0.8 设计系统）",
      "记录本次调研中发现的系统问题（v07_contracts）",
      "更新 goal_ledger.json 追踪目标完成情况",
    ],
    output: "08-html/index.html + 09-publish 发布记录",
  },
];
