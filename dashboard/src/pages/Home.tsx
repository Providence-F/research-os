// src/pages/Home.tsx
// v5.0 看板主页：顶部介绍 + 多视图切换 + 详情抽屉

import { TopNav } from "@/components/nav/TopNav";
import { SystemIntro } from "@/components/hero/SystemIntro";
import { ListView } from "@/components/views/ListView";
import { WorkflowView } from "@/components/views/WorkflowView";
import { VersionTimeline } from "@/components/views/VersionTimeline";
import { DetailDrawer } from "@/components/shared/DetailDrawer";
import { useDashboardStore } from "@/store/useDashboardStore";

export function Home() {
  const { activeView } = useDashboardStore();

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#faf9f5" }}>
      <TopNav />
      <SystemIntro />

      <main>
        {activeView === "list" && <ListView />}
        {activeView === "workflow" && <WorkflowView />}
        {activeView === "timeline" && <VersionTimeline />}
      </main>

      <DetailDrawer />
    </div>
  );
}
