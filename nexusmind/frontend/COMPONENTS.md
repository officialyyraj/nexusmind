# NexusMind AI IDE - Component Specifications

## Component Hierarchy

```
NexusMind IDE
│
├── AppShell
│   ├── TopBar
│   │   ├── Logo
│   │   ├── ProjectSelector (Dropdown)
│   │   ├── ModelSelector (Dropdown)
│   │   ├── AgentStatusBadge
│   │   ├── GlobalSearch (Cmd+K trigger)
│   │   ├── NotificationBell
│   │   │   └── NotificationDropdown
│   │   ├── ThemeToggle
│   │   └── ProfileMenu
│   │       └── DropdownMenu
│   │
│   ├── Sidebar (Resizable, Collapsible)
│   │   ├── SidebarHeader
│   │   │   ├── SidebarToggle
│   │   │   └── SidebarTitle
│   │   │
│   │   ├── SidebarTabs
│   │   │   ├── SessionsTab
│   │   │   ├── ProjectsTab
│   │   │   ├── FilesTab
│   │   │   ├── MemoryTab
│   │   │   ├── GitTab
│   │   │   ├── PluginsTab
│   │   │   └── SettingsTab
│   │   │
│   │   └── SidebarContent (tab-specific)
│   │       ├── SessionsList
│   │       │   └── SessionCard (draggable)
│   │       ├── ProjectsList
│   │       │   └── ProjectCard (draggable)
│   │       ├── FileExplorer (React Arborist)
│   │       │   └── FileTreeNode
│   │       ├── MemoryExplorer
│   │       │   └── MemoryItem
│   │       ├── GitBrowser
│   │       │   ├── BranchSelector
│   │       │   └── CommitList
│   │       ├── PluginList
│   │       │   └── PluginItem
│   │       └── SettingsList
│   │           └── SettingsItem
│   │
│   ├── MainWorkspace
│   │   ├── TabBar
│   │   │   ├── Tab (closable, draggable, pinnable)
│   │   │   ├── TabOverflow (dropdown for many tabs)
│   │   │   └── NewTabButton
│   │   │
│   │   ├── WorkspaceContent
│   │   │   ├── EditorView
│   │   │   │   ├── MonacoEditor
│   │   │   │   │   ├── EditorToolbar
│   │   │   │   │   ├── EditorGutter
│   │   │   │   │   ├── EditorMinimap
│   │   │   │   │   └── EditorTabs
│   │   │   │   ├── FileTree (sidebar)
│   │   │   │   └── DiffViewer
│   │   │   │
│   │   │   ├── ChatView
│   │   │   │   ├── ChatHeader
│   │   │   │   │   ├── AgentSelector
│   │   │   │   │   └── ChatActions
│   │   │   │   ├── MessageList (virtualized)
│   │   │   │   │   ├── UserMessage
│   │   │   │   │   ├── AIMessage
│   │   │   │   │   │   ├── MarkdownRenderer
│   │   │   │   │   │   ├── CodeBlock
│   │   │   │   │   │   ├── MermaidDiagram
│   │   │   │   │   │   ├── TableRenderer
│   │   │   │   │   │   ├── Artifact
│   │   │   │   │   │   └── StreamingText
│   │   │   │   │   └── SystemMessage
│   │   │   │   └── ChatInput
│   │   │   │       ├── Input textarea
│   │   │   │       ├── FileUpload
│   │   │   │       └── SendButton
│   │   │   │
│   │   │   ├── WorkflowView
│   │   │   │   └── ReactFlowCanvas
│   │   │   │       ├── WorkflowNode
│   │   │   │       ├── WorkflowEdge
│   │   │   │       └── WorkflowControls
│   │   │   │
│   │   │   └── SplitView
│   │   │       ├── SplitPane
│   │   │       └── SplitDivider
│   │   │
│   │   └── BottomPanel (Collapsible, Resizable)
│   │       ├── BottomPanelTabs
│   │       │   ├── TerminalTab
│   │       │   ├── LogsTab
│   │       │   ├── DockerTab
│   │       │   ├── SandboxTab
│   │       │   ├── TestsTab
│   │       │   └── ConsoleTab
│   │       │
│   │       └── BottomPanelContent
│   │           ├── XTermTerminal
│   │           ├── LogViewer
│   │           │   ├── LogFilters
│   │           │   └── LogEntry
│   │           ├── DockerMonitor
│   │           ├── SandboxManager
│   │           ├── TestRunner
│   │           └── ConsoleOutput
│   │
│   ├── RightSidebar (Collapsible, Resizable)
│   │   ├── RightPanelHeader
│   │   │
│   │   ├── AgentActivity
│   │   │   ├── AgentCard (expandable)
│   │   │   │   ├── AgentHeader
│   │   │   │   │   ├── AgentAvatar
│   │   │   │   │   ├── AgentName
│   │   │   │   │   └── AgentStatus
│   │   │   │   ├── AgentMetrics
│   │   │   │   │   ├── TaskProgress
│   │   │   │   │   ├── TokenUsage
│   │   │   │   │   ├── CPUUsage
│   │   │   │   │   └── MemoryUsage
│   │   │   │   ├── AgentTools (collapsible)
│   │   │   │   │   └── ToolItem
│   │   │   │   └── AgentLogs (collapsible)
│   │   │   │       └── LogSnippet
│   │   │   │
│   │   │   └── AgentList
│   │   │
│   │   └── ExecutionStatus
│   │       ├── CurrentTask
│   │       ├── ReasoningTimeline
│   │       │   └── ReasonStep
│   │       └── MemoryAccess
│   │
│   └── CommandPalette (Modal, Cmd+K)
│       ├── CommandInput
│       ├── CommandList (virtualized)
│       │   ├── CommandGroup
│       │   │   ├── GroupHeader
│       │   │   └── CommandItem
│       │   └── CommandFooter
│       └── CommandResult
│
└── Modals
    ├── SettingsModal
    ├── PluginModal
    ├── NewProjectModal
    ├── NewSessionModal
    └── KeyboardShortcutsModal
```

