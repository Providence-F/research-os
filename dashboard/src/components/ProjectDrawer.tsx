// src/components/ProjectDrawer.tsx
// 项目详情抽屉：22 步清单 + 9 门禁状态 + 元信息
import type { ProjectPipeline } from "@/data/types";
import { workflow } from "@/data/workflow";
import { deriveHealth, HEALTH_META } from "@/lib/health";

const TOTAL_STEPS = workflow.steps.length;

interface Props {
  project: ProjectPipeline | null;
  onClose: () => void;
}

export function ProjectDrawer({ project, onClose }: Props) {
  if (!project) return null;
  const health = deriveHealth(project);

  return (
    <>
      <div className="drawer-mask" onClick={onClose} />
      <div className="drawer">
        <button className="drawer-close" onClick={onClose} aria-label="关闭">×</button>
        <h2 className="font-display">{project.name}</h2>
        <div className="d-meta">
          {project.category} · {project.depth} ·{" "}
          <span className={`status-pill ${HEALTH_META[health].className}`}>{HEALTH_META[health].label}</span>
          {" "}· 最后活动 {project.lastActivity || "—"}
        </div>
        {project.summary && <p style={{ fontSize: 13, color: "var(--muted)" }}>{project.summary}</p>}

        <div className="d-block">
          <div className="d-block-title">流水线位置 — {project.doneSteps}/{TOTAL_STEPS} 步</div>
          {workflow.steps.map((s, i) => {
            const st = project.steps[s.id] ?? "pending";
            const isCurrent = i === project.currentStepIndex;
            return (
              <div key={s.id} className={`d-step ${st === "done" ? "done" : "pending"}${isCurrent ? " current" : ""}`}>
                <span className="mark">{st === "done" ? "✓" : isCurrent ? "→" : "·"}</span>
                <span>{s.num} {s.label}</span>
                <span className="art">{s.artifact}</span>
              </div>
            );
          })}
        </div>

        <div className="d-block">
          <div className="d-block-title">门禁 — {project.gatesPassed}/9 通过</div>
          {workflow.gates.map((g) => {
            const pg = project.gates.find((x) => x.id === g.id);
            const passed = pg?.passed ?? false;
            return (
              <div key={g.id} className={`d-gate ${passed ? "pass" : "fail"}`}>
                <span className="gnum"><span>{g.number}</span></span>
                <span>{g.name}</span>
                <span className="req">{passed ? "已通过" : g.requirement}</span>
              </div>
            );
          })}
        </div>

        <div className="d-block">
          <div className="d-block-title">产出</div>
          <div className="d-step"><span>报告字数</span><span className="art">{project.reportChars ? `${(project.reportChars / 10000).toFixed(1)} 万字` : "—"}</span></div>
          <div className="d-step"><span>证据条目</span><span className="art">{project.evidenceCount || "—"}</span></div>
          <div className="d-step"><span>HTML 报告</span><span className="art">{project.hasHtml ? "已生成" : "未生成"}</span></div>
        </div>
      </div>
    </>
  );
}
