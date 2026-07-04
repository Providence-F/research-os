// src/components/views/VersionTimeline.tsx
// 版本时间线视图：9 个版本倒序

import { versions } from "@/data/versions";
import { VersionBlock } from "@/components/shared/VersionBlock";

export function VersionTimeline() {
  return (
    <div style={{ padding: "20px 24px" }}>
      <div
        className="mx-auto"
        style={{ maxWidth: "1100px" }}
      >
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
            版本时间线
          </h2>
          <span
            style={{
              fontFamily: "JetBrains Mono, monospace",
              fontSize: "11px",
              color: "#b0aea5",
            }}
          >
            9 个版本 · 倒序 · v0.10 → v0.5 回退
          </span>
        </div>

        {/* 回退提示横幅 */}
        <div
          style={{
            padding: "10px 14px",
            backgroundColor: "#b85b4408",
            borderLeft: "2px solid #b85b44",
            marginBottom: "16px",
          }}
        >
          <span
            style={{
              fontFamily: "JetBrains Mono, monospace",
              fontSize: "10px",
              color: "#b85b44",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            ← ROLLBACK
          </span>
          <span
            style={{
              fontFamily: "Poppins, sans-serif",
              fontSize: "12px",
              color: "#5e5d59",
              marginLeft: "8px",
            }}
          >
            v0.10 过度工程化 → 回退到 v0.5 做减法，保留核心流程
          </span>
        </div>

        {/* 版本列表 */}
        <div>
          {versions.map((v) => (
            <VersionBlock key={v.id} version={v} />
          ))}
        </div>
      </div>
    </div>
  );
}
