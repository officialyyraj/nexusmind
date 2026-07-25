import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface PanelsState {
  sidebarCollapsed: boolean;
  sidebarWidth: number;
  sidebarTab: string;
  rightPanelCollapsed: boolean;
  rightPanelWidth: number;
  bottomPanelCollapsed: boolean;
  bottomPanelHeight: number;
  bottomPanelTab: string;
  toggleSidebar: () => void;
  toggleRightPanel: () => void;
  toggleBottomPanel: () => void;
  setSidebarWidth: (w: number) => void;
  setRightPanelWidth: (w: number) => void;
  setBottomPanelHeight: (h: number) => void;
  setSidebarTab: (t: string) => void;
  setBottomPanelTab: (t: string) => void;
}

export const usePanelsStore = create<PanelsState>()(persist((set) => ({
  sidebarCollapsed: false, sidebarWidth: 280, sidebarTab: 'sessions',
  rightPanelCollapsed: false, rightPanelWidth: 320,
  bottomPanelCollapsed: true, bottomPanelHeight: 240, bottomPanelTab: 'terminal',
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  toggleRightPanel: () => set((s) => ({ rightPanelCollapsed: !s.rightPanelCollapsed })),
  toggleBottomPanel: () => set((s) => ({ bottomPanelCollapsed: !s.bottomPanelCollapsed })),
  setSidebarWidth: (w) => set({ sidebarWidth: Math.max(200, Math.min(400, w)) }),
  setRightPanelWidth: (w) => set({ rightPanelWidth: Math.max(240, Math.min(480, w)) }),
  setBottomPanelHeight: (h) => set({ bottomPanelHeight: Math.max(120, Math.min(600, h)) }),
  setSidebarTab: (t) => set({ sidebarTab: t }),
  setBottomPanelTab: (t) => set({ bottomPanelTab: t, bottomPanelCollapsed: false }),
}), { name: 'panels' }));
