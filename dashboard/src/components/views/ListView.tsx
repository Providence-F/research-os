// src/components/views/ListView.tsx
// 列表视图（默认）：按 5 类主体分组列表

import { projects, groupByCategory, categoryOrder } from "@/data/projects";
import { ProjectRow } from "@/components/shared/ProjectRow";
import { CategoryHeader } from "@/components/shared/CategoryHeader";

export function ListView() {
  const groups = groupByCategory(projects);

  return (
    <div style={{ padding: "20px 24px" }}>
      <div className="mx-auto" style={{ maxWidth: "1440px" }}>
        {/* 视图标题 */}
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
            调研产出列表
          </h2>
          <span
            style={{
              fontFamily: "JetBrains Mono, monospace",
              fontSize: "11px",
              color: "#b0aea5",
            }}
          >
            共 {projects.length} 个 · 按 5 类主体分组
          </span>
        </div>

        {/* 5 类分组 */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
          {categoryOrder.map((cat) => {
            const list = groups[cat];
            if (list.length === 0) return null;
            return (
              <div key={cat}>
                <CategoryHeader category={cat} count={list.length} />
                <div style={{ borderBottom: "1px solid #e8e6dc" }}>
                  {list.map((p) => (
                    <ProjectRow key={p.id} project={p} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
