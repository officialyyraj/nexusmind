# NexusMind AI IDE - Frontend Architecture

## Overview

NexusMind is an AI-native IDE for autonomous multi-agent development, comparable to Cursor, Claude Code, and Devin. The frontend is a production-grade application built for speed, reliability, and developer experience.

---

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Speed** | Target 60 FPS, virtualized lists, code splitting |
| **Minimal** | Remove visual noise, information density over decoration |
| **Modern** | Next.js 15, React 19, TypeScript 5.5+ |
| **Professional** | Enterprise-grade UX, production-ready |
| **Keyboard-first** | All features accessible via keyboard |
| **Responsive** | Desktop-first, tablet support |

---

## Tech Stack

### Core

| Technology | Purpose |
|------------|---------|
| Next.js 15 | App router, SSR, streaming |
| React 19 | UI framework |
| TypeScript 5.5+ | Type safety |
| Tailwind CSS v4 | Styling |

### UI Components

| Technology | Purpose |
|------------|---------|
| shadcn/ui | Base components |
| Radix UI | Primitive components |
| Lucide | Icons |
| MagicUI | Enhanced components |
| Aceternity UI | Specific patterns only |

### State & Data

| Technology | Purpose |
|------------|---------|
| Zustand | Global state |
| TanStack Query | Server state |
| TanStack Table | Tables |
| TanStack Virtual | Virtualization |

### Specialized

| Technology | Purpose |
|------------|---------|
| Monaco Editor | Code editing |
| xterm.js | Terminal |
| React Flow | Workflow visualization |
| cmdk | Command palette |
| react-resizable-panels | Layout panels |
| next-themes | Theming |
| Sonner | Notifications |
| Shiki | Syntax highlighting |
| Mermaid | Diagrams |
| dnd-kit | Drag and drop |
| Fuse.js | Fuzzy search |

---

