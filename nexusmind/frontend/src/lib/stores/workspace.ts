import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Agent, Session } from '@/types';

// File types
export interface WorkspaceFile {
  id: string;
  name: string;
  path: string;
  content: string;
  language: string;
  modified: boolean;
  readonly?: boolean;
  cursorPosition?: { line: number; column: number };
  scrollPosition?: { top: number; left: number };
}

export interface EditorTab {
  id: string;
  title: string;
  type: 'editor' | 'chat' | 'workflow' | 'terminal' | 'preview' | 'diff';
  icon?: string;
  pinned: boolean;
  closable: boolean;
  data?: Record<string, unknown>;
  // Editor-specific
  fileId?: string;
  splitDirection?: 'horizontal' | 'vertical';
  diffOriginal?: string;
  diffModified?: string;
}

export interface SplitLayout {
  id: string;
  direction: 'horizontal' | 'vertical';
  sizes: number[];
  children: (SplitLayout | EditorTab)[];
}

export interface SearchQuery {
  query: string;
  regex: boolean;
  caseSensitive: boolean;
  wholeWord: boolean;
  includeHidden: boolean;
  maxResults: number;
}

export interface WorkspaceSearchResult {
  fileId: string;
  filePath: string;
  line: number;
  column: number;
  match: string;
  context: string;
}

interface WorkspaceState {
  // Session state
  currentSession: Session | null;
  sessions: Session[];
  
  // Editor state
  openFiles: WorkspaceFile[];
  activeFileId: string | null;
  tabs: EditorTab[];
  activeTabId: string | null;
  
  // Split layout
  splitLayout: SplitLayout | null;
  activeSplitId: string | null;
  
  // Search state
  searchQuery: SearchQuery | null;
  searchResults: WorkspaceSearchResult[];
  isSearching: boolean;
  
  // Recently opened
  recentlyOpened: string[]; // file IDs
  
  // Agents
  activeAgents: Agent[];
  
  // Actions - Session
  setCurrentSession: (s: Session | null) => void;
  addSession: (s: Session) => void;
  
  // Actions - Files
  openFile: (f: WorkspaceFile) => void;
  closeFile: (id: string) => void;
  updateFile: (id: string, updates: Partial<WorkspaceFile>) => void;
  setActiveFile: (id: string | null) => void;
  
  // Actions - Tabs
  openTab: (t: EditorTab) => void;
  closeTab: (id: string) => void;
  setActiveTab: (id: string | null) => void;
  pinTab: (id: string) => void;
  unpinTab: (id: string) => void;
  reorderTabs: (fromIndex: number, toIndex: number) => void;
  closeOtherTabs: (id: string) => void;
  closeAllTabs: () => void;
  
  // Actions - Split Layout
  setSplitLayout: (layout: SplitLayout | null) => void;
  setActiveSplit: (id: string | null) => void;
  updateSplitLayout: (id: string, updates: Partial<SplitLayout>) => void;
  
  // Actions - Search
  setSearchQuery: (q: SearchQuery | null) => void;
  setSearchResults: (results: WorkspaceSearchResult[]) => void;
  setIsSearching: (searching: boolean) => void;
  
  // Actions - Recently opened
  addToRecentlyOpened: (id: string) => void;
  
  // Actions - Agents
  addAgent: (a: Agent) => void;
  updateAgent: (id: string, u: Partial<Agent>) => void;
  
  // Actions - Reset
  reset: () => void;
}

