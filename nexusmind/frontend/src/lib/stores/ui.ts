import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIState {
  theme: 'dark' | 'light' | 'system';
  fontSize: number;
  commandPaletteOpen: boolean;
  notifications: Array<{ id: string; type: string; title: string; message?: string }>;
  setTheme: (t: 'dark' | 'light' | 'system') => void;
  setFontSize: (s: number) => void;
  toggleCommandPalette: () => void;
  addNotification: (n: { type: string; title: string; message?: string }) => void;
  removeNotification: (id: string) => void;
}

export const useUIStore = create<UIState>()(persist((set) => ({
  theme: 'dark', fontSize: 14, commandPaletteOpen: false, notifications: [],
  setTheme: (t) => set({ theme: t }),
  setFontSize: (s) => set({ fontSize: s }),
  toggleCommandPalette: () => set((st) => ({ commandPaletteOpen: !st.commandPaletteOpen })),
  addNotification: (n) => set((st) => ({ notifications: [...st.notifications, { ...n, id: crypto.randomUUID() }] })),
  removeNotification: (id) => set((st) => ({ notifications: st.notifications.filter((n) => n.id !== id) })),
}), { name: 'ui' }));