## Folder Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── (auth)/                 # Auth group
│   │   ├── login/
│   │   └── signup/
│   ├── (dashboard)/            # Dashboard group
│   │   ├── page.tsx           # Dashboard home
│   │   ├── agents/
│   │   ├── projects/
│   │   ├── sessions/
│   │   └── settings/
│   ├── (workspace)/            # IDE workspace group
│   │   ├── [sessionId]/
│   │   │   ├── page.tsx       # Workspace view
│   │   │   ├── editor/         # Code editor
│   │   │   ├── chat/          # Agent chat
│   │   │   ├── terminal/       # Terminal
│   │   │   └── logs/          # Log viewer
│   │   └── layout.tsx
│   ├── api/                    # API routes (if needed)
│   ├── layout.tsx
│   ├── globals.css
│   └── providers.tsx
│
├── components/
│   ├── ui/                    # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── dialog.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── tabs.tsx
│   │   ├── tooltip.tsx
│   │   └── ...
│   │
│   ├── layout/                # Layout components
│   │   ├── app-shell.tsx      # Main shell
│   │   ├── sidebar.tsx
│   │   ├── topbar.tsx
│   │   ├── right-panel.tsx
│   │   ├── bottom-panel.tsx
│   │   ├── tab-bar.tsx
│   │   └── panel-resizer.tsx
│   │
│   ├── workspace/             # Workspace components
│   │   ├── editor/
│   │   │   ├── monaco-editor.tsx
│   │   │   ├── file-tree.tsx
│   │   │   ├── diff-viewer.tsx
│   │   │   └── editor-tabs.tsx
│   │   ├── chat/
│   │   │   ├── chat-container.tsx
│   │   │   ├── message.tsx
│   │   │   ├── code-block.tsx
│   │   │   ├── markdown-renderer.tsx
│   │   │   ├── mermaid-renderer.tsx
│   │   │   ├── streaming-message.tsx
│   │   │   └── artifact.tsx
│   │   ├── terminal/
│   │   │   ├── xterm-terminal.tsx
│   │   │   └── terminal-tabs.tsx
│   │   ├── logs/
│   │   │   ├── log-viewer.tsx
│   │   │   └── log-entry.tsx
│   │   └── activity/
│   │       ├── agent-status.tsx
│   │       ├── task-progress.tsx
│   │       ├── token-usage.tsx
│   │       └── reasoning-timeline.tsx
│   │
│   ├── agents/                # Agent components
│   │   ├── agent-card.tsx
│   │   ├── agent-avatar.tsx
│   │   ├── agent-list.tsx
│   │   ├── agent-activity.tsx
│   │   └── agent-tools.tsx
│   │
│   ├── dashboard/            # Dashboard components
│   │   ├── metrics-grid.tsx
│   │   ├── running-agents.tsx
│   │   ├── task-queue.tsx
│   │   ├── resource-monitor.tsx
│   │   ├── recent-sessions.tsx
│   │   └── project-card.tsx
│   │
│   ├── workflow/             # Workflow visualization
│   │   ├── workflow-canvas.tsx
│   │   ├── execution-graph.tsx
│   │   ├── task-dependency.tsx
│   │   └── memory-graph.tsx
│   │
│   ├── plugins/              # Plugin components
│   │   ├── marketplace.tsx
│   │   ├── plugin-card.tsx
│   │   ├── plugin-manager.tsx
│   │   └── plugin-config.tsx
│   │
│   ├── memory/               # Memory components
│   │   ├── memory-explorer.tsx
│   │   ├── memory-graph.tsx
│   │   └── memory-search.tsx
│   │
│   └── shared/               # Shared components
│       ├── command-palette.tsx
│       ├── search.tsx
│       ├── keyboard-shortcuts.tsx
│       ├── context-menu.tsx
│       └── notifications.tsx
│
├── lib/
│   ├── api/                  # API client
│   │   ├── client.ts        # API client
│   │   ├── endpoints/        # Endpoint definitions
│   │   │   ├── agents.ts
│   │   │   ├── sessions.ts
│   │   │   ├── projects.ts
│   │   │   ├── plugins.ts
│   │   │   └── memory.ts
│   │   └── hooks/           # API hooks
│   │       ├── use-agents.ts
│   │       ├── use-sessions.ts
│   │       └── ...
│   │
│   ├── stores/              # Zustand stores
│   │   ├── workspace.ts     # Workspace state
│   │   ├── panels.ts        # Panel layout
│   │   ├── tabs.ts          # Tab state
│   │   ├── theme.ts         # Theme state
│   │   ├── keyboard.ts      # Keyboard shortcuts
│   │   └── notifications.ts  # Notification state
│   │
│   ├── hooks/               # Custom hooks
│   │   ├── use-keyboard.ts
│   │   ├── use-panel.ts
│   │   ├── use-stream.ts
│   │   └── ...
│   │
│   ├── utils/               # Utilities
│   │   ├── cn.ts           # className utility
│   │   ├── format.ts        # Formatting utilities
│   │   └── ...
│   │
│   └── constants/           # Constants
│       ├── shortcuts.ts
│       └── config.ts
│
├── types/                    # TypeScript types
│   ├── agent.ts
│   ├── session.ts
│   ├── project.ts
│   ├── workspace.ts
│   └── api.ts
│
├── styles/                   # Global styles
│   └── globals.css
│
├── public/
│   ├── fonts/
│   └── images/
│
├── .env.local
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── components.json           # shadcn/ui config
└── package.json
```

---

## Component Hierarchy

```
App Shell
├── TopBar
│   ├── ProjectSelector
│   ├── ModelSelector
│   ├── AgentStatusBadge
│   ├── GlobalSearch
│   ├── NotificationsBell
│   └── ProfileMenu
│
├── Sidebar (collapsible, resizable)
│   ├── SidebarHeader
│   ├── SidebarTabs
│   │   ├── SessionsList
│   │   ├── ProjectsList
│   │   ├── FileExplorer
│   │   ├── MemoryExplorer
│   │   ├── GitBrowser
│   │   ├── PluginList
│   │   └── SettingsList
│   └── SidebarFooter
│
├── MainWorkspace
│   ├── TabBar
│   │   ├── Tab (closable, draggable)
│   │   └── NewTabButton
│   │
│   ├── WorkspacePanels
│   │   ├── EditorPanel
│   │   │   ├── MonacoEditor
│   │   │   ├── FileTree
│   │   │   └── EditorTabs
│   │   │
│   │   ├── ChatPanel
│   │   │   ├── ChatHeader
│   │   │   ├── MessageList (virtualized)
│   │   │   ├── StreamingMessage
│   │   │   └── ChatInput
│   │   │
│   │   └── SplitView (resizable)
│   │       ├── LeftPane
│   │       └── RightPane
│   │
│   └── BottomPanel (collapsible)
│       ├── BottomPanelTabs
│       │   ├── Terminal
│       │   ├── Logs
│       │   ├── Docker
│       │   ├── Sandbox
│       │   ├── Tests
│       │   └── Console
│       └── BottomPanelContent
│
├── RightSidebar (collapsible)
│   ├── AgentActivity
│   │   ├── AgentCards
│   │   ├── TaskProgress
│   │   ├── TokenUsage
│   │   └── ReasoningTimeline
│   │
│   └── ExecutionStatus
│       ├── CurrentTask
│       ├── ToolUsage
│       └── MemoryAccess
│
└── CommandPalette (modal)
    ├── SearchInput
    ├── CommandList (virtualized)
    └── CommandGroup
