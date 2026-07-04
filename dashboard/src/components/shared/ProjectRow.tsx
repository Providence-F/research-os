// src/components/shared/ProjectRow.tsx
// 列表视图中的一行

import type { Project } from "@/data/types";
import { categoryMeta, deliveryStatusLabel } from "@/data/projects";
import { useDashboardStore } from "@/store/useDashboardStore";

interface Props {
  project: Project;
}

export function ProjectRow({ project }: Props) {
  const { selectProject, selectedProjectId } = useDashboardStore();
  const meta = categoryMeta[project.category];
  const isSelected = selectedProjectId === project.id;

  return (
    <div
      onClick={() => selectProject(project.id)}
      className="flex items-center gap-3 cursor-pointer"
      style={{
        padding: "8px 12px",
        borderBottom: "1px solid #f4f3ee",
        backgroundColor: isSelected ? "#f4e4de" : "transparent",
        transition: "background-color 0.12s ease",
      }}
      onMouseEnter={(e) => {
        if (!isSelected) e.currentTarget.style.backgroundColor = "#faf9f5";
      }}
      onMouseLeave={(e) => {
        if (!isSelected) e.currentTarget.style.backgroundColor = "transparent";
      }}
    >
      {/* 左侧色条 */}
      <span
        style={{
          width: "3px",
          height: "20px",
          backgroundColor: meta.color,
          borderRadius: "1px",
          flexShrink: 0,
        }}
      />

      {/* 版本号 */}
      <span
        style={{
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "11px",
          color: "#b0aea5",
          flexShrink: 0,
          width: "44px",
        }}
      >
        {project.version}
      </span>

      {/* 项目名 */}
      <span
        style={{
          fontFamily: "Poppins, sans-serif",
          fontSize: "13px",
          fontWeight: 500,
          color: "#141413",
          flex: 1,
          minWidth: 0,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {project.name}
      </span>

      {/* 交付状态 */}
      <span
        style={{
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "10px",
          color:
            project.deliveryStatus === "trae"
              ? "#5e5d59"
              : "#6a9bcc",
          flexShrink: 0,
        }}
      >
        {deliveryStatusLabel[project.deliveryStatus]}
      </span>

      {/* 日期 */}
      {project.date && (
        <span
          style={{
            fontFamily: "JetBrains Mono, monospace",
            fontSize: "10px",
            color: "#b0aea5",
            flexShrink: 0,
            width: "44px",
            textAlign: "right",
          }}
        >
          {project.date}
        </span>
      )}
    </div>
  );
}
