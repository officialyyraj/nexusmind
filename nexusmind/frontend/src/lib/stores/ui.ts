import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIState {
  theme: 'dark' | 'light' | 'system';
  fontSize: number;
  commandPaletteOpen: boolean;
  sidebarOpen: boolean;
  terminalOpen: boolean;
  notifications: Array<{ id: string; type: string; title: string; message?: string }>;
  setTheme: (t: 'dark' | 'light' | 'system') => void;
  setFontSize: (s: number) => void;
  toggleCommandPalette: () => void;
  toggleSidebar: () => void;
  toggleTerminal: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTerminalOpen: (open: boolean) => void;
  addNotification: (n: { type: string; title: string; message?: string }) => void;
  removeNotification: (id: string) => void;
}

export const useUIStore = create<UIState>()(persist((set) => ({
  theme: 'dark', 
  fontSize: 14, 
  commandPaletteOpen: false,
  sidebarOpen: true,
  terminalOpen: true,
  notifications: [],
  setTheme: (t) => set({ theme: t }),
  setFontSize: (s) => set({ fontSize: s }),
  toggleCommandPalette: () => set((st) => ({ commandPaletteOpen: !st.commandPaletteOpen })),
  toggleSidebar: () => set((st) => ({ sidebarOpen: !st.sidebarOpen })),
  toggleTerminal: () => set((st) => ({ terminalOpen: !st.terminalOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setTerminalOpen: (open) => set({ terminalOpen: open }),
  addNotification: (n) => set((st) => ({ notifications: [...st.notifications, { ...n, id: crypto.randomUUID() }] })),
  removeNotification: (id) => set((st) => ({ notifications: st.notifications.filter((n) => n.id !== id) })),
}), { name: 'ui' }));
