// Core Types

export type AgentStatus = 'idle' | 'running' | 'paused' | 'error' | 'completed';
export type AgentType = 'planner' | 'researcher' | 'coder' | 'reviewer' | 'tester' | 'documentation' | 'manager';
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';
export type SessionStatus = 'active' | 'paused' | 'completed';

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
  name: string;
  projectId?: string;
  status: SessionStatus;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
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
