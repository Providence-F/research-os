// src/store/useDashboardStore.ts
// v5.0 状态管理：视图切换 + 详情抽屉

import { create } from "zustand";

export type ViewType = "list" | "workflow" | "timeline";

interface DashboardState {
  activeView: ViewType;
  selectedProjectId: string | null;
  drawerOpen: boolean;

  setView: (view: ViewType) => void;
  selectProject: (id: string) => void;
  closeDrawer: () => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  activeView: "list",
  selectedProjectId: null,
  drawerOpen: false,

  setView: (view) => set({ activeView: view }),

  selectProject: (id) =>
    set({
      selectedProjectId: id,
      drawerOpen: true,
    }),

  closeDrawer: () =>
    set({
      drawerOpen: false,
      // 延迟清除 id，让抽屉动画先完成
    }),
}));