```

---

## Routing Structure

| Route | Component | Description |
|-------|----------|-------------|
| `/` | Dashboard | Home with metrics overview |
| `/agents` | AgentsView | Agent management |
| `/agents/[id]` | AgentDetail | Single agent view |
| `/projects` | ProjectsView | Project list |
| `/projects/[id]` | ProjectDetail | Project detail |
| `/sessions` | SessionsView | Session list |
| `/sessions/[id]` | WorkspaceView | Full IDE workspace |
| `/settings` | SettingsView | Settings page |
| `/settings/profile` | ProfileSettings | Profile settings |
| `/settings/plugins` | PluginSettings | Plugin management |
| `/settings/keys` | APIKeySettings | API key management |
| `/login` | LoginPage | Authentication |
| `/signup` | SignupPage | Registration |

### Nested Routes (Workspace)

```
/sessions/[sessionId]
├── /sessions/[sessionId]/editor     # Code editor view
├── /sessions/[sessionId]/chat        # Chat view
├── /sessions/[sessionId]/terminal    # Terminal view
└── /sessions/[sessionId]/workflow   # Workflow visualization
```

---

## State Management Architecture

### Zustand Stores

```
┌─────────────────────────────────────────────────────────────┐
│                     Zustand Global State                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Workspace  │  │   Panels    │  │    Tabs     │        │
│  │   Store    │  │   Store     │  │   Store     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Theme     │  │  Keyboard   │  │Notification │        │
│  │   Store     │  │   Store     │  │   Store     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Workspace Store (`stores/workspace.ts`)

```typescript
interface WorkspaceState {
  // Session
  currentSession: Session | null;
  sessions: Session[];
  
  // Files
  openFiles: File[];
  activeFile: File | null;
  fileTree: FileNode[];
  
  // Agents
  activeAgents: Agent[];
  agentActivities: Map<string, AgentActivity>;
  
  // Actions
  setSession: (session: Session) => void;
  openFile: (file: File) => void;
  closeFile: (fileId: string) => void;
  addAgent: (agent: Agent) => void;
  updateAgent: (id: string, updates: Partial<Agent>) => void;
}
```

#### Panels Store (`stores/panels.ts`)

```typescript
interface PanelsState {
  // Layout
  sidebarWidth: number;
  sidebarCollapsed: boolean;
  rightPanelWidth: number;
  rightPanelCollapsed: boolean;
  bottomPanelHeight: number;
  bottomPanelCollapsed: boolean;
  
  // Panel visibility
  visiblePanels: PanelType[];
  
  // Actions
  setSidebarWidth: (width: number) => void;
  toggleSidebar: () => void;
  setBottomPanelHeight: (height: number) => void;
}
```

#### Tabs Store (`stores/tabs.ts`)

