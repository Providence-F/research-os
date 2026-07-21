// src/pages/Home.tsx
import { useState } from "react";
import { projects } from "@/data/projects";
import { stats } from "@/data/stats";
import type { ProjectPipeline } from "@/data/types";
import { StatsBar } from "@/components/StatsBar";
import { PipelineTrack } from "@/components/PipelineTrack";
import { ProjectTable } from "@/components/ProjectTable";
import { ProjectDrawer } from "@/components/ProjectDrawer";
import { VersionTimeline } from "@/components/VersionTimeline";

export function Home() {
  const [selected, setSelected] = useState<ProjectPipeline | null>(null);

  return (
    <div className="shell">
      <header className="topbar">
        <div>
          <div className="topbar-title font-display">Research OS 控制塔</div>
          <div className="topbar-sub">深度调研生产线：23 步 · 12 门禁 · 项目实时落点</div>
        </div>
        <div className="topbar-meta">
          <div className="version-badge">{stats.currentVersion}</div>
          <div>数据同步于 {stats.syncedAt}</div>
        </div>
      </header>

      <section className="section">
        <StatsBar />
      </section>

      <section className="section">
        <div className="section-head">
          <span className="section-kicker">Pipeline</span>
          <span className="section-title font-display">生产线：每个项目卡在哪个位置</span>
        </div>
        <p className="section-desc">
          圆点 = 项目，落在它当前所处的步骤上。颜色 = 健康度。菱形 = 门禁。堆积处即瓶颈。
        </p>
        <PipelineTrack projects={projects} onSelect={setSelected} />
      </section>

      <section className="section">
        <div className="section-head">
          <span className="section-kicker">Projects</span>
          <span className="section-title font-display">项目清单</span>
        </div>
        <ProjectTable projects={projects} selectedId={selected?.id ?? null} onSelect={setSelected} />
      </section>

      <section className="section">
        <div className="section-head">
          <span className="section-kicker">Evolution</span>
          <span className="section-title font-display">系统演化</span>
        </div>
        <VersionTimeline />
      </section>

      <footer className="footer-note">
        <span>数据链：projects/ → scripts/sync_dashboard.py → dashboard/src/data/*.ts（机械检查，无语义判断）</span>
        <span>Smart Agent. Dumb Tools.</span>
      </footer>

      <ProjectDrawer project={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
