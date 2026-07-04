// src/components/shared/DetailDrawer.tsx
// 右侧滑出的详情抽屉

import { useDashboardStore } from "@/store/useDashboardStore";
import { findById, categoryMeta, deliveryStatusLabel } from "@/data/projects";

export function DetailDrawer() {
  const { drawerOpen, selectedProjectId, closeDrawer } = useDashboardStore();

  if (!selectedProjectId) return null;

  const project = findById(selectedProjectId);
  if (!project) return null;

  const meta = categoryMeta[project.category];

  return (
    <>
      {/* 遮罩 */}
      {drawerOpen && (
        <div
          onClick={closeDrawer}
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(20, 20, 19, 0.2)",
            zIndex: 40,
            opacity: drawerOpen ? 1 : 0,
            transition: "opacity 0.2s ease",
          }}
        />
      )}

      {/* 抽屉 */}
      <aside
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          bottom: 0,
          width: "420px",
          backgroundColor: "#faf9f5",
          borderLeft: "1px solid #e8e6dc",
          zIndex: 50,
          transform: drawerOpen ? "translateX(0)" : "translateX(100%)",
          transition: "transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
          overflowY: "auto",
        }}
      >
        <div style={{ padding: "20px 24px" }}>
          {/* 关闭按钮 */}
          <div className="flex justify-end" style={{ marginBottom: "12px" }}>
            <button
              onClick={closeDrawer}
              style={{
                fontFamily: "JetBrains Mono, monospace",
                fontSize: "11px",
                color: "#5e5d59",
                padding: "4px 8px",
                border: "1px solid #e8e6dc",
                borderRadius: "3px",
                backgroundColor: "transparent",
                cursor: "pointer",
              }}
            >
              ✕ ESC
            </button>
          </div>

          {/* 分类标签 + 版本 */}
          <div className="flex items-center gap-2" style={{ marginBottom: "8px" }}>
            <span
              style={{
                fontFamily: "JetBrains Mono, monospace",
                fontSize: "10px",
                color: meta.color,
                border: `1px solid ${meta.color}55`,
                backgroundColor: `${meta.color}08`,
                padding: "2px 6px",
                borderRadius: "2px",
              }}
            >
              {meta.name}
            </span>
            <span
              style={{
                fontFamily: "JetBrains Mono, monospace",
                fontSize: "10px",
                color: "#b0aea5",
              }}
            >
              {project.version} · {project.date}
            </span>
          </div>

          {/* 项目名 */}
          <h2
            style={{
              fontFamily: "Poppins, sans-serif",
              fontSize: "20px",
              fontWeight: 600,
              color: "#141413",
              lineHeight: "1.3",
              marginBottom: "16px",
              letterSpacing: "-0.01em",
            }}
          >
            {project.name}
          </h2>

          {/* 一句话主题 */}
          <div style={{ marginBottom: "20px" }}>
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
              主题
            </div>
            <p
              style={{
                fontFamily: "Lora, serif",
                fontSize: "14px",
                color: "#141413",
                lineHeight: "1.6",
              }}
            >
              {project.summary}
            </p>
          </div>

          {/* 大致内容 */}
          {project.overview && (
            <div
              style={{
                padding: "12px 14px",
                backgroundColor: "#fff",
                border: "1px solid #e8e6dc",
                borderRadius: "3px",
                marginBottom: "16px",
              }}
            >
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
                调研内容
              </div>
              <p
                style={{
                  fontFamily: "Poppins, sans-serif",
                  fontSize: "12px",
                  color: "#141413",
                  lineHeight: "1.6",
                }}
              >
                {project.overview}
              </p>
            </div>
          )}

          {/* 主要主题 */}
          {project.keyTopics && project.keyTopics.length > 0 && (
            <div style={{ marginBottom: "16px" }}>
              <div
                style={{
                  fontFamily: "JetBrains Mono, monospace",
                  fontSize: "10px",
                  color: "#5e5d59",
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  marginBottom: "8px",
                }}
              >
                主要主题
              </div>
              <div className="flex flex-wrap gap-1">
                {project.keyTopics.map((topic, i) => (
                  <span
                    key={i}
                    style={{
                      fontFamily: "JetBrains Mono, monospace",
                      fontSize: "10px",
                      color: "#141413",
                      backgroundColor: `${meta.color}12`,
                      border: `1px solid ${meta.color}33`,
                      padding: "3px 8px",
                      borderRadius: "2px",
                    }}
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 核心发现 */}
          {project.keyFindings && project.keyFindings.length > 0 && (
            <div style={{ marginBottom: "16px" }}>
              <div
                style={{
                  fontFamily: "JetBrains Mono, monospace",
                  fontSize: "10px",
                  color: "#5e5d59",
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  marginBottom: "8px",
                }}
              >
                核心发现
              </div>
              <ul style={{ listStyle: "none", padding: 0 }}>
                {project.keyFindings.map((finding, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2"
                    style={{ marginBottom: "6px" }}
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
                      {finding}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 交付状态 */}
          <div
            style={{
              padding: "10px 12px",
              backgroundColor: "#fff",
              border: "1px solid #e8e6dc",
              borderRadius: "3px",
              marginBottom: "16px",
            }}
          >
            <div
              style={{
                fontFamily: "JetBrains Mono, monospace",
                fontSize: "10px",
                color: "#5e5d59",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                marginBottom: "4px",
              }}
            >
              交付状态
            </div>
            <div
              style={{
                fontFamily: "Poppins, sans-serif",
                fontSize: "13px",
                color:
                  project.deliveryStatus === "trae"
                    ? "#141413"
                    : "#5e5d59",
                fontWeight: 500,
              }}
            >
              {deliveryStatusLabel[project.deliveryStatus]}
            </div>
            {project.htmlPath && (
              <div
                style={{
                  fontFamily: "JetBrains Mono, monospace",
                  fontSize: "10px",
                  color: "#b0aea5",
                  marginTop: "4px",
                  wordBreak: "break-all",
                }}
              >
                {project.htmlPath}
              </div>
            )}
          </div>

          {/* 迭代关系（如有） */}
          {project.iteration?.note && (
            <div
              style={{
                padding: "10px 12px",
                backgroundColor: "#d9775708",
                borderLeft: "2px solid #d97757",
              }}
            >
              <div
                style={{
                  fontFamily: "JetBrains Mono, monospace",
                  fontSize: "10px",
                  color: "#d97757",
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  marginBottom: "4px",
                }}
              >
                迭代关系
              </div>
              <p
                style={{
                  fontFamily: "Lora, serif",
                  fontSize: "12px",
                  fontStyle: "italic",
                  color: "#5e5d59",
                  lineHeight: "1.5",
                }}
              >
                {project.iteration.note}
              </p>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
