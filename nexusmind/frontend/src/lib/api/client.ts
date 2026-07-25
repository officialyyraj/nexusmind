import type { Agent, Session, Message, Project, Plugin, MemoryItem, LogEntry, Model, 
                 MCPServerConfig, MCPServerInfo, MCPServerHealth, MCPTool, MCPToolInvocationResult, MCPStatus } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

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
};