```typescript
interface TabsState {
  tabs: Tab[];
  activeTab: string | null;
  pinnedTabs: Set<string>;
  
  // Actions
  openTab: (tab: Tab) => void;
  closeTab: (tabId: string) => void;
  setActiveTab: (tabId: string) => void;
  reorderTabs: (fromIndex: number, toIndex: number) => void;
  pinTab: (tabId: string) => void;
}
```

### TanStack Query (Server State)

```
┌─────────────────────────────────────────────────────────────┐
│                   TanStack Query (Server State)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Agents     │  │  Sessions   │  │  Projects   │        │
│  │  Queries    │  │  Queries    │  │  Queries    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Plugins    │  │   Memory    │  │    Logs     │        │
│  │  Queries    │  │  Queries    │  │  Queries    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Streaming Subscriptions                    │  │
│  │   (Agent activity, Logs, Token usage, etc.)          │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Query Hooks

```typescript
// agents/queries.ts
export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: api.agents.list,
    refetchInterval: 30000,
  });
}

export function useAgent(id: string) {
  return useQuery({
    queryKey: ['agents', id],
    queryFn: () => api.agents.get(id),
  });
}

export function useAgentActivity(id: string) {
  return useSubscription({
    queryKey: ['agents', id, 'activity'],
    subscriptionFn: () => api.agents.subscribeActivity(id),
  });
}
```

---

## API Integration Architecture

### API Client

```
┌─────────────────────────────────────────────────────────────┐
│                      API Client                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Axios Instance                       │  │
│  │   - Base URL from env                                │  │
│  │   - Auth interceptors                                │  │
│  │   - Error handling                                   │  │
│  │   - Request/response logging                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Endpoints                           │  │
│  │   - /api/v1/agents                                   │  │
│  │   - /api/v1/sessions                                 │  │
│  │   - /api/v1/projects                                 │  │
│  │   - /api/v1/plugins                                  │  │
│  │   - /api/v1/memory                                   │  │
│  │   - /api/v1/routing                                  │  │
│  │   - /api/v1/improvement                              │  │
│  │   - /api/v1/files                                    │  │
│  │   - /api/v1/terminal                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### API Types

```typescript
// types/api.ts

// Base response
interface ApiResponse<T> {
  data: T;
  meta?: {
    total?: number;
    page?: number;
    limit?: number;
  };
}

// Streaming response
interface StreamingResponse<T> {
  done: boolean;
  data?: T;
  error?: string;
}

// WebSocket events
interface WSMessage {
  type: 'agent_activity' | 'log' | 'token_usage' | 'task_update';
  payload: unknown;
}
```

### Endpoint Definitions

```typescript
// lib/api/endpoints/agents.ts

export const agentsApi = {
  list: () => 
    api.get<Agent[]>('/agents'),
  
  get: (id: string) => 
    api.get<Agent>(`/agents/${id}`),
  
  create: (data: CreateAgentInput) => 
    api.post<Agent>('/agents', data),
  
  update: (id: string, data: UpdateAgentInput) => 
    api.patch<Agent>(`/agents/${id}`, data),
  
  delete: (id: string) => 
    api.delete(`/agents/${id}`),
  
  subscribe: (id: string) => 
    api.subscribe<AgentActivity>(`/agents/${id}/subscribe`),
  
  execute: (id: string, task: string) => 
    api.post<ExecutionResult>(`/agents/${id}/execute`, { task }),
};

// lib/api/endpoints/sessions.ts

export const sessionsApi = {
  list: (params?: ListSessionsParams) => 
    api.get<Session[]>('/sessions', { params }),
  
  get: (id: string) => 
    api.get<Session>(`/sessions/${id}`),
  
  create: (data: CreateSessionInput) => 
    api.post<Session>('/sessions', data),
  
  messages: (id: string, params?: PaginationParams) => 
    api.get<Message[]>(`/sessions/${id}/messages`, { params }),
  
  send: (id: string, content: string) => 
    api.post<Message>(`/sessions/${id}/messages`, { content }),
  
  stream: (id: string) => 
    api.stream<Message>(`/sessions/${id}/stream`),
};
```

---

## UI Design Guidelines

### Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| H1 | Inter | 24px | 600 |
| H2 | Inter | 20px | 600 |
| H3 | Inter | 16px | 600 |
| Body | Inter | 14px | 400 |
| Small | Inter | 12px | 400 |
| Code | JetBrains Mono | 13px | 400 |

### Spacing

```typescript
const spacing = {
  xs: '4px',    // 0.25rem
  sm: '8px',    // 0.5rem
  md: '12px',   // 0.75rem
  lg: '16px',   // 1rem
  xl: '24px',   // 1.5rem
  '2xl': '32px', // 2rem
};
```

### Colors

#### Dark Theme (Default)

```typescript
const colors = {
  background: '#09090b',      // zinc-950
  surface: '#18181b',         // zinc-900
  surfaceElevated: '#27272a',  // zinc-800
  border: '#3f3f46',          // zinc-700
  borderHover: '#52525b',     // zinc-600
  text: '#fafafa',            // zinc-50
  textSecondary: '#a1a1aa',  // zinc-400
  textMuted: '#71717a',       // zinc-500
  accent: '#3b82f6',          // blue-500
  accentHover: '#2563eb',     // blue-600
  success: '#22c55e',        // green-500
  warning: '#f59e0b',         // amber-500
  error: '#ef4444',           // red-500
};
```

### Component Guidelines

#### Buttons

| Variant | Background | Text | Border |
|---------|------------|------|--------|
| Primary | accent | white | none |
| Secondary | surface | text | border |
| Ghost | transparent | text | none |
| Destructive | error | white | none |

#### Cards

- Background: surface
- Border: border (1px)
- Border-radius: 8px
- Padding: 16px
- Hover: borderHover (1px)

#### Input Fields

- Background: surfaceElevated
- Border: border (1px)
- Border-radius: 6px
- Height: 36px
- Focus: accent ring (2px)

### Layout Grid

```typescript
// Layout constants
const layout = {
  sidebar: {
    width: 280,
    minWidth: 200,
    maxWidth: 400,
  },
  rightPanel: {
    width: 320,
    minWidth: 240,
    maxWidth: 480,
  },
  bottomPanel: {
    height: 240,
    minHeight: 120,
    maxHeight: 600,
  },
  tabBar: {
    height: 40,
  },
  topBar: {
    height: 48,
  },
};
```

### Animation Guidelines

Use Motion library sparingly:

| Animation | Duration | Easing |
|-----------|----------|--------|
| Page transition | 200ms | ease-out |
| Sidebar collapse | 200ms | ease-in-out |
| Card hover | 150ms | ease-out |
| Button press | 100ms | ease-out |
| Panel resize | 0ms | none (instant) |
| Tooltip | 100ms | ease-out |

### Icon Usage

- Use Lucide icons exclusively
- Size: 16px (small), 20px (default), 24px (large)
- Stroke: 1.5px
- Color: inherit from text color

---

## Performance Strategy

### Code Splitting

```typescript
// Dynamic imports for heavy components
const MonacoEditor = dynamic(
  () => import('@/components/workspace/editor/monaco-editor'),
  { 
    ssr: false,
    loading: () => <EditorSkeleton />
  }
);

const XTermTerminal = dynamic(
  () => import('@/components/workspace/terminal/xterm-terminal'),
  { ssr: false }
);

const ReactFlowCanvas = dynamic(
  () => import('@/components/workflow/workflow-canvas'),
  { ssr: false }
);
```

### Virtualization

```typescript
// TanStack Virtual for large lists
const virtualizer = useVirtualizer({
  count: messages.length,
  getScrollElement: () => containerRef.current,
  estimateSize: () => 80,
  overscan: 5,
});
```

### Memoization

```typescript
// Memoize expensive computations
const sortedAgents = useMemo(
  () => agents.sort((a, b) => a.name.localeCompare(b.name)),
  [agents]
);

// Memoize callbacks
const handleTabChange = useCallback(
  (tabId: string) => setActiveTab(tabId),
  []
);

// React.memo for pure components
const AgentCard = React.memo(AgentCardComponent, (prev, next) => {
  return prev.agent.id === next.agent.id &&
         prev.agent.status === next.agent.status;
});
```

### Image Optimization

