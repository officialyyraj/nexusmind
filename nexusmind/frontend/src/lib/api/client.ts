import type { Agent, Session, Message, Project, Plugin, MemoryItem, LogEntry, Model, 
                 MCPServerConfig, MCPServerInfo, MCPServerHealth, MCPTool, MCPToolInvocationResult, MCPStatus } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  agents: {
    list: () => request<Agent[]>('/agents'),
    get: (id: string) => request<Agent>(`/agents/${id}`),
    create: (data: Partial<Agent>) => request<Agent>('/agents', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: string, data: Partial<Agent>) => request<Agent>(`/agents/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
    delete: (id: string) => request<void>(`/agents/${id}`, { method: 'DELETE' }),
  },
  sessions: {
    list: (params?: Record<string, string>) => request<Session[]>(`/sessions?${new URLSearchParams(params)}`),
    get: (id: string) => request<Session>(`/sessions/${id}`),
    create: (data: Partial<Session>) => request<Session>('/sessions', { method: 'POST', body: JSON.stringify(data) }),
    messages: (id: string, params?: Record<string, string>) => request<Message[]>(`/sessions/${id}/messages?${new URLSearchParams(params)}`),
    send: (id: string, content: string) => request<Message>(`/sessions/${id}/messages`, { method: 'POST', body: JSON.stringify({ content }) }),
  },
  projects: {
    list: () => request<Project[]>('/projects'),
    get: (id: string) => request<Project>(`/projects/${id}`),
    create: (data: Partial<Project>) => request<Project>('/projects', { method: 'POST', body: JSON.stringify(data) }),
  },
  plugins: {
    list: () => request<Plugin[]>('/plugins'),
    get: (id: string) => request<Plugin>(`/plugins/${id}`),
    enable: (id: string) => request<void>(`/plugins/${id}/enable`, { method: 'POST' }),
    disable: (id: string) => request<void>(`/plugins/${id}/disable`, { method: 'POST' }),
  },
  memory: {
    search: (query: string) => request<MemoryItem[]>('/memory/search?q=' + encodeURIComponent(query)),
    get: (id: string) => request<MemoryItem>(`/memory/${id}`),
  },
  logs: {
    list: (params?: Record<string, string>) => request<LogEntry[]>('/logs?' + new URLSearchParams(params)),
  },
  routing: {
    models: () => request<Model[]>('/routing/models'),
    route: (taskType: string) => request<{ model: Model }>('/routing/route', { method: 'POST', body: JSON.stringify({ taskType }) }),
  },
  mcp: {
    // Server management
    listServers: () => request<MCPServerInfo[]>('/mcp/servers'),
    listServerConfigs: () => request<MCPServerConfig[]>('/mcp/servers/configs'),
    getServer: (name: string) => request<MCPServerInfo>(`/mcp/servers/${name}`),
    addServer: (config: MCPServerConfig) => request<MCPServerInfo>('/mcp/servers', { 
      method: 'POST', 
      body: JSON.stringify(config) 
    }),
    removeServer: (name: string) => request<void>(`/mcp/servers/${name}`, { method: 'DELETE' }),
    startServer: (name: string) => request<MCPServerInfo>(`/mcp/servers/${name}/start`, { method: 'POST' }),
    stopServer: (name: string) => request<void>(`/mcp/servers/${name}/stop`, { method: 'POST' }),
    restartServer: (name: string) => request<MCPServerInfo>(`/mcp/servers/${name}/restart`, { method: 'POST' }),
    enableServer: (name: string) => request<MCPServerInfo>(`/mcp/servers/${name}/enable`, { method: 'POST' }),
    disableServer: (name: string) => request<void>(`/mcp/servers/${name}/disable`, { method: 'POST' }),
    
    // Tool management
    listTools: (serverName?: string) => request<MCPTool[]>(serverName ? `/mcp/tools?server_name=${serverName}` : '/mcp/tools'),
    getTool: (name: string) => request<MCPTool>(`/mcp/tools/${name}`),
    discoverTools: (serverName: string) => request<MCPTool[]>(`/mcp/tools/${serverName}/discover`, { method: 'POST' }),
    executeTool: (name: string, args?: Record<string, unknown>, timeout?: number) => 
      request<MCPToolInvocationResult>('/mcp/tools/' + name + '/execute', { 
        method: 'POST', 
        body: JSON.stringify({ arguments: args, timeout }) 
      }),
    
    // Health and status
    getStatus: () => request<MCPStatus>('/mcp/status'),
    getHealth: (serverName?: string) => request<MCPServerHealth | MCPServerHealth[]>(
      serverName ? `/mcp/health?server_name=${serverName}` : '/mcp/health'
    ),
    
    // Bulk operations
    startAllServers: () => request<MCPServerInfo[]>('/mcp/start-all', { method: 'POST' }),
    stopAllServers: () => request<void>('/mcp/stop-all', { method: 'POST' }),
  },
  executions: {
    list: (params?: { sessionId?: string; state?: string; limit?: number; offset?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.sessionId) searchParams.set('session_id', params.sessionId);
      if (params?.state) searchParams.set('state', params.state);
      if (params?.limit) searchParams.set('limit', String(params.limit));
      if (params?.offset) searchParams.set('offset', String(params.offset));
      return request<{ executions: unknown[]; total: number; limit: number; offset: number }>(
        `/executions?${searchParams}`
      );
    },
    get: (id: string) => request<unknown>(`/executions/${id}`),
    getSteps: (id: string) => request<unknown[]>(`/executions/${id}/steps`),
    getLogs: (id: string, limit = 100, offset = 0) => request<unknown[]>(
      `/executions/${id}/logs?limit=${limit}&offset=${offset}`
    ),
    create: (data: { sessionId?: string; task: string; prompt?: string; agentTypes?: string[]; maxRetries?: number }) =>
      request<unknown>('/executions', { method: 'POST', body: JSON.stringify(data) }),
    cancel: (id: string) => request<unknown>(`/executions/${id}/cancel`, { method: 'POST' }),
    pause: (id: string) => request<unknown>(`/executions/${id}/pause`, { method: 'POST' }),
    resume: (id: string) => request<unknown>(`/executions/${id}/resume`, { method: 'POST' }),
    retry: (id: string) => request<unknown>(`/executions/${id}/retry`, { method: 'POST' }),
  },
  sandbox: {
    list: () => request<unknown[]>('/sandbox'),
    allocate: (data: { image?: string; workspace?: string }) => 
      request<unknown>('/sandbox/allocate', { method: 'POST', body: JSON.stringify(data) }),
    getStatus: (id: string) => request<{ id: string; status: string }>(`/sandbox/${id}/status`),
    listFiles: (sandboxId: string, path = '/workspace') => 
      request<{ files: { name: string; path: string; type: string; size?: number }[] }>(
        `/${sandboxId}/files?path=${encodeURIComponent(path)}`
      ),
    readFile: (sandboxId: string, path: string) => 
      request<{ sandboxId: string; path: string; content: string }>(`/${sandboxId}/files/${encodeURIComponent(path)}`),
    writeFile: (sandboxId: string, path: string, content: string) => 
      request<{ sandboxId: string; path: string; written: boolean }>(
        `/${sandboxId}/files`, 
        { method: 'POST', body: JSON.stringify({ path, content }) }
      ),
    execute: (sandboxId: string, command: string, timeout = 300) => 
      request<unknown>(`/${sandboxId}/execute`, { 
        method: 'POST', 
        body: JSON.stringify({ command, timeout }) 
      }),
    release: (id: string) => request<unknown>(`/sandbox/${id}`, { method: 'DELETE' }),
  },
  monitoring: {
    health: () => request<{ status: string; service: string; version: string }>('/health'),
    metrics: () => request<unknown>('/metrics'),
  },
};

// WebSocket URL helper
export function getWebSocketUrl(sessionId?: string): string {
  if (sessionId) {
    return `${WS_BASE}/ws/sessions/${sessionId}`;
  }
  return `${WS_BASE}/ws`;
}
