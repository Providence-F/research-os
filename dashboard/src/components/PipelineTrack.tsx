// src/components/PipelineTrack.tsx
// 流水线轨道：23 步 + 12 门禁 + 项目 token 落点 —— 看板主视觉
import { useMemo } from "react";
import { workflow } from "@/data/workflow";
import type { ProjectPipeline } from "@/data/types";
import { deriveHealth, HEALTH_META } from "@/lib/health";

const CELL_W = 66;          // 每步列宽 px
const TOKEN = 11;           // token 直径
const TOKEN_GAP = 3;        // token 间距
const PER_ROW = 4;          // 每步列内每行 token 数
const ROW_H = TOKEN + TOKEN_GAP;

interface Props {
  projects: ProjectPipeline[];
  onSelect: (p: ProjectPipeline) => void;
}

export function PipelineTrack({ projects, onSelect }: Props) {
  const steps = workflow.steps;

  // 阶段色带：连续同 phase 的步骤合并
  const bands = useMemo(() => {
    const out: { phase: string; name: string; color: string; width: number }[] = [];
    for (const s of steps) {
      const meta = workflow.phases.find((p) => p.id === s.phase);
      const last = out[out.length - 1];
      if (last && last.phase === s.phase) {
        last.width += CELL_W;
      } else {
        out.push({ phase: s.phase, name: meta?.name ?? s.phase, color: meta?.color ?? "#999", width: CELL_W });
      }
    }
    return out;
  }, [steps]);

  // 每步的项目分桶（按 currentStepIndex；完成的项目归入最后一步）
  const buckets = useMemo(() => {
    const map = new Map<number, ProjectPipeline[]>();
    for (const p of projects) {
      const idx = Math.min(p.currentStepIndex, steps.length - 1);
      if (!map.has(idx)) map.set(idx, []);
      map.get(idx)!.push(p);
    }
    return map;
  }, [projects, steps.length]);

  // 步骤 id → 门禁（用于在步骤右缘画门禁菱形）
  const gateAfter = useMemo(() => {
    const m = new Map<string, (typeof workflow.gates)[number]>();
    for (const g of workflow.gates) m.set(g.afterStep, g);
    return m;
  }, []);

  const innerWidth = steps.length * CELL_W;

  return (
    <div className="pipeline-card">
      <div className="pipeline-scroll">
        <div className="pipeline-inner" style={{ width: innerWidth }}>
          {/* 阶段色带 */}
          <div className="phase-bands">
            {bands.map((b) => (
              <div key={b.phase + b.width} className="phase-band" style={{ width: b.width, background: b.color }}>
                {b.name}
              </div>
            ))}
          </div>

          {/* token 落点区 */}
          <div className="token-field">
            {Array.from(buckets.entries()).map(([idx, list]) =>
              list.map((p, i) => {
                const row = Math.floor(i / PER_ROW);
                const col = i % PER_ROW;
                const x = idx * CELL_W + CELL_W / 2 + (col - (PER_ROW - 1) / 2) * (TOKEN + TOKEN_GAP) - TOKEN / 2;
                const y = 190 - 8 - row * ROW_H - TOKEN;
                const health = deriveHealth(p);
                const stepName = p.currentStepIndex >= steps.length ? "已交付" : steps[p.currentStepIndex].label;
                return (
                  <div
                    key={p.id}
                    className={`token ${HEALTH_META[health].className}`}
                    style={{ left: x, top: y }}
                    title={`${p.name}\n位置：${stepName}\n进度：${p.doneSteps}/${steps.length} 步 · 门禁 ${p.gatesPassed}/9\n${HEALTH_META[health].label}`}
                    onClick={() => onSelect(p)}
                  />
                );
              })
            )}
            {/* 每步堆积计数 */}
            {Array.from(buckets.entries()).map(([idx, list]) =>
              list.length >= 3 ? (
                <div key={`c-${idx}`} className="step-count" style={{ left: idx * CELL_W + CELL_W / 2 }}>
                  {list.length}
                </div>
              ) : null
            )}
          </div>

          {/* 步骤节点行 */}
          <div className="step-row">
            {steps.map((s, i) => {
              const gate = gateAfter.get(s.id);
              const hasProjects = buckets.has(i);
              return (
                <div key={s.id} className={`step-cell${hasProjects ? " done-zone" : ""}`} style={{ width: CELL_W }}>
                  <div className="step-node" />
                  {gate && (
                    <div
                      className="gate-diamond"
                      title={`门禁 ${gate.number}：${gate.name}\n${gate.requirement}`}
                    />
                  )}
                  <div className="step-num">{s.num}</div>
                  <div className="step-label">{s.label}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 图例 */}
      <div className="pipeline-legend">
        {(Object.keys(HEALTH_META) as (keyof typeof HEALTH_META)[]).map((h) => (
          <span key={h} className="legend-item">
            <span className={`legend-dot token ${HEALTH_META[h].className}`} style={{ position: "static", width: 10, height: 10 }} />
            {HEALTH_META[h].label}
          </span>
        ))}
        <span className="legend-item">
          <span className="legend-gate" /> 门禁（共 9 个）
        </span>
        <span className="legend-item" style={{ marginLeft: "auto" }}>
          点击圆点查看项目详情 · 数字徽章为该步骤堆积项目数
        </span>
      </div>
    </div>
  );
}
