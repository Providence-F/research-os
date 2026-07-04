// src/data/types.ts
// v5.0 数据模型：按调研主体分类，不按成功失败分

export type ProjectCategory =
  | "product"    // 产品拆解
  | "industry"   // 行业赛道
  | "tech"       // 技术深度
  | "personal"   // 个人决策
  | "system";    // 系统自身

export type DeliveryStatus =
  | "trae"         // 在 Trae 上执行
  | "claude-code"; // 在 Claude Code 上执行

export interface Project {
  id: string;
  name: string;
  category: ProjectCategory;
  version: string;          // 诞生版本 "v0.5"
  deliveryStatus: DeliveryStatus;
  summary: string;          // 一句话主题
  htmlPath?: string;        // 产出 HTML 路径
  relations: string[];      // 关联项目 id
  iteration?: {             // 迭代关系（可选）
    precursorId?: string;
    successorId?: string;
    note?: string;
  };
  date?: string;            // 交付日期 "06-26" / "07-01"
  // 详情抽屉内容
  overview?: string;        // 大致内容（2-3 句话描述调研做了什么）
  keyTopics?: string[];     // 主要主题（3-5 个关键词）
  keyFindings?: string[];   // 核心发现/结论（2-4 条）
}

// 工作流阶段
export interface WorkflowPhase {
  id: string;
  number: string;           // "1.0" / "2.0" ...
  name: string;
  purpose: string;         // 阶段目的
  keySteps: string[];      // 关键步骤（2-3 个）
  output: string;          // 产出
  isCore?: boolean;        // 核心阶段标记
}

export interface Version {
  id: string;               // "v0.5"
  date: string;             // "07-04"
  summary: string;          // 一句话总结
  changes: string[];        // 变更摘要（来自 CHANGELOG）
  isCurrent?: boolean;
  isRollback?: boolean;     // v0.10 → v0.5 回退
}

export interface Stats {
  hero: {
    versions: number;
    outputs: number;
    categories: number;
    currentVersion: string;
  };
}

// 分类元信息（颜色、中文名）
export interface CategoryMeta {
  id: ProjectCategory;
  name: string;       // 中文名
  color: string;      // 主色
  description: string; // 一句话描述
}
