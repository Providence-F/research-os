// src/components/ProjectTable.tsx
import { useMemo, useState } from "react";
import type { ProjectPipeline, Health } from "@/data/types";
import { workflow } from "@/data/workflow";
import { deriveHealth, HEALTH_META, currentStepOf, gateById } from "@/lib/health";

const TOTAL_STEPS = workflow.steps.length;
const FILTERS: (Health | "all")[] = ["all", "active", "blocked", "published", "stale", "untracked"];
const FILTER_LABEL: Record<string, string> = {
  all: "全部", active: "流水线中", blocked: "门禁卡住", published: "已交付", stale: "停滞", untracked: "未纳入",
};

interface Props {
  projects: ProjectPipeline[];
  selectedId: string | null;
  onSelect: (p: ProjectPipeline) => void;
}

export function ProjectTable({ projects, selectedId, onSelect }: Props) {
  const [filter, setFilter] = useState<Health | "all">("all");
  const [q, setQ] = useState("");

  const rows = useMemo(() => {
    return projects.filter((p) => {
      if (filter !== "all" && deriveHealth(p) !== filter) return false;
      if (q && !p.name.toLowerCase().includes(q.toLowerCase())) return false;
      return true;
    });
  }, [projects, filter, q]);

  return (
    <div className="table-card">
      <div className="table-toolbar">
        {FILTERS.map((f) => (
          <span key={f} className={`filter-chip${filter === f ? " on" : ""}`} onClick={() => setFilter(f)}>
            {FILTER_LABEL[f]}
          </span>
        ))}
        <input className="search-input" placeholder="搜索项目名…" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      <div style={{ overflowX: "auto" }}>
        <table className="plist">
          <thead>
            <tr>
              <th>项目</th><th>分类</th><th>深度</th><th>进度</th><th>当前步骤</th>
              <th>门禁</th><th>状态</th><th>最后活动</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => {
              const health = deriveHealth(p);
              const step = currentStepOf(p);
              const blocked = gateById(p.blockedGate);
              return (
                <tr key={p.id} className={selectedId === p.id ? "selected" : ""} onClick={() => onSelect(p)}>
                  <td>
                    <div className="p-name">{p.name}</div>
                    {p.summary && <div className="p-summary">{p.summary}</div>}
                  </td>
                  <td className="p-cat">{p.category}</td>
                  <td className="p-mono">{p.depth}</td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <div className="progress-track">
                        <div className={`progress-fill${health === "published" ? " ok" : ""}`} style={{ width: `${Math.round(p.progress * 100)}%` }} />
                      </div>
                      <span className="p-mono">{p.doneSteps}/{TOTAL_STEPS}</span>
                    </div>
                  </td>
                  <td className="p-mono" style={{ maxWidth: 140, overflow: "hidden", textOverflow: "ellipsis" }}>
                    {step ? `${step.num} ${step.label}` : "已交付"}
                    {blocked && <span className="blocked-badge" title={`卡在门禁 ${blocked.number}：${blocked.name}`}>卡{blocked.number}</span>}
                  </td>
                  <td>
                    <span className="gate-mini" title={`门禁通过 ${p.gatesPassed}/${workflow.gates.length}`}>
                      {p.gates.map((g) => (
                        <span key={g.id} className={`gate-pip${g.passed ? " pass" : ""}`} />
                      ))}
                    </span>
                  </td>
                  <td>
                    <span className={`status-pill ${HEALTH_META[health].className}`}>{HEALTH_META[health].label}</span>
                  </td>
                  <td className="p-mono">{p.lastActivity || "—"}</td>
                </tr>
              );
            })}
            {rows.length === 0 && (
              <tr><td colSpan={8} style={{ textAlign: "center", color: "var(--faint)", padding: 30 }}>无匹配项目</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
