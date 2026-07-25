# NexusMind AI IDE - State Management Architecture

## Overview

The state management architecture uses a hybrid approach combining Zustand for global client state and TanStack Query for server state, with React Context for theming and providers.

```
┌─────────────────────────────────────────────────────────────┐
│                    State Architecture                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                    React Context                      │  │
│  │   - ThemeProvider                                     │  │
│  │   - ToastProvider                                    │  │
│  │   - ModalProvider                                    │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                    Zustand (Client State)            │  │
│  │                                                       │  │
│  │   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │  │
│  │   │Workspace│ │ Panels  │ │  Tabs   │ │ Keyboard│ │  │
│  │   │ Store  │ │ Store   │ │ Store   │ │ Store   │ │  │
│  │   └─────────┘ └─────────┘ └─────────┘ └─────────┘ │  │
│  │                                                       │  │
│  │   ┌─────────┐ ┌─────────┐                           │  │
│  │   │Theme   │ │Notif.   │                           │  │
│  │   │Store   │ │Store    │                           │  │
│  │   └─────────┘ └─────────┘                           │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                  TanStack Query (Server State)         │  │
│  │                                                       │  │
│  │   ┌─────────┐ ┌─────────┐ ┌─────────┐              │  │
│  │   │ Agents  │ │Sessions │ │Projects │              │  │
│  │   │ Queries │ │ Queries │ │ Queries │              │  │
│  │   └─────────┘ └─────────┘ └─────────┘              │  │
│  │                                                       │  │
│  │   ┌─────────┐ ┌─────────┐ ┌─────────┐              │  │
│  │   │Plugins  │ │ Memory  │ │ Files   │              │  │
│  │   │ Queries │ │ Queries │ │ Queries │              │  │
│  │   └─────────┘ └─────────┘ └─────────┘              │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Zustand Stores

### Store 1: Workspace Store

```typescript
// lib/stores/workspace.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface File {
  id: string;
  name: string;
  path: string;
  content: string;
  language: string;
  modified: boolean;
}

interface Session {
  id: string;
  name: string;
  projectId: string;
  createdAt: Date;
  updatedAt: Date;
}

interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'idle' | 'running' | 'paused' | 'error';
  currentTask?: string;
}

interface WorkspaceState {
  // Current session
  currentSession: Session | null;
  sessions: Session[];
  
  // Files
  openFiles: File[];
  activeFileId: string | null;
  fileTree: FileNode[];
  
  // Agents
  activeAgents: Agent[];
  
  // Actions
  setCurrentSession: (session: Session | null) => void;
  addSession: (session: Session) => void;
  removeSession: (sessionId: string) => void;
  
  openFile: (file: File) => void;
  closeFile: (fileId: string) => void;
  setActiveFile: (fileId: string) => void;
  updateFileContent: (fileId: string, content: string) => void;
  
  addAgent: (agent: Agent) => void;
  updateAgent: (id: string, updates: Partial<Agent>) => void;
  removeAgent: (id: string) => void;
  
  resetWorkspace: () => void;
}

