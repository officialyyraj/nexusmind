# NexusMind AI IDE - Component Specifications

## Component Hierarchy

```
NexusMind IDE
в”‚
в”њв”Ђв”Ђ AppShell
в”‚   в”њв”Ђв”Ђ TopBar
в”‚   в”‚   в”њв”Ђв”Ђ Logo
в”‚   в”‚   в”њв”Ђв”Ђ ProjectSelector (Dropdown)
в”‚   в”‚   в”њв”Ђв”Ђ ModelSelector (Dropdown)
в”‚   в”‚   в”њв”Ђв”Ђ AgentStatusBadge
в”‚   в”‚   в”њв”Ђв”Ђ GlobalSearch (Cmd+K trigger)
в”‚   в”‚   в”њв”Ђв”Ђ NotificationBell
в”‚   в”‚   в”‚   в””в”Ђв”Ђ NotificationDropdown
в”‚   в”‚   в”њв”Ђв”Ђ ThemeToggle
в”‚   в”‚   в””в”Ђв”Ђ ProfileMenu
в”‚   в”‚       в””в”Ђв”Ђ DropdownMenu
в”‚   в”‚
в”‚   в”њв”Ђв”Ђ Sidebar (Resizable, Collapsible)
в”‚   в”‚   в”њв”Ђв”Ђ SidebarHeader
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ SidebarToggle
в”‚   в”‚   в”‚   в””в”Ђв”Ђ SidebarTitle
в”‚   в”‚   в”‚
в”‚   в”‚   в”њв”Ђв”Ђ SidebarTabs
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ SessionsTab
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ ProjectsTab
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ FilesTab
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ MemoryTab
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ GitTab
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ PluginsTab
в”‚   в”‚   в”‚   в””в”Ђв”Ђ SettingsTab
в”‚   в”‚   в”‚
в”‚   в”‚   в””в”Ђв”Ђ SidebarContent (tab-specific)
в”‚   в”‚       в”њв”Ђв”Ђ SessionsList
в”‚   в”‚       в”‚   в””в”Ђв”Ђ SessionCard (draggable)
в”‚   в”‚       в”њв”Ђв”Ђ ProjectsList
в”‚   в”‚       в”‚   в””в”Ђв”Ђ ProjectCard (draggable)
в”‚   в”‚       в”њв”Ђв”Ђ FileExplorer (React Arborist)
в”‚   в”‚       в”‚   в””в”Ђв”Ђ FileTreeNode
в”‚   в”‚       в”њв”Ђв”Ђ MemoryExplorer
в”‚   в”‚       в”‚   в””в”Ђв”Ђ MemoryItem
в”‚   в”‚       в”њв”Ђв”Ђ GitBrowser
в”‚   в”‚       в”‚   в”њв”Ђв”Ђ BranchSelector
в”‚   в”‚       в”‚   в””в”Ђв”Ђ CommitList
в”‚   в”‚       в”њв”Ђв”Ђ PluginList
в”‚   в”‚       в”‚   в””в”Ђв”Ђ PluginItem
в”‚   в”‚       в””в”Ђв”Ђ SettingsList
в”‚   в”‚           в””в”Ђв”Ђ SettingsItem
в”‚   в”‚
в”‚   в”њв”Ђв”Ђ MainWorkspace
в”‚   в”‚   в”њв”Ђв”Ђ TabBar
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ Tab (closable, draggable, pinnable)
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ TabOverflow (dropdown for many tabs)
в”‚   в”‚   в”‚   в””в”Ђв”Ђ NewTabButton
в”‚   в”‚   в”‚
в”‚   в”‚   в”њв”Ђв”Ђ WorkspaceContent
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ EditorView
в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ MonacoEditor
в”‚   в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ EditorToolbar
в”‚   в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ EditorGutter
в”‚   в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ EditorMinimap
в”‚   в”‚   в”‚   в”‚   в”‚   в””в”Ђв”Ђ EditorTabs
в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ FileTree (sidebar)
в”‚   в”‚   в”‚   в”‚   в””в”Ђв”Ђ DiffViewer
в”‚   в”‚   в”‚   в”‚
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ ChatView
в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ ChatHeader
в”‚   в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ AgentSelector
в”‚   в”‚   в”‚   в”‚   в”‚   в””в”Ђв”Ђ ChatActions
в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ MessageList (virtualized)
в”‚   в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ UserMessage
в”‚   в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ AIMessage
в”‚   в”‚   в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ MarkdownRenderer
в”‚   в”‚   в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ CodeBlock
в”‚   в”‚   в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ MermaidDiagram
в”‚   в”‚   в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ TableRenderer
в”‚   в”‚   в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ Artifact
в”‚   в”‚   в”‚   в”‚   в”‚   в”‚   в””в”Ђв”Ђ StreamingText
в”‚   в”‚   в”‚   в”‚   в”‚   в””в”Ђв”Ђ SystemMessage
в”‚   в”‚   в”‚   в”‚   в””в”Ђв”Ђ ChatInput
в”‚   в”‚   в”‚   в”‚       в”њв”Ђв”Ђ Input textarea
в”‚   в”‚   в”‚   в”‚       в”њв”Ђв”Ђ FileUpload
в”‚   в”‚   в”‚   в”‚       в””в”Ђв”Ђ SendButton
в”‚   в”‚   в”‚   в”‚
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ WorkflowView
в”‚   в”‚   в”‚   в”‚   в””в”Ђв”Ђ ReactFlowCanvas
в”‚   в”‚   в”‚   в”‚       в”њв”Ђв”Ђ WorkflowNode
в”‚   в”‚   в”‚   в”‚       в”њв”Ђв”Ђ WorkflowEdge
в”‚   в”‚   в”‚   в”‚       в””в”Ђв”Ђ WorkflowControls
в”‚   в”‚   в”‚   в”‚
в”‚   в”‚   в”‚   в””в”Ђв”Ђ SplitView
в”‚   в”‚   в”‚       в”њв”Ђв”Ђ SplitPane
в”‚   в”‚   в”‚       в””в”Ђв”Ђ SplitDivider
в”‚   в”‚   в”‚
в”‚   в”‚   в””в”Ђв”Ђ BottomPanel (Collapsible, Resizable)
в”‚   в”‚       в”њв”Ђв”Ђ BottomPanelTabs
в”‚   в”‚       в”‚   в”њв”Ђв”Ђ TerminalTab
в”‚   в”‚       в”‚   в”њв”Ђв”Ђ LogsTab
в”‚   в”‚       в”‚   в”њв”Ђв”Ђ DockerTab
в”‚   в”‚       в”‚   в”њв”Ђв”Ђ SandboxTab
в”‚   в”‚       в”‚   в”њв”Ђв”Ђ TestsTab
в”‚   в”‚       в”‚   в””в”Ђв”Ђ ConsoleTab
в”‚   в”‚       в”‚
в”‚   в”‚       в””в”Ђв”Ђ BottomPanelContent
в”‚   в”‚           в”њв”Ђв”Ђ XTermTerminal
в”‚   в”‚           в”њв”Ђв”Ђ LogViewer
в”‚   в”‚           в”‚   в”њв”Ђв”Ђ LogFilters
в”‚   в”‚           в”‚   в””в”Ђв”Ђ LogEntry
в”‚   в”‚           в”њв”Ђв”Ђ DockerMonitor
в”‚   в”‚           в”њв”Ђв”Ђ SandboxManager
в”‚   в”‚           в”њв”Ђв”Ђ TestRunner
в”‚   в”‚           в””в”Ђв”Ђ ConsoleOutput
в”‚   в”‚
в”‚   в”њв”Ђв”Ђ RightSidebar (Collapsible, Resizable)
в”‚   в”‚   в”њв”Ђв”Ђ RightPanelHeader
в”‚   в”‚   в”‚
в”‚   в”‚   в”њв”Ђв”Ђ AgentActivity
в”‚   в”‚   в”‚   в”њв”Ђв”Ђ AgentCard (expandable)
в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ AgentHeader
в”‚   в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ AgentAvatar
в”‚   в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ AgentName
в”‚   в”‚   в”‚   в”‚   в”‚   в””в”Ђв”Ђ AgentStatus
в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ AgentMetrics
в”‚   в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ TaskProgress
в”‚   в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ TokenUsage
в”‚   в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ CPUUsage
в”‚   в”‚   в”‚   в”‚   в”‚   в””в”Ђв”Ђ MemoryUsage
в”‚   в”‚   в”‚   в”‚   в”њв”Ђв”Ђ AgentTools (collapsible)
в”‚   в”‚   в”‚   в”‚   в”‚   в””в”Ђв”Ђ ToolItem
в”‚   в”‚   в”‚   в”‚   в””в”Ђв”Ђ AgentLogs (collapsible)
в”‚   в”‚   в”‚   в”‚       в””в”Ђв”Ђ LogSnippet
в”‚   в”‚   в”‚   в”‚
в”‚   в”‚   в”‚   в””в”Ђв”Ђ AgentList
в”‚   в”‚   в”‚
в”‚   в”‚   в””в”Ђв”Ђ ExecutionStatus
в”‚   в”‚       в”њв”Ђв”Ђ CurrentTask
в”‚   в”‚       в”њв”Ђв”Ђ ReasoningTimeline
в”‚   в”‚       в”‚   в””в”Ђв”Ђ ReasonStep
в”‚   в”‚       в””в”Ђв”Ђ MemoryAccess
в”‚   в”‚
в”‚   в””в”Ђв”Ђ CommandPalette (Modal, Cmd+K)
в”‚       в”њв”Ђв”Ђ CommandInput
в”‚       в”њв”Ђв”Ђ CommandList (virtualized)
в”‚       в”‚   в”њв”Ђв”Ђ CommandGroup
в”‚       в”‚   в”‚   в”њв”Ђв”Ђ GroupHeader
в”‚       в”‚   в”‚   в””в”Ђв”Ђ CommandItem
в”‚       в”‚   в””в”Ђв”Ђ CommandFooter
в”‚       в””в”Ђв”Ђ CommandResult
в”‚
в””в”Ђв”Ђ Modals
    в”њв”Ђв”Ђ SettingsModal
    в”њв”Ђв”Ђ PluginModal
    в”њв”Ђв”Ђ NewProjectModal
    в”њв”Ђв”Ђ NewSessionModal
    в””в”Ђв”Ђ KeyboardShortcutsModal
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

---

## Workspace Components (Production-Grade Code Editor)

### Component Structure

```
Workspace Components
├── Workspace (Main Container)
│   ├── FileExplorer
│   │   ├── FileTreeNode (recursive)
│   │   ├── SearchInput
│   │   └── ContextMenu
│   ├── WorkspaceSearch
│   │   ├── SearchInput
│   │   ├── SearchOptions (regex, case, whole word)
│   │   ├── ReplaceInput
│   │   └── SearchResults
│   │       └── ResultGroup (by file)
│   ├── WorkspaceEditor
│   │   ├── TabBar
│   │   │   └── Tab (draggable, pinnable)
│   │   ├── EditorToolbar
│   │   │   ├── SplitButton
│   │   │   └── MaximizeButton
│   │   └── MonacoEditor (single or split)
│   │       ├── EditorInstance
│   │       └── EditorInstance (for split)
│   ├── DiffViewer
│   │   ├── ViewModeToggle (side-by-side, inline)
│   │   ├── DiffHeader
│   │   ├── DiffContent (Monaco DiffEditor)
│   │   └── ChangesPanel (accept/reject)
│   ├── ArtifactViewer
│   │   ├── ViewToggle (preview, raw)
│   │   ├── ActionButtons (copy, download, maximize)
│   │   └── ContentArea
│   │       ├── MarkdownRenderer
│   │       ├── CodeRenderer (syntax highlighting)
│   │       ├── ImageViewer (zoom controls)
│   │       ├── HtmlPreviewer (iframe)
│   │       └── MermaidPreviewer
│   └── TabBar
│       ├── SortableTabs (dnd-kit)
│       ├── PinnedTabs
│       ├── OverflowMenu
│       └── ContextMenu
```

### Key Features

#### Monaco Editor
- Multi-tab editing with drag-and-drop reordering
- Split editor (horizontal/vertical)
- Minimap toggle
- Breadcrumbs navigation
- File outline integration
- Auto-save with configurable delay
- Read-only preview mode
- Syntax highlighting for 50+ languages

#### Diff Viewer
- Monaco DiffEditor for high quality diffs
- Side-by-side and inline modes
- Accept/Reject individual changes
- Accept All / Reject All
- Real-time change statistics

#### Artifact Viewer
- GitHub Flavored Markdown with GFM
- Syntax highlighting (Prism)
- Tables, task lists, code blocks
- Mermaid diagram rendering
- Image viewer with zoom controls
- HTML preview in sandboxed iframe
- JSON/YAML formatting and highlighting
- Copy and download buttons

#### File Explorer
- Recursive tree with expand/collapse
- File icons by extension
- Search/filter files
- Context menu (open, preview, compare, delete)
- Drag and drop support
- File type icons

#### Tab Management
- Drag and drop reordering (dnd-kit)
- Pin/unpin tabs
- Close others/close all
- Modified indicator
- Overflow menu for many tabs
- Context menu on right-click

#### Workspace Search
- Full-text search across open files
- Regex search support
- Case-sensitive/whole-word options
- Replace and replace all
- Results grouped by file
- Click to navigate to result

#### State Persistence
- Open tabs persisted
- Cursor position (per file)
- Scroll position (per file)
- Split layout configuration
- Recently opened files (limit: 20)
- Pinned tabs

### API Integration

```typescript
// Workspace Store
interface WorkspaceState {
  // Files
  openFiles: WorkspaceFile[];
  activeFileId: string | null;
  openFile: (file: WorkspaceFile) => void;
  closeFile: (id: string) => void;
  updateFile: (id: string, updates: Partial<WorkspaceFile>) => void;

