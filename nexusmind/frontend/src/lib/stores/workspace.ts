import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Agent, Session } from '@/types';

interface File { id: string; name: string; path: string; content: string; language: string; modified: boolean; }
interface Tab { id: string; title: string; type: string; icon?: string; pinned: boolean; closable: boolean; data?: Record<string, unknown>; }

interface WorkspaceState {
  currentSession: Session | null;
  sessions: Session[];
  openFiles: File[];
  activeFileId: string | null;
  tabs: Tab[];
  activeTabId: string | null;
  activeAgents: Agent[];
  setCurrentSession: (s: Session | null) => void;
  addSession: (s: Session) => void;
  openFile: (f: File) => void;
  closeFile: (id: string) => void;
  openTab: (t: Tab) => void;
  closeTab: (id: string) => void;
  setActiveTab: (id: string | null) => void;
  addAgent: (a: Agent) => void;
  updateAgent: (id: string, u: Partial<Agent>) => void;
  reset: () => void;
}

export const useWorkspaceStore = create<WorkspaceState>()(persist((set) => ({
  currentSession: null, sessions: [], openFiles: [], activeFileId: null, tabs: [], activeTabId: null, activeAgents: [],
  setCurrentSession: (s) => set({ currentSession: s }),
  addSession: (s) => set((st) => ({ sessions: [...st.sessions, s] })),
  openFile: (f) => set((st) => ({ openFiles: [...st.openFiles, f], activeFileId: f.id })),
  closeFile: (id) => set((st) => ({ openFiles: st.openFiles.filter((f) => f.id !== id) })),
  openTab: (t) => set((st) => ({ tabs: [...st.tabs, t], activeTabId: t.id })),
  closeTab: (id) => set((st) => ({ tabs: st.tabs.filter((t) => t.id !== id) })),
  setActiveTab: (id) => set({ activeTabId: id }),
  addAgent: (a) => set((st) => ({ activeAgents: [...st.activeAgents, a] })),
  updateAgent: (id, u) => set((st) => ({ activeAgents: st.activeAgents.map((a) => a.id === id ? { ...a, ...u } : a) })),
  reset: () => set({ currentSession: null, sessions: [], openFiles: [], tabs: [], activeAgents: [] }),
}), { name: 'workspace' }));
