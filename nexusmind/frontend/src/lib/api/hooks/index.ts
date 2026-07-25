import { useQuery } from '@tanstack/react-query';
import { api } from '../client';

export function useAgents() { 
  return useQuery({ queryKey: ['agents'], queryFn: api.agents.list }); 
}

export function useAgent(id: string) { 
  return useQuery({ queryKey: ['agents', id], queryFn: () => api.agents.get(id), enabled: !!id }); 
}

export function useSessions() { 
  return useQuery({ queryKey: ['sessions'], queryFn: () => api.sessions.list() }); 
}

export function useSession(id: string) { 
  return useQuery({ queryKey: ['sessions', id], queryFn: () => api.sessions.get(id), enabled: !!id }); 
}

export function useSessionMessages(sessionId: string) { 
  return useQuery({ queryKey: ['sessions', sessionId, 'messages'], queryFn: () => api.sessions.messages(sessionId), enabled: !!sessionId }); 
}

export function useProjects() { 
  return useQuery({ queryKey: ['projects'], queryFn: api.projects.list }); 
}

export function usePlugins() { 
  return useQuery({ queryKey: ['plugins'], queryFn: api.plugins.list }); 
}

export function useLogs(params?: Record<string, string>) { 
  return useQuery({ queryKey: ['logs', params], queryFn: () => api.logs.list(params) }); 
}

export function useModels() { 
  return useQuery({ queryKey: ['models'], queryFn: api.routing.models }); 
}