  // Tabs
  tabs: EditorTab[];
  activeTabId: string | null;
  openTab: (tab: EditorTab) => void;
  closeTab: (id: string) => void;
  pinTab: (id: string) => void;
  unpinTab: (id: string) => void;
  reorderTabs: (fromIndex: number, toIndex: number) => void;
  closeOtherTabs: (id: string) => void;
  closeAllTabs: () => void;

  // Search
  searchQuery: SearchQuery | null;
  searchResults: SearchResult[];
  setSearchQuery: (q: SearchQuery | null) => void;
  setSearchResults: (results: SearchResult[]) => void;

  // Split Layout
  splitLayout: SplitLayout | null;
  setSplitLayout: (layout: SplitLayout | null) => void;

  // Recently Opened
  recentlyOpened: string[];
  addToRecentlyOpened: (id: string) => void;
}
```

### File Types Supported

| Type | Extension | Preview |
|------|-----------|---------|
| Markdown | .md | GitHub Flavored Markdown |
| HTML | .html | Sandboxed iframe |
| JSON | .json | Formatted with syntax highlighting |
| YAML | .yaml, .yml | Formatted with syntax highlighting |
| XML | .xml | Formatted with syntax highlighting |
| Image | .png, .jpg, .svg | Zoomable viewer |
| PDF | .pdf | Page navigation |
| Mermaid | - | Diagram rendering |
| Code | .ts, .js, .py, etc. | Syntax highlighted |
| Plain Text | .txt | Raw text |

### Keyboard Shortcuts

| Action | Shortcut | Context |
|--------|----------|---------|
| Save | Cmd+S | Editor |
| Search | Cmd+Shift+F | Global |
| Find in Files | Cmd+Shift+F | Files |
| Command Palette | Cmd+K | Global |
| Close Tab | Cmd+W | Workspace |
| New Tab | Cmd+T | Workspace |
| Split Editor | Cmd+\ | Editor |
| Toggle Sidebar | Cmd+B | Workspace |

---

## Workflow Visualization Components

### Component Structure

```
Workflow Components
├── WorkflowPage
│   ├── WorkflowGraph (React Flow)
│   │   ├── WorkflowNode (draggable, selectable)
│   │   └── WorkflowEdge (animated, styled by status)
│   ├── AgentInspectorPanel
│   │   ├── OverviewTab
│   │   ├── ActionsTab
│   │   ├── OutputTab
│   │   └── MetricsTab
│   ├── ExecutionTimeline
│   │   ├── TimelineEvent (expandable)
│   │   └── PlaybackControls
│   ├── LogCorrelationPanel
│   │   ├── LogFilter
│   │   ├── LogSearch
│   │   └── LogGroup (by node)
│   └── WorkflowOverview
│       ├── StatsGrid
│       ├── ProgressCard
│       └── ExportButtons
```

### Key Features

#### Workflow Graph
- Real-time visualization using React Flow
- Node states: idle, running, waiting, completed, failed, retrying
- Animated edges showing data flow
- Node selection with visual highlighting
- MiniMap navigation
- Zoom and pan controls

#### Agent Inspector
- Detailed agent information panel
- Real-time metrics display
- Token usage tracking
- Memory access history
- Recent actions timeline
- Error reporting

#### Execution Timeline
- Chronological event display
- Playback controls (play, pause, replay)
- Speed adjustment (0.5x, 1x, 2x, 4x)
- Duration tracking
- Node correlation on click

#### Log Correlation
- Grouped by node
- Level filtering (debug, info, warn, error)
- Related items display (files, memory, tools)
- Search functionality
- Expandable details

#### Export
- JSON export with full workflow state
- PNG/SVG export for diagrams
- Include/exclude options

### State Management

```typescript
interface WorkflowState {
  currentWorkflow: WorkflowExecution | null;
  selectedNodeId: string | null;
  selectedAgent: AgentInspector | null;
  timeline: TimelineEvent[];
  logs: LogCorrelation[];
  filter: WorkflowFilter;
  isLive: boolean;
  playbackSpeed: number;
  
