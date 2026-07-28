// Core Types

export type AgentStatus = 'idle' | 'running' | 'paused' | 'error' | 'completed';
export type AgentType = 'planner' | 'researcher' | 'coder' | 'reviewer' | 'tester' | 'documentation' | 'manager';
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';
export type SessionStatus = 'active' | 'paused' | 'completed';
export type TransportType = 'stdio' | 'http' | 'sse';
export type ServerStatus = 'stopped' | 'starting' | 'running' | 'error';

export interface Agent {
  id: string;
  name: string;
  type: AgentType;
  status: AgentStatus;
  model: string;
  currentTask?: string;
  progress?: number;
  startedAt?: string;
  elapsedTime?: number;
  currentTool?: string;
  tokenUsage?: TokenUsage;
  cpuUsage?: number;
  memoryUsage?: number;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: number;
  assignedAgent?: string;
  dependencies: string[];
  createdAt: string;
  completedAt?: string;
}

export interface Session {
  id: string;
  title: string | null;
  status: string;
  created_at: string | null;
  updated_at: string | null;
  agent_states?: Record<string, unknown>;
  context?: Record<string, unknown>;
}

export interface Message {
  id: string;
  sessionId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  attachments?: Attachment[];
  artifacts?: Artifact[];
  citations?: Citation[];
}

export interface Attachment {
  type: 'file' | 'image' | 'code';
  name: string;
  url: string;
}

export interface Artifact {
  type: 'code' | 'table' | 'diagram' | 'chart';
  language?: string;
  content: string;
  title?: string;
}

export interface Citation {
  source: string;
  url: string;
  text: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  createdAt: string;
  updatedAt: string;
  sessionCount: number;
}

export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  cost: number;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  source: string;
  message: string;
  metadata?: Record<string, unknown>;
}

export interface Plugin {
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;
  status: 'installed' | 'enabled' | 'disabled' | 'error';
  pluginType: 'tool' | 'agent' | 'workflow' | 'api' | 'ui_panel';
  permissions: string[];
}

export interface MemoryItem {
  id: string;
  type: 'fact' | 'preference' | 'context' | 'knowledge';
  content: string;
  embedding?: number[];
  createdAt: string;
  accessedAt: string;
  accessCount: number;
}

export interface WorkflowNode {
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

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  type?: 'default' | 'success' | 'error' | 'condition';
  label?: string;
}

export interface Model {
  id: string;
  name: string;
  provider: 'ollama' | 'openai' | 'anthropic';
  contextLength: number;
  capabilities: string[];
  costPer1kInput: number;
  costPer1kOutput: number;
  enabled: boolean;
}

export interface Metric {
  name: string;
  value: number;
  unit: string;
  timestamp: string;
}

export interface DockerContainer {
  id: string;
  name: string;
  image: string;
  status: 'running' | 'stopped' | 'paused';
  ports: string[];
  createdAt: string;
}

export interface GitBranch {
  name: string;
  isDefault: boolean;
  isProtected: boolean;
  lastCommit: string;
}

export interface GitCommit {
  hash: string;
  message: string;
  author: string;
  timestamp: string;
}

// Workflow and Agent Visualization Types

export type NodeStatus = 'idle' | 'running' | 'waiting' | 'completed' | 'failed' | 'retrying';
export type ExecutionPhase = 'start' | 'planning' | 'research' | 'coding' | 'review' | 'testing' | 'documentation' | 'complete';

export interface WorkflowExecution {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  startedAt: string;
  completedAt?: string;
  duration?: number;
  nodes: WorkflowNodeState[];
  edges: WorkflowEdgeState[];
  currentNode?: string;
  progress: number;
  projectId?: string;
  sessionId?: string;
  model?: string;
}

export interface WorkflowNodeState {
  id: string;
  name: string;
  type: 'planner' | 'researcher' | 'coder' | 'reviewer' | 'tester' | 'documentation' | 'manager' | 'input' | 'output' | 'condition' | 'tool';
  status: NodeStatus;
  position: { x: number; y: number };
  assignedAgent?: string;
  currentTask?: string;
  currentTool?: string;
  progress: number;
  retryCount: number;
  maxRetries: number;
  startedAt?: string;
  completedAt?: string;
  duration?: number;
  output?: string;
  error?: string;
  tokenUsage?: TokenUsage;
  memoryLookups?: MemoryAccess[];
  recentActions?: Action[];
  logs?: string[];
}