```typescript
// next/image for all images
<Image
  src={avatar}
  alt={name}
  width={32}
  height={32}
  className="rounded-full"
/>
```

### Bundle Optimization

```typescript
// next.config.js
module.exports = {
  modularizeImports: {
    'lucide-react': {
      transform: 'lucide-react/dist/esm/icons/{{member}}',
    },
  },
};
```

### Loading States

```typescript
// Skeleton loaders
function AgentCardSkeleton() {
  return (
    <div className="animate-pulse space-y-3">
      <div className="h-4 w-3/4 bg-surface-elevated rounded" />
      <div className="h-3 w-1/2 bg-surface-elevated rounded" />
    </div>
  );
}

// Optimistic updates
const mutation = useMutation({
  mutationFn: createAgent,
  onMutate: async (newAgent) => {
    await queryClient.cancelQueries(['agents']);
    const previous = queryClient.getQueryData(['agents']);
    queryClient.setQueryData(['agents'], (old) => [...old, newAgent]);
    return { previous };
  },
  onError: (err, newAgent, context) => {
    queryClient.setQueryData(['agents'], context.previous);
  },
});
```

---

## Accessibility Strategy

### Keyboard Navigation

```typescript
// Focus management
const useFocusManagement = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  
  const focusNext = () => {
    const focusable = containerRef.current?.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    // Move focus to next element
  };
  
  return { containerRef, focusNext };
};
```

### ARIA Support

```typescript
// Semantic HTML + ARIA
<button
  aria-label="Close tab"
  aria-pressed={isActive}
  onClick={onClose}
>
  <Icon name="x" />
</button>

// Live regions for updates
<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
>
  {statusMessage}
</div>
```

### Screen Reader

```typescript
// Skip links
<a href="#main-content" className="sr-only focus:not-sr-only">
  Skip to main content
</a>

// Screen reader announcements
const announce = useToast()?.announce;

useEffect(() => {
  announce('Agent status changed to running', { politeness: 'polite' });
}, [agentStatus]);
```

### High Contrast

```typescript
// CSS variables for theming
:root {
  --color-text: #fafafa;
  --color-text-high-contrast: #ffffff;
}

@media (prefers-contrast: high) {
  :root {
    --color-text: var(--color-text-high-contrast);
  }
}
```

---

## File Structure Summary

```
frontend/
├── app/                    # 12 files (routes)
├── components/
│   ├── ui/                # 20+ shadcn components
│   ├── layout/            # 8 layout components
│   ├── workspace/         # 15+ workspace components
│   ├── agents/            # 5 agent components
│   ├── dashboard/          # 6 dashboard components
│   ├── workflow/          # 4 workflow components
│   ├── plugins/           # 4 plugin components
│   ├── memory/            # 3 memory components
│   └── shared/            # 5 shared components
├── lib/
│   ├── api/               # 10+ endpoint files
│   ├── stores/            # 6 Zustand stores
│   ├── hooks/             # 15+ custom hooks
│   └── utils/            # 5 utility files
├── types/                 # 10+ type files
└── styles/               # 1 global stylesheet
```

---

## Component Count Summary

| Category | Components |
|----------|------------|
| UI Primitives | 20+ |
| Layout | 8 |
| Workspace | 15+ |
| Agents | 5 |
| Dashboard | 6 |
| Workflow | 4 |
| Plugins | 4 |
| Memory | 3 |
| Shared | 5 |
| **Total** | **70+** |

---

## Implementation Priority

### Phase 1: Core Shell (Week 1)
1. App layout (shell, sidebar, topbar)
2. Panel system (resizable)
3. Tab system
4. Theme provider

### Phase 2: Dashboard (Week 2)
1. Metrics dashboard
2. Agent cards
3. Project list
4. Session list

### Phase 3: Workspace (Week 3)
1. Monaco editor integration
2. File explorer
3. Chat interface
4. Terminal integration

### Phase 4: Advanced (Week 4)
1. React Flow visualization
2. Command palette
3. Memory explorer
4. Plugin system UI

### Phase 5: Polish (Week 5)
1. Animations (Motion)
2. Keyboard shortcuts
3. Accessibility audit
4. Performance optimization