const initialState = {
  currentSession: null,
  sessions: [],
  openFiles: [],
  activeFileId: null,
  fileTree: [],
  activeAgents: [],
};

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      setCurrentSession: (session) => set({ currentSession: session }),
      
      addSession: (session) => set((state) => ({
        sessions: [...state.sessions, session],
      })),
      
      removeSession: (sessionId) => set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== sessionId),
      })),
      
      openFile: (file) => set((state) => {
        const exists = state.openFiles.find((f) => f.id === file.id);
        if (exists) {
          return { activeFileId: file.id };
        }
        return {
          openFiles: [...state.openFiles, file],
          activeFileId: file.id,
        };
      }),
      
      closeFile: (fileId) => set((state) => {
        const newFiles = state.openFiles.filter((f) => f.id !== fileId);
        let newActiveId = state.activeFileId;
        if (state.activeFileId === fileId) {
          newActiveId = newFiles.length > 0 ? newFiles[newFiles.length - 1].id : null;
        }
        return { openFiles: newFiles, activeFileId: newActiveId };
      }),
      
      setActiveFile: (fileId) => set({ activeFileId: fileId }),
      
      updateFileContent: (fileId, content) => set((state) => ({
        openFiles: state.openFiles.map((f) =>
          f.id === fileId ? { ...f, content, modified: true } : f
        ),
      })),
      
      addAgent: (agent) => set((state) => ({
        activeAgents: [...state.activeAgents, agent],
      })),
      
      updateAgent: (id, updates) => set((state) => ({
        activeAgents: state.activeAgents.map((a) =>
          a.id === id ? { ...a, ...updates } : a
        ),
      })),
      
      removeAgent: (id) => set((state) => ({
        activeAgents: state.activeAgents.filter((a) => a.id !== id),
      })),
      
      resetWorkspace: () => set(initialState),
    }),
    {
      name: 'nexusmind-workspace',
      partialize: (state) => ({
        // Only persist these fields
        sessions: state.sessions,
        openFiles: state.openFiles,
      }),
    }
  )
);
```

### Store 2: Panels Store

```typescript
// lib/stores/panels.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface PanelsState {
  // Sidebar
  sidebarCollapsed: boolean;
  sidebarWidth: number;
  sidebarTab: 'sessions' | 'projects' | 'files' | 'memory' | 'git' | 'plugins' | 'settings';
  
  // Right Panel
  rightPanelCollapsed: boolean;
  rightPanelWidth: number;
  rightPanelTab: 'agents' | 'execution';
  
  // Bottom Panel
  bottomPanelCollapsed: boolean;
  bottomPanelHeight: number;
  bottomPanelTab: 'terminal' | 'logs' | 'docker' | 'sandbox' | 'tests' | 'console';
  
  // Layout Presets
  activePreset: string | null;
  
  // Actions
  toggleSidebar: () => void;
  setSidebarWidth: (width: number) => void;
  setSidebarTab: (tab: PanelsState['sidebarTab']) => void;
  
  toggleRightPanel: () => void;
  setRightPanelWidth: (width: number) => void;
  setRightPanelTab: (tab: PanelsState['rightPanelTab']) => void;
  
  toggleBottomPanel: () => void;
  setBottomPanelHeight: (height: number) => void;
  setBottomPanelTab: (tab: PanelsState['bottomPanelTab']) => void;
  
  setActivePreset: (preset: string | null) => void;
  resetPanels: () => void;
}

const DEFAULT_WIDTHS = {
  sidebar: 280,
  rightPanel: 320,
  bottomPanel: 240,
};

export const usePanelsStore = create<PanelsState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      sidebarWidth: DEFAULT_WIDTHS.sidebar,
      sidebarTab: 'sessions',
      
      rightPanelCollapsed: false,
      rightPanelWidth: DEFAULT_WIDTHS.rightPanel,
      rightPanelTab: 'agents',
      
      bottomPanelCollapsed: true,
      bottomPanelHeight: DEFAULT_WIDTHS.bottomPanel,
      bottomPanelTab: 'terminal',
      
      activePreset: null,
      
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      setSidebarWidth: (width) => set({ sidebarWidth: Math.max(200, Math.min(400, width)) }),
      setSidebarTab: (tab) => set({ sidebarTab: tab }),
      
      toggleRightPanel: () => set((s) => ({ rightPanelCollapsed: !s.rightPanelCollapsed })),
      setRightPanelWidth: (width) => set({ rightPanelWidth: Math.max(240, Math.min(480, width)) }),
      setRightPanelTab: (tab) => set({ rightPanelTab: tab }),
      
      toggleBottomPanel: () => set((s) => ({ bottomPanelCollapsed: !s.bottomPanelCollapsed })),
      setBottomPanelHeight: (height) => set({ bottomPanelHeight: Math.max(120, Math.min(600, height)) }),
      setBottomPanelTab: (tab) => set({ bottomPanelTab: tab, bottomPanelCollapsed: false })),
      
      setActivePreset: (preset) => set({ activePreset: preset }),
      resetPanels: () => set({
        sidebarCollapsed: false,
        sidebarWidth: DEFAULT_WIDTHS.sidebar,
        rightPanelCollapsed: false,
        rightPanelWidth: DEFAULT_WIDTHS.rightPanel,
        bottomPanelCollapsed: true,
        bottomPanelHeight: DEFAULT_WIDTHS.bottomPanel,
      }),
    }),
    { name: 'nexusmind-panels' }
  )
);
```

### Store 3: Tabs Store

```typescript
// lib/stores/tabs.ts
import { create } from 'zustand';

interface Tab {
  id: string;
  title: string;
  type: 'editor' | 'chat' | 'workflow' | 'terminal' | 'diff';
  icon?: string;
  pinned: boolean;
  closable: boolean;
  data?: Record<string, unknown>;
}

interface TabsState {
  tabs: Tab[];
  activeTabId: string | null;
  
  openTab: (tab: Tab) => void;
  closeTab: (tabId: string) => void;
  setActiveTab: (tabId: string) => void;
  reorderTabs: (fromIndex: number, toIndex: number) => void;
  pinTab: (tabId: string) => void;
  unpinTab: (tabId: string) => void;
  closeAllTabs: () => void;
  closeOtherTabs: (tabId: string) => void;
}