  // Actions
  updateNode: (nodeId: string, updates: Partial<WorkflowNodeState>) => void;
  selectNode: (nodeId: string | null) => void;
  toggleLive: () => void;
  replayWorkflow: () => void;
  exportWorkflow: (format: 'json' | 'png' | 'svg') => void;
}
```

### Node Types

| Type | Icon | Description |
|------|------|-------------|
| planner | Brain | Task planning and decomposition |
| researcher | Search | Information gathering |
| coder | Code | Code implementation |
| reviewer | Eye | Code review |
| tester | TestTube | Testing and QA |
| documentation | FileText | Documentation generation |
| manager | User | Overall coordination |

### Node States

| State | Color | Animation |
|-------|-------|-----------|
| idle | Gray | None |
| running | Blue | Pulse |
| waiting | Yellow | None |
| completed | Green | None |
| failed | Red | None |
| retrying | Orange | Pulse |

### Performance Considerations

- Virtualization for large log lists
- Debounced search updates
- Memoized component rendering
- React Flow optimization for 100+ nodes

---

## Security Components

### Security Dashboard

```
Security Components
├── SecurityDashboard
│   ├── OverviewTab
│   │   ├── SecurityStatsGrid
│   │   └── RecentEventsList
│   ├── AuditLogsTab
│   │   ├── Filters
│   │   └── LogsTable
│   ├── FailedLoginsTab
│   ├── APIKeysTab
│   └── PermissionsTab
```

### Backend Security Modules

```
Backend Security Modules
├── app/security/
│   ├── __init__.py
│   ├── rbac.py
│   │   ├── Roles (Owner, Admin, Developer, Viewer)
│   │   ├── Permissions (30+ granular permissions)
│   │   └── RBACService
│   ├── audit.py
│   │   ├── AuditAction (40+ audited actions)
│   │   ├── AuditLevel (debug, info, warning, error, critical)
│   │   └── AuditService
│   ├── secrets.py
│   │   ├── SecretsManager (Fernet encryption)
│   │   ├── APIKeyManager
│   │   └── SecretsValidator
│   ├── csrf.py
│   │   ├── CSRFService
│   │   └── CSRFProtection
│   ├── validation.py
│   │   ├── InputValidator
│   │   ├── PluginInputValidator
│   │   └── Security validators
│   ├── middleware.py
│   │   ├── SecurityHeadersMiddleware
│   │   ├── RateLimitMiddleware
│   │   └── RequestIDMiddleware
│   └── routes.py
│       ├── Audit Logs API
│       ├── Security Dashboard API
│       └── RBAC Management API
```

### Roles and Permissions

#### Roles

| Role | Description | Permission Count |
|------|-------------|------------------|
| Owner | Full access, can manage billing | All permissions |
| Admin | Full access except billing | ~30 permissions |
| Developer | Can manage projects, sessions, agents | ~20 permissions |
| Viewer | Read-only access | ~12 permissions |

#### Permission Categories

| Category | Permissions |
|----------|------------|
| Projects | read, write, delete, share |
| Sessions | read, write, delete |
| Agents | read, write, execute |
| Plugins | read, write, install, uninstall |
| Memory | read, write, delete |
| Docker | read, execute, manage |
| Terminal | read, execute |
| GitHub | read, write, execute |
| MCP | read, write, execute |
| Settings | read, write, admin |
| Workspace | read, write, share, admin |

### Workspace Permissions

| Permission | Description |
|------------|-------------|
| Private | Only owner can access |
| Shared | Shared with specific users |
| Read Only | Shared users can only read |
| Read/Write | Shared users can read and write |

### Audit Logging

#### Audited Actions

**Authentication:**
- `auth:login`, `auth:logout`, `auth:login_failed`
- `auth:password_change`, `auth:password_reset`

**User Management:**
- `user:create`, `user:update`, `user:delete`
- `user:role_change`, `user:permission_change`

**Projects:**
- `project:create`, `project:update`, `project:delete`
- `project:share`, `project:unshare`

**Docker:**
- `docker:container_start`, `docker:container_stop`, `docker:container_delete`
- `docker:image_pull`

**Terminal:**
- `terminal:execute`, `terminal:command`

**GitHub:**
- `github:connect`, `github:disconnect`, `github:pull`, `github:push`
- `github:pr_create`, `github:pr_merge`

**Security:**
- `security:event`, `security:rate_limit_exceeded`
- `security:csrf_failure`, `security:auth_failure`

### Secrets Encryption

- API keys encrypted with Fernet (AES-128-CBC)
- GitHub tokens encrypted at rest
- OpenAI/Anthropic keys encrypted
- MCP credentials encrypted
- Database credentials encrypted
- Never exposed to frontend

### Security Headers

| Header | Value |
|--------|-------|
| Content-Security-Policy | Strict CSP with self-only sources |
| X-Frame-Options | DENY |
| X-Content-Type-Options | nosniff |
| Strict-Transport-Security | max-age=31536000; includeSubDomains |
| Referrer-Policy | strict-origin-when-cross-origin |
| Permissions-Policy | Disabled features by default |

### Input Validation

- Email format validation
- UUID format validation
- SQL injection detection
- Script injection detection
- Path traversal prevention
- Command injection prevention
- MCP tool input validation
- GitHub webhook validation

### Rate Limiting

- 60 requests per minute (configurable)
- Per-IP rate limiting
- X-RateLimit headers in responses
- Retry-After header on 429

### CSRF Protection

- Token-based CSRF protection
- 1-hour token expiration
- Token validation middleware
- Safe method exemptions (GET, HEAD, OPTIONS)
---

## Shared Components

### ErrorBoundary

Error boundary component for catching React errors.

```typescript
interface ErrorBoundaryProps {
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

// Usage
<ErrorBoundary fallback={<ErrorFallback />}>
  <Component />
</ErrorBoundary>
```

### Skeleton Components

Loading skeleton components for various UI elements.

```typescript
// Available skeletons
<Skeleton />
<FileTreeSkeleton count={6} />
<TabBarSkeleton count={4} />
<EditorSkeleton />
<ChatMessageSkeleton />
<CardSkeleton />
<DashboardSkeleton />
<WorkflowSkeleton />
<SidebarSkeleton />
<LoadingSpinner text="Loading..." size="md" />
<EmptyState
  icon={<FileCode />}
  title="No files"
  description="Create a new file"
  action={<Button>Create</Button>}
/>
```

### CommandPalette

Enhanced command palette with keyboard navigation.

```typescript
interface CommandItem {
  id: string;
  label: string;
  icon?: ReactNode;
  shortcut?: string;
  category?: string;
  action: () => void;
  disabled?: boolean;
}
```

## Hooks

### Keyboard Navigation Hooks

- useKeyboardShortcut - Register keyboard shortcuts
- useFocusManagement - Manage focus states
- useListNavigation - Navigate lists with keyboard
- useEscapeHandler - Handle escape key
- useGlobalKeyboard - Global keyboard shortcuts

### Performance Hooks

- useDebounce - Debounce values
- useThrottle - Throttle values
- useMediaQuery - Media query matching
- useBreakpoint - Responsive breakpoints
- useWindowSize - Window dimensions
- useLocalStorage - Persistent storage
- useAsync - Async state management
- useIntersectionObserver - Element visibility
- useClickOutside - Click detection
- useFocusTrap - Focus containment
