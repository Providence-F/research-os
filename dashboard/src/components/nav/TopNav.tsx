// src/components/nav/TopNav.tsx
// 顶部导航：Logo + 视图切换 + 当前版本徽章

import { useDashboardStore, type ViewType } from "@/store/useDashboardStore";
import { stats } from "@/data/stats";

const views: { id: ViewType; label: string }[] = [
  { id: "list", label: "列表" },
  { id: "workflow", label: "工作流" },
  { id: "timeline", label: "版本时间线" },
];

export function TopNav() {
  const { activeView, setView } = useDashboardStore();

  return (
    <header
      className="sticky top-0 z-30 border-b"
      style={{
        backgroundColor: "#faf9f5",
        borderColor: "#e8e6dc",
        height: "56px",
      }}
    >
      <div
        className="mx-auto flex h-full items-center justify-between px-6"
        style={{ maxWidth: "1440px" }}
      >
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div
            style={{
              fontFamily: "Poppins, sans-serif",
              fontSize: "15px",
              fontWeight: 600,
              color: "#141413",
              letterSpacing: "-0.01em",
            }}
          >
            Research OS
          </div>
          <span style={{ color: "#b0aea5", fontSize: "12px" }}>/</span>
          <span
            style={{
              fontFamily: "JetBrains Mono, monospace",
              fontSize: "12px",
              color: "#5e5d59",
            }}
          >
            Dashboard
          </span>
        </div>

        {/* 视图切换 */}
        <nav className="flex items-center gap-1">
          {views.map((v) => (
            <button
              key={v.id}
              onClick={() => setView(v.id)}
              style={{
                fontFamily: "Poppins, sans-serif",
                fontSize: "12px",
                fontWeight: 500,
                padding: "6px 12px",
                borderRadius: "4px",
                color: activeView === v.id ? "#141413" : "#5e5d59",
                backgroundColor: activeView === v.id ? "#f4e4de" : "transparent",
                transition: "all 0.15s ease",
              }}
            >
              {v.label}
            </button>
          ))}
        </nav>

        {/* 当前版本徽章 */}
        <div
          style={{
            fontFamily: "JetBrains Mono, monospace",
            fontSize: "11px",
            color: "#b85b44",
            border: "1px solid #b85b4455",
            backgroundColor: "#b85b4408",
            padding: "3px 8px",
            borderRadius: "3px",
          }}
        >
          {stats.hero.currentVersion} · 当前
        </div>
      </div>
    </header>
  );
}
