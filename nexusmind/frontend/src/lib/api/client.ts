import type { Agent, Session, Message, Project, Plugin, MemoryItem, LogEntry, Model } from '@/types';

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
};