const initialState = {
  currentSession: null,
  sessions: [],
  openFiles: [],
  activeFileId: null,
  tabs: [],
  activeTabId: null,
  splitLayout: null,
  activeSplitId: null,
  searchQuery: null,
  searchResults: [],
  isSearching: false,
  recentlyOpened: [],
  activeAgents: [],
};

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      // Session actions
      setCurrentSession: (s) => set({ currentSession: s }),
      addSession: (s) => set((st) => ({ sessions: [...st.sessions, s] })),
      
      // File actions
      openFile: (f) => {
        const state = get();
        const existing = state.openFiles.find((file) => file.id === f.id);
        if (existing) {
          set({ activeFileId: f.id });
          return;
        }
        set((st) => ({
          openFiles: [...st.openFiles, f],
          activeFileId: f.id,
        }));
        // Add to tabs
        const tab: EditorTab = {
          id: `tab-${f.id}`,
          title: f.name,
          type: 'editor',
          pinned: false,
          closable: true,
          fileId: f.id,
        };
        set((st) => ({
          tabs: [...st.tabs, tab],
          activeTabId: tab.id,
        }));
        // Add to recently opened
        get().addToRecentlyOpened(f.id);
      },
      
      closeFile: (id) => {
        const state = get();
        const file = state.openFiles.find((f) => f.id === id);
        if (!file) return;
        
        set((st) => ({
          openFiles: st.openFiles.filter((f) => f.id !== id),
          activeFileId: st.activeFileId === id ? null : st.activeFileId,
        }));
        
        // Close corresponding tab
        const tabId = `tab-${id}`;
        set((st) => ({
          tabs: st.tabs.filter((t) => t.id !== tabId),
          activeTabId: st.activeTabId === tabId ? null : st.activeTabId,
        }));
      },
      
      updateFile: (id, updates) => set((st) => ({
        openFiles: st.openFiles.map((f) => 
          f.id === id ? { ...f, ...updates } : f
        ),
      })),
      
      setActiveFile: (id) => {
        set({ activeFileId: id });
        if (id) {
          const tabId = `tab-${id}`;
          set({ activeTabId: tabId });
          get().addToRecentlyOpened(id);
        }
      },
      
      // Tab actions
      openTab: (t) => set((st) => {
        const existing = st.tabs.find((tab) => tab.id === t.id);
        if (existing) {
          return { activeTabId: t.id };
        }
        return { tabs: [...st.tabs, t], activeTabId: t.id };
      }),
      
      closeTab: (id) => {
        const state = get();
        const tab = state.tabs.find((t) => t.id === id);
        if (!tab) return;
        
        set((st) => {
          const newTabs = st.tabs.filter((t) => t.id !== id);
          let newActiveTabId = st.activeTabId;
          
          if (st.activeTabId === id) {
            const idx = st.tabs.findIndex((t) => t.id === id);
            if (newTabs.length > 0) {
              newActiveTabId = newTabs[Math.max(0, idx - 1)]?.id || null;
            } else {
              newActiveTabId = null;
            }
          }
          
          return { tabs: newTabs, activeTabId: newActiveTabId };
        });
        
        // Close corresponding file if it's an editor tab
        if (tab.type === 'editor' && tab.fileId) {
          set((st) => ({
            openFiles: st.openFiles.filter((f) => f.id !== tab.fileId),
            activeFileId: st.activeFileId === tab.fileId ? null : st.activeFileId,
          }));
        }
      },
      
      setActiveTab: (id) => {
        set({ activeTabId: id });
        if (id) {
          const tab = get().tabs.find((t) => t.id === id);
          if (tab?.type === 'editor' && tab.fileId) {
            set({ activeFileId: tab.fileId });
            get().addToRecentlyOpened(tab.fileId);
          }
        }
      },
      
      pinTab: (id) => set((st) => ({
        tabs: st.tabs.map((t) => 
          t.id === id ? { ...t, pinned: true } : t
        ),
      })),
      
      unpinTab: (id) => set((st) => ({
        tabs: st.tabs.map((t) => 
          t.id === id ? { ...t, pinned: false } : t
        ),
      })),
      
      reorderTabs: (fromIndex, toIndex) => set((st) => {
        const newTabs = [...st.tabs];
        const [removed] = newTabs.splice(fromIndex, 1);
        newTabs.splice(toIndex, 0, removed);
        return { tabs: newTabs };
      }),
      
      closeOtherTabs: (id) => set((st) => ({
        tabs: st.tabs.filter((t) => t.id === id || t.pinned),
      })),
      
      closeAllTabs: () => set((st) => ({
        tabs: st.tabs.filter((t) => t.pinned),
      })),
      
      // Split layout actions
      setSplitLayout: (layout) => set({ splitLayout: layout }),
      setActiveSplit: (id) => set({ activeSplitId: id }),
      updateSplitLayout: (id, updates) => set((st) => {
        if (!st.splitLayout) return {};
        
        const updateInLayout = (layout: SplitLayout): SplitLayout => {
          if (layout.id === id) {
            return { ...layout, ...updates };
          }
          return {
            ...layout,
            children: layout.children.map((child) => {
              if ('children' in child) {
                return updateInLayout(child as SplitLayout);
              }
              return child;
            }),
          };
        };
        
        return { splitLayout: updateInLayout(st.splitLayout) };
      }),
      
      // Search actions
      setSearchQuery: (q) => set({ searchQuery: q }),
      setSearchResults: (results) => set({ searchResults: results }),
      setIsSearching: (searching) => set({ isSearching: searching }),
      
      // Recently opened actions
      addToRecentlyOpened: (id) => set((st) => {
        const filtered = st.recentlyOpened.filter((i) => i !== id);
        return { recentlyOpened: [id, ...filtered].slice(0, 20) };
      }),
      
      // Agent actions
      addAgent: (a) => set((st) => ({ activeAgents: [...st.activeAgents, a] })),
      updateAgent: (id, u) => set((st) => ({
        activeAgents: st.activeAgents.map((a) => 
          a.id === id ? { ...a, ...u } : a
        ),
      })),
      
      // Reset
      reset: () => set(initialState),
    }),
    {
      name: 'nexusmind-workspace',
      partialize: (state) => ({
        recentlyOpened: state.recentlyOpened,
        tabs: state.tabs,
        splitLayout: state.splitLayout,
      }),
    }
  )
);

// Helper hooks
export const useActiveFile = () => {
  const { openFiles, activeFileId } = useWorkspaceStore();
  return openFiles.find((f) => f.id === activeFileId);
};

export const useActiveTab = () => {
  const { tabs, activeTabId } = useWorkspaceStore();
  return tabs.find((t) => t.id === activeTabId);
};

export const useEditorTabs = () => {
  const { tabs } = useWorkspaceStore();
  return tabs.filter((t) => t.type === 'editor');
};