---

## Component Props Specifications

### AppShell

```typescript
interface AppShellProps {
  children: React.ReactNode;
  sidebarCollapsed?: boolean;
  rightPanelCollapsed?: boolean;
  bottomPanelCollapsed?: boolean;
  onSidebarToggle?: () => void;
  onRightPanelToggle?: () => void;
  onBottomPanelToggle?: () => void;
}
```

### TopBar

```typescript
interface TopBarProps {
  projectName?: string;
  currentModel?: string;
  agentStatus?: AgentStatus;
  onProjectSelect?: (projectId: string) => void;
  onModelSelect?: (modelId: string) => void;
  onSearchOpen?: () => void;
  onNotificationsOpen?: () => void;
}
```

### Sidebar

```typescript
interface SidebarProps {
  activeTab: SidebarTab;
  collapsed: boolean;
  width: number;
  onTabChange: (tab: SidebarTab) => void;
  onToggle: () => void;
  onWidthChange: (width: number) => void;
}

type SidebarTab = 'sessions' | 'projects' | 'files' | 'memory' | 'git' | 'plugins' | 'settings';
```

### TabBar

```typescript
interface TabBarProps {
  tabs: Tab[];
  activeTabId: string | null;
  onTabSelect: (tabId: string) => void;
  onTabClose: (tabId: string) => void;
  onTabReorder: (fromIndex: number, toIndex: number) => void;
  onNewTab?: () => void;
}

interface Tab {
  id: string;
  title: string;
  type: 'editor' | 'chat' | 'workflow' | 'terminal';
  icon?: string;
  pinned?: boolean;
  modified?: boolean;
  closable?: boolean;
}
```

### MonacoEditor

```typescript
interface MonacoEditorProps {
  file: File;
  content: string;
  language?: string;
  readOnly?: boolean;
  onChange?: (value: string) => void;
  onSave?: () => void;
  onFormat?: () => void;
  theme?: 'dark' | 'light';
  minimap?: boolean;
  lineNumbers?: 'on' | 'off' | 'relative';
}
```

### AgentCard

```typescript
interface AgentCardProps {
  agent: Agent;
  expanded?: boolean;
  onExpand?: () => void;
  onSelect?: () => void;
  onKill?: () => void;
  onRestart?: () => void;
}

interface Agent {
  id: string;
  name: string;
  avatar?: string;
  type: AgentType;
  model: string;
  status: 'idle' | 'running' | 'paused' | 'error' | 'completed';
  currentTask?: string;
  progress?: number;
  startedAt?: Date;
  elapsedTime?: number;
  currentTool?: string;
  memoryAccesses?: MemoryAccess[];
  tokenUsage?: TokenUsage;
  cpuUsage?: number;
  memoryUsage?: number;
  logs?: LogEntry[];
}

interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  cost: number;
}
```

### ChatMessage

```typescript
interface ChatMessageProps {
  message: Message;
  onCodeCopy?: (code: string) => void;
  onCodeRun?: (code: string, language: string) => void;
  onFilePreview?: (filePath: string) => void;
  onDiffPreview?: (before: string, after: string) => void;
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  attachments?: Attachment[];
  artifacts?: Artifact[];
  citations?: Citation[];
  streaming?: boolean;
}

interface Artifact {
  type: 'code' | 'table' | 'diagram' | 'chart';
  language?: string;
  content: string;
  title?: string;
}
```

### LogViewer

```typescript
interface LogViewerProps {
  logs: LogEntry[];
  maxHeight?: number;
  autoScroll?: boolean;
  filters?: LogFilters;
  onFilterChange?: (filters: LogFilters) => void;
  onEntryClick?: (entry: LogEntry) => void;
}

interface LogEntry {
  id: string;
  timestamp: Date;
  level: 'debug' | 'info' | 'warn' | 'error';
  source: string;
  message: string;
  metadata?: Record<string, unknown>;
}
```

