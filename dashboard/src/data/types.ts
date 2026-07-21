// src/data/types.ts
// Research OS v2.0 看板数据模型 —— 流水线中心（pipeline-centric）
// 看板定位：报告生产线的控制塔，不是项目宣传页。

export type PhaseId = "define" | "collect" | "analyze" | "review" | "deliver";

export interface Phase {
  id: PhaseId;
  name: string;
  color: string;
}

export interface WorkflowStep {
  id: string;            // step_9_6_adversarial_review
  num: string;           // "9.6"
  label: string;         // 对抗式审核
  phase: PhaseId;
  artifact: string;      // 06-review/adversarial_review.json
  gateAfter?: string | null; // 该步骤完成后触发的门禁 id
}

export interface WorkflowGate {
  id: string;            // gate_5
  number: number;        // 与状态机文档「门禁 N」一致
  name: string;          // 对抗式审核
  afterStep: string;     // 触发步骤 id
  requirement: string;   // 一句话通过条件
}

export interface WorkflowDef {
  phases: Phase[];
  steps: WorkflowStep[];
  gates: WorkflowGate[];
}

export type StepStatus = "done" | "pending";

export interface ProjectGate {
  id: string;
  passed: boolean;
}

export interface ProjectPipeline {
  id: string;
  name: string;
  category: string;        // 中文分类名
  depth: string;           // R0/R1/R2/R3 或 —
  status: string;          // research_state.json 原始 status 或机械推断
  tracked: boolean;        // 是否有 research_state.json
  currentStepIndex: number; // 首个未完成步骤下标；22 = 全部完成
  progress: number;         // 0..1
  doneSteps: number;
  steps: Record<string, StepStatus>;
  gates: ProjectGate[];
  gatesPassed: number;
  blockedGate: string | null; // 卡点门禁 id（当前位置前首个未过门禁）
  hasHtml: boolean;
  reportChars: number;
  evidenceCount: number;
  lastActivity: string;    // YYYY-MM-DD
  summary: string;         // 一句话主题
}

export interface VersionInfo {
  id: string;
  date: string;
  summary: string;
  changes: string[];
  isCurrent?: boolean;
}

export interface SystemStats {
  totalProjects: number;
  published: number;
  inPipeline: number;
  blocked: number;
  untracked: number;
  totalEvidence: number;
  totalReportChars: number;
  currentVersion: string;
  syncedAt: string;
}

// 项目健康度（派生展示态）
export type Health = "published" | "active" | "blocked" | "stale" | "untracked";