export interface WorkflowEdgeState {
  id: string;
  source: string;
  target: string;
  status: 'pending' | 'active' | 'completed' | 'skipped';
  type?: 'default' | 'success' | 'error' | 'condition';
  label?: string;
}

export interface AgentInspector {
  id: string;
  name: string;
  type: string;
  model: string;
  status: NodeStatus;
  currentTask?: string;
  currentTool?: string;
  memoryLookups: MemoryAccess[];
  tokenUsage?: TokenUsage;
  duration?: number;
  recentActions: Action[];
  output?: string;
  errors: string[];
  metrics: AgentMetrics;
}

export interface MemoryAccess {
  id: string;
  type: 'fact' | 'preference' | 'context' | 'knowledge';
  content: string;
  accessedAt: string;
  accessCount: number;
}

export interface Action {
  id: string;
  type: 'tool' | 'memory' | 'file' | 'message' | 'decision';
  description: string;
  timestamp: string;
  duration?: number;
  success: boolean;
  details?: Record<string, unknown>;
}

export interface AgentMetrics {
  cpuUsage: number;
  memoryUsage: number;
  tokensPerSecond?: number;
  tasksCompleted: number;
  tasksFailed: number;
}

export interface TimelineEvent {
  id: string;
  phase: ExecutionPhase;
  nodeId?: string;
  nodeName?: string;
  status: 'started' | 'completed' | 'failed' | 'skipped';
  timestamp: string;
  duration?: number;
  details?: string;
}

export interface LogCorrelation {
  logId: string;
  nodeId: string;
  nodeName: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  timestamp: string;
  relatedFiles?: string[];
  relatedMemory?: string[];
  relatedTools?: string[];
}

export interface WorkflowFilter {
  agentIds?: string[];
  statuses?: NodeStatus[];
  projectId?: string;
  sessionId?: string;
  model?: string;
  searchQuery?: string;
}

export interface WorkflowExport {
  format: 'json' | 'png' | 'svg';
  includeLogs: boolean;
  includeMetrics: boolean;
  includeTimeline: boolean;
}

// MCP Types

export interface MCPServerConfig {
  name: string;
  transport: TransportType;
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  url?: string;
  headers?: Record<string, string>;
  enabled: boolean;
  trusted: boolean;
  auto_reconnect: boolean;
  health_check_interval: number;
  timeout: number;
  allowlist: string[];
  blocklist: string[];
}

export interface MCPServerInfo {
  name: string;
  status: ServerStatus;
  transport: TransportType;
  tools_count: number;
  started_at?: string;
  last_error?: string;
  trusted: boolean;
  allowlist: string[];
  blocklist: string[];
}

export interface MCPServerHealth {
  server_name: string;
  healthy: boolean;
  latency_ms?: number;
  last_check?: string;
  error?: string;
}

export interface MCPToolParameter {
  name: string;
  type: string;
  description?: string;
  required: boolean;
  default?: unknown;
  enum?: unknown[];
}

export interface MCPTool {
  name: string;
  description: string;
  server_name: string;
  input_schema: Record<string, unknown>;
  parameters: MCPToolParameter[];
  version?: string;
  tags: string[];
  permissions: string[];
  metadata: Record<string, unknown>;
}

export interface MCPToolInvocationResult {
  success: boolean;
  tool_name: string;
  result?: unknown;
  error?: string;
  execution_time: number;
  server_name: string;
}

export interface MCPStatus {
  enabled: boolean;
  initialized: boolean;
  servers: {
    total: number;
    running: number;
    error: number;
  };
  tools: {
    total: number;
    by_server: Record<string, number>;
  };
}

export interface MCPConfig {
  enabled: boolean;
  servers: MCPServerConfig[];
  default_timeout: number;
  auto_discover: boolean;
}
