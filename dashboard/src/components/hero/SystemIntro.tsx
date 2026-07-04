// src/components/hero/SystemIntro.tsx
// 系统介绍区（v0.6.2）：品牌感设计 + KPI + 核心特性

import { kpiBlocks, systemFeatures, systemDefinition } from "@/data/stats";

export function SystemIntro() {
  return (
    <section
      style={{
        borderBottom: "1px solid #e8e6dc",
        padding: "72px 24px 56px",
        backgroundColor: "#faf9f5",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* 背景装饰：右上角极淡的橙色渐变 */}
      <div
        style={{
          position: "absolute",
          top: "-200px",
          right: "-100px",
          width: "600px",
          height: "600px",
          background:
            "radial-gradient(circle, #d9775708 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />

      <div
        className="mx-auto fade-in-up"
        style={{ maxWidth: "1440px", position: "relative" }}
      >
        {/* 品牌标识 */}
        <div style={{ marginBottom: "32px" }}>
          {/* 小标识行 */}
          <div
            className="flex items-center gap-3"
            style={{ marginBottom: "20px" }}
          >
            <div
              style={{
                width: "32px",
                height: "32px",
                background:
                  "linear-gradient(135deg, #d97757 0%, #b85b44 100%)",
                borderRadius: "6px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontFamily: "Poppins, sans-serif",
                fontSize: "18px",
                fontWeight: 700,
                color: "#faf9f5",
              }}
            >
              R
            </div>
            <span
              style={{
                fontFamily: "JetBrains Mono, monospace",
                fontSize: "11px",
                color: "#5e5d59",
                textTransform: "uppercase",
                letterSpacing: "0.12em",
              }}
            >
              Research Operating System
            </span>
          </div>

          {/* 品牌主标题 */}
          <h1
            style={{
              fontFamily: "Poppins, sans-serif",
              fontSize: "56px",
              fontWeight: 600,
              color: "#141413",
              lineHeight: "1.05",
              letterSpacing: "-0.03em",
              marginBottom: "20px",
            }}
          >
            Research OS
          </h1>

          {/* 系统一句话定义 */}
          <p
            style={{
              fontFamily: "Lora, serif",
              fontSize: "22px",
              fontWeight: 400,
              lineHeight: "1.4",
              color: "#5e5d59",
              maxWidth: "780px",
              marginBottom: "0",
            }}
          >
            {systemDefinition}
          </p>
        </div>

        {/* 4 块 KPI */}
        <div
          className="grid grid-cols-4 gap-4"
          style={{ marginBottom: "40px", marginTop: "40px" }}
        >
          {kpiBlocks.map((kpi, i) => (
            <div
              key={i}
              style={{
                padding: "18px 20px",
                backgroundColor: "#fff",
                border: "1px solid #e8e6dc",
                borderRadius: "6px",
                transition: "border-color 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "#d9775755";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "#e8e6dc";
              }}
            >
              <div
                style={{
                  fontFamily: "JetBrains Mono, monospace",
                  fontSize: "10px",
                  color: "#5e5d59",
                  textTransform: "uppercase",
                  letterSpacing: "0.1em",
                  marginBottom: "8px",
                }}
              >
                {kpi.label}
              </div>
              <div className="flex items-baseline gap-1">
                <span
                  style={{
                    fontFamily: "JetBrains Mono, monospace",
                    fontSize: "36px",
                    fontWeight: 500,
                    color: "#141413",
                    lineHeight: "1.1",
                    letterSpacing: "-0.02em",
                  }}
                >
                  {kpi.value}
                </span>
                {kpi.suffix && (
                  <span
                    style={{
                      fontFamily: "Poppins, sans-serif",
                      fontSize: "14px",
                      color: "#5e5d59",
                    }}
                  >
                    {kpi.suffix}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* 核心特性 */}
        <div className="grid grid-cols-4 gap-6">
          {systemFeatures.map((f, i) => (
            <div key={i}>
              <div
                style={{
                  fontFamily: "JetBrains Mono, monospace",
                  fontSize: "10px",
                  color: "#d97757",
                  marginBottom: "8px",
                }}
              >
                0{i + 1}
              </div>
              <div
                style={{
                  fontFamily: "Poppins, sans-serif",
                  fontSize: "15px",
                  fontWeight: 600,
                  color: "#141413",
                  marginBottom: "6px",
                  letterSpacing: "-0.01em",
                }}
              >
                {f.title}
              </div>
              <p
                style={{
                  fontFamily: "Poppins, sans-serif",
                  fontSize: "13px",
                  color: "#5e5d59",
                  lineHeight: "1.55",
                }}
              >
                {f.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