export const useTabsStore = create<TabsState>((set, get) => ({
  tabs: [],
  activeTabId: null,
  
  openTab: (tab) => set((state) => {
    const exists = state.tabs.find((t) => t.id === tab.id);
    if (exists) {
      return { activeTabId: tab.id };
    }
    return {
      tabs: [...state.tabs, tab],
      activeTabId: tab.id,
    };
  }),
  
  closeTab: (tabId) => set((state) => {
    const index = state.tabs.findIndex((t) => t.id === tabId);
    const newTabs = state.tabs.filter((t) => t.id !== tabId);
    let newActiveId = state.activeTabId;
    
    if (state.activeTabId === tabId && newTabs.length > 0) {
      newActiveId = newTabs[Math.min(index, newTabs.length - 1)].id;
    }
    
    return { tabs: newTabs, activeTabId: newActiveId };
  }),
  
  setActiveTab: (tabId) => set({ activeTabId: tabId }),
  
  reorderTabs: (fromIndex, toIndex) => set((state) => {
    const newTabs = [...state.tabs];
    const [removed] = newTabs.splice(fromIndex, 1);
    newTabs.splice(toIndex, 0, removed);
    return { tabs: newTabs };
  }),
  
  pinTab: (tabId) => set((state) => ({
    tabs: state.tabs.map((t) => t.id === tabId ? { ...t, pinned: true } : t),
  })),
  
  unpinTab: (tabId) => set((state) => ({
    tabs: state.tabs.map((t) => t.id === tabId ? { ...t, pinned: false } : t),
  })),
  
  closeAllTabs: () => set({ tabs: [], activeTabId: null }),
  
  closeOtherTabs: (tabId) => set((state) => ({
    tabs: state.tabs.filter((t) => t.id === tabId || t.pinned),
    activeTabId: tabId,
  })),
}));
```

### Store 4: Theme Store

```typescript
// lib/stores/theme.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Theme = 'dark' | 'light' | 'system';
type AccentColor = 'blue' | 'green' | 'orange' | 'purple' | 'pink';

interface ThemeState {
  theme: Theme;
  accentColor: AccentColor;
  fontSize: number;
  fontFamily: string;
  
  setTheme: (theme: Theme) => void;
  setAccentColor: (color: AccentColor) => void;
  setFontSize: (size: number) => void;
  setFontFamily: (family: string) => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'dark',
      accentColor: 'blue',
      fontSize: 14,
      fontFamily: 'Inter',
      
      setTheme: (theme) => set({ theme }),
      setAccentColor: (color) => set({ accentColor: color }),
      setFontSize: (size) => set({ fontSize: Math.max(12, Math.min(20, size)) }),
      setFontFamily: (family) => set({ fontFamily: family }),
    }),
    { name: 'nexusmind-theme' }
  )
);
```

### Store 5: Keyboard Store

```typescript
// lib/stores/keyboard.ts
import { create } from 'zustand';

interface Shortcut {
  key: string;
  modifiers: ('ctrl' | 'alt' | 'shift' | 'meta')[];
  description: string;
  action: () => void;
}

interface KeyboardState {
  shortcuts: Map<string, Shortcut>;
  isCommandPaletteOpen: boolean;
  
  registerShortcut: (id: string, shortcut: Shortcut) => void;
  unregisterShortcut: (id: string) => void;
  executeShortcut: (id: string) => void;
  
  openCommandPalette: () => void;
  closeCommandPalette: () => void;
  toggleCommandPalette: () => void;
}

export const useKeyboardStore = create<KeyboardState>((set, get) => ({
  shortcuts: new Map(),
  isCommandPaletteOpen: false,
  
  registerShortcut: (id, shortcut) => set((state) => {
    const newShortcuts = new Map(state.shortcuts);
    newShortcuts.set(id, shortcut);
    return { shortcuts: newShortcuts };
  }),
  
  unregisterShortcut: (id) => set((state) => {
    const newShortcuts = new Map(state.shortcuts);
    newShortcuts.delete(id);
    return { shortcuts: newShortcuts };
  }),
  
  executeShortcut: (id) => {
    const shortcut = get().shortcuts.get(id);
    if (shortcut) {
      shortcut.action();
    }
  },
  
  openCommandPalette: () => set({ isCommandPaletteOpen: true }),
  closeCommandPalette: () => set({ isCommandPaletteOpen: false }),
  toggleCommandPalette: () => set((s) => ({ isCommandPaletteOpen: !s.isCommandPaletteOpen })),
}));
```

### Store 6: Notifications Store

```typescript
// lib/stores/notifications.ts
import { create } from 'zustand';

type NotificationType = 'info' | 'success' | 'warning' | 'error';

interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface NotificationsState {
  notifications: Notification[];
  
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}

export const useNotificationsStore = create<NotificationsState>((set) => ({
  notifications: [],
  
  addNotification: (notification) => set((state) => ({
    notifications: [
      ...state.notifications,
      { ...notification, id: crypto.randomUUID() },
    ],
  })),
  
  removeNotification: (id) => set((state) => ({
    notifications: state.notifications.filter((n) => n.id !== id),
  })),
  
  clearAll: () => set({ notifications: [] }),
}));
```

---

## TanStack Query Setup

```typescript
// lib/api/query-provider.tsx
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ReactNode, useState } from 'react';

export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            gcTime: 10 * 60 * 1000, // 10 minutes
            retry: 1,
            refetchOnWindowFocus: false,
          },
          mutations: {
            retry: 0,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

### Query Hooks

```typescript
// lib/api/hooks/use-agents.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';

export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: () => api.agents.list(),
  });
}

export function useAgent(id: string) {
  return useQuery({
    queryKey: ['agents', id],
    queryFn: () => api.agents.get(id),
    enabled: !!id,
  });
}

export function useCreateAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreateAgentInput) => api.agents.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}

export function useUpdateAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateAgentInput }) =>
      api.agents.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['agents', id] });
    },
  });
}

export function useDeleteAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => api.agents.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}
```

```typescript
// lib/api/hooks/use-sessions.ts
import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { api } from '../client';

export function useSessions(params?: ListSessionsParams) {
  return useQuery({
    queryKey: ['sessions', params],
    queryFn: () => api.sessions.list(params),
  });
}

export function useSession(id: string) {
  return useQuery({
    queryKey: ['sessions', id],
    queryFn: () => api.sessions.get(id),
    enabled: !!id,
  });
}

export function useSessionMessages(sessionId: string, params?: PaginationParams) {
  return useInfiniteQuery({
    queryKey: ['sessions', sessionId, 'messages', params],
    initialPageParam: 0,
    queryFn: ({ pageParam }) => api.sessions.messages(sessionId, { ...params, cursor: pageParam }),
    getNextPageParam: (lastPage) => lastPage.meta?.cursor,
    enabled: !!sessionId,
  });
}

export function useSendMessage() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ sessionId, content }: { sessionId: string; content: string }) =>
      api.sessions.send(sessionId, { content }),
    onSuccess: (_, { sessionId }) => {
      queryClient.invalidateQueries({ queryKey: ['sessions', sessionId, 'messages'] });
    },
  });
}
```

---

## React Context Providers

```typescript
// app/providers.tsx
'use client';

import { QueryProvider } from '@/lib/api/query-provider';
import { ThemeProvider } from 'next-themes';
import { Toaster } from '@/components/ui/sonner';
import { ModalProvider } from '@/components/shared/modal-provider';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryProvider>
      <ThemeProvider
        attribute="class"
        defaultTheme="dark"
        enableSystem
        disableTransitionOnChange
      >
        <ModalProvider>
          {children}
          <Toaster position="bottom-right" />
        </ModalProvider>
      </ThemeProvider>
    </QueryProvider>
  );
}
```

---

## Data Flow Patterns

### Optimistic Updates

```typescript
const useToggleAgentStatus = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: AgentStatus }) =>
      api.agents.update(id, { status }),
    
    onMutate: async ({ id, status }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['agents'] });
      
      // Snapshot previous value
      const previous = queryClient.getQueryData(['agents']);
      
      // Optimistically update
      queryClient.setQueryData(['agents'], (old: Agent[]) =>
        old.map((agent) => (agent.id === id ? { ...agent, status } : agent))
      );
      
      return { previous };
    },
    
    onError: (err, { id }, context) => {
      // Rollback on error
      queryClient.setQueryData(['agents'], context?.previous);
    },
    
    onSettled: () => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
};
```

### Real-time Updates (WebSocket)

```typescript
// lib/api/subscriptions.ts
import { useEffect, useState, useCallback } from 'react';
import { api } from './client';
import { useQueryClient } from '@tanstack/react-query';

export function useAgentSubscription(agentId: string) {
  const queryClient = useQueryClient();
  const [activity, setActivity] = useState<AgentActivity | null>(null);
  
  useEffect(() => {
    if (!agentId) return;
    
    const ws = api.agents.subscribe(agentId);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      // Update query cache
      queryClient.setQueryData(['agents', agentId], (old) => ({
        ...old,
        ...data,
      }));
      
      // Update local activity state
      setActivity(data.activity);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return () => {
      ws.close();
    };
  }, [agentId, queryClient]);
  
  return activity;
}
```
