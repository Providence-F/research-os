// src/lib/health.ts
// 项目健康度派生（展示层纯函数，数据来自 sync 的机械检查）
import type { ProjectPipeline, Health } from "@/data/types";
import { workflow } from "@/data/workflow";

const TOTAL_STEPS = workflow.steps.length;
const STALE_DAYS = 14;

export function deriveHealth(p: ProjectPipeline): Health {
  if (!p.tracked) return "untracked";
  if (p.currentStepIndex >= TOTAL_STEPS) return "published";
  if (["published", "completed", "validated"].includes(p.status)) return "published";
  if (p.blockedGate) return "blocked";
  if (p.lastActivity) {
    const days = (Date.now() - new Date(p.lastActivity).getTime()) / 86400000;
    if (days > STALE_DAYS) return "stale";
  }
  return "active";
}

export const HEALTH_META: Record<Health, { label: string; className: string }> = {
  published: { label: "已交付", className: "published" },
  active: { label: "流水线中", className: "active" },
  blocked: { label: "门禁卡住", className: "blocked" },
  stale: { label: "停滞", className: "stale" },
  untracked: { label: "未纳入", className: "untracked" },
};

export function currentStepOf(p: ProjectPipeline) {
  if (p.currentStepIndex >= TOTAL_STEPS) return null;
  return workflow.steps[p.currentStepIndex];
}

export function gateById(id: string | null) {
  return workflow.gates.find((g) => g.id === id) ?? null;
}
