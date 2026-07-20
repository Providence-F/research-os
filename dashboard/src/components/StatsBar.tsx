// src/components/StatsBar.tsx
import { stats } from "@/data/stats";

const CELLS = [
  { num: stats.totalProjects, label: "项目总数", tone: "" },
  { num: stats.published, label: "已交付", tone: "ok" },
  { num: stats.inPipeline, label: "流水线中", tone: "accent" },
  { num: stats.blocked, label: "门禁卡住", tone: "danger" },
  { num: stats.totalEvidence, label: "证据条目", tone: "" },
  { num: `${(stats.totalReportChars / 10000).toFixed(1)}w`, label: "报告总字数", tone: "" },
];

export function StatsBar() {
  return (
    <div className="stats-grid">
      {CELLS.map((c) => (
        <div className="stat-cell" key={c.label}>
          <div className={`stat-num ${c.tone}`}>{c.num}</div>
          <div className="stat-label">{c.label}</div>
        </div>
      ))}
    </div>
  );
}
