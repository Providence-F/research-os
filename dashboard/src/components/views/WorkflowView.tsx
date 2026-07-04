// src/components/views/WorkflowView.tsx
// 工作流视图：5 阶段展示

import { workflowPhases } from "@/data/workflow";

export function WorkflowView() {
  return (
    <div style={{ padding: "20px 24px" }}>
      <div className="mx-auto" style={{ maxWidth: "1100px" }}>
        <div
          className="flex items-baseline justify-between"
          style={{ marginBottom: "20px" }}
        >
          <h2
            style={{
              fontFamily: "Poppins, sans-serif",
              fontSize: "15px",
              fontWeight: 600,
              color: "#141413",
            }}
          >
            调研工作流
          </h2>
          <span
            style={{
              fontFamily: "JetBrains Mono, monospace",
              fontSize: "11px",
              color: "#b0aea5",
            }}
          >
            5 阶段 · 从意图挖掘到读者模拟
          </span>
        </div>

        {/* 阶段列表 */}
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {workflowPhases.map((phase) => (
            <div
              key={phase.id}
              style={{
                backgroundColor: "#fff",
                border: "1px solid #e8e6dc",
                borderLeft: "3px solid #d97757",
                borderRadius: "4px",
                padding: "16px 20px",
              }}
            >
              {/* 阶段头 */}
              <div className="flex items-baseline gap-3" style={{ marginBottom: "10px" }}>
                <span
                  style={{
                    fontFamily: "JetBrains Mono, monospace",
                    fontSize: "13px",
                    fontWeight: 600,
                    color: "#b0aea5",
                  }}
                >
                  {phase.number}
                </span>
                <span
                  style={{
                    fontFamily: "Poppins, sans-serif",
                    fontSize: "15px",
                    fontWeight: 600,
                    color: "#141413",
                  }}
                >
                  {phase.name}
                </span>
              </div>

              {/* 目的 */}
              <p
                style={{
                  fontFamily: "Poppins, sans-serif",
                  fontSize: "13px",
                  color: "#5e5d59",
                  lineHeight: "1.5",
                  marginBottom: "10px",
                }}
              >
                {phase.purpose}
              </p>

              {/* 关键步骤 + 产出 */}
              <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "20px" }}>
                {/* 关键步骤 */}
                <div>
                  <div
                    style={{
                      fontFamily: "JetBrains Mono, monospace",
                      fontSize: "10px",
                      color: "#5e5d59",
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      marginBottom: "6px",
                    }}
                  >
                    关键步骤
                  </div>
                  <ul style={{ listStyle: "none", padding: 0 }}>
                    {phase.keySteps.map((step, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-2"
                        style={{ marginBottom: "3px" }}
                      >
                        <span
                          style={{
                            fontFamily: "JetBrains Mono, monospace",
                            fontSize: "10px",
                            color: "#d97757",
                            marginTop: "2px",
                          }}
                        >
                          ▸
                        </span>
                        <span
                          style={{
                            fontFamily: "Poppins, sans-serif",
                            fontSize: "12px",
                            color: "#141413",
                            lineHeight: "1.5",
                          }}
                        >
                          {step}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 产出 */}
                <div>
                  <div
                    style={{
                      fontFamily: "JetBrains Mono, monospace",
                      fontSize: "10px",
                      color: "#5e5d59",
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      marginBottom: "6px",
                    }}
                  >
                    产出
                  </div>
                  <p
                    style={{
                      fontFamily: "JetBrains Mono, monospace",
                      fontSize: "11px",
                      color: "#788c5d",
                      lineHeight: "1.5",
                    }}
                  >
                    {phase.output}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