### CommandPalette

```typescript
interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect?: (command: Command) => void;
}

interface Command {
  id: string;
  title: string;
  description?: string;
  icon?: string;
  shortcut?: string;
  category: 'navigation' | 'action' | 'file' | 'agent' | 'settings';
  action: () => void | Promise<void>;
}
```

### WorkflowCanvas

```typescript
interface WorkflowCanvasProps {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  onNodeClick?: (node: WorkflowNode) => void;
  onEdgeClick?: (edge: WorkflowEdge) => void;
  onNodesChange?: (nodes: WorkflowNode[]) => void;
  onEdgesChange?: (edges: WorkflowEdge[]) => void;
}

interface WorkflowNode {
  id: string;
  type: 'agent' | 'task' | 'tool' | 'condition' | 'input' | 'output';
  position: { x: number; y: number };
  data: {
    label: string;
    icon?: string;
    status?: 'pending' | 'running' | 'completed' | 'failed';
    agentType?: AgentType;
    task?: Task;
  };
}

interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  type?: 'default' | 'success' | 'error' | 'condition';
  label?: string;
}
```

---

## Component Behavior Specifications

### Panel Resizing

| Panel | Default Size | Min Size | Max Size | Resize Handle |
|-------|-------------|----------|----------|---------------|
| Sidebar | 280px | 200px | 400px | Right edge |
| Right Panel | 320px | 240px | 480px | Left edge |
| Bottom Panel | 240px | 120px | 600px | Top edge |

### Drag and Drop

| Component | Drop Target | Drop Effect |
|-----------|-------------|-------------|
| Tab | TabBar | Reorder |
| File | File Tree | Move |
| Session | Session List | Reorder |
| Project | Project List | Reorder |
| Node | Workflow Canvas | Move/Connect |

### Keyboard Shortcuts

| Action | Shortcut | Context |
|--------|----------|---------|
| Command Palette | `Cmd+K` | Global |
| Quick Open | `Cmd+P` | Global |
| Search | `Cmd+Shift+F` | Global |
| Settings | `Cmd+,` | Global |
| New Tab | `Cmd+T` | Workspace |
| Close Tab | `Cmd+W` | Workspace |
| Toggle Sidebar | `Cmd+B` | Workspace |
| Toggle Right Panel | `Cmd+J` | Workspace |
| Toggle Bottom Panel | `Cmd+\`` | Workspace |
| Save | `Cmd+S` | Editor |
| Format | `Cmd+Shift+P` | Editor |
| Run Code | `Cmd+Enter` | Editor |
| New Session | `Cmd+N` | Dashboard |
| Toggle Theme | `Cmd+Shift+T` | Global |

---

## State Management Per Component

### Transient State (Local)

```typescript
// Component-local, does not persist
interface LocalState {
  hover?: boolean;
  focus?: boolean;
  expanded?: boolean;
  selected?: boolean;
}
```

### Session State (Zustand)

```typescript
// Persists in session, resets on reload
interface SessionState {
  sidebarCollapsed: boolean;
  rightPanelCollapsed: boolean;
  bottomPanelCollapsed: boolean;
  sidebarWidth: number;
  rightPanelWidth: number;
  bottomPanelHeight: number;
  activeTabs: string[];
  openFiles: string[];
}
```

### Persistent State (LocalStorage)

```typescript
// Persists across sessions
interface PersistentState {
  theme: 'dark' | 'light' | 'system';
  accentColor: string;
  layoutPresets: LayoutPreset[];
  recentSessions: string[];
  pinnedProjects: string[];
  keyboardShortcuts: ShortcutMap;
}
```

---

## Performance Requirements

| Component | Target FPS | Virtualization | Lazy Load |
|-----------|-----------|----------------|-----------|
| MessageList | 60 | Yes (>100 items) | No |
| FileTree | 60 | Yes (>500 items) | Yes |
| TabBar | 60 | Overflow dropdown | No |
| LogViewer | 60 | Yes (>1000 items) | No |
| WorkflowCanvas | 60 | Partial | Yes |
| AgentList | 60 | Yes (>20 agents) | Yes |

---

## Accessibility Requirements

| Component | ARIA Role | Keyboard Nav | Screen Reader |
|-----------|-----------|--------------|----------------|
| Sidebar | navigation | Arrow keys, Enter | Yes |
| TabBar | tablist | Arrow keys, Home/End | Yes |
| CommandPalette | dialog | Arrow keys, Enter, Escape | Yes |
| Editor | textbox | Standard editor keys | Yes (with VSCode) |
| AgentCard | article | Enter to select | Yes |
| Tree | tree | Arrow keys, Enter | Yes |
