// src/components/shared/CategoryHeader.tsx
// 分类标题 + 计数徽标

import type { ProjectCategory } from "@/data/types";
import { categoryMeta } from "@/data/projects";

interface Props {
  category: ProjectCategory;
  count: number;
}

export function CategoryHeader({ category, count }: Props) {
  const meta = categoryMeta[category];
  return (
    <div
      className="flex items-baseline justify-between"
      style={{
        borderBottom: `2px solid ${meta.color}`,
        paddingBottom: "6px",
        marginBottom: "8px",
      }}
    >
      <div className="flex items-baseline gap-2">
        <span
          style={{
            width: "8px",
            height: "8px",
            backgroundColor: meta.color,
            display: "inline-block",
            borderRadius: "1px",
          }}
        />
        <span
          style={{
            fontFamily: "Poppins, sans-serif",
            fontSize: "13px",
            fontWeight: 600,
            color: "#141413",
          }}
        >
          {meta.name}
        </span>
        <span
          style={{
            fontFamily: "Poppins, sans-serif",
            fontSize: "11px",
            color: "#5e5d59",
          }}
        >
          {meta.description}
        </span>
      </div>
      <span
        style={{
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "13px",
          fontWeight: 600,
          color: meta.color,
        }}
      >
        {count}
      </span>
    </div>
  );
}
