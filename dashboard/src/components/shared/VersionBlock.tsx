// src/components/shared/VersionBlock.tsx
// 时间线中的一个版本块

import { useState } from "react";
import type { Version } from "@/data/types";

interface Props {
  version: Version;
}

export function VersionBlock({ version }: Props) {
  const [expanded, setExpanded] = useState(version.isCurrent ?? false);

  return (
    <div
      style={{
        borderBottom: "1px solid #e8e6dc",
        padding: "14px 0",
      }}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-baseline gap-3 text-left"
      >
        {/* 版本号 */}
        <span
          style={{
            fontFamily: "JetBrains Mono, monospace",
            fontSize: "14px",
            fontWeight: 600,
            color: version.isCurrent ? "#b85b44" : "#141413",
            minWidth: "50px",
          }}
        >
          {version.id}
        </span>

        {/* 回退标记 */}
        {version.isRollback && (
          <span
            style={{
              fontFamily: "JetBrains Mono, monospace",
              fontSize: "9px",
              color: "#b85b44",
              border: "1px solid #b85b4455",
              padding: "1px 5px",
              borderRadius: "2px",
            }}
          >
            ← ROLLBACK
          </span>
        )}

        {/* 当前标记 */}
        {version.isCurrent && !version.isRollback && (
          <span
            style={{
              fontFamily: "JetBrains Mono, monospace",
              fontSize: "9px",
              color: "#788c5d",
              border: "1px solid #788c5d55",
              padding: "1px 5px",
              borderRadius: "2px",
            }}
          >
            CURRENT
          </span>
        )}

        {/* 日期 */}
        <span
          style={{
            fontFamily: "JetBrains Mono, monospace",
            fontSize: "11px",
            color: "#b0aea5",
          }}
        >
          {version.date}
        </span>

        {/* 一句话总结 */}
        <span
          style={{
            fontFamily: "Poppins, sans-serif",
            fontSize: "13px",
            color: "#5e5d59",
            flex: 1,
          }}
        >
          {version.summary}
        </span>

        {/* 展开箭头 */}
        <span
          style={{
            fontFamily: "JetBrains Mono, monospace",
            fontSize: "11px",
            color: "#b0aea5",
            transform: expanded ? "rotate(90deg)" : "rotate(0deg)",
            transition: "transform 0.15s ease",
          }}
        >
          →
        </span>
      </button>

      {/* 展开内容 */}
      {expanded && (
        <div
          style={{
            marginTop: "10px",
            marginLeft: "62px",
            paddingBottom: "6px",
          }}
        >
          <ul style={{ listStyle: "none", padding: 0 }}>
            {version.changes.map((change, i) => (
              <li
                key={i}
                className="flex items-start gap-2"
                style={{ marginBottom: "4px" }}
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
                    color: "#5e5d59",
                    lineHeight: "1.5",
                  }}
                >
                  {change}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
